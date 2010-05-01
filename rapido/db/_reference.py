
from _fields import Field
from _model import get_model, get_models, Model
from _errors import FieldError, DuplicateFieldError


__all__ = ('ManyToOne', 'OneToOne', 'OneToMany', 'ManyToMany')



class IRelation(object):

    is_reference_field = True

    def prepare(self, model_class):
        pass


class ManyToOne(Field, IRelation):
    """ManyToOne field represents either many-to-one relationship with other model.
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
        super(ManyToOne, self).__init__(**kw)
        self._reference = reference
        self.reverse_name = reverse_name
        self.cascade = cascade

    @property
    def reference(self):
        return get_model(self._reference)

    def prepare(self, model_class):

        if not self.reverse_name:
            self.reverse_name = '%s_set' % model_class.__name__.lower()
        
        if hasattr(self.reference, self.reverse_name):
            try:
                if getattr(self.reference, self.reverse_name).reverse_name == self.name:
                    return
            except:
                pass
            raise DuplicateFieldError('field %r aleady defined in referenced model %r' % (
                self.reverse_name, self.reference.__name__))

        f = OneToMany(model_class, self.name, name=self.reverse_name)
        self.reference.add_field(f)

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


class OneToMany(Field, IRelation):

    _data_type = None

    def __init__(self, reference, reverse_name=None, **kw):
        super(OneToMany, self).__init__(**kw)
        self._ref = reference
        self.reverse_name = reverse_name

    @property
    def reference(self):
        return get_model(self._ref)

    def prepare(self, model_class):

        if not self.reverse_name:
            self.reverse_name = model_class.__name__.lower()
        
        if hasattr(self.reference, self.reverse_name):
            try:
                if getattr(self.reference, self.reverse_name).reverse_name == self.name:
                    return
            except:
                pass
            raise DuplicateFieldError('field %r aleady defined in referenced model %r' % (
                self.reverse_name, self.reference.__name__))

        f = ManyToOne(model_class, self.name, name=self.reverse_name)
        self.reference.add_field(f)

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        return O2MSet(self, model_instance)

    def __set__(self, model_instance, value):
        raise ValueError("Field %r is readonly." % self.name)


class O2MSet(object):

    def __init__(self, field, instance):
        self.__field = field
        self.__obj = instance
        self.__ref = field.reference
        self.__ref_field = getattr(field.reference, field.reverse_name)

    def all(self):
        return self.__ref.filter('%s == :key' % (self.__field.reverse_name),
                key=self.__obj.key)

    def add(self, *objs):
        for obj in objs:
            if not isinstance(obj, self.__ref):
                raise TypeError('%r instance expected.' % self.__ref._model_name)
            setattr(obj, self.__field.reverse_name, self.__obj)
            obj.save()

    def remove(self, *objs):
        if self.__ref_field.required:
            raise FieldError("objects can't be removed from %r, delete the objects instead." % (
                self.__field.name))
        for obj in objs:
            if not isinstance(obj, self.__ref):
                raise TypeError('%r instances expected.' % self.__ref._model_name)
        from rapido.db.engines import database
        database.delete_from_keys(self.__ref, [obj.key for obj in objs if obj.key])

    def clear(self):
        if self.__ref_field.required:
            raise FieldError("objects can't be removed from %r, delete the objects instead." % (
                self.__field.name))

        # instead of removing records at once remove them in bunches
        l = 100
        q = self.all()
        result = q.fetch(l)
        while result:
            self.remove(*result)
            result = q.fetch(l)


class M2MSet(object):

    def __init__(self, field, instance):
        self.__field = field
        self.__obj = instance
        self.__ref = field.reference
        self.__m2m = field.m2m

        if not instance.key:
            raise ValueError('Model instance must be saved before using ManyToMany field.')

    def filter(self, query, **params):
        q = self.__m2m.filter('source == :key', key=self.__obj.key)
        if not query:
            return q
        return q.filter(query, **params)

    def objects(self, limit, offset=0):
        query = self.filter(None)
        objects = [o.target for o in query.fetch(limit, offset)]
        return objects

    def add(self, *objs):

        for obj in objs:
            if not isinstance(obj, self.__ref):
                raise TypeError('%s instances required' % (self.__ref._model_name))
            if not obj.key:
                raise ValueError('%r instances must me saved before using with ManyToMany field %r' % (
                    obj.__class__._model_name, self.__field.name))
        
        existing = [o.target for o in self.filter(None)]
        for obj in objs:
            if obj.key in existing:
                continue
            m2m = self.__m2m()
            m2m.source = self.__obj
            m2m.target = obj
            m2m.save()

    def remove(self, *objs):
        for obj in objs:
            if not isinstance(obj, self.__ref):
                raise TypeError('%s instances required' % (self.__ref._model_name))

        keys = [obj.key for obj in objs if obj.key]
        keys = [obj.key for obj in self.filter(None) if obj.target.key in keys]

        from rapido.db.engines import database
        database.delete_from_keys(self.__m2m, keys)

    def clear(self):
        # instead of removing records at once remove them in bunches
        l = 100
        result = self.objects(l)
        while result:
            self.remove(*result)
            result = self.objects(l)


class ManyToMany(Field, IRelation):

    _data_type = None

    def __init__(self, reference, **kw):
        super(ManyToMany, self).__init__(**kw)
        self._ref = reference

    @property
    def reference(self):
        return get_model(self._ref)

    def prepare(self, model_class):

        from _model import ModelType, Model

        #create intermediatory model
        cls = ModelType(self.get_m2m_name(), (Model,), {'__module__': model_class.__module__})
        cls.add_field(ManyToOne(model_class, name='source'))
        cls.add_field(ManyToOne(self.reference, name='target'))

        #XXX: create reverse lookup fields?
        #cls.source.prepare(cls)
        #cls.target.prepare(cls)

        self.m2m = cls

    def get_m2m_name(self):
        return '%s_%s' % (self.model_class._model_name.replace('.', '_'),
                          self.name)

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        return M2MSet(self, model_instance)

    def __set__(self, model_instance, value):
        raise ValueError('Field %r is read-only' % (self.name))

