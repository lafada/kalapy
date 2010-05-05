"""This module defines field classes to define relationship like many-to-one,
one-to-one, many-to-one and many-to-many between models.
"""


from _fields import Field
from _model import get_model, get_models, Model
from _query import Query
from _errors import FieldError, DuplicateFieldError


__all__ = ('ManyToOne', 'OneToOne', 'OneToMany', 'ManyToMany')


class IRelation(Field):
    """This class defines an interface method prepare which will called
    once all defined models are loaded. So the field would have chance
    to resolve early lookup references.
    """

    def __init__(self, reference, **kw):
        super(IRelation, self).__init__(**kw)
        self._reference = reference

    def prepare(self, model_class):
        """The relation field should implement this method to implement
        support code as at this point all the models will be resolved.
        """
        pass

    @property
    def reference(self):
        """Returns the reference class.
        """
        return get_model(self._reference, self.model_class._meta.package)

    @property
    def is_virtual(self):
        return self._data_type is None


class ManyToOne(IRelation):
    """ManyToOne field represents many-to-one relationship with other model.

    For example, a ManyToOne field defined in model A that refers to model B forms
    a many-to-one relationship from A to B. Every instance of B refers to a single
    instance of A and every instance of A can have many instances of B that refer
    it.

    A reverse lookup field will be automatically created in the reference model.
    In this case, a field `a_set` of type `OneToMany` will be automatically created
    on class B referencing class A.
    """

    _data_type = 'integer'

    def __init__(self, reference, reverse_name=None, cascade=False, **kw):
        """Create a new ManyToOne field referencing the given `reference` model.

        A reverse lookup field of type OneToMany will be created on the referenced
        model if it doesn't exist.

        Args:
            reference: reference model class
            reverse_name: name of the reverse lookup field in the referenced model
            cascade: None = set null, False = restrict and True = cascade
            **kw: other field params
        """
        super(ManyToOne, self).__init__(reference, **kw)
        self.reverse_name = reverse_name
        self.cascade = cascade

    def prepare(self, model_class, reverse_name=None, reverse_class=None):

        if not self.reverse_name:
            self.reverse_name = reverse_name or ('%s_set' % model_class.__name__.lower())

        if hasattr(self.reference, self.reverse_name):
            try:
                if getattr(self.reference, self.reverse_name).reverse_name == self.name:
                    return
            except:
                pass
            raise DuplicateFieldError('field %r already defined in referenced model %r' % (
                self.reverse_name, self.reference.__name__))

        c = reverse_class or OneToMany
        f = c(model_class, name=self.reverse_name, reverse_name=self.name)
        self.reference._meta.contribute_to_class(self.reference, f.name, f)

    def __get__(self, model_instance, model_class):
        return super(ManyToOne, self).__get__(model_instance, model_class)
        
    def __set__(self, model_instance, value):
        if value is not None and not isinstance(value, self.reference):
            raise ValueError("ManyToOne field %r value should be an instance of %r" % (
                self.name, self._reference.__name__))
        super(ManyToOne, self).__set__(model_instance, value)

    def to_database_value(self, model_instance):
        value = super(ManyToOne, self).to_database_value(model_instance)
        if isinstance(value, Model):
            return value.key
        return value

    def from_database_value(self, model_instance, value):
        if value is not None:
            return self.reference.get(value)
        return value


class OneToOne(ManyToOne):
    """OneToOne is basically ManyToOne with unique constraint.
    """
    def __init__(self, reference, reverse_name=None, cascade=False, **kw):
        kw['unique'] = True
        super(OneToOne, self).__init__(reference, reverse_name, cascade, **kw)

    def __set__(self, model_instance, value):
        super(OneToOne, self).__set__(model_instance, value)
        setattr(value, self.reverse_name, model_instance)

    def prepare(self, model_class):
        super(OneToOne, self).prepare(model_class, 
                reverse_name=model_class.__name__.lower(),
                reverse_class=O2ORel)

class O2ORel(IRelation):
    """OneToOne reverse lookup field to prevent recursive
    dependencies.
    """

    _data_type = None

    def __init__(self, reference, reverse_name, **kw):
        super(O2ORel, self).__init__(reference, **kw)
        self.reverse_name = reverse_name

    def __get__(self, model_instance, model_class):

        if model_instance is None:
            return self

        try: # if already fetched
            return model_instance._values[self.name]
        except:
            pass

        if model_instance.saved:
            value = self.reference.filter('%s == :key' % self.reverse_name,
                        key=model_instance.key).fetch(1)[0]
            model_instance._values[self.name] = value
            return value

        return None

    def __set__(self, model_instance, value):

        if model_instance is None:
            raise AttributeError('%r must be accessed with model instance' % (self.name))

        if not isinstance(value, self.reference):
            raise TypeError('Expected %r instance' % (self.reference._meta.name))

        super(O2ORel, self).__set__(model_instance, value)
        if getattr(value, self.reverse_name, None) != model_instance:
            setattr(value, self.reverse_name, model_instance)

    def prepare(self, model_class):
        pass


class O2MSet(object):
    """A descriptor class to access OneToMany fields.
    """

    def __init__(self, field, instance):
        self.__field = field
        self.__obj = instance
        self.__ref = field.reference
        self.__ref_field = getattr(field.reference, field.reverse_name)

    def __check(self, *objs):
        for obj in objs:
            if not isinstance(obj, self.__ref):
                raise TypeError('%s instances required' % (self.__ref._meta.name))
        if not self.__obj.saved:
            self.__obj.save()
        return objs

    def all(self):
        """Returns a `Query` object pre-filtered to return related objects.
        """
        self.__check()
        return self.__ref.filter('%s == :key' % (self.__field.reverse_name),
                key=self.__obj.key)

    def add(self, *objs):
        """Add new instances to the reference set.

        Raises:
            TypeError: if any given object is not an instance of referenced model
        """
        for obj in self.__check(*objs):
            setattr(obj, self.__field.reverse_name, self.__obj)
            obj.save()

    def remove(self, *objs):
        """Removes the provided instances from the reference set.
        
        Raises:
            FieldError: if referenced instance field is required field.
            TypeError: if any given object is not an instance of referenced model
        """
        if self.__ref_field.required:
            raise FieldError("objects can't be removed from %r, delete the objects instead." % (
                self.__field.name))
        
        from rapido.db.engines import database

        keys = [obj.key for obj in self.__check(*objs) if obj.key]
        database.delete_from_keys(self.__ref, keys)

    def clear(self):
        """Removes all referenced instances from the reference set.

        Raises:
            FieldError: if referenced instance field is required field.
            TypeError: if any given object is not an instance of referenced model
        """
        if not self.__obj.saved:
            return

        if self.__ref_field.required:
            raise FieldError("objects can't be removed from %r, \
                    delete the objects instead." % (
                self.__field.name))

        from rapido.db.engines import database

        # instead of removing records at once remove them in bunches
        l = 100
        q = self.all()
        result = q.fetch(l)
        while result:
            database.delete_from_keys(self.__ref, [o.key for o in result])
            result = q.fetch(l)


class M2MSet(object):
    """A descriptor class to access ManyToMany field.
    """

    def __init__(self, field, instance):
        self.__field = field
        self.__obj = instance
        self.__ref = field.reference
        self.__m2m = field.m2m

        self.__source_in = '%s in :keys' % field.source
        self.__target_in = '%s in :keys' % field.target
        self.__source_eq = '%s == :key' % field.source

    def __check(self, *objs):
        for obj in objs:
            if not isinstance(obj, self.__ref):
                raise TypeError('%s instances required' % (self.__ref._meta.name))
        if not self.__obj.saved:
            self.__obj.save()
        return objs

    def all(self):
        """Returns a `Query` object pre-filtered to return related objects.
        """
        self.__check()
        return Query(self.__m2m, lambda obj: getattr(obj, self.__field.target)).filter(
                self.__source_eq, key=self.__obj.key)

    def add(self, *objs):
        """Add new instances to the reference set.

        Raises:
            TypeError: if any given object is not an instance of referenced model
            ValueError: if any of the given object is not saved
        """
        keys = [obj.key for obj in self.__check(*objs) if obj.key]

        existing = self.all().filter(self.__target_in, keys=keys).fetch(-1)
        existing = [o.key for o in existing]

        for obj in objs:
            if obj.key in existing:
                continue
            if not obj.saved:
                obj.save()
            m2m = self.__m2m()
            setattr(m2m, self.__field.source, self.__obj)
            setattr(m2m, self.__field.target, obj)
            m2m.save()

    def remove(self, *objs):
        """Removes the provided instances from the reference set.
        
        Raises:
            TypeError: if any given object is not an instance of referenced model
        """
        keys = [obj.key for obj in self.__check(*objs) if obj.key]

        from rapido.db.engines import database
        database.delete_from_keys(self.__m2m, keys)

    def clear(self):
        """Removes all referenced instances from the reference set.
        """
        if not self.__obj.saved:
            return

        from rapido.db.engines import database

        # instead of removing records at once remove them in bunches
        l = 100
        q = self.all()
        result = q.fetch(l)
        while result:
            database.delete_from_keys(self.__m2m, [o.key for o in result])
            result = q.fetch(l)


class OneToMany(IRelation):
    """OneToMany field represents one-to-many relationship with other model.

    For example, a OneToMany field defined in model A that refers to model B forms
    a one-to-many relationship from A to B. Every instance of B refers to a single
    instance of A and every instance of A can have many instances of B that refer
    it.

    A reverse lookup field will be automatically created in the reference model.
    In this case, a field `a` of type `ManyToOne` will be automatically created
    on class B referencing class A.
    """

    _data_type = None

    def __init__(self, reference, reverse_name=None, **kw):
        super(OneToMany, self).__init__(reference, **kw)
        self.reverse_name = reverse_name

    def prepare(self, model_class):

        if not self.reverse_name:
            self.reverse_name = model_class.__name__.lower()
        
        if hasattr(self.reference, self.reverse_name):
            try:
                if getattr(self.reference, self.reverse_name).reverse_name == self.name:
                    return
            except:
                pass
            raise DuplicateFieldError('field %r already defined in referenced model %r' % (
                self.reverse_name, self.reference.__name__))

        f = ManyToOne(model_class, self.name, name=self.reverse_name)
        self.reference._meta.contribute_to_class(self.reference, f.name, f)

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        return O2MSet(self, model_instance)

    def __set__(self, model_instance, value):
        raise ValueError("Field %r is readonly." % self.name)


class ManyToMany(IRelation):
    """ManyToMany field represents many-to-many relationship with other model.

    For example, a ManyToMany field defined in model A that refers to model B
    forms a many-to-many relationship from A to B. Every instance of A can have
    many instances of B referenced by an intermediary model that also refers
    model A.

    Removing an instance of B from M2MSet will delete instances of the 
    intermediary model and thus breaking the many-to-many relationship.
    """

    _data_type = None

    def __init__(self, reference, reverse_name=None, **kw):
        super(ManyToMany, self).__init__(reference, **kw)
        self.reverse_name = reverse_name

    def get_reverse_field(self):

        if self.reverse_name is None:
            self.reverse_name = '%s_set' % (self.model_class.__name__.lower())

        if not self.reverse_name:
            return None

        reverse_field = getattr(self.reference, self.reverse_name, None)
        
        if reverse_field and reverse_field.reverse_name != self.name:
            raise DuplicateFieldError('field %r already defined in referenced model %r' % (
                self.reverse_name, self.reference.__name__))

        return reverse_field

    def prepare(self, model_class):

        reverse_field = self.get_reverse_field()

        if not reverse_field:

            from _model import ModelType, Model

            #create intermediary model

            name = '%s_%s' % (model_class.__name__.lower(), self.name)

            cls = ModelType(name, (Model,), {
                '__module__': model_class.__module__
            })

            cls._meta.contribute_to_class(cls, 'source', ManyToOne(model_class, name='source'))
            cls._meta.contribute_to_class(cls, 'target', ManyToOne(self.reference, name='target'))

            cls._meta.ref_models = [model_class, self.reference]

            self.m2m = cls
            self.source = 'source'
            self.target = 'target'
        else:
            self.m2m = reverse_field.m2m
            self.source = 'target'
            self.target = 'source'

        if not reverse_field and self.reverse_name:
            # create reverse lookup field
            f = ManyToMany(model_class, reverse_name=self.name, name=self.reverse_name)
            self.reference._meta.contribute_to_class(self._reference, f.name, f)
            f.prepare(self.reference)

    def __get__(self, model_instance, model_class):

        if model_instance is None:
            return self

        #if not model_instance.saved:
        #    raise AttributeError('%r can\'t be accessed unless instance is saved' % self.name)

        return M2MSet(self, model_instance)

    def __set__(self, model_instance, value):
        raise ValueError('Field %r is read-only' % (self.name))

