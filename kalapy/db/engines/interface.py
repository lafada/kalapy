"""
kalapy.db.engines.interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module defines the database interface to be implemented by backend engines.
The implementation is meant for internal use only. Users should use Model API
instead.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""

class IDatabase(object):
    """The database interface. Backend engines should implement this class
    with name `Database`.

    :param name: the name of the database
    :param host: the hostname where the database server is running
    :param port: the port on which the database server is listening
    :param user: the user name to connect to the database
    :param password: the database password
    """

    #: mimetype of return value of :meth:`schema_table`.
    schema_mime = "text/plain"

    def __init__(self, name, host=None, port=None, user=None, password=None):
        """Initialize the database.
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

    def schema_table(self, model):
        """Returns the schema information of the table for the given model.

        :param model: a subclass of :class:`Model`

        :returns: textual representaion of the model in the database
        """
        raise NotImplementedError

    def exists_table(self, name):
        """Check whether the table exists or not.

        :param name: name of the table

        :returns: True if table exists else False
        """
        raise NotImplementedError

    def create_table(self, model):
        """Create a table for the given model if it doesn't exist.

        :param model: a subclass of :class:`Model`
        """
        raise NotImplementedError

    def alter_table(self, model, name=None):
        """Alter the table associated for the given model. If name is given look
        for the table by that name (if model class name has been changed).

        :param model: a subclass of :class:`Model`
        :param name: if given, should be the name of table
        """
        raise NotImplementedError

    def drop_table(self, name):
        """Drop the table

        :param name: name of the table
        """
        raise NotImplementedError

    def update_records(self, instance, *args):
        """Update database records for the given model instances.

        The implementation should take care of:

            - Inserting records if records doesn't exist.
            - Updating `key` value of the given model instances.

        :param instance: an instance of :class:`Model` subclass
        :param args: more instances

        :returns: list of key values
        :raises:
            - :class:`DatabaseError`
            - :class:`IntegrityError`
        """
        raise NotImplementedError

    def delete_records(self, instance, *args):
        """Delete database records for the given model instances. This method
        also accepts keys.

        The implementation should take care of:

            - Updating `key` value of the given model instances to None.

        :param instance: a Model instance or a record key
        :param args: more Model instances or record keys

        :returns: list of key values which have been deleted.
        :raises:
            - :class:`DatabaseError`
            - :class:`IntegrityError`
        """
        raise NotImplementedError

    def select_from(self, query, params):
        """Execute the select query bound with the given params.

        :param query: the select query
        :param params: list of values bound to the query

        :returns: dict of name, value of the resultset
        :raises:
            - :class:`DatabaseError`
        """
        raise NotImplementedError

    def select_count(self, query, params):
        """Execute select count query bound with the given params.

        :param query: the select query
        :param params: list of values bound to the query

        :returns: integer, total number of records
        :raises:
            - :class:`DatabaseError`
        """
        raise NotImplementedError

