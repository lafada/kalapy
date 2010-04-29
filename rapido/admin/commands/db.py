from optparse import make_option
from rapido.admin import BaseCommand


class DBCommand(BaseCommand):

    name = 'database'
    args = '<package package ...>'
    help = 'Perform database related tasks.'
    scope = 'package'

    options = (
        make_option('-I', '--info', help='Show the table schema for given packages', 
            action='store_true'),
        make_option('-S', '--sync', help="Create the database tables for all the INSTALLED_PACKAGES whose tables haven't been created.", 
            action='store_true'),
        make_option('-B', '--backup', help='Create backup of the database.',
            metavar='FILE'),
        make_option('-R', '--restore', help='Restore the database from the given backup.',
            metavar='FILE'),
    )

    exclusive = ('-I', '-S', '-B', '-R')

    def execute(self, *args, **options):
        if options.get('info'):
            return self.info(*args)
        if options.get('sync'):
            return self.sync()
        if options.get('backup'):
            return self.backup(options['backup'])
        if options.get('restore'):
            return self.restore(options['restore'])
        self.print_help()

    def info(self, *packages):
        if not packages:
            self.error("At least one package name required.")

        from rapido import db
        from rapido.conf import settings
        from rapido.utils.imp import import_module

        if settings.DATABASE_ENGINE == "dummy":
            raise self.error("DATABASE_ENGINE is not configured.")

        for package in packages:
            if package not in settings.INSTALLED_PACKAGES:
                self.error('%r not in INSTALLED_PACKAGES' % package)

        models = []
        for package in packages:
            models.extend(db.get_models(package))

        #TODO: sort models by references

        from rapido.db.engines import database

        database.connect()
        try:
            for model in models:
                print model._table.schema()
        finally:
            database.close()

    def sync(self):
        pass

    def backup(self, dest):
        pass

    def restore(self, src):
        pass

