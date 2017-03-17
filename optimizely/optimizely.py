# Copyright 2016-2017, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numbers
import sys

from . import bucketer
from . import event_builder
from . import exceptions
from . import project_config
from .error_handler import NoOpErrorHandler as noop_error_handler
from .event_dispatcher import EventDispatcher as default_event_dispatcher
from .helpers import audience as audience_helper
from .helpers import enums
from .helpers import experiment as experiment_helper
from .helpers import validator
from .logger import NoOpLogger as noop_logger
from .logger import SimpleLogger


class Optimizely(object):
  """ Class encapsulating all SDK functionality. """

  def __init__(self, datafile, event_dispatcher=None, logger=None, error_handler=None, skip_json_validation=False):
    """ Optimizely init method for managing Custom projects.

    Args:
      datafile: JSON string representing the project.
      event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
      logger: Optional param which provides a log method to log messages. By default nothing would be logged.
      error_handler: Optional param which provides a handle_error method to handle exceptions.
                     By default all exceptions will be suppressed.
      skip_json_validation: Optional boolean param which allows skipping JSON schema validation upon object invocation.
                            By default JSON schema validation will be performed.
    """

    self.is_valid = True
    self.event_dispatcher = event_dispatcher or default_event_dispatcher
    self.logger = logger or noop_logger
    self.error_handler = error_handler or noop_error_handler

    try:
      self._validate_inputs(datafile, skip_json_validation)
    except exceptions.InvalidInputException as error:
      self.is_valid = False
      self.logger = SimpleLogger()
      self.logger.log(enums.LogLevels.ERROR, str(error))
      return

    try:
      self.config = project_config.ProjectConfig(datafile, self.logger, self.error_handler)
    except:
      self.is_valid = False
      self.config = None
      self.logger = SimpleLogger()
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.INVALID_INPUT_ERROR.format('datafile'))
      return

    self.bucketer = bucketer.Bucketer(self.config)

    try:
      self.event_builder = event_builder.get_event_builder(self.config, self.bucketer)
    except:
      self.is_valid = False
      self.logger = SimpleLogger()
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.UNSUPPORTED_DATAFILE_VERSION)

  def _validate_inputs(self, datafile, skip_json_validation):
    """ Helper method to validate all input parameters.

    Args:
      datafile: JSON string representing the project.
      skip_json_validation: Boolean representing whether JSON schema validation needs to be skipped or not.

    Raises:
      Exception if provided input is invalid.
    """

    if not skip_json_validation and not validator.is_datafile_valid(datafile):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('datafile'))

    if not validator.is_event_dispatcher_valid(self.event_dispatcher):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('event_dispatcher'))

    if not validator.is_logger_valid(self.logger):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('logger'))

    if not validator.is_error_handler_valid(self.error_handler):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('error_handler'))

  def _validate_preconditions(self, experiment, user_id, attributes):
    """ Helper method to validate all pre-conditions before we go ahead to bucket user.

    Args:
      experiment: Object representing the experiment.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Boolean depending upon whether all conditions are met or not.
    """

    if attributes and not validator.are_attributes_valid(attributes):
      self.logger.log(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')
      self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_FORMAT))
      return False

    if not experiment_helper.is_experiment_running(experiment):
      self.logger.log(enums.LogLevels.INFO, 'Experiment "%s" is not running.' % experiment.key)
      return False

    if experiment_helper.is_user_in_forced_variation(experiment.forcedVariations, user_id):
      return True

    if not audience_helper.is_user_in_experiment(self.config, experiment, attributes):
      self.logger.log(
        enums.LogLevels.INFO,
        'User "%s" does not meet conditions to be in experiment "%s".' % (user_id, experiment.key)
      )
      return False

    return True

  def activate(self, experiment_key, user_id, attributes=None):
    """ Buckets visitor and sends impression event to Optimizely.

    Args:
      experiment_key: Experiment which needs to be activated.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Variation key representing the variation the user will be bucketed in.
      None if user is not in experiment or if experiment is not Running.
    """

    if not self.is_valid:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.INVALID_DATAFILE.format('activate'))
      return None

    experiment = self.config.get_experiment_from_key(experiment_key)
    if not experiment:
      self.logger.log(enums.LogLevels.INFO, 'Not activating user "%s".' % user_id)
      return None

    if not self._validate_preconditions(experiment, user_id, attributes):
      self.logger.log(enums.LogLevels.INFO, 'Not activating user "%s".' % user_id)
      return None

    variation = self.bucketer.bucket(experiment, user_id)

    if not variation:
      self.logger.log(enums.LogLevels.INFO, 'Not activating user "%s".' % user_id)
      return None

    # Create and dispatch impression event
    impression_event = self.event_builder.create_impression_event(experiment, variation.id, user_id, attributes)
    self.logger.log(enums.LogLevels.INFO, 'Activating user "%s" in experiment "%s".' % (user_id, experiment.key))
    self.logger.log(enums.LogLevels.DEBUG,
                    'Dispatching impression event to URL %s with params %s.' % (impression_event.url,
                                                                                impression_event.params))
    try:
      self.event_dispatcher.dispatch_event(impression_event)
    except:
      error = sys.exc_info()[1]
      self.logger.log(enums.LogLevels.ERROR, 'Unable to dispatch impression event. Error: %s' % str(error))

    return variation.key

  def track(self, event_key, user_id,  attributes=None, event_tags=None):
    """ Send conversion event to Optimizely.

    Args:
      event_key: Event key representing the event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing visitor attributes and values which need to be recorded.
      event_tags: Dict representing metadata associated with the event.
    """

    if not self.is_valid:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.INVALID_DATAFILE.format('track'))
      return

    if attributes and not validator.are_attributes_valid(attributes):
      self.logger.log(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')
      self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_FORMAT))
      return

    if event_tags:
      if isinstance(event_tags, numbers.Number):
        event_tags = {
          'revenue': event_tags
        }
        self.logger.log(enums.LogLevels.WARNING,
                        'Event value is deprecated in track call. Use event tags to pass in revenue value instead.')

      if not validator.are_event_tags_valid(event_tags):
        self.logger.log(enums.LogLevels.ERROR, 'Provided event tags are in an invalid format.')
        self.error_handler.handle_error(exceptions.InvalidEventTagException(enums.Errors.INVALID_EVENT_TAG_FORMAT))
        return

    event = self.config.get_event(event_key)
    if not event:
      self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for event "%s".' % (user_id, event_key))
      return

    # Filter out experiments that are not running or that do not include the user in audience conditions
    valid_experiments = []
    for experiment_id in event.experimentIds:
      experiment = self.config.get_experiment_from_id(experiment_id)
      if not self._validate_preconditions(experiment, user_id, attributes):
        self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for experiment "%s".' % (user_id, experiment.key))
        continue
      valid_experiments.append(experiment)

    # Create and dispatch conversion event if there are valid experiments
    if valid_experiments:
      conversion_event = self.event_builder.create_conversion_event(event_key, user_id, attributes, event_tags,
                                                                    valid_experiments)
      self.logger.log(enums.LogLevels.INFO, 'Tracking event "%s" for user "%s".' % (event_key, user_id))
      self.logger.log(enums.LogLevels.DEBUG,
                      'Dispatching conversion event to URL %s with params %s.' % (conversion_event.url,
                                                                                  conversion_event.params))
      try:
        self.event_dispatcher.dispatch_event(conversion_event)
      except:
        error = sys.exc_info()[1]
        self.logger.log(enums.LogLevels.ERROR, 'Unable to dispatch conversion event. Error: %s' % str(error))

    else:
      self.logger.log(enums.LogLevels.INFO, 'There are no valid experiments for event "%s" to track.' % event_key)

  def get_variation(self, experiment_key, user_id, attributes=None):
    """ Gets variation where user will be bucketed.

    Args:
      experiment_key: Experiment for which user variation needs to be determined.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Variation key representing the variation the user will be bucketed in.
      None if user is not in experiment or if experiment is not Running.
    """

    if not self.is_valid:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.INVALID_DATAFILE.format('get_variation'))
      return None

    experiment = self.config.get_experiment_from_key(experiment_key)
    if not experiment:
      return None

    if not self._validate_preconditions(experiment, user_id, attributes):
      return None
    variation = self.bucketer.bucket(experiment, user_id)

    if variation:
      return variation.key

    return None
