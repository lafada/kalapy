import os
import sys
from optparse import OptionParser

from rapido import get_version
from _base import *

class Admin(object):

    def __init__(self):
        self.argv = sys.argv[:]
        self.prog = os.path.basename(self.argv[0])

    def print_help(self):
        print "Usage: %s command [options] [args]\n" % self.prog
        print "Options:"
        print "  --version  show programs version number and exit"
        print "  -h, --help   show this help message and exit"
        print "\nType '%s help command' for help on a specific command.\n" % (self.prog)
        print "Available commands:"

        scope = 'project' if self.prog == 'rapido-admin.py' else 'package'
        commands = get_commands(scope)
        for command, cls in commands:
            print "  %s" % (command)

        sys.exit(1)

    def run(self):

        try:
            command = self.argv[1]
        except:
            self.print_help()

        if command == "--version":
            print get_version()
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
    
    from rapido.conf import settings
    from werkzeug import import_string

    settings.update(settings_mod)
    
    sys.path.append(os.path.join(project_dir, os.pardir))
    import_string(project_name)
    sys.path.pop()
    
    return project_dir
    

def execute(settings_mod=None):
    if settings_mod:
        setup_environment(settings_mod)
    Admin().run()
