import os
import sys
from optparse import OptionParser

from _base import CommandError, BaseCommand, get_commands

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
        
    def help(self):
        
        sys.exit(1)
        
    def get_command(self, name):
        try:
            return get_commands()[name]
        except KeyError, e:
            print "Unknown command: %s" % name
            print "Type '%s help' for usage" % self.prog
            sys.exit(1)
            
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
        for command in commands:
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
                cls = self.get_command(self.argv[2])
                cls().print_help()
            else:
                self.print_help()
                
        elif command.startswith("-"):
            self.print_help()
        
        self.get_command(command)().run(self.argv)
        
        
