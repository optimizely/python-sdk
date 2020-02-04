from django.apps import AppConfig

from ... import optimizely
from .settings import optimizely_settings


class OptimizelyAppConfig(AppConfig):
    name = 'optimizely'

    def ready(self):
        optimizely_sdk.refresh()


optimizely_sdk = optimizely.Optimizely(
    sdk_key=optimizely_settings.SDK_KEY,
    datafile_fetching_strategy=optimizely.enums.DatafileFetchingStrategy.MANUAL,
)
