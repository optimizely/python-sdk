from django.apps import AppConfig

from . import sdk
from .settings import optimizely_settings


class OptimizelyAppConfig(AppConfig):
    name = 'optimizely'

    def ready(self):
        optimizely_sdk.refresh()


optimizely_sdk = sdk.DjangoOptimizely(sdk_key=optimizely_settings.SDK_KEY)
