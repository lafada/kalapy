import os

from rapido.conf import settings
from rapido.utils.implib import import_module


__all__ = ('Database', 'DatabaseError', 'IntegrityError', 'database')


if not settings.DATABASE_ENGINE:
    settings.DATABASE_ENGINE = 'dummy'

_engine_dir = os.path.join(os.path.dirname(__file__), settings.DATABASE_ENGINE)
if not os.path.exists(os.path.join(_engine_dir, '__init__.py')):
    raise ValueError("Engine '%s' not supported." % settings.DATABASE_ENGINE)

engine = import_module(settings.DATABASE_ENGINE, 'rapido.db.engines')

Database = engine.Database
DatabaseError = engine.DatabaseError
IntegrityError = engine.IntegrityError

database = Database(
    name=settings.DATABASE_NAME,
    host=settings.DATABASE_HOST,
    port=settings.DATABASE_PORT,
    user=settings.DATABASE_USER,
    password=settings.DATABASE_PASSWORD)

