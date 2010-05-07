import decimal, datetime
from time import time


from _errors import *


class Field(object):

    # for internal use only
    _serial = 0

    _data_type = "char"

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

        if value is None:
            return value

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
        return self.default_value()

    def default_value(self):
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
    
    _data_type = "char"

    def validate(self, value):
        if not isinstance(value, basestring):
            raise ValidationError(
                    'Property %r must be a str or unicode instance, not %r'
                    % (self.name, type(value).__name__))
        return value

class Text(String):

    _data_type = "text"


class Integer(Field):

    _data_type = "integer"

    def validate(self, value):
        if isinstance(value, basestring):
            try:
                return int(value)
            except:
                raise ValidationError('Invalid value: %r' % value)
        if not isinstance(value, (int, long)) or isinstance(value, bool):
            raise ValidationError(
                    'Property %s must be an int or long, not a %s'
                    % (self.name, type(value).__name__))
        return value


class Float(Field):

    _data_type = "float"

    def validate(self, value):
        if isinstance(value, basestring):
            try:
                return float(value)
            except:
                raise ValidationError('Invalid value: %r' % value)
        if not isinstance(value, float):
            raise ValidationError(
                    'Property %s must be a float, not a %s'
                    % (self.name, type(value).__name__))
        return value


class Decimal(Float):

    _data_type = "decimal"

    def validate(self, value):
        if isinstance(value, basestring):
            try:
                return decimal.Decimal(value)
            except:
                raise ValidationError('Invalid decimal value: %r' % value)
        if not isinstance(value, decimal.Decimal):
            raise ValidationError(
                    'Property %s must be a decimal.Decimal value, not a %s'
                    % (self.name, type(value).__name__))
        return value


class Boolean(Field):

    _data_type = "boolean"

    def validate(self, value):
        if isinstance(value, int):
            return bool(value)
        if value in (True, False): return value
        if value in ('t', 'True', 'y', 'Yes', '1'): return True
        if value in ('f', 'False', 'n', 'No', '0'): return False
        raise ValidationError('Expected either True or False')


class DateTime(Field):

    _data_type = "datetime"
    _python_type = datetime.datetime

    def __init__(self, label=None, auto_now=False, auto_now_add=False, **kw):
        super(DateTime, self).__init__(label=label, **kw)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    def validate(self, value):
        #TODO: try to convert the string value in to datetime
        if not isinstance(value, self._python_type):
            raise ValidationError('Property %r must be a %r' %
                          (self.name, self._data_type))
        return value

    def default_value(self):
        if self.auto_now or self.auto_now_add:
            return self.now()
        return super(DateTime, self).default_value()

    def python_to_database(self, value):
        if self.auto_now:
            return self.now()
        return super(DateTime, self).python_to_database(value)

    @staticmethod
    def now():
        return datetime.datetime.now()


def _date_to_datetime(value):
  """Convert a date to a datetime for datastore storage.

  Args:
    value: A datetime.date object.

  Returns:
    A datetime object with time set to 0:00.
  """
  assert isinstance(value, datetime.date)
  return datetime.datetime(value.year, value.month, value.day)


def _time_to_datetime(value):
  """Convert a time to a datetime for datastore storage.

  Args:
    value: A datetime.time object.

  Returns:
    A datetime object with date set to 1970-01-01.
  """
  assert isinstance(value, datetime.time)
  return datetime.datetime(1970, 1, 1,
                           value.hour, value.minute, value.second,
                           value.microsecond)

class Date(DateTime):

    _data_type = "date"
    _python_type = datetime.date

    def python_to_database(self, value):
        value = super(Date, self).python_to_database(value)
        if value is not None:
            assert isinstance(value, datetime.date)
        value = _date_to_datetime(value)
        return value

    def database_to_python(self, value):
        if value is not None:
            assert isinstance(value, datetime.datetime)
            value = value.date()
        return value

    @staticmethod
    def now():
        return datetime.datetime.now().date()
    
class Time(DateTime):

    _data_type = "time"
    _python_type = datetime.time

    def python_to_database(self, value):
        value = super(Time, self).python_to_database(value)
        if value is not None:
            assert isinstance(value, datetime.time), repr(value)
        value = _time_to_datetime(value)
        return value

    def database_to_python(self, value):
        if value is not None:
            assert isinstance(value, datetime.datetime)
        value = value.time()
        return value

    @staticmethod
    def now():
        return datetime.datetime.now().time()


class Binary(Field):
    _data_type = "blob"

