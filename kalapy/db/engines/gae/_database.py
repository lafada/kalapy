import re

try:
    from google.appengine.api import datastore
except ImportError:
    from _utils import setup_stubs
    setup_stubs()
    from google.appengine.api import datastore


from kalapy.db.engines.interface import IDatabase
from kalapy.db.model import Model


__all__ = ('DatabaseError', 'IntegrityError', 'Database')


_OPERATORS = ['<', '<=', '>', '>=', '=', '==', '!=', 'in']
_FILTER_REGEX = re.compile(
    '^\s*([^\s]+)(\s+(%s)\s*)?$' % '|'.join(_OPERATORS),
    re.IGNORECASE | re.UNICODE)


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
        return True

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
                obj._entity = entity = datastore.Entity(obj._meta.table)
            else:
                entity = obj._entity

            #TODO: convert values to GAE supported datatypes

            entity.update(items)
            obj._key = datastore.Put(entity)

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
        queries, orderings = self._build_queries(qset)

        entities = {}
        for query in queries:
            for e in query.Get(limit, offset):
                if e.key() in entities:
                    continue
                entities[e.key()] = e

        mq = MultiQuery([SortQuery('__none__', entities.values())], orderings)
        entities = mq.Get(limit, offset)

        return [dict(e, key=str(e.key())) for e in entities]

    def count(self, qset):
        return len(self.fetch(qset, -1, 0))

    def _query(self, kind, item, orderings):
        operator, value = item
        match = _FILTER_REGEX.match(operator)
        prop = match.group(1)
        op = '==' if match.group(3) is None else match.group(3)
        if op == 'in':
            assert isinstance(value, (list, tuple)), 'in operator requires list or tuple value'
            return MultiQuery(
                [Query(kind, {'%s =' % prop: v}) for v in value], orderings)
        elif op == '!=':
            return MultiQuery(
                [Query(kind, {'%s <' % prop: value}),
                 Query(kind, {'%s >' % prop: value})], orderings)
        else:
            return Query(kind, {'%s %s' % (prop, op): value})

    def _build_queries(self, qset):

        kind = qset.model._meta.table
        orderings = []

        result = []
        for q in qset:
            if len(q.items) > 1:
                result.append(MultiQuery(
                    [self._query(kind, item, orderings) for item in q.items], orderings))
            else:
                result.append(self._query(kind, q.items[0], orderings))

        if not result:
            return [datastore.Query(kind, {})], orderings
        return result, orderings


class Query(datastore.Query):

    def IsKeysOnly(self):
        return False


class MultiQuery(datastore.MultiQuery):

    def IsKeysOnly(self):
        return False


class SortQuery(Query):
    """This class is used to sort the final result.
    """
    def __init__(self, kind, result):
        super(SortQuery, self).__init__(kind, {})
        self.result = result

    def Run(self, **kw):
        return iter(self.result)

