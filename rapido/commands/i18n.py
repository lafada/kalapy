from optparse import make_option
from _base import BaseCommand

#TODO: not implemented yet

class BabelCommand(BaseCommand):

    args = ""
    
    options = (
        make_option("-l", "--locale", help="locale (e.g. en_US, fr_FR)",
            dest="locale"),
        make_option("-D", "--domain", help="message catalog domain",
            dest="domain", default="messages"),
        make_option("-a", "--packages", help="comma separated list of package names or ALL"),
    )
    
    def execute(self, *args, **options):
        pass
    
    
class Create(BabelCommand):
    
    name = "babel-init"
    help = "create catalogs for the given modules."
    
    
class Extract(BabelCommand):
    
    name = "babel-extract"
    help = "extract message for the given packages"
    
    
class Update(BabelCommand):
    
    name = "babel-update"
    help = "update message catalogs for the given packages"
    
    
class Compile(BabelCommand):
    
    name = "babel-compile"
    help = "compile message catalogs for the given packages"
    
    
class Clean(BabelCommand):
    
    name = "babel-clean"
    help = "clean all backup files."
    
    
