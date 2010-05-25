import os, sys
from optparse import OptionParser, make_option

from werkzeug import find_modules, import_string


__all__ = ['CommandError', 'BaseCommand', 'get_commands', 'get_command']


_commands = {}
_loaded = False

def load_commands():
    """Import all command modules.
    """
    global _loaded
    if not _loaded:
        for m in find_modules('rapido.admin.commands'):
            import_string(m)
        _loaded = True
    return _commands

def get_commands(scope):

    commands = load_commands()

    [commands.pop(k) for k, v in commands.items() if v.scope != scope]

    commands = commands.items()
    commands.sort(lambda a, b: cmp(a[0], b[0]))
    return commands


def get_command(name):
    try:
        return load_commands()[name]
    except KeyError:
        print "Unknown command: %s" % name
        print "Type '%s help' for usage" % sys.argv[0]
        sys.exit(1)


class CommandError(Exception):
    pass


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
    """Base class for implementing commands. The commands will be available
    to the project or package admin scripts depending on the defined scope of
    the command.
    """

    __metaclass__ = CommandType

    # name of the command
    name = ""
    
    # help string for the command
    help = ""
    
    # can be used in `usage` string
    args = ""
    
    # one of `package` or `project` else available in both the scopes
    scope = ""

    # command options
    options = (
        make_option('-v', '--verbose', help='Verbose output.', 
            action='store_true', default=False),
    )
    
    # list of options which are mutually exclusive
    exclusive = ()

    def __init__(self):
        self.verbose = False
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
        """Print help for the command and exit
        """
        self.parser.print_help()
        sys.exit(1)

    def error(self, message):
        """Raise command error
        """
        self.parser.error(message)

    def run(self, argv):
        options, args = self.parser.parse_args(argv[2:])
        self.verbose = options.verbose
        try:
            self.execute(*args, **options.__dict__)
        except CommandError, e:
            print "Error: %s\n" % (str(e))
            sys.exit(1)

    def execute(self, *args, **options):
        """This method will be called when command is executed
        """
        raise NotImplementedError


class OptionParserEx(OptionParser):

    exclusive = None

    def parse_args(self, args=None, values=None):
        result = OptionParser.parse_args(self, args, values)
        if self.exclusive:
            x = set([self.get_option(o) for o in self.exclusive])
            y = set([self.get_option(o) for o in args if o.startswith('-')])
            if len(x - y) != len(x) - 1:
                self.print_help()
                sys.exit(1)
        return result
