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


loader = Loader()
get_package = loader.get_package
get_packages = loader.get_packages

