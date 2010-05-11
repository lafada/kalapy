import os, decimal
import sqlite3 as dbapi

from rapido.db.engines import utils
from rapido.db.engines.relational import RelationalDatabase


dbapi.register_converter('bool', lambda s: s == '1')
dbapi.register_converter('datetime', utils.datetime_to_python)
dbapi.register_converter('decimal', utils.decimal_to_python)
dbapi.register_adapter(decimal.Decimal, utils.decimal_to_database)
dbapi.register_adapter(str, utils.str_to_database)


__all__ = ('DatabaseError', 'IntegrityError', 'Database')


DatabaseError = dbapi.DatabaseError
IntegrityError = dbapi.IntegrityError


class Database(RelationalDatabase):
    
    data_types = {
        "key"       :   "INTEGER PRIMARY KEY AUTOINCREMENT",
        "char"      :   "VARCHAR(%(size)s)",
        "text"      :   "TEXT",
        "integer"   :   "INTEGER",
        "float"     :   "FLOAT",
        "decimal"   :   "DECIMAL",
        "boolean"   :   "BOOL",
        "datetime"  :   "DATETIME",
        "binary"    :   "BLOB",
    }

    def connect(self):
        if self.connection is not None:
            return self

        if self.name != ":memory:":
            if not os.path.isfile(self.name):
                raise DatabaseError("Database '%s' doesn't exist." % self.name)

        self.connection = dbapi.connect(self.name, detect_types=dbapi.PARSE_DECLTYPES)
        return self
        
    def exists_table(self, name):
        cursor = self.cursor()
        cursor.execute("""
            SELECT "name" FROM sqlite_master 
                WHERE type = "table" AND name = ?;
            """, (name,))
        return bool(cursor.fetchone())

