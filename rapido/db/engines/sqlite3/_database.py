import os, decimal
import sqlite3

from rapido.db._errors import DatabaseError
from rapido.db._interface import IDatabase
from rapido.db._reference import ManyToOne

from rapido.db.engines import utils

sqlite3.register_converter('bool', lambda s: s == '1')
sqlite3.register_converter('datetime', utils.datetime_to_python)
sqlite3.register_converter('decimal', utils.decimal_to_python)
sqlite3.register_adapter(decimal.Decimal, utils.decimal_to_database)
sqlite3.register_adapter(str, utils.str_to_database)

class Database(IDatabase):
    
    data_types = {
        "key"       :   "INTEGER PRIMARY KEY AUTOINCREMENT",
        "char"      :   "CHAR",
        "text"      :   "VARCHAR",
        "integer"   :   "INTEGER",
        "float"     :   "FLOAT",
        "decimal"   :   "DECIMAL",
        "boolean"   :   "BOOL",
        "datetime"  :   "DATETIME",
        "binary"    :   "BLOB",
    }

    def __init__(self, name, host=None, port=None, user=None, password=None):
        super(Database, self).__init__(name, host, port, user, password)
        self.connection = None
        
    def connect(self):

        if self.connection is not None:
            return self

        if self.name != ":memory:":
            if not os.path.isfile(self.name):
                raise DatabaseError("Database '%s' doesn't exist." % self.name)

        if self.connection is None:
            self.connection = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)

        return self

    def close(self):
        if self.connection:
            self.connection.close()
        self.connection = None

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def cursor(self):
        if not self.connection:
            self.connect()
        return self.connection.cursor()
        
    def exists_table(self, name):
        cursor = self.cursor()
        cursor.execute("""
            SELECT "name" FROM sqlite_master 
                WHERE type = "table" AND name = ?;
            """, (name,))
        return bool(cursor.fetchone())

    def get_field_sql(self, field, for_alter=False):
        res = '"%s" %s' % (field.name, self.get_data_type(field))
        if not for_alter:
            if field.is_required:
                res = "%s NOT NULL" % res
            if field.is_unique:
                res = "%s UNIQUE" % res

        if isinstance(field, ManyToOne):
            res = '%s REFERENCES "%s" ("key")' % (res, field.reference._meta.table)
            if field.cascade:
                res = '%s ON DELETE CASCADE' % res
            elif field.is_required:
                res = '%s ON DELETE RESTRICT' % res
            elif field.cascade is None:
                res = '%s ON DELETE SET NULL' % res
        return res

    def get_create_sql(self, model):

        fields = [f for f in model.fields().values() if f._data_type is not None]
        fields_sql = [self.get_field_sql(f) for f in fields]

        # generate unique constraints
        for item in model._meta.unique:
            fields_sql.append('UNIQUE(%s)' % ", ".join(['"%s"' % f.name for f in item]))

        fields_sql = ",\n    ".join(fields_sql)

        return 'CREATE TABLE "%s" (\n    %s\n);' % (model._meta.table, fields_sql)

    def schema_table(self, model):
        return self.get_create_sql(model)
    
    def create_table(self, model):
        if not self.exists_table(model._meta.table):
            cursor = self.cursor()
            cursor.execute(self.get_create_sql(model))

    def drop_table(self, name):
        if self.exists_table(name):
            cursor = self.cursor()
            cursor.execute('DROP TABLE "%s"' % name)

    def alter_table(self, model, name=None):
        cursor = self.cursor()
        if name and self.exists_table(name):
            cursor.execute('ALTER TABLE "%s" RENAME TO "%s"' % (
                name, model._meta.table,))
        #TODO: alter columns if changed

    def insert_record(self, model):
        
        if model.is_saved:
            return self.update_record(model)
        
        items = model._to_database_values(True).items()

        keys = ['"%s"' % x[0] for x in items]
        vals = [x[1] for x in items]

        sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % (
                model._meta.table,
                ", ".join(keys),
                ", ".join(['?'] * len(vals)))

        cursor = self.cursor()
        cursor.execute(sql, vals)
        model._key = cursor.lastrowid
        
        return model.key

    def update_record(self, model):

        if not model.is_saved:
            return self.insert_record(model)
        
        items = model._to_database_values(True).items()
        
        keys = [x[0] for x in items]
        vals = [x[1] for x in items]

        keys = ", ".join(['"%s" = ?' % k for k in keys])
        sql = 'UPDATE "%s" SET %s WHERE "key" = ?' % (model._meta.table, keys)

        vals.append(model.key)

        cursor = self.cursor()
        cursor.execute(sql, vals)
        
        return model.key
    
    def delete_record(self, instance):
        if instance.is_saved:
            self.delete_from_keys(instance.__class__, instance.key)
            instance._key = None
            
    def delete_from_keys(self, model, keys):
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
        sql = 'DELETE FROM "%s" WHERE "key" IN (%s)' % (
                            model._meta.table, ", ".join(['?'] * len(keys)))
        cursor = self.cursor()
        cursor.execute(sql, keys)

    def select_from(self, query, params):
        cursor = self.cursor()
        cursor.execute(query, params)
        names = [desc[0] for desc in cursor.description]
        result = [dict([(name, row[i]) for i, name in enumerate(names)]) for row in cursor.fetchall()]
        return result

    def select_count(self, query, params):
        cursor = self.cursor()
        cursor.execute(query, params)
        try:
            return cursor.fetchone()[0]
        except:
            return 0
