import os
import sys
from optparse import OptionParser

from _base import CommandError, BaseCommand, get_commands, get_command

# import all command modules
def _load_commands():
    mods = [f[:-3] for f in os.listdir(__path__[0]) if f.endswith('.py') and not f.startswith('_')]
    for m in mods:
        __import__(m, globals())
_load_commands()


class Commander(object):
    
    def __init__(self):
        self.argv = sys.argv[:]
        self.prog = os.path.basename(self.argv[0])
        
    def get_version(self):
        return "1.0"
    
    def print_help(self):
        print "Usage: %s command [options] [args]\n" % self.prog
        print "Options:"
        print "  --version  show programs version number and exit"
        print "  -h, --help   show this help message and exit"
        print "\nType '%s command' for help on a specific command.\n" % (self.prog)
        print "Available commands:"
        commands = get_commands()
        for command, cls in commands:
            print "  %s" % (command)
        sys.exit(1)
        
    def run(self):
                
        try:
            command = self.argv[1]
        except:
            self.print_help()
            
        if command == "--version":
            print self.get_version()
            sys.exit(1)
            
        if command in ("-h", "--help"):
            self.print_help()

        if command == "help":
            if len(self.argv) > 2:
                cls = get_command(self.argv[2])
                cls().print_help()
            else:
                self.print_help()
                
        elif command.startswith("-"):
            self.print_help()
        
        get_command(command)().run(self.argv)
        
        
