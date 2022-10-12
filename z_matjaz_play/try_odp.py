import logging

# TODO - WHY DOESN'T IT PICK UP OPTIMIZELY MODULE ??????????????????
#   - then run the test code so I can test the sdk settings logger issue


from optimizely import logger
from optimizely import optimizely
from optimizely.helpers.sdk_settings import OptimizelySdkSettings


sdk_settings = OptimizelySdkSettings(odp_disabled=True)
optimizely_client = optimizely.Optimizely(sdk_key='QoaqTFiC4fgU4j9dZtadP',
                                          logger=logger.SimpleLogger(logging.DEBUG).logger,
                                          settings=sdk_settings)


x = optimizely_client.sdk_settings
print('SETTINGS ', x)