from importlib import import_module
import os

from django.apps import apps
from django.conf import settings


REQUIRED_DEVELOPER_CONFIG_KEYS = (
    'SDK_KEY',
)

DEFAULTS = {
    'SDK_KEY': os.environ.get('OPTIMIZELY_SDK_KEY'),
    'PROJECT_ID': os.environ.get('OPTIMIZELY_PROJECT_ID'),
    'PERSONAL_ACCESS_TOKEN': os.environ.get('OPTIMIZELY_PERSONAL_ACCESS_TOKEN'),
    'FEATURE_FLAG_MODELS': {
        'ONLY_MODELS': {},
        'ADDITIONAL_MODELS': {},
    },
    'STORAGE_STRATEGY': 'optimizely.integrations.django.storage.DjangoORMDatafileStorage',
}

IMPORT_STRINGS = (
    'STORAGE_STRATEGY',
)


def import_from_string(path):
    module_path, class_name = path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, class_name)


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

        if attr in IMPORT_STRINGS:
            val = import_from_string(val)

        if attr == 'FEATURE_FLAG_MODELS':
            model_config = {}
            if val.get('ONLY_MODELS'):
                model_config = val['ONLY_MODELS'].copy()
            else:
                model_config.update({settings.AUTH_USER_MODEL: {}})
                model_config.update(val['ADDITIONAL_MODELS'])

            val = {apps.get_model(k): v for k, v in model_config.items()}

        setattr(self, attr, val)
        return val


optimizely_settings = OptimizelySettings()
