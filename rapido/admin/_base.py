import os, sys
from optparse import OptionParser


__all__ = ['CommandError', 'BaseCommand', 'get_commands', 'get_command']


class CommandError(Exception):
    pass


_commands = {}


def get_commands():
    commands = _commands.copy()
    
    from rapido.conf import settings
    if settings.PROJECT_NAME:
        del commands['new-project']
    else:
        del commands['new-package']
    
    commands = commands.items()
    commands.sort(lambda a, b: cmp(a[0], b[0]))
    return commands


def get_command(name):
    try:
        return _commands[name]
    except KeyError:
        print "Unknown command: %s" % name
        print "Type '%s help' for usage" % sys.argv[0]
        sys.exit(1)


class CommandType(type):

    def __init__(cls, name, bases, attrs):
        super(CommandType, cls).__init__(name, bases, attrs)

        if "options" in attrs:
            cls.options = CommandType.merge_options(bases, attrs["options"])

        if name != "BaseCommand" and "name" in attrs:
            _commands[attrs["name"]] = cls

    @staticmethod
    def merge_options(bases, options):
        opts = []
        for base in bases:
            for op in getattr(base, "options", []):
                if op not in opts:
                    opts.append(op)
        opts.extend(options)
        return opts


class BaseCommand(object):

    __metaclass__ = CommandType

    name = ""
    help = ""
    args = ""

    options = ()
    exclusive = ()

    def __init__(self):
        self.parser = OptionParserEx(prog=os.path.basename(sys.argv[0]),
                usage=self.usage,
                #add_help_option=False,
                option_list=self.options)
        self.parser.exclusive = self.exclusive

    @property
    def usage(self):
        usage = "%%prog %s [options] %s" % (self.name, self.args)
        if self.help:
            usage = "%s\n\n%s" % (usage, self.help)
        if len(self.exclusive):
            usage = "%s\nOptions %s are mutually exclusive." % (usage, ", ".join(self.exclusive))
        return usage

    def print_help(self):
        self.parser.print_help()
        sys.exit(1)

    def run(self, argv):
        options, args = self.parser.parse_args(argv[2:])
        try:
            self.execute(*args, **options.__dict__)
        except CommandError, e:
            print "Error: %s\n" % (str(e))
            sys.exit(1)

    def execute(self, *args, **options):
        raise NotImplementedError


class OptionParserEx(OptionParser):

    exclusive = None

    def parse_args(self, args=None, values=None):

        result = OptionParser.parse_args(self, args, values)

        if self.exclusive:
            x = set([self.get_option(o) for o in self.exclusive])
            y = set([self.get_option(o) for o in args if o.startswith('-')])

            if len(x - y) != len(x) - 1:
                #self.error('Options %s are mutually exclusive.' % (', '.join(self.exclusive)))
                self.print_help()
                sys.exit(1)
        
        return result

