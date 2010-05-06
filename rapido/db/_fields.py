import decimal, datetime
from time import time


from _errors import *


class Field(object):

    # for internal use only
    _serial = 0

    _data_type = "string"

    def __init__(self, label=None, name=None, default=None, size=None,
            required=None, unique=False, indexed=None, selection=None):

        self._serial = Field._serial = Field._serial + 1

        self._label = label
        self._name = name
        self._default = default

        self._size = size
        self._required = required
        self._unique = unique
        self._indexed = indexed

        self._selection = selection() if callable(selection) else selection
        self._selection_list = [x[0] for x in self._selection] if self._selection else []

        self._validator = None

    def __repr__(self):
        return "<Field %s name='%s'>" % (self.__class__.__name__, self.name)

    def __configure__(self, model_class, name):

        self._name = name
        self.model_class = model_class

        if self._label is None:
            self._label = name.title()

    def __get__(self, model_instance, model_class):

        if model_instance is None:
            return self

        return model_instance._values.get(self.name)

    def __set__(self, model_instance, value):
        value = self._validate(model_instance, value)
        model_instance._values[self.name] = value

    def python_to_database(self, value):
        """Database representation of this field value.
        """
        return value

    def database_to_python(self, value):
        """Convert the given value to python representation for this field.
        """
        return value

    def _validate(self, model_instance, value):
        """Validate the given value. For internal use only, subclasses should
        override `validate` method instead.
        """
        if self.empty(value) and self.required:
            raise ValidationError("Field '%s' is required.", self.name)

        if self._selection and value not in self._selection_list:
            raise ValidationError("Field '%s' is '%s'; must be one of %s" % (
                                self.name, value, self._selection_list))

        if self._validator:
            self._validator(model_instance, value)

        return self.validate(value)

    def validate(self, value):
        """Check whether the given value is compatible with this field.
        Subclasses should override this method to convert provided value
        in compatible form and should raise `ValidationError` if the value
        is not compatible and can't be converted to proper value.
        """
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
    def col_name(self):
        return self._col_name

    @property
    def label(self):
        return self._label

    @property
    def size(self):
        return self._size

    @property
    def default(self):
        if callable(self._default):
            return self._default()
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


class AutoKey(Field):

    _data_type = 'key'

    def __init__(self):
        super(AutoKey, self).__init__(name="key")
        # nagative serial id so that it become first field in the model
        self._serial = - self._serial

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        return model_instance._key

    def __set__(self, model_instance, value):
        raise AttributeError('%r is a read-only primary key field.' % self.name)

class String(Field):
    pass


class Text(String):
    _data_type = "text"


class Integer(Field):
    _data_type = "integer"


class Float(Field):
    _data_type = "float"


class Decimal(Float):
    _data_type = "decimal"


class Boolean(Field):
    _data_type = "boolean"


class DateTime(Field):
    _data_type = "datetime"


class Date(DateTime):
    _data_type = "date"


class Time(DateTime):
    _data_type = "time"


class Binary(Field):
    _data_type = "blob"


