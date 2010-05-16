"""This module implements transaction management support.

This is just an initial implementation, a more powerful transaction management
support is required for web request/response life cycle.
"""
from rapido.db.engines import database, DatabaseError


__all__ = ('commit', 'rollback', 'run_in_transaction')


class TransactionError(DatabaseError):
    """The exception class for any transaction related errors.
    """
    pass


def enter_transaction():
    """Enter transaction management.
    """
    if getattr(database, '_in_transaction', False):
        raise TransactionError('Transaction already active')
    database._in_transaction = True

def leave_transaction():
    """Leave transaction management.
    """
    if getattr(database, '_in_transaction', False):
        rollback()

def commit():
    """Commit the active transaction, permanantly write the changes made in
    the transaction to the database.
    """
    database.commit()
    database._in_transaction = False

def rollback():
    """Rollback the active transaction, will discard all the changes made in
    the active transaction from the database.
    """
    database.rollback()
    database._in_transaction = False

def run_in_transaction(func, *args, **kw):
    """Run the specified function in transaction

    >>> u = User(name='some')
    >>> u.lang = 'en_EN'
    >>> run_in_transaction(u.save)

    :param func: the callable that should be run in transaction
    :param args: positional arguments to be passed to the func
    :param kw: keyword arguments to be passed to the func

    :returns: The result of the function being called.
    """
    enter_transaction()
    try:
        result = func(*args, **kw)
    except:
        rollback()
        raise
    else:
        commit()
    finally:
        leave_transaction()

    return result

