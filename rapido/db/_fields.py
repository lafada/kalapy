
from _errors import *


def validate(field):
    """A decorator to assign a validator for a field. Should only be used with 
    the methods of the class where the field is defined.

    >>>
    >>> class User(Model):
    >>>
    >>>     name = String(size=50)
    >>>
    >>>     @validate("name")
    >>>     def check_name(self, value):
    >>>         if len(value) < 3:
    >>>             raise ValidationError("Name is too short.")
    >>>
    """
    def wrapper(func):
        func._validates = field
        return func
    return wrapper


class Field(object):

    # for internal use only
    _creation_order = 0

    _data_type = "string"

    def __init__(self, label=None, name=None, default=None, size=None,
            required=None, unique=False, indexed=None, selection=None):

        self._creation_order = Field._creation_order = Field._creation_order + 1

        self._label = label
        self._name = name
        self._default = default

        self._size = size
        self._required = required
        self._unique = unique
        self._indexed = indexed

        self._selection = selection
        self._selection_list = [x[0] for x in selection] if selection else []

        self._validator = None

    def __repr__(self):
        return "<Field %s name='%s'>" % (self.__class__.__name__, self.name)

    def __configure__(self, model_class, name):
        if self._name is None:
            self._name = name

        if self._label is None:
            self._label = name.title()

        self.model_class = model_class

    def __get__(self, model_instance, model_class):

        if model_instance is None:
            return self

        return model_instance._values.get(self.name)

    def __set__(self, model_instance, value):
        value = self.validate(model_instance, value)
        model_instance._values[self.name] = value

    def to_database_value(self, model_instance):
        """Get the value to be stored in database for this field.
        """
        return self.__get__(model_instance, model_instance.__class__)

    def from_database_value(self, model_instance, value):
        """Get the value to be stored in model instance from the given
        value retrieved from database.
        """
        return value

    def validate(self, model_instance, value):

        if self.empty(value) and self.required:
            raise ValidationError("Field '%s' is required.", self.name)

        if self._selection and value not in self._selection_list:
            raise ValidationError("Field '%s' is '%s'; must be one of %s" % (
                                self.name, value, self._selection_list))

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

    @property
    def label(self):
        return self._label

    @property
    def size(self):
        return self._size

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
    _data_type = "text"


class Integer(Field):
    _data_type = "integer"


class Float(Field):
    _data_type = "float"


class Numeric(Float):
    _data_type = "decimal"


class Boolean(Field):
    _data_type = "bool"


class DateTime(Field):
    _data_type = "datetime"


class Date(DateTime):
    _data_type = "date"


class Time(DateTime):
    _data_type = "time"


class Binary(Field):
    _data_type = "blob"


