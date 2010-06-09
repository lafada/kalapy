from rapido.i18n import utils

# Install `gettext` aliased as `_` as a builtin
__builtins__['_'] = utils.gettext

