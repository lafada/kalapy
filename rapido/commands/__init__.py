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
        print "\nType '%s command' for help on a specific command.\n" % (self.prog)
        print "Available commands:"
        commands = get_commands()
        for command in commands:
            print "  %s" % (command)
        sys.exit(1)
        
    def get_command(self, name):
        try:
            return get_commands()[name]
        except KeyError, e:
            print "Unknown command: %s" % name
            print "Type '%s help' for usage" % self.prog
            sys.exit(1)
            
    def run(self):
        
        parser = OptionParser(usage="%prog command [options] [args]")
        options, args = parser.parse_args(self.argv)
                
        try:
            command = self.argv[1]
        except:
            print "Type '%s help' for usage" % self.prog
            sys.exit(1)

        if command == "help":
            if len(args) > 2:
                cls = self.get_command(args[2])
                cls().print_help()
            else:
                parser.print_help()
                self.help()
        
        self.get_command(command).run(self.argv)
        
        
