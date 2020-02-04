import os
from django.conf import settings


REQUIRED_DEVELOPER_CONFIG_KEYS = (
    'SDK_KEY',
)

DEFAULTS = {
    'SDK_KEY': os.environ.get('OPTIMIZELY_SDK_KEY'),
}


class OptimizelySettings(object):
    def __init__(self):
        self.developer_settings = getattr(settings, 'OPTIMIZELY', {})
        for key in REQUIRED_DEVELOPER_CONFIG_KEYS:
            assert getattr(self, key), "{} is required in settings".format(key)

    def __getattr__(self, attr):
        if attr not in DEFAULTS and attr not in REQUIRED_DEVELOPER_CONFIG_KEYS:
            raise AttributeError("Invalid Optimizely setting: {}".format(attr))

        try:
            val = self.developer_settings[attr]
        except KeyError:
            val = DEFAULTS[attr]

        setattr(self, attr, val)
        return val


optimizely_settings = OptimizelySettings()
