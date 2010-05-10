"""This module defines some class helpers to modify the behavior/properties
of the model class.
"""

import sys

from _fields import Field
from _model import ModelType


__all__ = ('meta', 'validate', 'unique')


def meta(name=None):
    """A decorator for Model subclasses to have alternate meta information.

    As model meta can't be re-initialized this decorator should only be used
    on direct subclass of db.Model

    Args:
        name: name for the model
    """
    def wrapper(cls):
        assert isinstance(cls, ModelType), 'Must be used with Model subclass'
        return cls

    frm = sys._getframe().f_back
    try:
        frm.f_locals['_MODEL_META__'] = dict(name=name)
    finally:
        del frm

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
    def decore(func):
        func._validates = field
        return func
    return decore


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

    def chk(item):
        if isinstance(item, (list, tuple)):
            return map(chk, item)
        if not isinstance(item, Field):
            raise TypeError('Field expected')

    map(chk, fields)

    for items in fields:

        if not isinstance(items, (list, tuple)):
            items._unique = True
            continue

        if not items:
            continue

        if len(items) == 1:
            items[0]._unique = True
        else:
            items[0]._unique_with = items

