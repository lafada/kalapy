"""
kalapy.db.engines.gae
~~~~~~~~~~~~~~~~~~~~~

Implementes Google AppEngine backend.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
from itertools import chain

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
        orderings = []
        try:
            name, how = qset.order
            how = Query.ASCENDING if how == 'ASC' else Query.DESCENDING
            orderings = [(name, how)]
        except:
            pass

        # The results should be ANDed

        query_set = self._build_query_set(qset, orderings)
        result_set = [[e for e in q.Get(limit, offset) if e] for q in query_set]

        keys = [set([e.key() for e in result]) for result in result_set]
        keys = reduce(lambda a, b: a & b, keys)

        result = {}
        for e in chain(*tuple(result_set)):
            if e.key() in keys:
                result.setdefault(e.key(), e)

        for e in sort_result(result.values(), orderings)[:limit]:
            yield dict(e, key=str(e.key()), _payload=e)

    def count(self, qset):
        return len(list(self.fetch(qset, -1, 0)))

    def _build_query_set(self, qset, orderings):

        kind = qset.model._meta.table

        def _query(item):
            name, op, value = item
            if op == 'in':
                return MultiQuery(
                    [Query(kind, {'%s =' % name: v}, orderings) for v in value], orderings)
            elif op == '!=':
                return MultiQuery(
                    [Query(kind, {'%s <' % name: value}, orderings),
                     Query(kind, {'%s >' % name: value}), orderings], orderings)
            else:
                return Query(kind, {'%s %s' % (name, op): value}, orderings)

        result = []
        for q in qset:
            if len(q.items) > 1:
                result.append(
                    MultiQuery([_query(item) for item in q.items], orderings))
            else:
                result.append(_query(q.items[0]))

        if not result:
            return [Query(kind, {}, orderings)]

        return result


class Query(datastore.Query):

    def __init__(self, kind, filters, orderings=None):
        super(Query, self).__init__(kind, filters)
        if orderings:
            self.Order(*orderings)

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


def sort_result(result, orderings):
    """A helper function to sort the final result.
    """
    try:
        name, how = orderings[0]
    except:
        return result

    def compare(a, b):
        if how == 2:
            return -cmp(a[name], b[name])
        return cmp(a[name], b[name])

    result.sort(compare)
    return result

