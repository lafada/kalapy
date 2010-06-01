"""
rapido.admin.commands.babel
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements `babel` command, which can be used to perform
various message catalogue related tasks. 

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LINCESE for more details.
"""
from rapido.admin import ActionCommand


class BabelCommand(ActionCommand):
    """Perform i18n message catalog actions.
    """

    name = 'babel'
    usage = '%name <action> [options]'

    options = (
        ('l', 'locale', '', 'locale (e.g. en_US, fr_FR)'),
        ('d', 'domain', 'messages', 'message catalog domain'),
    )

    def action_init(self, options, args):
        """Create catalogs
        """
        pass

    def action_extract(self, options, args):
        """Extract messages
        """
        pass

    def action_update(self, options, args):
        """Update message catalogs
        """
        pass

    def action_compile(self, options, args):
        """Compile message catalogs
        """
        pass
