import os

from rapido.admin import Command


class ScriptCommand(Command):
    """Run arbitrary script in the context of current project
    """
    name = 'script'
    usage = '%name <FILE>'
    
    def execute(self, options, args):
        try:
            script = args[0]
        except:
            self.print_help()

        if not os.path.exists(script):
            self.error("%r doesn't exist." % script)

        # load the packages
        from rapido.conf.loader import loader
        loader.load()

        execfile(script, {'__name__': '__main__'})

class ShellCommand(Command):
    """Runs a Python interactive interpreter
    """
    name = 'shell'
    
    def execute(self, options, args):

        # load the packages
        from rapido.conf.loader import loader
        loader.load()

        imported_objects = {}
        try: # Try activating rlcompleter, because it's handy.
            import readline
            import rlcompleter
            readline.set_completer(rlcompleter.Completer(imported_objects).complete)
            readline.parse_and_bind("tab:complete")
        except ImportError:
            pass

        import code
        code.interact(local=imported_objects)

