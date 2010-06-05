"""
rapido.db.query
~~~~~~~~~~~~~~~

This module implements Query class, which can be used to query for records
from the database.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.

"""
import re
from copy import deepcopy

from rapido.db.fields import FieldError


__all__ = ('Query',)


class Query(object):
    """The `Query` class provides methods to filter and fetch records from the
    database with simple pythonic conditions.

    >>> users = Query(User).filter("name = :name and age > :age", name="some", age=18)
    >>> users.order("-age")
    >>> first_ten = users.fetch(10, offset=0)
    >>> for user in first_ten:
    >>>     print "Name:", user.name

    The query string should not contain literal values but named parameters should
    be used to pass values.

    Also, `=` has special meaning, it stands for case-insensitive match (ilike in
    some dbms). You should use `==` for exact match.

    An instance of :class:`Query` can be constructed by passing :class:`Model`
    subclass as first argument. The contructor also accept a callable as a second
    argument to apply map on the result set.

    >>> names = Query(User, lambda obj: obj.name).filter('name = :name', name='some').fetch(-1)
    >>> print names
    ['some', 'someone', 'some1']

    :param model: a model, subclass of :class:`Model`
    :param mapper: a `callback` function to map query result
    """

    def __init__(self, model, mapper=None):
        """Create a new instance of :class:`Query` for the given `model`. The result
        set will be mapped with the given mapper.
        """
        if mapper and not callable(mapper):
            raise TypeError('mapper should be callable')

        self._model = model
        self._parser = Parser(model)
        self._all = []
        self._order = None
        self._mapper = mapper

    def __deepcopy__(self, meta):
        obj = self.__class__(self._model, self._mapper)
        obj._all = deepcopy(self._all, meta)
        obj._order = self._order
        return obj

    def filter(self, query, **kw):
        """Return a new :class:`Query` instance with the given query ANDed with
        current query set.

        >>> q = Query(User).filter('name = :name and age >= :age', name='some', age=20)
        >>> q1 = q.filter('dob >= :dob', dob='2001-01-01')
        >>> q2 = q.filter('dob < :dob', dob='2001-01-01')

        :param query: The query string
        :keyword kw: Mapping to the keywords bound the given query

        :raises: :class:`DatabaseError`, :class:`FieldError`
        :returns: A new instance of :class:`Query`
        """
        obj = deepcopy(self)
        obj._all.append(obj._parser.parse(query, **kw))
        return obj

    def order(self, spec):
        """Order the query result with given spec.

        >>> q = Query(User).filter("name = :name and age >= :age", name="some", age=20)
        >>> q.order("-age")

        :param spec: field name, if prefixed with `-` order by DESC else ASC
        """
        self._order = "ORDER BY"
        if spec.startswith('-'):
            self._order = "%s \"%s\" DESC" % (self._order, spec[1:])
        else:
            self._order = "%s \"%s\" ASC" % (self._order, spec)
        return self

    def fetch(self, limit, offset=None):
        """Fetch the given number of records from the query object from the given offset.

        If limit is `-1` fetch all records.

        >>> q = Query(User).filter("name = :name and age >= :age", name="some", age=20)
        >>> for obj in q.fetch(20):
        >>>     print obj.name

        :param limit: number of records to be fetch, if -1 fetch all
        :param offset: offset from where to fetch records should be >= 0
        :type limit: integer
        :type offset: integer or None

        :returns: list of model instances or content if mapper is applied
        :rtype: list
        """
        from rapido.db.engines import database

        s, params = self._build_select('*', limit, offset)
        result = map(self._model._from_database_values, database.select_from(s, params))
        if self._mapper:
            return map(self._mapper, result)
        return result

    def fetchone(self, offset=0):
        """Fetch a single record from the query object with given offset.

        :returns: model instance or None
        """
        res = self.fetch(1, offset)
        return res[0] if res else None

    def fetchall(self):
        """Fetch all records. An alias to :meth:`fetch` with limit as -1.
        """
        return self.fetch(-1)

    def first(self):
        """Fetch the first record from the query object.
        """
        return self.fetchone()

    def count(self):
        """Return the number of records in the query object.
        """
        from rapido.db.engines import database

        s, params = self._build_select('count("key")')
        return database.select_count(s, params)

    def delete(self):
        """Delete all records matched by this query.

        For example:

        >>> Query(User).filter('name = :name', name='some').delete()

        will delete all the User records matching the name like 'some'
        """
        for obj in self.fetch(-1):
            obj.delete()

    def update(self, **kw):
        """Update all the matched records with the given keywords mapping to
        the field properties of the model of this query.

        For example:

        >>> Query(User).filter('name = :name', name='some').update(lang='en_EN')

        will update all the User records matching name like 'some' by updating
        `lang` to `en_EN`.

        :keyword kw: keyword args mapping to the field properties
        """
        for obj in self.fetch(-1):
            for k, v in kw.items():
                if k in obj._meta.fields:
                    setattr(obj, k, v)
            obj.save()

    def _build_select(self, what, limit=None, offset=None):
        """Build the select query.

        .. warning::

            For internal use only.
        """
        query = "SELECT %s FROM \"%s\"" % (what, self._model._meta.table)
        if self._all:
            query = "%s WHERE %s" % (query, " AND ".join(['(%s)' % s for s, b in self._all]))
        if self._order:
            query = "%s %s" % (query, self._order)
        if limit > -1:
            query = "%s LIMIT %d" % (query, limit)
            if offset > -1:
                query = "%s OFFSET %d" % (query, offset)

        params = []
        for q, b in self._all:
            params.extend(b)

        return query, params

    def __getitem__(self, arg):
        if isinstance(arg, (int, long)):
            try:
                return self.fetch(1, arg)[0]
            except IndexError:
                raise IndexError('The query returned fewer then %r results' % arg)
        else:
            raise ValueError('Only integer indices are supported.')

    def __iter__(self):
        offset = -1
        try:
            while True:
                offset += 1
                yield self.fetch(1, offset)[0]
        except Exception:
            pass


class Parser(object):
    """Simple regex based query parser.

    .. todo: move to `engines` as an inteface and let backend engines provide
             engine specific implementation.
    """

    pat_stmt = re.compile('([\w]+)\s+(>|<|>=|<=|==|!=|=|in|not in)\s+(:([\w]+))', re.I)
    pat_splt = re.compile('\s+(and|or)\s+', re.I)

    op_alias = {
        '<': 'lt',
        '>': 'gt',
        '>=': 'gte',
        '<=': 'lte',
        '==': 'eq',
        '!=': 'neq',
        '=': 'like',
        'in': 'in',
        'not in': 'not_in',
    }

    def __init__(self, model):
        self.model = model

    def split(self, query):
        """Split the query by `and` or `or` and return list of list of substrings.
        """
        return self.pat_splt.split(query)

    def statement(self, query, params):
        """Process the simple query statement.

        :param query: query substring, splited by `split`
        :param params: substitution values

        :returns:
            A tuple `(str, list)` where `str` is the statement and list of
            values to be bounded to the statement.
        :rtype: tuple
        """
        try:
            name, op, __var, var = self.pat_stmt.match(query).groups()
        except:
            raise Exception('Malformed query: %s', query)

        if name not in self.model._meta.fields:
            raise FieldError('No such field %r in model %r' % (
                name, self.model._meta.name))

        field = self.model._meta.fields[name]

        op = op.lower()
        op = self.op_alias.get(op, op)

        handler = getattr(self, 'handle_%s' % op)
        validator = getattr(self, 'validate_%s' % op, self.validate)
        value = validator(field, params[var])

        return handler(name, value), value

    def validate(self, field, value):
        return field.python_to_database(value)

    def validate_in(self, field, value):
        assert isinstance(value, (list, tuple))
        return [field.python_to_database(v) for v in value]

    def validate_not_in(self, field, value):
        return self.validate_in(field, value)

    def handle_in(self, name, value):
        return '"%s" IN (%s)' % (name, ', '.join(['%s'] * len(value)))

    def handle_not_in(self, name, value):
        assert isinstance(value, (list, tuple))
        return '"%s" NOT IN (%s)' % (name, ', '.join(['%s'] * len(value)))

    def handle_like(self, name, value):
        return '"%s" LIKE %%s' % (name)

    def handle_eq(self, name, value):
        return '"%s" = %%s' % (name)

    def handle_neq(self, name, value):
        return '"%s" != %%s' % (name)

    def handle_gt(self, name, value):
        return '"%s" > %%s' % (name)

    def handle_lt(self, name, value):
        return '"%s" < %%s' % (name)

    def handle_gte(self, name, value):
        return '"%s" >= %%s' % (name)

    def handle_lte(self, name, value):
        return '"%s" <= %%s' % (name)

    def parse(self, query, **params):

        bindings = []
        statements = self.split(query)

        for i, part in enumerate(statements):
            if part.upper() in ('AND', 'OR'):
                statements[i] = part.upper()
            else:
                statements[i], value = self.statement(part, params)
                if isinstance(value, (list, tuple)):
                    bindings.extend(value)
                else:
                    bindings.append(value)

        return " ".join(statements), bindings

