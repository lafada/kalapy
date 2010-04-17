
from rapido.db._model import get_model
from rapido.db._interface import IEntity


class Entity(IEntity):

    def __init__(self, database, name):
        super(Entity, self).__init__(database, name)
        self.cursor = self.database.cursor()

    def exists(self):
        self.cursor.execute("""
            SELECT "name" FROM sqlite_master 
                WHERE type = "table" AND name = ?;
            """, (self.name,))
        return bool(self.cursor.fetchone())

    def get_pk_sql(self):
        return '"id" INTEGER PRIMARY KEY AUTOINCREMENT'

    def get_column_sql(self, field, for_alter=False):
        res = '"%s" %s' % (field.name, self.database.get_data_type(field))
        if not for_alter:
            if field.required:
                res = "%s NOT NULL" % res
            if field.unique:
                res = "%s UNIQUE" % res

        #TODO: add reference
        return res

    def create(self):

        model = get_model(self.name)

        fields = model.fields().values()

        fields_sql = [self.get_pk_sql()] + [self.get_column_sql(f) for f in fields]
        fields_sql = ",\n    ".join(fields_sql)

        sql = 'CREATE TABLE "%s" (\n    %s\n);' % (self.name, fields_sql)

        self.cursor.execute(sql)

    def drop(self):
        self.cursor.execute("""
            DROP TABLE "%s"
            """ % (self.name,))

    def rename(self, new_name):
        self.cursor.execute('ALTER TABLE "%s" RENAME TO "%s"' % (
            self.name, new_name,))
    
    def insert(self, **kw):
        
        items = kw.items()

        keys = ['"%s"' % x[0] for x in items]
        vals = [x[1] for x in items]
        
        sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % (
                self.name, 
                ", ".join(keys), 
                ", ".join(['?'] * len(vals)))
        
        self.cursor.execute(sql, vals)
        
    def update(self, key, **kw):

        items = kw.items()

        keys = [x[0] for x in items]
        vals = [x[1] for x in items]

        keys = ", ".join(['"%s" = ?' % k for k in keys])

        sql = 'UPDATE "%(table)s" SET\n    %(keys)s\nWHERE "id" = ?' % dict(
                table=self.name, keys=keys)
        
        vals.append(key)

        self.cursor.execute(sql, vals)
    
    def delete(self, keys):

        if not isinstance(keys, (list, tuple)):
            keys = [keys]

        sql = 'DELETE FROM "%s" WHERE "id" IN (%s)' % (self.name, ", ".join(['?'] * len(keys)))

        self.cursor.execute(sql, keys)
    
    def field_exists(self, field):
        name = field if isinstance(field, basestring) else field.name
        sql = 'SELECT "%s" FROM "%s" LIMIT 1' % (name, self.name)
        try:
            self.cursor.execute(sql)
            return True
        except:
            return False
    
    def field_add(self, field):
        field_sql = self.get_column_sql(field, for_alter=True)
        sql = 'ALTER TABLE "%s" ADD COLUMN %s' % (self.name, fields_sql)
        self.cursor.execute(sql)
    
    def field_drop(self, field):
        #XXX: not supported
        pass
        
    def field_alter(self, field):
        #XXX: not supported
        pass


