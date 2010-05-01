
from _fields import Field
from _model import get_model, get_models, Model
from _errors import DuplicateFieldError


__all__ = ('ManyToOne', 'OneToOne', 'OneToMany')



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
        return self.reference.filter('%s == :key' % self.reverse_name, 
                key=model_instance.key)

    def __set__(self, model_instance, value):
        raise ValueError("Field %r is readonly." % self.name)


