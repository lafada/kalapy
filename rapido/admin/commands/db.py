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
    )

    exclusive = ('-I', '-S', '-B')

    def execute(self, *args, **options):
        if options.get('info'):
            return self.info(*args)
        if options.get('sync'):
            return self.sync()
        if options.get('backup'):
            return self.backup(options['backup'])
        self.print_help()

    def get_models(self, *packages):
        from rapido import db
        if packages:
            models = []
            for package in packages:
                models.extend(db.get_models(package))
        else:
            models = db.get_models()

        models.sort(lambda x,y: cmp(x._creation_order, y._creation_order))

        result = []
        pending = []

        def load_models(args):

            for model in args:
                if model in result or model in pending:
                    continue
                if model._meta.ref_models:
                    load_models(model._meta.ref_models)

                if model in models:
                    result.append(model)
                else:
                    pending.append(model)

        load_models(models)

        return result, pending

    def info(self, *packages):
        if not packages:
            self.error("At least one package name required.")

        from rapido.conf import settings
        from rapido.utils.imp import import_module

        if settings.DATABASE_ENGINE == "dummy":
            raise self.error("DATABASE_ENGINE is not configured.")

        for package in packages:
            if package not in settings.INSTALLED_PACKAGES:
                self.error('%r not in INSTALLED_PACKAGES' % package)

        models, pending = self.get_models(*packages)

        from rapido.db.engines import database

        database.connect()
        try:
            for model in models:
                print database.schema_table(model)

            if pending:
                print '\n-- the following tables should also be added (from other packages)\n'
                for model in pending:
                    print '  --', model._meta.table
                print
        finally:
            database.close()

    def sync(self):
        from rapido.conf import settings
        from rapido.utils.imp import import_module

        if settings.DATABASE_ENGINE == "dummy":
            raise self.error("DATABASE_ENGINE is not configured.")

        models, pending = self.get_models()
        
        from rapido.db.engines import database

        database.connect()
        try:
            for model in models:
                database.create_table(model)
        finally:
            database.close()

    def backup(self, dest):
        pass


