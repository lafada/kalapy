
from _fields import *


_REGISTRY = {}


def get(model):

    if isinstance(model, Model):
        return model

    # TODO: raise model doesn't exist
    return _REGISTRY[model]


class DuplicateFieldError(Exception):
    pass


class ModelType(type):
    
    def __init__(cls, name, bases, attrs):

        super(ModelType, cls).__init__(name, bases, attrs)

        cls._fields = ModelType.get_fields(cls, bases, attrs)

        _REGISTRY[name] = cls

    @staticmethod
    def get_fields(cls, bases, attrs):

        fields = {}

        for base in bases:
            defined = getattr(base, '_fields', {})
            for name, field in defined.items():
                if name in fields:
                    raise DuplicateFieldError("Duplicate field, %s, is inherited from both %s and %s." % (
                            name, fields[name].model_class.__name__, field.model_class.__name__))
            fields.update(defined)

        for name, attr in attrs.items():
            if isinstance(attr, Field):
                if name in fields:
                    raise DuplicateFieldError("Duplicate field, %s, is inherited from %s." % (
                            name, fields[name].model_class.__name__))
                fields[name] = attr
                attr.__configure__(cls, name)

        return fields


class Model(object):
    
    __metaclass__ = ModelType

    _name = None

    def __init__(self, **kw):
        pass

    @property
    def key(self):
        pass
    
    def put(self):
        pass
    
    def delete(self):
        pass

    @property
    def json(self):
        pass
    
    @classmethod
    def get(cls, keys):
        pass
        
    @classmethod
    def filter(cls, query, **kw):
        pass

    @classmethod
    def fields(cls):
        return cls._fields


