"""This module defines several interfaces to be implemented by database engines.
The implementation is meant for internal use only. Users should use the Model
API instead.
"""

from threading import local

from _errors import DatabaseError
from _model import cache as model_cache


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

    def create(self):
        """Create the database if it doesn't exist.
        """
        raise NotImplementedError

    def drop(self):
        """Drop the database.
        """
        raise NotImplementedError

    def cursor(self):
        """Return a dbapi2 complaint cursor instance.
        """
        raise NotImplementedError

    def select(self, entity, condition):
        """Select all the records of the given entity that passes 
        the given condition.

        Args:
            entity: the name of the entity on which to perform query
            condition: the filter condition

        Returns:
            a list of all records matched.
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


class IEntity(object):
    """The Entity interface, low level representation of the main storage 
    structure of the particular database engine.  For example, `table` in RDMBS
    and `entity` in BigTable.
    """

    def __init__(self, name):
        """Initialize the entity for the given model name

        Args:
            name: model name of the entity
        """
        self._model_name = name
        self._name = name.replace('.', '_')

    @property
    def cursor(self):
        return self.database.cursor()

    @property
    def name(self):
        return self._name

    @property
    def database(self):
        return self.__class__._database

    @property
    def model(self):
        return model_cache.get_model(self._model_name)

    def schema(self):
        """Get the schema representation of the entity.
        """
        raise NotImplementedError

    def exists(self):
        """Check whether the entity exists in the database.
        """
        raise NotImplementedError

    def create(self):
        """Create a new entity in the database if it doesn't exist.
        """
        raise NotImplementedError

    def drop(self):
        """Drop the current entity if it exists.
        """
        raise NotImplementedError

    def rename(self, new_name):
        """Rename the current entity with the given new name.

        Args:
            new_name: the new name for the entity
        """
        raise NotImplementedError

    def insert(self, **kw):
        """Insert a record to the entity with the given values.

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
        """Delete all the records from the entity identified with the
        given keys.

        Args:
            keys: list of keys
        """
        raise NotImplementedError

    def field_exists(self, field):
        """Check whether a field exists in the entity.

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
        """Change the definition of the entity field with the changed 
        attributes of the given field.

        Args:
            field: an instance of `db.Field`
        """
        raise NotImplementedError
