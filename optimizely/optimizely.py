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

  def __init__(self,
               datafile,
               event_dispatcher=None,
               logger=None,
               error_handler=None,
               skip_json_validation=False,
               user_profile_service=None):
    """ Optimizely init method for managing Custom projects.

    Args:
      datafile: JSON string representing the project.
      event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
      logger: Optional component which provides a log method to log messages. By default nothing would be logged.
      error_handler: Optional component which provides a handle_error method to handle exceptions.
                     By default all exceptions will be suppressed.
      skip_json_validation: Optional boolean param which allows skipping JSON schema validation upon object invocation.
                            By default JSON schema validation will be performed.
      user_profile_service: Optional component which provides methods to store and manage user profiles.
    """

    self.is_valid = True
    self.event_dispatcher = event_dispatcher or default_event_dispatcher
    self.logger = logger or noop_logger
    self.error_handler = error_handler or noop_error_handler
    self.user_profile_service = user_profile_service

    try:
      self._validate_instantiation_options(datafile, skip_json_validation)
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

    if not self.config.was_parsing_successful():
      self.is_valid = False
      self.logger = SimpleLogger()
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.UNSUPPORTED_DATAFILE_VERSION)
      return

    self.bucketer = bucketer.Bucketer(self.config)
    self.event_builder = event_builder.EventBuilder(self.config, self.bucketer)

  def _validate_instantiation_options(self, datafile, skip_json_validation):
    """ Helper method to validate all instantiation parameters.

    Args:
      datafile: JSON string representing the project.
      skip_json_validation: Boolean representing whether JSON schema validation needs to be skipped or not.

    Raises:
      Exception if provided instantiation options are valid.
    """

    if not skip_json_validation and not validator.is_datafile_valid(datafile):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('datafile'))

    if not validator.is_event_dispatcher_valid(self.event_dispatcher):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('event_dispatcher'))

    if not validator.is_logger_valid(self.logger):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('logger'))

    if not validator.is_error_handler_valid(self.error_handler):
     raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT_ERROR.format('error_handler'))

  def _validate_preconditions(self, experiment, attributes=None, event_tags=None):
    """ Helper method to validate all pre-conditions before we go ahead to bucket user.

    Args:
      experiment: Object representing the experiment.
      attributes: Dict representing user attributes.

    Returns:
      Boolean depending upon whether all conditions are met or not.
    """
    if not self._validate_user_inputs(attributes, event_tags):
      return False

    if not experiment_helper.is_experiment_running(experiment):
      self.logger.log(enums.LogLevels.INFO, 'Experiment "%s" is not running.' % experiment.key)
      return False

    return True

  def _validate_user_inputs(self, attributes=None, event_tags=None):
    """ Helper method to validate user inputs.

    Args:
      attributes: Dict representing user attributes.
      event_tags: Dict representing metadata associated with an event.

    Returns:
      Boolean True if inputs are valid. False otherwise.

    """

    if attributes and not validator.are_attributes_valid(attributes):
      self.logger.log(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')
      self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_FORMAT))
      return False

    if event_tags and not validator.are_event_tags_valid(event_tags):
      self.logger.log(enums.LogLevels.ERROR, 'Provided event tags are in an invalid format.')
      self.error_handler.handle_error(exceptions.InvalidEventTagException(enums.Errors.INVALID_EVENT_TAG_FORMAT))
      return False

    return True

  def _get_valid_experiments_for_event(self, event, user_id, attributes):
    """ Helper method to determine which experiments we should track for the given event.

    Args:
      event: The event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      List of tuples representing valid experiment IDs and variation IDs into which the user is bucketed.
    """
    valid_experiments = []
    for experiment_id in event.experimentIds:
      experiment = self.config.get_experiment_from_id(experiment_id)
      variation_key = self.get_variation(experiment.key, user_id, attributes)

      if not variation_key:
        self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for experiment "%s".' % (user_id, experiment.key))
        continue

      variation = self.config.get_variation_from_key(experiment.key, variation_key)
      valid_experiments.append((experiment_id, variation.id))

    return valid_experiments

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

    variation_key = self.get_variation(experiment_key, user_id, attributes)

    if not variation_key:
      self.logger.log(enums.LogLevels.INFO, 'Not activating user "%s".' % user_id)
      return None

    # Create and dispatch impression event
    experiment = self.config.get_experiment_from_key(experiment_key)
    variation = self.config.get_variation_from_key(experiment_key, variation_key)
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

    if event_tags:
      if isinstance(event_tags, numbers.Number):
        event_tags = {
          'revenue': event_tags
        }
        self.logger.log(enums.LogLevels.WARNING,
                        'Event value is deprecated in track call. Use event tags to pass in revenue value instead.')

    if not self._validate_user_inputs(attributes, event_tags):
      return

    event = self.config.get_event(event_key)
    if not event:
      self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for event "%s".' % (user_id, event_key))
      return

    # Filter out experiments that are not running or that do not include the user in audience conditions
    valid_experiments = self._get_valid_experiments_for_event(event, user_id, attributes)

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
      self.logger.log(enums.LogLevels.INFO,
                      'Experiment key "%s" is invalid. Not activating user "%s".' % (experiment_key,
                                                                                     user_id))
      return None

    if not self._validate_preconditions(experiment, attributes):
      return None

    forced_variation = self.bucketer.get_forced_variation(experiment, user_id)
    if forced_variation:
      return forced_variation.key

    if not audience_helper.is_user_in_experiment(self.config, experiment, attributes):
      self.logger.log(
        enums.LogLevels.INFO,
        'User "%s" does not meet conditions to be in experiment "%s".' % (user_id, experiment.key)
      )
      return None

    variation = self.bucketer.bucket(experiment, user_id)

    if variation:
      return variation.key

    return None
