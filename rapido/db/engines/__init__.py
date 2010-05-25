import os

from werkzeug import import_string
from rapido.conf import settings


__all__ = ('Database', 'DatabaseError', 'IntegrityError', 'database')


if not settings.DATABASE_ENGINE:
    settings.DATABASE_ENGINE = 'dummy'

_engine_dir = os.path.join(os.path.dirname(__file__), settings.DATABASE_ENGINE)
if not os.path.exists(os.path.join(_engine_dir, '__init__.py')):
    raise ValueError("Engine '%s' not supported." % settings.DATABASE_ENGINE)

engine = import_string('rapido.db.engines.%s' % settings.DATABASE_ENGINE)

Database = engine.Database
DatabaseError = engine.DatabaseError
IntegrityError = engine.IntegrityError

database = Database(
    name=settings.DATABASE_NAME,
    host=settings.DATABASE_HOST,
    port=settings.DATABASE_PORT,
    user=settings.DATABASE_USER,
    password=settings.DATABASE_PASSWORD)

