"""
kalapy.admin.commands.db
~~~~~~~~~~~~~~~~~~~~~~~~

This module implements `database` command to be used to perform
database specific admin tasks.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LINCESE for more details.
"""
import sys

from kalapy import db
from kalapy.admin import ActionCommand
from kalapy.conf import settings
from kalapy.conf.loader import loader
from kalapy.db.engines import database


try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_mimetype
    from pygments.formatters import TerminalFormatter

    lexer = get_lexer_for_mimetype(database.schema_mime)
    formatter = TerminalFormatter()

    def print_colorized(text):
        if sys.stdout.isatty():
            text = highlight(text, lexer, formatter).strip()
        sys.stdout.write(text)
        sys.stdout.write('\n')

#except ImportError:
except:
    def print_colorized(text):
        sys.stdout.write(text)
        sys.stdout.write('\n')


class DBCommand(ActionCommand):
    """Perform database related tasks.
    """
    name = 'database'
    usage = '%name <action> [options]'

    def execute(self, options, args):

        if settings.DATABASE_ENGINE == "dummy":
            raise self.error("DATABASE_ENGINE is not configured.")

        database.connect()
        try:
            # load packages
            loader.load()
            super(DBCommand, self).execute(options, args)
        finally:
            database.close()

    def get_models(self, *packages):
        """Similar to `db.get_models` but returns a tuple, (list of models,
        list of models referenced from other packages)

        Where list of models will be sorted according to relationships to ensure
        a model comes next to models it referencing.

        :param packages: sequence of package names
        :returns: a tuple
        """
        models = db.get_models(*packages)

        result = []
        pending = []

        def adjust_models(args):
            for model in args:
                if model in result or model in pending:
                    continue
                if model._meta.ref_models:
                    adjust_models([m for m in model._meta.ref_models if m != model])
                if model in models:
                    result.append(model)
                else:
                    pending.append(model)

        adjust_models(models)

        return result, pending

    def action_info(self, options, packages):
        """Show the table schema for the given packages
        """
        if not packages:
            raise self.error('no package name provided.')
        models, pending = self.get_models(*packages)
        for model in models:
            print_colorized(database.schema_table(model))
        if pending:
            print_colorized('\n-- the following tables should also be added (from other packages)\n')
            for model in pending:
                print_colorized('  -- %s' % model._meta.table)
            print

    def action_sync(self, options, args):
        """Create the database tables for all the INSTALLED_PACKAGES whose
        tables haven't been created yet.
        """
        models, __pending = self.get_models()
        try:
            for model in models:
                if options.verbose:
                    print "Sync table %r" % (model._meta.table)
                database.create_table(model)
        except:
            database.rollback()
            raise
        else:
            database.commit()

    def action_reset(self, options, args):
        """Reset the model tables. Use with care, will drop all the tables.
        """

        ans = raw_input("""
Be careful, all the tables of database %r will be dropped.
All the data stored in the database will be lost too.

Are you sure about this action? (y/N): """ % settings.DATABASE_NAME)

        if ans.lower() != 'y': return

        models, __pending = self.get_models()
        models.reverse()
        try:
            for model in models:
                if options.verbose:
                    print "Drop table %r" % model._meta.table
                database.drop_table(model._meta.table)
        except:
            database.rollback()
            raise
        else:
            database.commit()

        self.action_sync(options, args)

