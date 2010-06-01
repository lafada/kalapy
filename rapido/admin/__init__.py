import os, sys

from _base import *


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


def execute_command(args=None, settings_mod=None):
    """Execute admin commands with specified args and settings module.
    """
    if settings_mod:
        setup_environment(settings_mod)
    Main().run(args)

