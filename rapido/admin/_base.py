"""
This module implemented api to write management scripts.
"""
import re, os, sys, types, getopt

from rapido import get_version


__all__ = ('CommandError', 'Command', 'ActionCommand', 'Main')


class CommandError(Exception):
    """Base exception class for all command related errors.
    """
    pass


class Options(object):
    """Options class instance is used to access command options.
    """
    def __init__(self, names, types_, values):
        self.__names = {}
        self.__types = types_
        self.__values = {}

        for l, s in names.items():
            if s: self.__names[s] = l
            self.__names[l.replace('-', '_')] = l

        for k, v in values:
            k = k.strip('-').replace('-', '_')
            k = self.__names[k]
            try:
                type_, default = self.__types[k]
                if type_ is types.BooleanType:
                    v = True
                else:
                    v = type_(v)
            except:
                pass
            self.__values.setdefault(k, v)

        for k, (t, d) in self.__types.items():
            k = k.replace('-', '_')
            self.__values.setdefault(k, d)

    def __repr__(self):
        return str(self.__values)

    def __getattr__(self, name):
        try:
            return super(Options, self).__getattribute__(name)
        except:
            try:
                return self.__values[self.__names.get(name, name)]
            except:
                pass
            raise

class Parser(object):
    """Command parser. It prepares short & long options from the options
    list, validates the options and can parse command line arguments into
    :class:`Options` and `args` list.
    """

    def __init__(self, options_list):
        self.__options = []
        self.__names = {}
        self.__types = {}

        for short, long, default, help in options_list:
            if not long:
                raise CommandError('Invalid option: (%r, %r, %r, %r)' % (
                    short, long, default, help))

            short = (short or '').strip('-')
            long = long.strip('-')

            if len(short) > 1:
                short = short[0]

            self.__names[long] = short
            self.__types[long] = (type(default), default)

            if short: short = '-%s' % short
            if long: long = '--%s' % long

            self.__options.append((short, long, default, help))

    def parse(self, args):
        """Parse the given arguments and return an instance of :class:`Options`
        and a list of args.

        :param args: arguments, a list or tuple
        :returns: tuple, (Options instance, args list)
        """
        shorts = ''
        longs = []

        for l, s in self.__names.items():
            t, d = self.__types[l]

            if t is types.BooleanType:
                shorts += '%s' % s
                longs.append(l)
            else:
                shorts += '%s:' % s
                longs.append('%s=' % l)

        options, args = getopt.gnu_getopt(args, shorts, longs)
        return Options(self.__names, self.__types, options), args

    def options_text(self):
        """Returns options help text.
        """
        n = max([len(opt[1]) for opt in self.__options])
        c = max([len(opt[0]) for opt in self.__options])

        c = c + 2 if c else 0

        fmt = '%%%ds %%-%ds %%s' % (c, n)
        opts = []

        for short, long, default, help in self.__options:
            opts.append(fmt % (short, long, help))

        if opts:
            return '\noptions:\n\n%s\n' % ('\n'.join(opts))
        return '\n'


#: cache of all registered commands
REGISTRY = {}


class CommandType(type):
    """Meta class for :class:`Command`
    """
    def __init__(cls, name, bases, attrs):
        super(CommandType, cls).__init__(name, bases, attrs)
        options = list(cls.options)
        for base in bases:
            for opt in getattr(base, "options", []):
                if opt not in options:
                    options.append(opt)
        cls.options = tuple(options)
        if cls.name:
            REGISTRY[cls.name] = cls


class Command(object):
    """Base command class. Every subclass of the command class should
    provide it's own docstring which will be used as an additional help
    for the command.

    For example::

        class MyCommand(Command):
            '''This is mycommand's help string...
            '''

            name = 'mycommand'
            usage = '%name [options] [args]'
            options = (
                ('l', 'list', '', 'list somthing...'),
                ('v', 'verbose', False, 'be verbose...'),
            )

            def execute(self, options, args):
                ...

    """

    __metaclass__ = CommandType

    #: name of the command
    name = ""

    #: usage string (single line only)
    usage = "%name [options] [args]"

    #: options list (short, long, default, help)
    options = (
        ('v', 'verbose', False, 'enable verbose output'),
        ('h', 'help', False, 'display help and exit'),
    )

    def __init__(self):
        self.parser = Parser(self.options)

    @property
    def doc(self):
        """Additional help for the command.
        """
        doc = self.__class__.__doc__ or ''
        doc = doc.strip()
        if not doc:
            return ''
        pat = re.compile('^(    |\t)', re.M)
        doc = pat.sub('', doc)
        return '\n%s\n' % doc

    def get_help(self):
        """get the help string for the command.
        """
        prog = os.path.basename(sys.argv[0])
        usage = self.usage.replace('%name', self.name, 1)
        
        text = '%s %s\n%s%s' % (
            prog, usage, self.doc, self.parser.options_text())
        return text

    @property
    def help(self):
        """Help string for the command.
        """
        return self.get_help()

    def error(self, msg):
        """Print the given error message and exit.
        """
        print msg
        sys.exit(1)
        
    def print_help(self):
        """Print help text and exit.
        """
        print self.help
        sys.exit(0)

    def run(self, args=None):
        """Run the command with specified arguments. If args is None it uses
        `sys.argv[1:]`.

        :param args: arguments
        """
        if args is None:
            args = sys.argv[1:]

        assert isinstance(args, (list, tuple))

        try:
            options, args = self.parser.parse(args)
        except getopt.GetoptError, e:
            self.error(e)

        if options.help:
            self.print_help()
        
        self.execute(options, args)

    def execute(self, options, args):
        """Subclasses should implment this method the perform any 
        actions.
        """
        raise NotImplementedError()


class ActionCommand(Command):
    """A special kind of Command to perform various actions which can be
    executed by providing the action name as first agument.

    Actions are defined as member functions with `action_` prefix,
    for example::

        class DBCommand(ActionCommand):
            name = 'database'
            usage = '%name <action> [options]'

            options = (
                ...
            )

            def action_init(self, options, args):
                ...

            def action_sync(self, options, args):
                ...

    """
    
    usage = '%name <action> [options] [args]'
    
    def __init__(self):
        super(ActionCommand, self).__init__()
        self.actions = [a[7:] for a in dir(self) if a.startswith('action_') \
                and isinstance(getattr(self, a), types.MethodType)]

    def get_help(self):
        help = super(ActionCommand, self).get_help()
        if self.actions:
            help += "\navailable actions:\n\n"
            for action in self.actions:
                help += '  %s\n' % action
        return help

    def execute(self, options, args):
        if not self.actions:
            raise CommandError('No actions defined in command %r' % (
                self.__class__.__name__))

        if not args:
            raise self.error('no action given')

        action = args.pop(0)
        getattr(self, 'action_%s' % action)(options, args)



class Main(object):
    """A helper class to run registered commands.
    """

    def __init__(self):
        self.prog = os.path.basename(sys.argv[0])

    def print_help(self):
        print "Usage: %s <command> [options] [args]" % self.prog
        print
        print "options:"
        print
        print "  -h --help    show help text and exit"
        print "     --version show version information and exit"
        print
        print "available commands:"
        print
        for name in REGISTRY:
            print "  %s" % name
        print
        print 'use "%s help <command>" for more details on a command' % self.prog
        sys.exit(1)

    def run(self, args=None):
        args = args or sys.argv[1:]
        
        try:
            opts, args = getopt.getopt(args, 'h', ['help', 'version'])
            opts = dict(opts)
        except:
            opts = {}
            args = []
            
        if '-h' in opts or '--help' in opts:
            self.print_help()
        
        if '--version' in opts:
            print get_version()
            sys.exit(0)
        
        if not args:
            self.print_help()
        if args[0] == 'help':
            if len(args) == 1:
                self.print_help()
            args = [args[1], '-h']

        cmd = args.pop(0)
        
        if cmd.startswith('-'):
            self.print_help()
        
        try:
            command = REGISTRY[cmd]
        except:
            raise CommandError('no such command %r' % cmd)

        command().run(args)


