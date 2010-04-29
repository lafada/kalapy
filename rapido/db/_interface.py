"""This module defines several interfaces to be implemented by database engines.
The implementation is meant for internal use only. Users should use the Model
API instead.
"""

from threading import local

from _errors import DatabaseError
from _model import get_model

class IDatabase(local):
    """The Database interface. The backend engines should implement this 
    interface with a class Database.
    """

    data_types = {}

    def __init__(self, name, host=None, port=None, user=None, password=None, autocommit=False):
        """Initialize the database.

        Args:
            name: the name of the database
            host: the hostname where the database server is running
            port: the port on which the database server is listening
            user: the user name to connect to the database
            password: the database password
            autocommit: whether to enable autocommit or not
        """
        self.name = name
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.autocommit = autocommit

    def connect(self):
        """Connect to the database.
        """
        raise NotImplementedError

    def close(self):
        """Close the database connection.
        """
        raise NotImplementedError

    def commit(self):
        """Commit the changes to the database.
        """
        raise NotImplementedError

    def rollback(self):
        """Rollback all the changes made since the last commit.
        """
        raise NotImplementedError

    def cursor(self):
        """Return a dbapi2 complaint cursor instance.
        """
        raise NotImplementedError

    def get_data_type(self, field):
        """Get the internal datatype for the given field supported by the database.
        """
        try:
            res = self.data_types[field.data_type]
            return "%s(%s)" % (res, field.size) if field.size else res
        except KeyError:
            raise DatabaseError("Unsupported datatype '%s'" % field.data_type)


class ITable(object):
    """Table interface. Backend engines should implement this interface 
    with name `Table`.
    """

    def __init__(self, model):
        """Initialize the table for the given model class

        Args:
            model: the model class
        """
        self._model_name = model._model_name
        self._name = model._model_name.replace('.', '_')

    @property
    def name(self):
        return self._name

    @property
    def database(self):
        return self.__class__._database
    
    @property
    def model(self):
        return get_model(self._model_name)

    def schema(self):
        """Get the schema representation of the table.
        """
        raise NotImplementedError

    def exists(self):
        """Check whether the table exists in the database.
        """
        raise NotImplementedError

    def create(self):
        """Create a new table in the database if it doesn't exist.
        """
        raise NotImplementedError

    def drop(self):
        """Drop the current table if it exists.
        """
        raise NotImplementedError

    def rename(self, new_name):
        """Rename the current table with the given new name.

        Args:
            new_name: the new name for the table
        """
        raise NotImplementedError

    def insert(self, **kw):
        """Insert a record to the table with the given values.

        Args:
            **kw: the key, value pairs for the given record.
        """
        raise NotImplementedError

    def update(self, key, **kw):
        """Update a particular record identified with the given key.

        Args:
            key: the key to identify the record
            **kw: the items to be updated
        """
        raise NotImplementedError

    def delete(self, keys):
        """Delete all the records from the table identified with the
        given keys.

        Args:
            keys: list of keys
        """
        raise NotImplementedError

    def select(self, query, params):
        """Execute the given select query bounded with the given params
        and return list of model instances represented by this table.

        Args:
            query: select query
            params: bounding values

        Returns:
            list of model instances
        """
        raise NotImplementedError

    def count(self, query, params):
        """Same as `select` but returns total number of records counted
        by the given query.

        Args:
            query: select count query
            params: bounding values

        Returns:
            integer, total number of records counted
        """
        raise NotImplementedError

    def field_exists(self, field):
        """Check whether a field exists in the table.

        Args:
            field: an instance of `db.Field`
        """
        raise NotImplementedError

    def field_add(self, field):
        """Add the field if it doesn't exist.
        Args:
            field: an instance of `db.Field`
        """
        raise NotImplementedError

    def field_drop(self, field):
        """Drop the given field.
        Args:
            field: an instance of `db.Field`
        """
        raise NotImplementedError

    def field_alter(self, field):
        """Change the definition of the table field with the changed 
        attributes of the given field.

        Args:
            field: an instance of `db.Field`
        """
        raise NotImplementedError
