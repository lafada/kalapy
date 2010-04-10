import inspect

def validate(field):
    """A decorator to assign a validator for a field. Should be used on model methods only.

    >>>
    >>> class User(Model):
    >>>
    >>>     name = String(size=50)
    >>>
    >>>     @validate("name")
    >>>     def check_name(self, value):
    >>>         if len(value) < 3:
    >>>             raise BadValueError("Name is too short.")
    >>>
    """
    
    _frame = inspect.currentframe()
    _locals = _frame.f_back.f_locals
    
    _field = _locals.get(field)
    
    if not isinstance(_field, Field):
        raise Exception("A field '%s' should be defined." % field)
    
    def wrapper(func):
        _field._validator = func
        return func

    return wrapper


class Field(object):
    
    _data_type = "string"
    
    def __init__(self, label=None, name=None, default=None, size=None,
            required=None, unique=False, indexed=None):

        self._label = label
        self._name = name
        self._default = default

        self._size = size
        self._required = required
        self._unique = unique
        self._indexed = indexed

        self._validator = None

    def __configure__(self, model_class, name):
        if self._name is None:
            self._name = name

        if self._label is None:
            self._label = name.title()

        self.model_class = model_class

    def __get__(self, model_instance, model_class):

        if model_instance is None:
            return self
        
        return getattr(model_instance, self._attr_name(), None)

    def __set__(self, model_instance, value):
        value = self.validate(model_instance, value)
        setattr(model_instance, self._attr_name(), value)

    def validate(self, model_instance, value):

        if self.empty(value) and self.required:
            raise ValueError("Field '%s' is required.", self.name)

        if self._validator:            
            self._validator(model_instance, value)

        return value

    def empty(self, value):
        return not value

    @property
    def data_type(self):
        return self._data_type
    
    @property
    def name(self):
        return self._name
    
    def _attr_name(self):
        return '_' + self.name

    @property
    def label(self):
        return self._label

    @property
    def default(self):
        return self._default

    @property
    def required(self):
        return self._required

    @property
    def unique(self):
        return self._unique

    @property
    def indexed(self):
        return self._indexed


class String(Field):
    pass


class Text(String):
    pass


class Integer(Field):
    pass


class Float(Field):
    pass


class Numeric(Float):
    pass


class Boolean(Field):
    pass


class DateTime(Field):
    pass


class Date(DateTime):
    pass


class Time(DateTime):
    pass


class Binary(Field):
    pass


class Selection(Field):
    """Selection field restricts the value of the field to the given set of values.
    
    >>> language = Selection(String, selection=[("en", "English"), 
    >>>                                         ("fr", "French"), 
    >>>                                         ("de", "German")], required=False)
    """
    
    def __init__(self, field, selection, **kw):
        pass


class ManyToOne(Field):
    pass


class OneToMany(Field):
    pass


class ManyToMany(Field):
    pass


