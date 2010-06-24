"""
kalapy.db.engines.gae
~~~~~~~~~~~~~~~~~~~~~

Implementes Google AppEngine backend.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
try:
    from google.appengine.api import datastore
except ImportError:
    from _utils import setup_stubs
    setup_stubs()
    from google.appengine.api import datastore

from google.appengine.api import datastore_errors

from kalapy.db.engines.interface import IDatabase
from kalapy.db.model import Model


__all__ = ('DatabaseError', 'IntegrityError', 'Database')


class DatabaseError(Exception):
    pass


class IntegrityError(DatabaseError):
    pass


class Database(IDatabase):

    schema_mime = 'text/x-python'

    def __init__(self, name, host=None, port=None, user=None, password=None):
        super(Database, self).__init__(name, host, port, user, password)

    def connect(self):
        pass

    def close(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def schema_table(self, model):
        result = "class %s(db.Model):" % model.__name__
        for name, field in model.fields().items():
            result += "\n    %s = db.%s(...)" % (name, field.__class__.__name__)
        return result

    def exists_table(self, name):
        pass

    def create_table(self, model):
        pass

    def alter_table(self, model, name=None):
        pass

    def drop_table(self, name):
        pass

    def update_records(self, instance, *args):

        result = []
        instances = [instance]
        instances.extend(args)

        for obj in instances:
            if not isinstance(instance, Model):
                raise TypeError('update_records expects Model instances')
            items = obj._to_database_values(True)

            if not obj.is_saved:
                obj._payload = datastore.Entity(obj._meta.table)

            #TODO: convert values to GAE supported datatypes

            obj._payload.update(items)
            obj._key = str(datastore.Put(obj._payload))

            result.append(obj.key)
            obj.set_dirty(False)

        return result

    def delete_records(self, instance, *args):

        instances = [instance]
        instances.extend(args)

        for obj in instances:
            if not isinstance(instance, Model):
                raise TypeError('delete_records expectes Model instances')

        keys = [obj.key for obj in instances]
        datastore.Delete(keys)

        for obj in instances:
            obj._key = None
            obj.set_dirty(True)

        return keys

    def fetch(self, qset, limit, offset):
        limit = datastore.MAXIMUM_RESULTS if limit == -1 else limit
        queries = self._build_queries(qset)

        entities = {}
        for query in queries:
            for e in query.Get(limit, offset):
                if e.key() in entities:
                    continue
                entities[e.key()] = e

        for e in SortResult(entities.values()).get(limit, qset.order):
            if e is not None:
                yield dict(e, key=str(e.key()), _payload=e)

    def count(self, qset):
        return len(list(self.fetch(qset, -1, 0)))

    def _query(self, kind, item):
        name, op, value = item
        if op == 'in':
            return MultiQuery(
                [Query(kind, {'%s =' % name: v}) for v in value], [])
        elif op == '!=':
            return MultiQuery(
                [Query(kind, {'%s <' % name: value}),
                 Query(kind, {'%s >' % name: value})], [])
        else:
            return Query(kind, {'%s %s' % (name, op): value})

    def _build_queries(self, qset):

        kind = qset.model._meta.table
        orderings = []

        result = []
        for q in qset:
            if len(q.items) > 1:
                result.append(MultiQuery(
                    [self._query(kind, item) for item in q.items], []))
            else:
                result.append(self._query(kind, q.items[0]))

        if not result:
            return [Query(kind, {})]
        return result


class Query(datastore.Query):

    def IsKeysOnly(self):
        return False

    def Run(self, **kwargs):
        try:
            try:
                return iter([datastore.Get(self['key ='])])
            except KeyError:
                return iter([datastore.Get(self['key =='])])
        except datastore_errors.EntityNotFoundError:
            return iter([None])
        except KeyError:
            return super(Query, self).Run(**kwargs)


class MultiQuery(datastore.MultiQuery):

    def IsKeysOnly(self):
        return False


class SortResult(object):
    """This class is used to sort the final result.
    """
    def __init__(self, result):
        self.result = result

    def get(self, limit, order=None):
        result = self.result[:limit]
        if not order:
            return result

        direction = 1
        if order.startswith('-'):
            direction = 2
            order = order[1:]

        def compare(a, b):
            if direction == 2:
                return -cmp(a[order], b[order])
            return cmp(a[order], b[order])

        result.sort(compare)
        return result

