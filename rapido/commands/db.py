from _base import BaseCommand

from rapido.db.engines import database


class DBCommand(BaseCommand):
    args = "<package package ...>"
    

class Schema(DBCommand):
    
    name = "db-schema"
    help = "print the database shema"
    args = "[args]"
    
    def execute(self, *args, **options):
        pass
    
class Sync(DBCommand):
    
    name = "db-sync"
    help = "sync database"
    args = "[args]"
    
    def execute(self, *args, **options):
        pass
    
class Reset(DBCommand):
    
    name = "db-reset"
    help = "CAUTION: destructive, will drop all existing tables from the database."
    args = "[args]"
    
    def execute(self, *args, **options):
        pass
    
class Backup(DBCommand):
    
    name = "db-backup"
    help = "backup the database."
    args = ""
    
class Restore(DBCommand):
    
    name = "db-restore"
    help = "restore the database from the given dump file."
    args = ""
    
    
