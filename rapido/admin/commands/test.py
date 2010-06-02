"""
rapido.admin.commands.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements `test` command to run testsuites.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LINCESE for more details.
"""
import os

from rapido.admin import Command, execute_command
from rapido.conf import settings
from rapido.test import run_tests


class TestCommand(Command):
    """Run the specified tests names. A test name can be,

        package_name of an installed package or
        package_name.TestClass or
        package_name.TestClass.test_something

    If test names are not given run all the tests of the installed packages.
    """
    name = 'test'
    usage = '%name [name [name [name [...]]]]'

    def execute(self, options, args):

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

        # sync database tables
        execute_command(['database', 'sync'])

        run_tests(args, 2 if options.verbose else 0)

