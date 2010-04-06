

def validate(field, model_class=None):
    """A decorator to assign a validator for a field of the given
    model_class which if None then assumes current class.

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

    def wraper(func):

        _class = model_class or func.im_class

        _field = getattr(_class, field)
        _field.validator = func

        return func

    return wrapper


class Field(object):
    
    _data_type = "string"
    
    def __init__(self, label=None, name=None, default=None, size=None,
            required=None, unique=False, indexed=None, validator=None):

        self._label = label
        self._name = name
        self._default = default

        self._size = size
        self._required = required
        self._unique = unique
        self._indexed = indexed

        self.validator = validator

    def __configure__(self, model_class, name):
        if self._name is None:
            self._name = name

        if self._label is None:
            self._label = name.title()

        self.model_class = model_class

    def __get__(self, model_instance, model_class):

        if model_instance is None:
            return self

        return getattr(model_instance, self.name, None)

    def __set__(self, model_instance, value):
        value = self.validate(value)
        setattr(model_instance, self.name, value)

    def validate(self, value):

        if self.empty(value) and self.required:
            raise BadValueError("Field '%s' is required.", self.name)

        if callable(self.validator):
            self.validator(value)

        return value

    def empty(self, value):
        return not value

    @property
    def data_type(self):
        return self._data_type
    
    @property
    def name(self):
        return self._name

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


