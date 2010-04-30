
from _fields import Field
from _model import get_model, get_models, Model


__all__ = ('Reference', 'Collection')


class Reference(Field):

    def __init__(self, reference, collection_name=None, cascade=None, **kw):
        super(Reference, self).__init__(**kw)
        self._reference = reference
        self.collection_name = collection_name
        self.cascade = cascade

    @property
    def reference(self):
        return get_model(self._reference)

    def __get__(self, model_instance, model_class):
        return super(Reference, self).__get__(model_instance, model_class)
        
    def __set__(self, model_instance, value):
        if value is not None and not isinstance(value, self.reference):
            raise ValueError("Reference field %r value should be an instance of %r" % (
                self.name, self._reference.__name__))
        super(Reference, self).__set__(model_instance, value)

    def to_database_value(self, model_instance):
        value = super(Reference, self).to_database_value(model_instance)
        if isinstance(value, Model):
            return value.key
        return value

    def from_database_value(self, model_instance, value):
        if value is not None:
            return self.reference.get(value)
        return value


class Collection(Field):

    def __init__(self, reference, reference_name=None, **kw):
        super(Collection, self).__init__(**kw)
        self._reference = reference
        self._reference_name = reference_name

