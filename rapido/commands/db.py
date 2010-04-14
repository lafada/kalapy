
from _base import BaseCommand

class DBCommand(BaseCommand):
    
    name = "db"
    help = "database commands"
    args = "[args]"
    
    def execute(self, *args, **options):
        pass
    
