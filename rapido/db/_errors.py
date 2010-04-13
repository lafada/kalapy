"""This module defines several common exception classes.
"""

class DatabaseError(Exception):
    pass


class FieldError(DatabaseError):
    pass


class DuplicateFieldError(FieldError):
    pass


class ValidationError(ValueError):
    pass

