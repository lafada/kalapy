import os

from rapido.conf import settings
from rapido.utils.imp import import_module


__all__ = ('list_engines', 'engine', 'database')


if not settings.DATABASE_ENGINE:
    settings.DATABASE_ENGINE = 'dummy'

path = os.path.dirname(__file__)
ENGINES = [n for n in os.listdir(path) \
           if os.path.isfile(os.path.join(path, n, '__init__.py'))]
del path

def load_engine(name):
    if name not in ENGINES:
        raise ValueError("Engine '%s' not supported." % name)
    return import_module(name, 'rapido.db.engines')

engine = load_engine(settings.DATABASE_ENGINE)

Database = engine.Database
Entity = engine.Entity

database = Database(
    name = settings.DATABASE_NAME,
    host = settings.DATABASE_HOST,
    port = settings.DATABASE_PORT,
    user = settings.DATABASE_USER,
    password = settings.DATABASE_PASSWORD)

Entity._database = database

