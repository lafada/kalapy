"""
rapido.db.engines
~~~~~~~~~~~~~~~~~

This module provides database backend storage interface. Dynamically
loads the configured storage engine and exports implemented interfaces.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
import os

from werkzeug import import_string
from werkzeug.local import LocalStack

from rapido.conf import settings
from rapido.utils import signals


__all__ = ('Database', 'DatabaseError', 'IntegrityError', 'database')


if not settings.DATABASE_ENGINE:
    settings.DATABASE_ENGINE = 'dummy'

_engine_dir = os.path.join(os.path.dirname(__file__), settings.DATABASE_ENGINE)
if not os.path.exists(os.path.join(_engine_dir, '__init__.py')):
    raise ValueError(
        _("Engine %(name)r not supported.", name=settings.DATABASE_ENGINE))

engine = import_string('rapido.db.engines.%s' % settings.DATABASE_ENGINE)

Database = engine.Database
DatabaseError = engine.DatabaseError
IntegrityError = engine.IntegrityError


class Connection(object):

    __ctx = LocalStack()

    def __getattr__(self, name):
        if self.__ctx.top is None:
            self.connect()
        return getattr(self.__ctx.top, name)

    def connect(self):
        if self.__ctx.top is None:
            db = Database(
                    name=settings.DATABASE_NAME,
                    host=settings.DATABASE_HOST,
                    port=settings.DATABASE_PORT,
                    user=settings.DATABASE_USER,
                    password=settings.DATABASE_PASSWORD)
            self.__ctx.push(db)
        self.__ctx.top.connect()

    def close(self):
        if self.__ctx.top is not None:
            self.__ctx.top.close()
            self.__ctx.pop()


#: context local database connection
database = Connection()


def commit():
    """Commit the changes to the database.
    """
    database.commit()


def rollback():
    """Rollback all the changes made since the last commit.
    """
    database.rollback()


@signals.connect('request-started')
def open_connection():
    """Open database connection when request started.
    """
    database.connect()


@signals.connect('request-finished')
def close_connection():
    """Close database connection when request ends.
    """
    database.close()


@signals.connect('request-exception')
def rollback_connection(error):
    """Rollback database connection, if there is any unhandled exception
    during request processing.
    """
    database.rollback()

