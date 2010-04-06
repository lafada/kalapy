
from _connection import get_connection


def run_in_transaction(self, callback, *args, **kw):
    
    connection = get_connection()
    database = connection.database
    
    try:
        database.begin_transaction()
        try:
            res = callback(*args, **kw)
            database.commit()
            return res
        except:
            database.rollback()
    finally:
        database.end_transaction()
