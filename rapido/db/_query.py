import re

from _errors import FieldError


__all__ = ('Query',)


class Query(object):
    """The query object. It provides methods to filter and fetch records
    from the database with simple pythonic conditions.

    >>> users = Query(User).filter("name = :name and age > :age", name="some", age=18)
    >>> users.order("-age")
    >>> first_ten = users.fetch(10, offset=0)
    >>> for user in first_ten:
    >>>     print "Name:", user.name

    The query string should not contain literal values but named parameters should be
    used to pass values.

    Also, `=` has special meaning, it stands for case-insensitive match (ilike in some dbms).
    You should use `==` for exact match.
    """

    def __init__(self, model, mapper=None):
        """Create a new Query for the given model. The result set will be mapped
        with the given mapper.

        Args:
            model: the model
            mapper: a callback function to map query result
        """
        if mapper and not callable(mapper):
            raise TypeError('mapper should be callable')

        self._model = model
        self._parser = Parser(model)
        self._all = []
        self._order = None
        self._mapper = mapper

    def filter(self, query, **kw):
        """Filter with the given query."
        
        >>> Query(User).filter("name ilike :name and age >= :age", name="some", age=20)
        """
        self._all.append(self._parser.parse(query, **kw))
        return self

    def order(self, spec):
        """Order the query result with given spec.
        
        >>> q = Query(User).filter("name ilike :name and age >= :age", name="some", age=20)
        >>> q.order("-age")
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
        
        >>> q = Query(User).filter("name ilike :name and age >= :age", name="some", age=20)
        >>> for obj in q.fetch(20):
        >>>     print obj.name

        Args:
            limit: number of records to be fetch, if -1 fetch all
            offset: offset from where to fetch records should be >= 0
        """
        s = self._select('*', limit, offset)
        params = []
        for q, b in self._all:
            params.extend(b)

        from rapido.db.engines import database

        result = map(self._model._from_db_values, database.select_from(s, params))
        if self._mapper:
            return map(self._mapper, result)
        return result

    def count(self):
        """Return the number of records in the query object.
        """
        table = self._model._table
        s = self._select('count("id")')
        params = []
        for q, b in self._all:
            params.extend(b)
            
        from rapido.db.engines import database
        return database.select_count(s, params)

    def _select(self, what, limit=None, offset=None):
        """Build the select statement. For internal use only.
        """
        result = "SELECT %s FROM \"%s\"" % (what, self._model._meta.table)
        if self._all:
            result = "%s WHERE %s" % (result, " AND ".join(['(%s)' % s for s, b in self._all]))
        if self._order:
            result = "%s %s" % (result, self._order)
        if limit > -1:
            result = "%s LIMIT %d" % (result, limit)
            if offset > -1:
                result = "%s OFFSET %d" % (result, offset)
        return result

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
        except Exception, e:
            pass


class Parser(object):
    """Simple regex based query parser.
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

    name_alias = {
        'key': 'id',
    }

    def __init__(self, model):
        self.model = model

    def split(self, query):
        """Split the query by `and` or `or` and return list of list of substrings.
        """
        return self.pat_splt.split(query)

    def statement(self, query, params):
        """Process the simple query statement.

        Args:
            query: query substring, splited by `split`
            params: substitution values

        Returns:
            a tuple (str, list) where str is the statement and list of values
            to be bounded to the statement.
        """
        try:
            name, op, var_, var = self.pat_stmt.match(query).groups()
        except:
            raise Exception('Malformed query: %s', query)

        if name.lower() not in self.name_alias and \
                name not in self.model._meta.fields:
            raise FieldError('No such field %r in model %r' % (
                name, self.model._meta.name))

        name = self.name_alias.get(name, name)
        field = self.model._meta.fields[name]

        op = op.lower()
        op = self.op_alias.get(op, op)
        name = self.name_alias.get(name.lower(), name)

        handler = getattr(self, 'handle_%s' % op)
        validator = getattr(self, 'validate_%s' % op, lambda f, v: v)
        value = validator(field, params[var])

        return handler(name, value), value

    def validate_in(self, field, value):
        assert isinstance(value, (list, tuple))
        return [field.to_database(v) for v in value]

    def handle_in(self, name, value):
        return '"%s" IN (%s)' % (name, ', '.join(['?'] * len(value)))

    def handle_not_in(self, name, value):
        assert isinstance(value, (list, tuple))
        return '"%s" NOT IN (%s)' % (name, ', '.join(['?'] * len(value)))

    def handle_like(self, name, value):
        return '"%s" LIKE ?' % (name)

    def handle_eq(self, name, value):
        return '"%s" = ?' % (name)

    def handle_neq(self, name, value):
        return '"%s" != ?' % (name)

    def handle_gt(self, name, value):
        return '"%s" > ?' % (name)

    def handle_lt(self, name, value):
        return '"%s" < ?' % (name)

    def handle_gte(self, name, value):
        return '"%s" >= ?' % (name)

    def handle_lte(self, name, value):
        return '"%s" <= ?' % (name)

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

