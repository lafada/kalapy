import os

from rapido.admin import BaseCommand, get_command
from rapido.conf import settings
from rapido.test import run_tests

class TestCommand(BaseCommand):

    name = 'test'
    args = '[name [name [name [...]]]]'
    help = ('Run the specified tests names. A test name can be,\n'
            '  package_name of an installed package or\n'
            '  package_name.TestClass or\n'
            '  package_name.TestClass.test_something\n\n'
            'If test names are not given run all the tests of the installed packages.')
    scope = 'package'

    def execute(self, *args, **options):
        
        dbname = settings.DATABASE_NAME
        if settings.DATABASE_ENGINE == 'sqlite3':
            dbname = os.path.basename(dbname)
        if dbname and not dbname.lower().startswith('test_'):
            self.error("Invalid database %r, test database name must start with 'test_'" % dbname)
                    
        if not args:
            args = [d for d in os.listdir('.') if os.path.exists(os.path.join(d, 'tests.py'))]
            args = [a for a in args if a in settings.INSTALLED_PACKAGES]
            
        if not args:
            raise self.error('No package installed yet.')
        
        # sync tables
        cmd = get_command('database')()
        cmd.execute(sync=True)
        
        run_tests(args, 2 if self.verbose else 0)

