import os
import sqlite3

from rapido.db._errors import DatabaseError
from rapido.db._interface import IDatabase

from _entity import Entity


class Database(IDatabase):
    
    def __init__(self, name, host=None, port=None, user=None, password=None, autocommit=False):
        super(Database, self).__init__(name, host, port, user, password, autocommit)
        self.connection = None
        
    def connect(self):

        if self.connection is not None:
            return self

        if self.name != ":memory:":
            if not os.path.isfile(self.name):
                raise DatabaseError("Database '%s' doesn't exist." % self.name)

        if self.connection is None:
            self.connection = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)

        if self.autocommit:
            self.connection.isolation_level = None

        return self
    
    def close(self):
        self.connection = None

    def commit(self):
        self.connection.commit()
    
    def rollback(self):
        self.connection.rollback()

    def create(self):
        # SQLite database will be created automatically upon connect
        self.connect()
        self.close()
        return self
    
    def drop(self):
        self.close()
        if self.name == ":memory:":
            return
        os.remove(self.name)

    def cursor(self):
        return self.connection.cursor()

    def get(self, entity):
        return Entity(self, entity)

    def select(self, entity, condition):
        raise NotImplementedError("Not implemented yet.")

