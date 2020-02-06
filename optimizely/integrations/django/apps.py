from django.apps import AppConfig

from ... import integrations
from . import sdk
from .settings import optimizely_settings


class OptimizelyAppConfig(AppConfig):
    name = 'optimizely.integrations.django'

    def __init__(self, app_name, app_module):
        super(OptimizelyAppConfig, self).__init__(app_name, app_module)
        self.path = integrations.django.__path__[0]

    def ready(self):
        optimizely_sdk.refresh()


optimizely_sdk = sdk.DjangoOptimizely(sdk_key=optimizely_settings.SDK_KEY)
