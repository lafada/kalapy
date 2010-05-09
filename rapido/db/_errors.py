"""This module defines several common exception classes.
"""


class _Exception(Exception):

    def __new__(cls, *args, **kw):
        from rapido.db import engines
        proxy = getattr(engines, cls.__name__, cls)
        return super(_Exception, cls).__new__(proxy)


class DatabaseError(_Exception):
    pass


class IntegrityError(DatabaseError):
    pass


class FieldError(AttributeError):
    pass


class ValidationError(ValueError):
    pass

