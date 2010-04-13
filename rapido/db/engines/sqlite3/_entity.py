
from rapido.db._interface import IEntity


class Entity(IEntity):

    def __init__(self, database, name):
        super(IEntity, self).__init__(database, name)
        
    def cursor(self):
        return self.database.cursor()
    
    def exists(self):
        cursor = self.cursor()
        try:
            cursor.execute("""
            SELECT name FROM sqlite_master 
                WHERE type = 'table' AND name = ?;
            """, (self.name,))
            return bool(cursor.fetchone())
        finally:
            cursor.close()
    
    def create(self):
        cursor = self.cursor()
        try:
            cursor.execute("""
            CREATE TABLE %s (
                key INTEGER PRIMARY KEY AUTOINCREMENT
            );
            """ % (self.name,))
        
            #TODO: update table definition
        finally:
            cursor.close()
    
    def drop(self):
        cursor = self.cursor()
        try:
            cursor.execute("DROP TABLE %s" % (self.name,))
            return True
        finally:
            cursor.close()
    
    def rename(self, new_name):
        curr = self.cursor()
        try:
            curr.execute('ALTER TABLE %s RENAME TO %s' % (self.name, new_name,))
        finally:
            curr.close()
    
    def insert(self, **kw):
        
        items = kw.items()
        keys = [x[0] for x in items]
        vals = [x[1] for x in items]
        
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (
                self.name, 
                ", ".join(keys), 
                ", ".join(['?'] * len(vals)))
        
        curr = self.cursor()
        try:
            curr.execute(sql, vals)
        finally:
            curr.close()
        
    def update(self, key, **kw):
        raise NotImplementedError
    
    def delete(self, keys):
        curr = self.cursor()
        sql = "DELETE FROM %s WHERE id IN %s" % (self.name, tuple(keys))
        curr.execute(sql)
    
    def column_exists(self, field):
        raise NotImplementedError
    
    def column_add(self, field):
        #TODO: generate sql from field
        curr = self.cursor()
        curr.execute("""
        ALTER TABLE %s
            ADD COLUMN %s TEXT
        """ % (self.name, field))
        curr.close()
    
    def column_drop(self, field):
        #XXX: not supported
        pass
        
    def column_alter(self, field, name=None, size=None, datatype=None):
        #XXX: not supported
        pass
    
