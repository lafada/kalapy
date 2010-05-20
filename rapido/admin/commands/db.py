import sys
from optparse import make_option


from rapido.admin import BaseCommand
from rapido.conf import settings
from rapido.conf.loader import loader

from rapido import db
from rapido.db import transaction
from rapido.db.engines import database

try:
    from pygments import highlight
    from pygments.lexers import SqlLexer
    from pygments.formatters import TerminalFormatter

    lexer = SqlLexer()
    formatter = TerminalFormatter()

    def print_colorized(text):
        if sys.stdout.isatty():
            text = highlight(text, lexer, formatter).strip()
        sys.stdout.write(text)
        sys.stdout.write('\n')

except ImportError:
    def print_colorized(text):
        sys.stdout.write(text)
        sys.stdout.write('\n')


class DBCommand(BaseCommand):

    name = 'database'
    args = '<package package ...>'
    help = 'Perform database related tasks.'
    scope = 'package'

    options = (
        make_option('-I', '--info', help='Show the table schema for the given packages', 
            action='store_true'),
        make_option('-S', '--sync', help="Create the database tables for all the INSTALLED_PACKAGES whose tables haven't been created yet.", 
            action='store_true'),
        make_option('-B', '--backup', help='Create backup of the database.',
            metavar='FILE'),
        make_option('--reset', help='Reset the model tables. Use with care, will drop all the tables.',
            action='store_true'),
    )

    exclusive = ('-I', '-S', '-B', '--reset')

    def execute(self, *args, **options):
        
        if settings.DATABASE_ENGINE == "dummy":
            raise self.error("DATABASE_ENGINE is not configured.")
        
        database.connect()
        try:
            # load packages
            loader.load()
            if options.get('info'):
                return self.info(*args)
            if options.get('sync'):
                return self.sync()
            if options.get('reset'):
                return self.reset()
            if options.get('backup'):
                return self.backup(options['backup'])
        finally:
            database.close()
        self.print_help()

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

    def info(self, *packages):
        models, pending = self.get_models(*packages)
        for model in models:
            print_colorized(database.schema_table(model))
        if pending:
            print_colorized('\n-- the following tables should also be added (from other packages)\n')
            for model in pending:
                print_colorized('  -- %s' % model._meta.table)
            print

    def sync(self):
        models, __pending = self.get_models()
        try:
            for model in models:
                if self.verbose:
                    print "Sync table %r" % (model._meta.table)
                database.create_table(model)
        except:
            database.rollback()
            raise
        else:
            database.commit()
            
    def reset(self):
        
        ans = raw_input("""
Be careful, all the tables of database %r will be dropped.
All the data stored in the database will be lost too.

Are you sure about this action? (y/N): """ % settings.DATABASE_NAME)

        if ans.lower() != 'y': return
        
        models, __pending = self.get_models()
        models.reverse()
        try:
            for model in models:
                if self.verbose:
                    print "Drop table %r" % model._meta.table
                database.drop_table(model._meta.table)
        except:
            database.rollback()
            raise
        else:
            database.commit()
            
        self.sync()

    def backup(self, dest):
        print "Not implemented yet!"
