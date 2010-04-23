import types

from rapido.conf import default


class Settings(object):
    """Settings class holds package settings. 
    """
    def __init__(self):
        self.update(default)

    def update(self, settings_module):
        """Update the settings with provided settings_module.
        """
        if not isinstance(settings_module, types.ModuleType):
            raise ValueError("setting_module should be a module type.")
        for setting in dir(settings_module):
            if setting == setting.upper():
                setattr(self, setting, getattr(settings_module, setting))

settings = Settings()

