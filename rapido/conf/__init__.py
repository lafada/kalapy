import types

from rapido.conf import default
from rapido.utils import load_module


class Settings(object):

    def __init__(self):
        self.update(default)

    def update(self, settings_module=None, **options):

        if settings_module:
            if not isinstance(settings_module, types.ModuleType):
                raise ValueError("setting_module should be a module type.")
            for setting in dir(settings_module):
                if setting == setting.upper():
                    setattr(self, setting, getattr(settings_module, setting))
        for setting, value in options.items():
            setattr(self, settings, value)


settings = Settings()

