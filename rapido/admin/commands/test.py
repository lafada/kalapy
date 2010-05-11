import os

from rapido.admin import BaseCommand
from rapido.conf import settings

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
        
        if not args:
            args = [d for d in os.listdir('.') if os.path.exists(os.path.join(d, 'tests.py'))]
            args = [a for a in args if a in settings.INSTALLED_PACKAGES]
            
        if not args:
            raise self.error('No package installed yet.')

        from rapido import db
        from rapido.test import run_tests

        # load all models
        db.get_models()

        run_tests(args, 2)

