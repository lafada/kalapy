"""
This module defines several interfaces to be implemented by database engines.
The implementation is meant for internal use only. Users should use the Model
api instead.
"""

class IDatabase(object):
    """The Database interface. The backend engines should implement this 
    interface with a class Database.
    """

    data_types = {}
    
    def __init__(self, name, host=None, port=None, user=None, password=None, autocommit=False):
        """Initialize the database.

        Args:
            name: the name of the database
            host: the hostname where the database server is running
            port: the port on which the database server is listning
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
        """Return a dbapi2 compiant cursor instance.
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

    def get_data_type(self, kind, size=None):
        try:
            res = self.data_types[kind]
        except KeyError:
            raise DatabaseError("Unsupported datatype '%s'" % kind)

        return "%s(%s)" % (res, size) if size else res


class IEntity(object):
    """The Entity inteface, low level representation of the main storage 
    structure of the perticular database engine.  For example, `table` in RDMBS
    and `entity` in BigTable.
    """

    def __init__(self, database, name):
        """Initialize the entity instance.

        Args:
            database: the database instance
            name: name of the entity
        """
        self.database = database
        self.name = name
    
    def exists(self):
        """Check whether the entiry exists in the database.
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
        """Rename the current entiry with the given new name.

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
        """Update a perticular record identified with the given key.

        Args:
            key: the key to identify the record
            **kw: the items to be updated
        """
        raise NotImplementedError
    
    def delete(self, keys):
        """Delete all the records from the entiry identified with the
        given keys.

        Args:
            keys: list of keys
        """
        raise NotImplementedError

    
    def column_exists(self, name):
        """Check whether the given column exists in the entiry.
        Args:
            name: the name of a column
        """
        raise NotImplementedError
    
    def column_add(self, field):
        """Add a column for the given `field`.
        Args:
            field: an instance of perticular Field type
        """
        raise NotImplementedError
    
    def column_drop(self, field):
        """Drop the given field.
        Args:
            field: an instance of perticular Field type or name of the column
        """
        raise NotImplementedError
    
    def column_alter(self, field):
        """Change the definition of the column with the changed 
        attribures of the field.

        Args:
            field: an instance of Field type
        """
        raise NotImplementedError
    

