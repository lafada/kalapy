import os
import sys

from optparse import make_option, OptionParser


class CommandError(Exception):
    pass


_commands = {}

def get_commands():
    return _commands

class CommandType(type):

    def __init__(cls, name, bases, attrs):
        super(CommandType, cls).__init__(name, bases, attrs)
        
        if name != "BaseCommand" and "name" in attrs:
            _commands[attrs["name"]] = cls


class BaseCommand(object):
    
    __metaclass__ = CommandType

    name = ""
    help = ""
    args = ""

    options = ()

    def __init__(self):
        self.parser = OptionParser(prog=sys.argv[0],
                usage=self.usage,
                version=self.version,
                option_list=self.options)

    @property
    def usage(self):
        return "%%prog %s [options] %s" % (self.name, self.args)
    
    @property
    def version(self):
        return "1.0"
    
    def print_help(self):
        self.parser.print_help()
        sys.exit(1)

    def run(self, argv):
        options, args = self.parser.parse_args(argv[1:])
        try:
            self.execute(*args, **options.__dict__)
        except CommandError, e:
            print "Error: %s\n" %(str(e))
            sys.exit(1)

    def execute(self, *args, **options):
        raise NotImplementedError


    
