
from rapido.conf import settings
from rapido.utils import load_module

def load_engine(name):
    try:
        return load_module('_database', 'rapido.db.engines.%s' % name)
    except ImportError:
        raise

engine = load_engine(settings.DATABASE_ENGINE)

database = engine.Database(
    name = settings.DATABASE_NAME,
    host = settings.DATABASE_HOST,
    port = settings.DATABASE_PORT,
    user = settings.DATABASE_USER,
    password = settings.DATABASE_PASSWORD)

