
from rapido.db._interface import IEntity


class Entity(IEntity):

    def __init__(self, database, name):
        super(Entity, self).__init__(database, name)
        self.cursor = self.database.cursor()

    def exists(self):
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
                WHERE type = 'table' AND name = ?;
            """, (self.name,))
        return bool(self.cursor.fetchone())

    def create(self):
        self.cursor.execute("""
            CREATE TABLE %s (
                key INTEGER PRIMARY KEY AUTOINCREMENT
            );
            """ % (self.name,))

    def drop(self):
        self.cursor.execute("DROP TABLE %s" % (self.name,))

    def rename(self, new_name):
        self.cursor.execute('ALTER TABLE %s RENAME TO %s' % (self.name, new_name,))
    
    def insert(self, **kw):
        
        items = kw.items()

        keys = [x[0] for x in items]
        vals = [x[1] for x in items]
        
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (
                self.name, 
                ", ".join(keys), 
                ", ".join(['?'] * len(vals)))
        
        self.cursor.execute(sql, vals)
        
    def update(self, key, **kw):

        items = kw.items()

        keys = [x[0] for x in items]
        vals = [x[1] for x in items]

        keys = ", ".join(["%s = ?" % k for k in keys])

        sql = "UPDATE %(table)s SET\n    %(keys)s\nWHERE key = ?" % dict(
                table=self.name, keys=keys)

        vals.append(key)

        self.cursor.execute(sql, vals)
    
    def delete(self, keys):

        if not isinstance(keys, (list, tuple)):
            keys = [keys]

        sql = "DELETE FROM %s WHERE key IN (%s)" % (self.name, ", ".join(['?'] * len(keys)))
        self.cursor.execute(sql, keys)
    
    def column_exists(self, field):
        name = field if isinstance(field, basestring) else field.name
        sql = "SELECT %s FROM %s LIMIT 1" % (name, self.name)
        try:
            self.cursor.execute(sql)
            return True
        except:
            return False
    
    def column_add(self, field):

        datatype = DATA_TYPES.get(field.data_type, "TEXT") % (dict(size=field.size))

        sql = "ALTER TABLE %(name)s ADD COLUMN %(col)s %(datatype)s" % dict(
                name=self.name, col=field.name, datatype=datatype)

        self.cursor.execute(sql)
    
    def column_drop(self, field):
        #XXX: not supported
        pass
        
    def column_alter(self, field, name=None, size=None, datatype=None):
        #XXX: not supported
        pass

DATA_TYPES = {
        "string"    :   "CHAR[%(size)s]",
        "text"      :   "VARCHAR",
        "integer"   :   "INTEGER",
        "float"     :   "FLOAT",
        "numeric"   :   "CHAR",
        "boolean"   :   "BOOL",
        "datetime"  :   "CHAR[20]",
        "date"      :   "CHAR[10]",
        "time"      :   "CHAR[10]",
        "binary"    :   "BLOB",
}

