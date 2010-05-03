"""This module defines some class helpers to modify the behaviour/properties
of the model class.
"""

import re, types, inspect


__all__ = ('validate', 'unique')


MODEL_HELPERNAME = '__model_helpers_'


def classhelper(func):

    def wrapper(*args, **kw):

        def handler(cls):
            return func(cls, *args, **kw)

        frame = inspect.currentframe().f_back.f_back
        try:
            helpers = frame.f_locals.setdefault(MODEL_HELPERNAME, [])
            helpers.append(handler)
        finally:
            del frame

        return func
    return wrapper


def validate(field):
    """A helper decorator to assign a validator for a field. Should only be 
    used with the methods of the class where the field is defined.

    >>>
    >>> class User(Model):
    >>>
    >>>     name = String(size=50)
    >>>
    >>>     @validate('name')
    >>>     def check_name(self, value):
    >>>         if len(value) < 3:
    >>>             raise ValidationError('Name is too short.')
    >>>
    """
    
    @classhelper
    def handler(cls, func, field):
        from _fields import Field

        if isinstance(field, Field) and field.name not in cls._meta.fields:
            raise ValueError('No such field %r' % field.name)

        if isinstance(field, basestring):
            if field not in cls._meta.fields:
                raise ValueError('No such field %r' % field)
            field = cls._meta.fields[field]

        assert isinstance(field, Field)

        field._validator = func

    def wrapper(func):
        handler(func, field)
        return func

    return wrapper


def unique(*fields):
    """A helper function to be used to define unique constraints, single or combined,
    in model classes.

    For example,

    >>> class A(db.Model):
    >>>     a = db.String()
    >>>     b = db.String()
    >>>     c = db.String()
    >>>
    >>>     db.unique(a, [b, c])

    Declares uniqueness of `a` and combined uniqueness of `b` & `c`.
    """

    @classhelper
    def handler(cls, *fields):
        from _fields import Field

        unique = []
        for items in fields:
            if not isinstance(items, (list, tuple)):
                items = [items]
            items = list(items)
            for i, field in enumerate(items):
                if isinstance(field, basestring) and field not in cls._meta.fields:
                    raise ValueError('No such field %r' % field)
                if isinstance(field, Field):
                    items[i] = field.name

        cls._meta.unique = fields

    handler(*fields)

