import os, sys, types

__all__ = ('load_module',)


def load_module(name, package=None):
    """Dynamically import a given module.

    If package is given search within the package directory else
    search form `sys.path` directories.

    Args:
        name: name of the module to be imported
        package: the package of the module

    Returns:
        module instance

    Raises:
        ImportError
    """
    if package and isinstance(package, types.ModuleType):
        package = os.path.dirname(package.__file__).replace('/', '.')

    name = ".".join([package or "", name])

    try:
        return sys.modules[name]
    except KeyError:
        __import__(name)
        return sys.modules[name]

