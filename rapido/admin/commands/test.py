
from rapido.admin import BaseCommand

class TestCommand(BaseCommand):

    name = 'test'
    args = 'package [package [package [...]]]'
    help = 'Run the test suite for speficied packages.'
    scope = 'package'

    def execute(self, *args, **options):

        if not args:
            self.print_help()

        from rapido import db
        from rapido.test import run_tests

        # load all models
        db.get_models()

        run_tests(args, 2)

