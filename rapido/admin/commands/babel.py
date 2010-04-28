from optparse import make_option
from rapido.admin import BaseCommand

#TODO: not implemented yet

class BabelCommand(BaseCommand):

    name = 'babel'
    help = 'Perform i18n message catalogs tasks.'
    scope = 'package'

    options = (
        make_option('-i', '--init', help='Create catalogs',
            dest='PACKAGES'),
        make_option('-x', '--extract', help='Extract messages',
            dest='PACKAGES'),
        make_option('-u', '--update', help='Update message catalogs',
            dest='PACKAGES'),
        make_option('-c', '--compile', help='Compile message catalogs',
            dest='PACKAGES'),
        make_option("-l", "--locale", help="locale (e.g. en_US, fr_FR)",
            dest="locale"),
        make_option("-D", "--domain", help="message catalog domain",
            dest="domain", default="messages"),
    )

    exclusive = ('-i', '-x', '-u', '-c')

    def execute(self, *args, **options):
        pass

