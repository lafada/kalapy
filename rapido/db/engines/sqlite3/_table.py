from rapido.db._interface import ITable
from rapido.db._reference import ManyToOne


class Table(ITable):

    def __init__(self, model):
        super(Table, self).__init__(model)

    def exists(self):
        cursor = self.database.cursor()
        cursor.execute("""
            SELECT "name" FROM sqlite_master 
                WHERE type = "table" AND name = ?;
            """, (self.name,))
        return bool(cursor.fetchone())

    def get_pk_sql(self):
        return '"id" INTEGER PRIMARY KEY AUTOINCREMENT'

    def get_field_sql(self, field, for_alter=False):
        res = '"%s" %s' % (field.name, self.database.get_data_type(field))
        if not for_alter:
            if field.required:
                res = "%s NOT NULL" % res
            if field.unique:
                res = "%s UNIQUE" % res

        if isinstance(field, ManyToOne):
            res = '%s REFERENCES "%s" ("id")' % (res, field.reference._table.name)
            if field.cascade:
                res = '%s ON DELETE CASCADE' % res
            elif field.required:
                res = '%s ON DELETE RESTRICT' % res
            else:
                res = '%s ON DELETE SET NULL' % res
        return res

    def get_create_sql(self):
        fields = self.model.fields().values()
        fields.sort(lambda a, b: cmp(a._creation_order, b._creation_order))

        fields_sql = [self.get_pk_sql()] + [self.get_field_sql(f) for f in fields]
        fields_sql = ",\n    ".join(fields_sql)

        return 'CREATE TABLE "%s" (\n    %s\n);' % (self.name, fields_sql)

    def schema(self):
        return self.get_create_sql()

    def create(self):
        if not self.exists():
            cursor = self.database.cursor()
            cursor.execute(self.get_create_sql())

    def drop(self):
        if self.exists():
            cursor = self.database.cursor()
            cursor.execute('DROP TABLE "%s"' % self.name)

    def rename(self, new_name):
        if self.exists():
            cursor = self.database.cursor()
            cursor.execute('ALTER TABLE "%s" RENAME TO "%s"' % (
                self.name, new_name,))

    def insert(self, **kw):

        items = kw.items()

        keys = ['"%s"' % x[0] for x in items]
        vals = [x[1] for x in items]

        sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % (
                self.name,
                ", ".join(keys),
                ", ".join(['?'] * len(vals)))

        cursor = self.database.cursor()
        cursor.execute(sql, vals)

        return cursor.lastrowid

    def update(self, key, **kw):

        items = kw.items()

        keys = [x[0] for x in items]
        vals = [x[1] for x in items]

        keys = ", ".join(['"%s" = ?' % k for k in keys])

        sql = 'UPDATE "%(table)s" SET\n    %(keys)s\nWHERE "id" = ?' % dict(
                table=self.name, keys=keys)

        vals.append(key)

        cursor = self.database.cursor()
        cursor.execute(sql, vals)

    def delete(self, keys):
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
        sql = 'DELETE FROM "%s" WHERE "id" IN (%s)' % (self.name, ", ".join(['?'] * len(keys)))
        cursor = self.database.cursor()
        cursor.execute(sql, keys)

    def select(self, query, params):
        cursor = self.database.cursor()
        cursor.execute(query, params)

        names = [desc[0] for desc in cursor.description]
        result = []
        for row in cursor.fetchall():
            obj = self.model()
            for i, name in enumerate(names):
                if row[i] is None:
                    continue
                if name != 'id':
                    setattr(obj, name, row[i])
                else:
                    obj._key = row[i]
            result.append(obj)
        return result

    def count(self, query, params):
        cursor = self.database.cursor()
        cursor.execute(query, params)
        try:
            return cursor.fetchone()[0]
        except:
            return 0

    def field_exists(self, field):
        name = field if isinstance(field, basestring) else field.name
        sql = 'SELECT "%s" FROM "%s" LIMIT 1' % (name, self.name)
        try:
            cursor = self.database.cursor()
            cursor.execute(sql)
            return True
        except:
            return False

    def field_add(self, field):
        field_sql = self.get_field_sql(field, for_alter=True)
        sql = 'ALTER TABLE "%s" ADD COLUMN %s' % (self.name, field_sql)
        cursor = self.database.cursor()
        cursor.execute(sql)

    def field_drop(self, field):
        #XXX: not supported
        pass

    def field_alter(self, field):
        #XXX: not supported
        pass
