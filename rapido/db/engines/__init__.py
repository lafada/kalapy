import os

from rapido.conf import settings
from rapido.utils import load_module


__all__ = ('list_engines', 'connection')


if not settings.DATABASE_ENGINE:
    settings.DATABASE_ENGINE = 'dummy'


def list_engines():
    path = os.path.dirname(__file__)
    return [n for n in os.listdir(path) if os.path.isfile(os.path.join(path, n, '_database.py'))]


ENGINES = list_engines()


def load_engine(name):

    if name not in ENGINES:
        raise ValueError("Engine '%s' not supported." % name)

    return load_module('_database', 'rapido.db.engines.%s' % name)


engine = load_engine(settings.DATABASE_ENGINE)


database = engine.Database(
    name = settings.DATABASE_NAME,
    host = settings.DATABASE_HOST,
    port = settings.DATABASE_PORT,
    user = settings.DATABASE_USER,
    password = settings.DATABASE_PASSWORD)

