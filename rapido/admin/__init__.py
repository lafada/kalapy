import os
import sys
from optparse import OptionParser

from rapido.utils.imp import import_module

from _base import *


# import all command modules
def _load_commands():
    cmddir = os.path.join(__path__[0], 'commands') 
    mods = [f[:-3] for f in os.listdir(cmddir) if f.endswith('.py') and not f.startswith('_')]
    for m in mods:
        import_module(m, 'rapido.admin.commands')
_load_commands()


class Admin(object):

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
        print "\nType '%s help command' for help on a specific command.\n" % (self.prog)
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


def setup_environment(settings_mod):
    """Prepare the runtime environment. Used by project 'admin.py' script.
    It will update the configuration settings and load the project.
    """
    project_dir = os.path.dirname(settings_mod.__file__)
    project_name = os.path.basename(project_dir)
    
    lib_dir = os.path.join(project_dir, 'lib')
    
    # prepend the project_dir/lib to sys.path if exists
    if os.path.exists(lib_dir):
        sys.path.insert(0, lib_dir)
    
    from rapido.conf import settings
    settings.update(settings_mod)
    
    sys.path.append(os.path.join(project_dir, os.pardir))
    import_module(project_name)
    sys.path.pop()
    
    return project_dir
    

def execute(settings_mod=None):
    if settings_mod:
        setup_environment(settings_mod)
    Admin().run()
