"""
This module defines a Loader class to automatically load all the installed
packages given in settings.INSTALLED_PACKAGES.
"""
import os

from rapido.conf import settings
from rapido.utils.implib import import_module

try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading


class Loader(object):
    """Loader class automatically loads all the installed packages listed
    in settings.INSTALLED_PACKAGES.
    """

    # Borg pattern
    __shared_state = dict(
        packages = {},
        lock = _threading.RLock(),
        loaded = False
    )

    def __init__(self):
        self.__dict__ = self.__shared_state

    def load(self, tests=False):
        """Load the installed packages.

        :param tests: whether to load unittest module or not
        """
        if self.loaded:
            return

        self.lock.acquire()
        try:
            for package in settings.INSTALLED_PACKAGES:
                if package in self.packages:
                    continue
                self.packages[package] = registry = {}

                try: # load models module
                    registry['models'] = import_module('models', package)
                except ImportError:
                    pass

                try: # load web module
                    registry['web'] = import_module('web', package)
                except ImportError:
                    pass

                if tests:
                    try: # load tests module
                        registry['tests'] = import_module('tests', package)
                    except ImportError:
                        pass

            self.loaded = True

            # resolve any model references
            from rapido.db._model import cache
            cache.resolve_references()
        finally:
            self.lock.release()

    def get_package(self, name):
        """Get the package resources which have been loaded by the loader.

        :param name: name of an package
        :returns: a dict or None
        """
        self.load()
        return self.packages.get(name)

    def get_packages(self):
        """Get the list of all the installed packages.
        """
        self.load()
        return self.packages.keys()

    def get_static_dirs(self):
        result = {}
        for package, registry in self.packages.items():
            if 'static' in registry:
                result['/static/%s' % package.lower()] = registry['static']
        return result

    def get_dirs(self, name, prefix='', absolute=False, toplevel=False):
        """Return all the dirs found by the given name withing the installed
        packages.

        For example::

            >>> get_dirs('static', prefix='/static')
            >>> get_dirs('tamplates')

        :param name: directory name
        :param prefix: package_name prefix
        :param absolute: if True return the absolute paths
        :param toplevel: if True also include top level dir

        :returns: 
            a dict with package_name as key prefixed with the given prefix and full
            path to the dir.
        """
        dirs = {}
        abspath = os.path.abspath if absolute else lambda a: a
        if toplevel and os.path.exists(name):
            key = prefix if prefix else '.'
            dirs[key] = abspath(name)
        for package in self.packages:
            path = os.path.join(package, name)
            if os.path.exists(path):
                key = '%s/%s' % (prefix, package) if prefix else name
                dirs[key] = abspath(path)
        return dirs


loader = Loader()
get_package = loader.get_package
get_packages = loader.get_packages

