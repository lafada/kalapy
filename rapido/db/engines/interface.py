"""
This module defines the database interface to be implemented by backend engines.
The implementation is meant for internal use only. Users should use Model API
instead.
"""

from threading import local

class IDatabase(local):
    """The database interface. Backend engines should implement this class
    with name `Database`.
    """
    
    data_types = {}
    
    def __init__(self, name, host=None, port=None, user=None, password=None):
        """Initialize the database.

        Args:
            name: the name of the database
            host: the hostname where the database server is running
            port: the port on which the database server is listening
            user: the user name to connect to the database
            password: the database password
        """
        self.name = name
        self.host = host
        self.port = port
        self.user = user
        self.password = password
    
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
        """Get the internal datatype for the given field supported by the 
        database.
        """
        try:
            return self.data_types[field.data_type] % dict(
                [(k, getattr(field, k)) for k in dir(field)])
        except KeyError:
            from rapido.db.engines import DatabaseError
            raise DatabaseError("Unsupported datatype '%s'" % field.data_type)
    
    def schema_table(self, model):
        """Returns the schema information of the table for the given model.
        """
        raise NotImplementedError
    
    def exists_table(self, name):
        """Check whether the table exists or not.
        """
        raise NotImplementedError
    
    def create_table(self, model):
        """Create a table for the given model if it doesn't exist.
        """
        raise NotImplementedError
    
    def alter_table(self, model, name=None):
        """Alter the table associated for the given model. If name is given look
        for the table by that name (if model class name has been changed).
        """
        raise NotImplementedError
    
    def drop_table(self, name):
        """Drop the table
        """
        raise NotImplementedError

    def update_records(self, instance, *args):
        """Update database records for the given model instances.

        The implementation should take care of:

            - Inserting records if records doesn't exist.
            - Updating `key` value of the given model instances.

        Args:
            instance: a Model instance
            *args: more Model instances

        Returns:
            list of key values
        """
        raise NotImplementedError

    def delete_records(self, instance, *args):
        """Delete database records for the given model instances. This method
        also accepts keys.

        The implementation should take care of:

            - Updating `key` value of the given model instances to None.

        Args:
            instance: a Model instance or a record key
            *args: more Model instances or record keys

        Returns:
            list of key values which have been deleted.
        """
        raise NotImplementedError
    
    def select_from(self, query, params):
        """Execute the select query bound with the given params.
        
        Args:
            query: the select query
            params: list of values bound to the query
            
        Returns:
            dict of name, value of the resultset
        """
        raise NotImplementedError
    
    def select_count(self, query, params):
        """Execute select count query bound with the given params.
        
        Args:
            query: the select query
            params: list of values bound to the query
            
        Returns:
            integer, total number of records
        """
        raise NotImplementedError
    
