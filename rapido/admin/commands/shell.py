import os

from rapido.admin import BaseCommand


class ScriptCommand(BaseCommand):

    name = 'script'
    args = 'FILE'
    help = 'Run arbitrary script in the context of current project.'
    scope = 'package'

    def execute(self, *args, **options):
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

class ShellCommand(BaseCommand):

    name = 'shell'
    help = 'Runs a Python interactive interpreter.'
    scope = 'package'

    def execute(self, *args, **options):

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

