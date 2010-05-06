"""This module defines some class helpers to modify the behaviour/properties
of the model class.
"""

from _fields import Field


__all__ = ('validate', 'unique')


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

        if len(items) == 1:
            items[0]._unique = True
            continue

        if not items:
            continue

        first = items[0]
        first._unique_with = unique_with = [first]

        for field in items[1:]:
            unique_with.append(field)

