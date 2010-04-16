from types import FunctionType, MethodType

from _errors import *
from _fields import *


class ModelType(type):
    
    def __init__(cls, name, bases, attrs):

        super(ModelType, cls).__init__(name, bases, attrs)

        parents = [b for b in bases if isinstance(b, ModelType)]
        if not parents:
            # This is not a subclass of Model so do nothing
            return

        if len(parents) > 1:
            raise DatabaseError("Multiple inheritance is not supported.")

        cls._parent = parent = parents[0]

        cls._values = {}
        cls._fields = dict(getattr(parent, '_fields', {}))

        for name, attr in attrs.items():

            # prepare fields
            if isinstance(attr, Field):
                if name in cls._fields:
                    raise DuplicateFieldError("Duplicate field, %s, already defined in parent class." % (name))
                cls._fields[name] = attr
                attr.__configure__(cls, name)
            
            # prepare validators
            if isinstance(attr, FunctionType) and hasattr(attr, '_validates'):
                
                field = attr._validates
                if isinstance(field, basestring):
                    field = getattr(cls, field, None)

                if not isinstance(field, Field):
                    raise FieldError("Field '%s' is not defined." % attr._validates)

                field._validator = attr


class Model(object):
    
    __metaclass__ = ModelType
    
    def __init__(self, **kw):

        fields = self.fields()
        for name, value in kw.items():
            if name in fields:
                setattr(self, name, value)

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


class Query(object):
    """The query object. It provides methods to filter and fetch records
    from the database with simple pythonic conditions.

    >>> users = Query(User).filter("name ilike :name and age > :age", name="some", age=18)
    >>> users.order("-age")
    >>> first_ten = users.fetch(10, offset=0)
    >>> for user in first_ten:
    >>>     print "Name:", user.name
    """

    def __init__(self, model):
        """Create a new Query for the given model.

        Args:
            model: the model
        """
        self.model = model
    
    def filter(self, query, **kw):
        """Filter with the given query."
        
        >>> Query(User).filter("name ilike :name and age >= :age", name="some", age=20)
        """
        raise NotImplementedError
    
    def order(self, spec):
        """Order the query result with given spec.
        
        >>> q = Query(User).filter("name ilike :name and age >= :age", name="some", age=20)
        >>> q.order("-age")
        """
        raise NotImplementedError
    
    def fetch(self, limit, offset=0):
        """Fetch the given number of records from the query object from the given offset.
        
        >>> q = Query(User).filter("name ilike :name and age >= :age", name="some", age=20)
        >>> for obj in q.fetch(20):
        >>>     print obj.name
        """
        raise NotImplementedError
    
    def count(self):
        """Return the number of records in the query object.
        """
        raise NotImplementedError


