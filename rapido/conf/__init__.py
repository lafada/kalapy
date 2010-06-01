"""
rapido.conf
~~~~~~~~~~~

Configurations and application package loading.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LINCESE for more details.
"""
import os, types

from rapido.conf import default


class Settings(object):
    """Settings class holds package settings.
    """

    __freezed = False

    def __init__(self):
        self.__update(default)
        self.__freezed = False

    def __update(self, settings_module):
        """Update the settings with provided settings_module.
        """
        if not isinstance(settings_module, types.ModuleType):
            raise ValueError("setting_module should be a module type.")
        for setting in dir(settings_module):
            if setting == setting.upper():
                setattr(self, setting, getattr(settings_module, setting))

    def update(self, settings_module):
        """Update the settings with provided settings_module.
        """
        self.__update(settings_module)
        self.PROJECT_DIR = os.path.dirname(settings_module.__file__)
        self.__freezed = True

    def __setattr__(self, name, value):
        if self.__freezed:
            raise AttributeError('Can not change settings.')
        super(Settings, self).__setattr__(name, value)


settings = Settings()
