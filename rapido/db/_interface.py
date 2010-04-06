

class IDatabase(object):

    def __new__(cls, name):
        return object.__new__(cls, name)
    
    def __init__(self, name):
        self.name = name
    
    def connect(self):
        raise NotImplementedError
    
    def close(self):
        raise NotImplementedError
    
    def begin_transaction(self):
        raise NotImplementedError
    
    def end_transaction(self):
        raise NotImplementedError
    
    def commit(self):
        raise NotImplementedError
    
    def rollback(self):
        raise NotImplementedError           

    @staticmethod
    def get_databases():
        raise NotImplementedError
    
    @staticmethod
    def create(name):
        raise NotImplementedError
    
    @staticmethod
    def drop(name):
        raise NotImplementedError
    
    @staticmethod
    def dump(name):
        raise NotImplementedError
    
    @staticmethod
    def restore(name, dumpfile):
        raise NotImplementedError
    
    
class ITable(object):
    
    def __init__(self, name):
        self.name = name
    
    @staticmethod
    def exists(name):
        raise NotImplementedError
    
    @staticmethod
    def create(name):
        raise NotImplementedError
    
    @staticmethod
    def drop(name):
        raise NotImplementedError
    
    @staticmethod
    def rename(old_name, new_name):
        raise NotImplementedError
    
    def insert(self, **kw):
        raise NotImplementedError
    
    def update(self, key, **kw):
        raise NotImplementedError
    
    def delete(self, keys):
        raise NotImplementedError
    
    def column_exists(self, name):
        raise NotImplementedError
    
    def column_add(self, field):
        raise NotImplementedError
    
    def column_drop(self, field):
        raise NotImplementedError
    
    def column_alter(self, field, name=None, size=None, datatype=None):
        raise NotImplementedError
    
    def add_contraint(self, name, spec=None):
        """Add a contraint with the given name as specified in spec.       
        Only supposrts UNIQUE and CHECK contraints.
        
        >>> tbl.add_constraint("unq_name", "UNIQUE(name)")
        >>> tbl.add_constraint("chk_age", "CHECK(age >= 20)")
        """
        raise NotImplementedError
    
    def drop_contraint(self, name):
        """Drop the given contraint.
        """
        raise NotImplementedError
    

class IQuery(object):
    
    def filter(self, query, **kw):
        """Filter with the given query."
        
        >>> q.filter("name ILIKE :name AND age >= :age", name="some", age=20)
        """
        raise NotImplementedError
    
    def order(self, spec):
        """Order the query result with given spec.
        
        >>> q = q.filter("name ILIKE :name AND age >= :age", name="some", age=20)
        >>> q.order("-age")
        """
        raise NotImplementedError
    
    def fetch(self, limit, offset=0):
        """Fetch the given number of records from the query object from the given offset.
        
        >>> q = q.filter("name ILIKE :name AND age >= :age", name="some", age=20)
        >>> for obj in q.fetch(20):
        >>>     print obj.name
        """
        raise NotImplementedError
    
    def count(self):
        """Return the number of records in the query object.
        """
        raise NotImplementedError


