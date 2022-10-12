import logging

from optimizely import logger
from optimizely import optimizely
from optimizely.helpers.sdk_settings import OptimizelySdkSettings

sdk_key = 'QoaqTFiC4fgU4j9dZtadP'

# =============================================
print('-------  WORKS  -------')
optimizely_client = optimizely.Optimizely(sdk_key=sdk_key,
                                          logger=logger.SimpleLogger(logging.DEBUG),
                                          settings=OptimizelySdkSettings(odp_disabled=False))

optimizely_client.sdk_settings
print()


# =============================================
print('-------  SETTINGS IS NOT INSTANCE OF OptimizelySdkSettings  -------')

class InvalidClass:
    pass

optimizely_client2 = optimizely.Optimizely(sdk_key=sdk_key,
                                          logger=logger.SimpleLogger(logging.DEBUG),
                                          settings=InvalidClass)            # TODO None should not triger log for not being sdk instance

optimizely_client2.sdk_settings
print()


# =============================================
print('-------  INVALID LOGGER  -------')
class InvalidLogger:
    pass

optimizely_client3 = optimizely.Optimizely(sdk_key=sdk_key,
                                          logger=InvalidLogger,
                                          settings=OptimizelySdkSettings(odp_disabled=False))

optimizely_client3.sdk_settings
print()