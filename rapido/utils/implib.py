import os, sys, types

__all__ = ('import_module',)


def import_module(name, package=None):
    """Dynamically import a given module. Relative import is not 
    supported though.

    If package is given search within the package directory else
    search form `sys.path` directories.

    :param name: name of the module to be imported
    :param package: the package of the module

    :returns: module instance
    :raises: `ImportError`
    """
    if package and isinstance(package, types.ModuleType):
        package = os.path.dirname(package.__file__).replace('/', '.')

    if package:
        name = "%s.%s" % (package, name)

    try:
        return sys.modules[name]
    except KeyError:
        __import__(name)
        return sys.modules[name]

