# Copyright 2016-2018, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numbers
import sys

from . import decision_service
from . import entities
from . import event_builder
from . import exceptions
from . import project_config
from .error_handler import NoOpErrorHandler as noop_error_handler
from .event_dispatcher import EventDispatcher as default_event_dispatcher
from .helpers import enums
from .helpers import validator
from .logger import NoOpLogger as noop_logger
from .logger import SimpleLogger
from .notification_center import NotificationCenter as notification_center


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

    self.event_builder = event_builder.EventBuilder(self.config)
    self.decision_service = decision_service.DecisionService(self.config, user_profile_service)
    self.notification_center = notification_center(self.logger)

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

  def _get_decisions(self, event, user_id, attributes):
    """ Helper method to retrieve decisions for the user for experiment(s) using the provided event.

    Args:
      event: The event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      List of tuples representing valid experiment IDs and variation IDs into which the user is bucketed.
    """
    decisions = []
    for experiment_id in event.experimentIds:
      experiment = self.config.get_experiment_from_id(experiment_id)
      variation_key = self.get_variation(experiment.key, user_id, attributes)

      if not variation_key:
        self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for experiment "%s".' % (user_id, experiment.key))
        continue

      variation = self.config.get_variation_from_key(experiment.key, variation_key)
      decisions.append((experiment_id, variation.id))

    return decisions

  def _send_impression_event(self, experiment, variation, user_id, attributes):
    """ Helper method to send impression event.

    Args:
      experiment: Experiment for which impression event is being sent.
      variation: Variation picked for user for the given experiment.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.
    """

    impression_event = self.event_builder.create_impression_event(experiment,
                                                                  variation.id,
                                                                  user_id,
                                                                  attributes)

    self.logger.log(enums.LogLevels.DEBUG,
                    'Dispatching impression event to URL %s with params %s.' % (impression_event.url,
                                                                                impression_event.params))

    try:
      self.event_dispatcher.dispatch_event(impression_event)
    except:
      error = sys.exc_info()[1]
      self.logger.log(enums.LogLevels.ERROR, 'Unable to dispatch impression event. Error: %s' % str(error))
    self.notification_center.send_notifications(enums.NotificationTypes.ACTIVATE,
                                                experiment, user_id, attributes, variation, impression_event)

  def _get_feature_variable_for_type(self, feature_key, variable_key, variable_type, user_id, attributes):
    """ Helper method to determine value for a certain variable attached to a feature flag based on type of variable.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      variable_key: Key of the variable whose value is to be accessed.
      variable_type: Type of variable which could be one of boolean/double/integer/string.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Value of the variable. None if:
      - Feature key is invalid.
      - Variable key is invalid.
      - Mismatch with type of variable.
    """
    if feature_key is None:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      return None

    if variable_key is None:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      return None

    if user_id is None:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.NONE_USER_ID_PARAMETER)
      return None

    feature_flag = self.config.get_feature_from_key(feature_key)
    if not feature_flag:
      return None

    variable = self.config.get_variable_for_feature(feature_key, variable_key)
    if not variable:
      return None

    # Return None if type differs
    if variable.type != variable_type:
      self.logger.log(
        enums.LogLevels.WARNING,
        'Requested variable type "%s", but variable is of type "%s". '
        'Use correct API to retrieve value. Returning None.' % (variable_type, variable.type)
      )
      return None

    decision = self.decision_service.get_variation_for_feature(feature_flag, user_id, attributes)
    if decision.variation:
      variable_value = self.config.get_variable_value_for_variation(variable, decision.variation)

    else:
      variable_value = variable.defaultValue
      self.logger.log(
        enums.LogLevels.INFO,
        'User "%s" is not in any variation or rollout rule. '
        'Returning default value for variable "%s" of feature flag "%s".' % (user_id, variable_key, feature_key)
      )

    try:
      actual_value = self.config.get_typecast_value(variable_value, variable_type)
    except:
      self.logger.log(enums.LogLevels.ERROR, 'Unable to cast value. Returning None.')
      actual_value = None

    return actual_value

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

    experiment = self.config.get_experiment_from_key(experiment_key)
    variation = self.config.get_variation_from_key(experiment_key, variation_key)

    # Create and dispatch impression event
    self.logger.log(enums.LogLevels.INFO, 'Activating user "%s" in experiment "%s".' % (user_id, experiment.key))
    self._send_impression_event(experiment, variation, user_id, attributes)

    return variation.key

  def track(self, event_key, user_id, attributes=None, event_tags=None):
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

    if not self._validate_user_inputs(attributes, event_tags):
      return

    event = self.config.get_event(event_key)
    if not event:
      self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for event "%s".' % (user_id, event_key))
      return

    # Filter out experiments that are not running or that do not include the user in audience
    # conditions and then determine the decision i.e. the corresponding variation
    decisions = self._get_decisions(event, user_id, attributes)

    # Create and dispatch conversion event if there are any decisions
    if decisions:
      conversion_event = self.event_builder.create_conversion_event(
        event_key, user_id, attributes, event_tags, decisions
      )
      self.logger.log(enums.LogLevels.INFO, 'Tracking event "%s" for user "%s".' % (event_key, user_id))
      self.logger.log(enums.LogLevels.DEBUG,
                      'Dispatching conversion event to URL %s with params %s.' % (conversion_event.url,
                                                                                  conversion_event.params))
      try:
        self.event_dispatcher.dispatch_event(conversion_event)
      except:
        error = sys.exc_info()[1]
        self.logger.log(enums.LogLevels.ERROR, 'Unable to dispatch conversion event. Error: %s' % str(error))
      self.notification_center.send_notifications(enums.NotificationTypes.TRACK, event_key, user_id,
                                                  attributes, event_tags, conversion_event)
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

    if not self._validate_user_inputs(attributes):
      return None

    variation = self.decision_service.get_variation(experiment, user_id, attributes)
    if variation:
      return variation.key

    return None

  def is_feature_enabled(self, feature_key, user_id, attributes=None):
    """ Returns true if the feature is enabled for the given user.

    Args:
      feature_key: The key of the feature for which we are determining if it is enabled or not for the given user.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      True if the feature is enabled for the user. False otherwise.
    """

    if not self.is_valid:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.INVALID_DATAFILE.format('is_feature_enabled'))
      return False

    if feature_key is None:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      return False

    if user_id is None:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.NONE_USER_ID_PARAMETER)
      return False

    feature = self.config.get_feature_from_key(feature_key)
    if not feature:
      return False

    decision = self.decision_service.get_variation_for_feature(feature, user_id, attributes)
    if decision.variation:
      # Send event if Decision came from an experiment.
      if decision.source == decision_service.DECISION_SOURCE_EXPERIMENT:
        self._send_impression_event(decision.experiment,
                                    decision.variation,
                                    user_id,
                                    attributes)

      if decision.variation.featureEnabled:
        self.logger.log(enums.LogLevels.INFO, 'Feature "%s" is enabled for user "%s".' % (feature_key, user_id))
        return True
      else:
        self.logger.log(enums.LogLevels.INFO, 'Feature "%s" is not enabled for user "%s".' % (feature_key, user_id))
        return False

    self.logger.log(enums.LogLevels.INFO, 'Feature "%s" is not enabled for user "%s".' % (feature_key, user_id))
    return False

  def get_enabled_features(self, user_id, attributes=None):
    """ Returns the list of features that are enabled for the user.

    Args:
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      A list of the keys of the features that are enabled for the user.
    """

    enabled_features = []
    if not self.is_valid:
      self.logger.log(enums.LogLevels.ERROR, enums.Errors.INVALID_DATAFILE.format('get_enabled_features'))
      return enabled_features

    for feature in self.config.feature_key_map.values():
      if self.is_feature_enabled(feature.key, user_id, attributes):
        enabled_features.append(feature.key)

    return enabled_features

  def get_feature_variable_boolean(self, feature_key, variable_key, user_id, attributes=None):
    """ Returns value for a certain boolean variable attached to a feature flag.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      variable_key: Key of the variable whose value is to be accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Boolean value of the variable. None if:
      - Feature key is invalid.
      - Variable key is invalid.
      - Mismatch with type of variable.
    """

    variable_type = entities.Variable.Type.BOOLEAN
    return self._get_feature_variable_for_type(feature_key, variable_key, variable_type, user_id, attributes)

  def get_feature_variable_double(self, feature_key, variable_key, user_id, attributes=None):
    """ Returns value for a certain double variable attached to a feature flag.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      variable_key: Key of the variable whose value is to be accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Double value of the variable. None if:
      - Feature key is invalid.
      - Variable key is invalid.
      - Mismatch with type of variable.
    """

    variable_type = entities.Variable.Type.DOUBLE
    return self._get_feature_variable_for_type(feature_key, variable_key, variable_type, user_id, attributes)

  def get_feature_variable_integer(self, feature_key, variable_key, user_id, attributes=None):
    """ Returns value for a certain integer variable attached to a feature flag.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      variable_key: Key of the variable whose value is to be accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Integer value of the variable. None if:
      - Feature key is invalid.
      - Variable key is invalid.
      - Mismatch with type of variable.
    """

    variable_type = entities.Variable.Type.INTEGER
    return self._get_feature_variable_for_type(feature_key, variable_key, variable_type, user_id, attributes)

  def get_feature_variable_string(self, feature_key, variable_key, user_id, attributes=None):
    """ Returns value for a certain string variable attached to a feature.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      variable_key: Key of the variable whose value is to be accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      String value of the variable. None if:
      - Feature key is invalid.
      - Variable key is invalid.
      - Mismatch with type of variable.
    """

    variable_type = entities.Variable.Type.STRING
    return self._get_feature_variable_for_type(feature_key, variable_key, variable_type, user_id, attributes)

  def set_forced_variation(self, experiment_key, user_id, variation_key):
    """ Force a user into a variation for a given experiment.

    Args:
     experiment_key: A string key identifying the experiment.
     user_id: The user ID.
     variation_key: A string variation key that specifies the variation which the user.
     will be forced into. If null, then clear the existing experiment-to-variation mapping.

    Returns:
      A boolean value that indicates if the set completed successfully.
    """

    return self.config.set_forced_variation(experiment_key, user_id, variation_key)

  def get_forced_variation(self, experiment_key, user_id):
    """ Gets the forced variation for a given user and experiment.

    Args:
      experiment_key: A string key identifying the experiment.
      user_id: The user ID.

    Returns:
      The forced variation key. None if no forced variation key.
    """

    forced_variation = self.config.get_forced_variation(experiment_key, user_id)
    return forced_variation.key if forced_variation else None
