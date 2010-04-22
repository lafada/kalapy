import types
import threading

from rapido.conf import settings
from rapido.utils import load_module
from rapido.utils.collections import OrderedDict

class Cache(object):
    """A cache that stores packages and their models. For internal
    use only.
    """

    def __init__(self):
        
        self.packages = OrderedDict()
        self.models = OrderedDict()

        self.loaded = False
        self.lock = threading.RLock()
        
    def _populate(self):

        if self.loaded:
            return

        self.lock.acquire()
        try:
            if self.loaded:
                return
            for package in settings.INSTALLED_PACKAGES:
                self.load_package(package)
            self.loaded = True
        finally:
            self.lock.release()


    def load_package(self, package_name):
        """Loads the package with provided fully qualified name and
        returns the model module.

        Args:
            package_name: fully qualified name of the package

        Returns:
            model module or None if models are not defined
        """

        if package_name in self.packages:
            return self.packages[package_name]

        try:
            self.packages[package_name] = load_module("models", package_name)
        except ImportError:
            self.packages[package_name] = None

        return self.packages[package_name]

    def get_models(self, package=None):
        """Returns the list of all models defined in the given package. If package
        is None then returns list of all installed models.

        Args:
            package: package name
        """
        self._populate()
        if package:
            return self.models.get(package, OrderedDict()).values()
        models = []
        for model in self.models.itervalues():
            models.extend(model.values())
        return models

    def get_model(self, name):
        self._populate()
        package = name.split('.')
        package = package[0] if len(package) > 1 else ''
        return self.models.get(package, OrderedDict()).get(name.lower())

    def register_models(self, *models):
        for model in models:
            name = model._model_name.lower()
            package = name.split('.')
            package = package[0] if len(package) > 1 else ''
            registered = self.models.setdefault(package, OrderedDict())
            registered[name] = model


cache = Cache()

