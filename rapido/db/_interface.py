"""
This module defines the database interface to be implemented by backend engines.
The implementation is meant for internal use only. Users should use Model API
instead.
"""

from threading import local

from _errors import DatabaseError


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
        """Get the internal datatype for the given field supported by the database.
        """
        try:
            res = self.data_types[field.data_type]
            return "%s(%s)" % (res, field.size) if field.size else res
        except KeyError:
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
    
    def insert_into(self, instance):
        """Insert the model instance into database table.
        
        Args:
            instance: an instance of Model
        """
        raise NotImplementedError
    
    def update_table(self, instance):
        """Update the model instance into database table.
        
        Args:
            instance: and instance of Model
        """
        raise NotImplementedError
    
    def delete_from(self, instance):
        """Delete the model instance from the database table.
        """
        raise NotImplementedError
    
    def delete_by_keys(self, model, keys):
        """Delete all the records from model table referenced by the given keys.
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
    
