import re


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

    def __init__(self, model):
        """Create a new Query for the given model.

        Args:
            model: the model
        """
        self._model = model
        self._parser = Parser()
        self._all = []
        self._order = None

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
        
        >>> q = Query(User).filter("name ilike :name and age >= :age", name="some", age=20)
        >>> for obj in q.fetch(20):
        >>>     print obj.name
        """
        s = self._select('*', limit, offset)
        params = []
        for q, b in self._all:
            params.extend(b)

        table = self._model._table
        return table.select(s, params)

    def count(self):
        """Return the number of records in the query object.
        """
        table = self._model._table
        s = self._select('count("id")')
        params = []
        for q, b in self._all:
            params.extend(b)
        return table.count(s, params)

    def _select(self, what, limit=None, offset=None):
        """Build the select statement. For internal use only.
        """
        result = "SELECT %s FROM \"%s\"" % (what, self._model._table._name)
        if self._all:
            result = "%s WHERE %s" % (result, " AND ".join(['(%s)' % s for s, b in self._all]))
        if self._order:
            result = "%s %s" % (result, self._order)
        if limit:
            result = "%s LIMIT %d" % (result, limit)
        if offset is not None:
            result = "%s OFFSET %d" % (result, offset)
        return result

    def __str__(self):
        return self._select('*')

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
            raise Exception('Maleformed query: %s', query)

        op = op.lower()
        op = self.op_alias.get(op, op)

        handler = getattr(self, 'handle_%s' % op)
        value = params[var]
        return handler(name, value), value

    def handle_in(self, name, value):
        assert isinstance(value, (list, tuple))
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

