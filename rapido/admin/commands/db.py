from optparse import make_option
from rapido.admin import BaseCommand


class DBCommand(BaseCommand):

    name = "db"
    args = ""
    help = 'Perform database related tasks.'

    options = (
        make_option('-i', '--info', help='Show schema information', dest='PACKAGES'),
        make_option('-S', '--sync', help='Sync database', action='store_true'),
        make_option('-R', '--reset', help='Reset database', action='store_true'),
    )

    exclusive = ('-i', '-S', '-R')

    def execute(self, *args, **options):
        pass

