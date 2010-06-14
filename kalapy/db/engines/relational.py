"""
kalapy.db.engines.relational
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides an abstract implementation of database engine interface
for relational database systems. Engines for an RDBMS should inherit from the
:class:`RelationalDatabase` instead of :class:`IDatabase`.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
from kalapy.db.engines.interface import IDatabase
from kalapy.db.model import Model
from kalapy.db.reference import ManyToOne


__all__ = ('RelationalDatabase')


class RelationalDatabase(IDatabase):

    def __init__(self, name, host=None, port=None, user=None, password=None):
        super(RelationalDatabase, self).__init__(name, host, port, user, password)
        self.connection = None

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

    def lastrowid(self, cursor, model):
        return cursor.lastrowid

    def update_records(self, instance, *args):

        result = []
        instances = [instance] + list(args)

        cursor = self.cursor()

        for obj in instances:

            assert isinstance(obj, Model), 'update_records expects Model instances'

            items = obj._to_database_values(True).items()

            keys = [x[0] for x in items]
            vals = [x[1] for x in items]

            if not obj.is_saved:
                keys = ['"%s"' % k for k in keys]
                sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % (
                        obj._meta.table,
                        ", ".join(keys),
                        ", ".join(['%s'] * len(vals)))
                cursor.execute(sql, vals)
                obj._key = self.lastrowid(cursor, obj.__class__)
                result.append(obj.key)
            else:
                keys = ", ".join(['"%s" = %%s' % k for k in keys])
                sql = 'UPDATE "%s" SET %s WHERE "key" = %%s' % (obj._meta.table, keys)

                vals.append(obj.key)
                cursor.execute(sql, vals)
                result.append(obj.key)

            obj.set_dirty(False)

        return result

    def delete_records(self, instance, *args):

        assert isinstance(instance, Model), 'delete_records expectes Model instances'

        instances = [instance]
        instances.extend(args)

        keys = [o.key for o in instances]

        sql = 'DELETE FROM "%s" WHERE "key" IN (%s)' % (
                            instance._meta.table, ", ".join(['%s'] * len(keys)))

        cursor = self.cursor()
        cursor.execute(sql, keys)

        for obj in instances:
            obj._key = None
            obj.set_dirty(True)

        return keys

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

