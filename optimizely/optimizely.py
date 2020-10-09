# Copyright 2016-2020, Optimizely
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
from six import string_types

from . import decision_service
from . import entities
from . import event_builder
from . import exceptions
from . import logger as _logging
from .config_manager import AuthDatafilePollingConfigManager
from .config_manager import PollingConfigManager
from .config_manager import StaticConfigManager
from .error_handler import NoOpErrorHandler as noop_error_handler
from .event import event_factory, user_event_factory
from .event.event_processor import ForwardingEventProcessor
from .event_dispatcher import EventDispatcher as default_event_dispatcher
from .helpers import enums, validator
from .notification_center import NotificationCenter
from .optimizely_config import OptimizelyConfigService


class Optimizely(object):
    """ Class encapsulating all SDK functionality. """

    def __init__(
        self,
        datafile=None,
        event_dispatcher=None,
        logger=None,
        error_handler=None,
        skip_json_validation=False,
        user_profile_service=None,
        sdk_key=None,
        config_manager=None,
        notification_center=None,
        event_processor=None,
        datafile_access_token=None,
    ):
        """ Optimizely init method for managing Custom projects.

    Args:
      datafile: Optional JSON string representing the project. Must provide at least one of datafile or sdk_key.
      event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
      logger: Optional component which provides a log method to log messages. By default nothing would be logged.
      error_handler: Optional component which provides a handle_error method to handle exceptions.
                     By default all exceptions will be suppressed.
      skip_json_validation: Optional boolean param which allows skipping JSON schema validation upon object invocation.
                            By default JSON schema validation will be performed.
      user_profile_service: Optional component which provides methods to store and manage user profiles.
      sdk_key: Optional string uniquely identifying the datafile corresponding to project and environment combination.
               Must provide at least one of datafile or sdk_key.
      config_manager: Optional component which implements optimizely.config_manager.BaseConfigManager.
      notification_center: Optional instance of notification_center.NotificationCenter. Useful when providing own
                           config_manager.BaseConfigManager implementation which can be using the
                           same NotificationCenter instance.
      event_processor: Optional component which processes the given event(s).
                       By default optimizely.event.event_processor.ForwardingEventProcessor is used
                       which simply forwards events to the event dispatcher.
                       To enable event batching configure and use optimizely.event.event_processor.BatchEventProcessor.
      datafile_access_token: Optional string used to fetch authenticated datafile for a secure project environment.
    """
        self.logger_name = '.'.join([__name__, self.__class__.__name__])
        self.is_valid = True
        self.event_dispatcher = event_dispatcher or default_event_dispatcher
        self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
        self.error_handler = error_handler or noop_error_handler
        self.config_manager = config_manager
        self.notification_center = notification_center or NotificationCenter(self.logger)
        self.event_processor = event_processor or ForwardingEventProcessor(
            self.event_dispatcher, logger=self.logger, notification_center=self.notification_center,
        )

        try:
            self._validate_instantiation_options()
        except exceptions.InvalidInputException as error:
            self.is_valid = False
            # We actually want to log this error to stderr, so make sure the logger
            # has a handler capable of doing that.
            self.logger = _logging.reset_logger(self.logger_name)
            self.logger.exception(str(error))
            return

        config_manager_options = {
            'datafile': datafile,
            'logger': self.logger,
            'error_handler': self.error_handler,
            'notification_center': self.notification_center,
            'skip_json_validation': skip_json_validation,
        }

        if not self.config_manager:
            if sdk_key:
                config_manager_options['sdk_key'] = sdk_key
                if datafile_access_token:
                    config_manager_options['datafile_access_token'] = datafile_access_token
                    self.config_manager = AuthDatafilePollingConfigManager(**config_manager_options)
                else:
                    self.config_manager = PollingConfigManager(**config_manager_options)
            else:
                self.config_manager = StaticConfigManager(**config_manager_options)

        self.event_builder = event_builder.EventBuilder()
        self.decision_service = decision_service.DecisionService(self.logger, user_profile_service)

    def _validate_instantiation_options(self):
        """ Helper method to validate all instantiation parameters.

    Raises:
      Exception if provided instantiation options are valid.
    """
        if self.config_manager and not validator.is_config_manager_valid(self.config_manager):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('config_manager'))

        if not validator.is_event_dispatcher_valid(self.event_dispatcher):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('event_dispatcher'))

        if not validator.is_logger_valid(self.logger):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('logger'))

        if not validator.is_error_handler_valid(self.error_handler):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('error_handler'))

        if not validator.is_notification_center_valid(self.notification_center):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('notification_center'))

        if not validator.is_event_processor_valid(self.event_processor):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('event_processor'))

    def _validate_user_inputs(self, attributes=None, event_tags=None):
        """ Helper method to validate user inputs.

    Args:
      attributes: Dict representing user attributes.
      event_tags: Dict representing metadata associated with an event.

    Returns:
      Boolean True if inputs are valid. False otherwise.

    """

        if attributes and not validator.are_attributes_valid(attributes):
            self.logger.error('Provided attributes are in an invalid format.')
            self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_FORMAT))
            return False

        if event_tags and not validator.are_event_tags_valid(event_tags):
            self.logger.error('Provided event tags are in an invalid format.')
            self.error_handler.handle_error(exceptions.InvalidEventTagException(enums.Errors.INVALID_EVENT_TAG_FORMAT))
            return False

        return True

    def _send_impression_event(self, project_config, experiment, variation, flag_key, rule_key, rule_type, user_id,
                               attributes):
        """ Helper method to send impression event.

    Args:
      project_config: Instance of ProjectConfig.
      experiment: Experiment for which impression event is being sent.
      variation: Variation picked for user for the given experiment.
      flag_key: key for a feature flag.
      rule_key: key for an experiment.
      rule_type: type for the source.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.
    """
        variation_id = variation.id if variation is not None else None
        user_event = user_event_factory.UserEventFactory.create_impression_event(
            project_config, experiment, variation_id, flag_key, rule_key, rule_type, user_id, attributes
        )

        self.event_processor.process(user_event)

        # Kept for backward compatibility.
        # This notification is deprecated and new Decision notifications
        # are sent via their respective method calls.
        if len(self.notification_center.notification_listeners[enums.NotificationTypes.ACTIVATE]) > 0:
            log_event = event_factory.EventFactory.create_log_event(user_event, self.logger)
            self.notification_center.send_notifications(
                enums.NotificationTypes.ACTIVATE, experiment, user_id, attributes, variation, log_event.__dict__,
            )

    def _get_feature_variable_for_type(
        self, project_config, feature_key, variable_key, variable_type, user_id, attributes,
    ):
        """ Helper method to determine value for a certain variable attached to a feature flag based on type of variable.

    Args:
      project_config: Instance of ProjectConfig.
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
        if not validator.is_non_empty_string(feature_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('feature_key'))
            return None

        if not validator.is_non_empty_string(variable_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('variable_key'))
            return None

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        if not self._validate_user_inputs(attributes):
            return None

        feature_flag = project_config.get_feature_from_key(feature_key)
        if not feature_flag:
            return None

        variable = project_config.get_variable_for_feature(feature_key, variable_key)
        if not variable:
            return None

        # For non-typed method, use type of variable; else, return None if type differs
        variable_type = variable_type or variable.type
        if variable.type != variable_type:
            self.logger.warning(
                'Requested variable type "%s", but variable is of type "%s". '
                'Use correct API to retrieve value. Returning None.' % (variable_type, variable.type)
            )
            return None

        feature_enabled = False
        source_info = {}
        variable_value = variable.defaultValue
        decision = self.decision_service.get_variation_for_feature(project_config, feature_flag, user_id, attributes)
        if decision.variation:

            feature_enabled = decision.variation.featureEnabled
            if feature_enabled:
                variable_value = project_config.get_variable_value_for_variation(variable, decision.variation)
                self.logger.info(
                    'Got variable value "%s" for variable "%s" of feature flag "%s".'
                    % (variable_value, variable_key, feature_key)
                )
            else:
                self.logger.info(
                    'Feature "%s" is not enabled for user "%s". '
                    'Returning the default variable value "%s".' % (feature_key, user_id, variable_value)
                )
        else:
            self.logger.info(
                'User "%s" is not in any variation or rollout rule. '
                'Returning default value for variable "%s" of feature flag "%s".' % (user_id, variable_key, feature_key)
            )

        if decision.source == enums.DecisionSources.FEATURE_TEST:
            source_info = {
                'experiment_key': decision.experiment.key,
                'variation_key': decision.variation.key,
            }

        try:
            actual_value = project_config.get_typecast_value(variable_value, variable_type)
        except:
            self.logger.error('Unable to cast value. Returning None.')
            actual_value = None

        self.notification_center.send_notifications(
            enums.NotificationTypes.DECISION,
            enums.DecisionNotificationTypes.FEATURE_VARIABLE,
            user_id,
            attributes or {},
            {
                'feature_key': feature_key,
                'feature_enabled': feature_enabled,
                'source': decision.source,
                'variable_key': variable_key,
                'variable_value': actual_value,
                'variable_type': variable_type,
                'source_info': source_info,
            },
        )
        return actual_value

    def _get_all_feature_variables_for_type(
        self, project_config, feature_key, user_id, attributes,
    ):
        """ Helper method to determine value for all variables attached to a feature flag.

    Args:
      project_config: Instance of ProjectConfig.
      feature_key: Key of the feature whose variable's value is being accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Dictionary of all variables. None if:
      - Feature key is invalid.
    """
        if not validator.is_non_empty_string(feature_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('feature_key'))
            return None

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        if not self._validate_user_inputs(attributes):
            return None

        feature_flag = project_config.get_feature_from_key(feature_key)
        if not feature_flag:
            return None

        feature_enabled = False
        source_info = {}

        decision = self.decision_service.get_variation_for_feature(project_config, feature_flag, user_id, attributes)
        if decision.variation:

            feature_enabled = decision.variation.featureEnabled
            if feature_enabled:
                self.logger.info(
                    'Feature "%s" is enabled for user "%s".' % (feature_key, user_id)
                )
            else:
                self.logger.info(
                    'Feature "%s" is not enabled for user "%s".' % (feature_key, user_id)
                )
        else:
            self.logger.info(
                'User "%s" is not in any variation or rollout rule. '
                'Returning default value for all variables of feature flag "%s".' % (user_id, feature_key)
            )

        all_variables = {}
        for variable_key in feature_flag.variables:
            variable = project_config.get_variable_for_feature(feature_key, variable_key)
            variable_value = variable.defaultValue
            if feature_enabled:
                variable_value = project_config.get_variable_value_for_variation(variable, decision.variation)
                self.logger.debug(
                    'Got variable value "%s" for variable "%s" of feature flag "%s".'
                    % (variable_value, variable_key, feature_key)
                )

            try:
                actual_value = project_config.get_typecast_value(variable_value, variable.type)
            except:
                self.logger.error('Unable to cast value. Returning None.')
                actual_value = None

            all_variables[variable_key] = actual_value

        if decision.source == enums.DecisionSources.FEATURE_TEST:
            source_info = {
                'experiment_key': decision.experiment.key,
                'variation_key': decision.variation.key,
            }

        self.notification_center.send_notifications(
            enums.NotificationTypes.DECISION,
            enums.DecisionNotificationTypes.ALL_FEATURE_VARIABLES,
            user_id,
            attributes or {},
            {
                'feature_key': feature_key,
                'feature_enabled': feature_enabled,
                'variable_values': all_variables,
                'source': decision.source,
                'source_info': source_info,
            },
        )
        return all_variables

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
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('activate'))
            return None

        if not validator.is_non_empty_string(experiment_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('experiment_key'))
            return None

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('activate'))
            return None

        variation_key = self.get_variation(experiment_key, user_id, attributes)

        if not variation_key:
            self.logger.info('Not activating user "%s".' % user_id)
            return None

        experiment = project_config.get_experiment_from_key(experiment_key)
        variation = project_config.get_variation_from_key(experiment_key, variation_key)

        # Create and dispatch impression event
        self.logger.info('Activating user "%s" in experiment "%s".' % (user_id, experiment.key))
        self._send_impression_event(project_config, experiment, variation, '', experiment.key,
                                    enums.DecisionSources.EXPERIMENT, user_id, attributes)

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
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('track'))
            return

        if not validator.is_non_empty_string(event_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('event_key'))
            return

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return

        if not self._validate_user_inputs(attributes, event_tags):
            return

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('track'))
            return

        event = project_config.get_event(event_key)
        if not event:
            self.logger.info('Not tracking user "%s" for event "%s".' % (user_id, event_key))
            return

        user_event = user_event_factory.UserEventFactory.create_conversion_event(
            project_config, event_key, user_id, attributes, event_tags
        )

        self.event_processor.process(user_event)
        self.logger.info('Tracking event "%s" for user "%s".' % (event_key, user_id))

        if len(self.notification_center.notification_listeners[enums.NotificationTypes.TRACK]) > 0:
            log_event = event_factory.EventFactory.create_log_event(user_event, self.logger)
            self.notification_center.send_notifications(
                enums.NotificationTypes.TRACK, event_key, user_id, attributes, event_tags, log_event.__dict__,
            )

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
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('get_variation'))
            return None

        if not validator.is_non_empty_string(experiment_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('experiment_key'))
            return None

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_variation'))
            return None

        experiment = project_config.get_experiment_from_key(experiment_key)
        variation_key = None

        if not experiment:
            self.logger.info('Experiment key "%s" is invalid. Not activating user "%s".' % (experiment_key, user_id))
            return None

        if not self._validate_user_inputs(attributes):
            return None

        variation = self.decision_service.get_variation(project_config, experiment, user_id, attributes)
        if variation:
            variation_key = variation.key

        if project_config.is_feature_experiment(experiment.id):
            decision_notification_type = enums.DecisionNotificationTypes.FEATURE_TEST
        else:
            decision_notification_type = enums.DecisionNotificationTypes.AB_TEST

        self.notification_center.send_notifications(
            enums.NotificationTypes.DECISION,
            decision_notification_type,
            user_id,
            attributes or {},
            {'experiment_key': experiment_key, 'variation_key': variation_key},
        )

        return variation_key

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
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('is_feature_enabled'))
            return False

        if not validator.is_non_empty_string(feature_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('feature_key'))
            return False

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return False

        if not self._validate_user_inputs(attributes):
            return False

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('is_feature_enabled'))
            return False

        feature = project_config.get_feature_from_key(feature_key)
        if not feature:
            return False

        feature_enabled = False
        source_info = {}
        decision = self.decision_service.get_variation_for_feature(project_config, feature, user_id, attributes)
        is_source_experiment = decision.source == enums.DecisionSources.FEATURE_TEST
        is_source_rollout = decision.source == enums.DecisionSources.ROLLOUT

        if (is_source_rollout or not decision.variation) and project_config.get_send_flag_decisions_value():
            self._send_impression_event(
                project_config, decision.experiment, decision.variation, feature.key, decision.experiment.key if
                decision.experiment else '', decision.source, user_id, attributes
            )

        if decision.variation:
            if decision.variation.featureEnabled is True:
                feature_enabled = True
            # Send event if Decision came from an experiment.
            if is_source_experiment:
                source_info = {
                    'experiment_key': decision.experiment.key,
                    'variation_key': decision.variation.key,
                }
                self._send_impression_event(
                    project_config, decision.experiment, decision.variation, feature.key, decision.experiment.key,
                    decision.source, user_id, attributes
                )

        if feature_enabled:
            self.logger.info('Feature "%s" is enabled for user "%s".' % (feature_key, user_id))
        else:
            self.logger.info('Feature "%s" is not enabled for user "%s".' % (feature_key, user_id))

        self.notification_center.send_notifications(
            enums.NotificationTypes.DECISION,
            enums.DecisionNotificationTypes.FEATURE,
            user_id,
            attributes or {},
            {
                'feature_key': feature_key,
                'feature_enabled': feature_enabled,
                'source': decision.source,
                'source_info': source_info,
            },
        )

        return feature_enabled

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
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('get_enabled_features'))
            return enabled_features

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return enabled_features

        if not self._validate_user_inputs(attributes):
            return enabled_features

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_enabled_features'))
            return enabled_features

        for feature in project_config.feature_key_map.values():
            if self.is_feature_enabled(feature.key, user_id, attributes):
                enabled_features.append(feature.key)

        return enabled_features

    def get_feature_variable(self, feature_key, variable_key, user_id, attributes=None):
        """ Returns value for a variable attached to a feature flag.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      variable_key: Key of the variable whose value is to be accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Value of the variable. None if:
      - Feature key is invalid.
      - Variable key is invalid.
    """
        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_feature_variable'))
            return None

        return self._get_feature_variable_for_type(project_config, feature_key, variable_key, None, user_id, attributes)

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
        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_feature_variable_boolean'))
            return None

        return self._get_feature_variable_for_type(
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

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
        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_feature_variable_double'))
            return None

        return self._get_feature_variable_for_type(
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

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
        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_feature_variable_integer'))
            return None

        return self._get_feature_variable_for_type(
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

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
        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_feature_variable_string'))
            return None

        return self._get_feature_variable_for_type(
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

    def get_feature_variable_json(self, feature_key, variable_key, user_id, attributes=None):
        """ Returns value for a certain JSON variable attached to a feature.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      variable_key: Key of the variable whose value is to be accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Dictionary object of the variable. None if:
      - Feature key is invalid.
      - Variable key is invalid.
      - Mismatch with type of variable.
    """

        variable_type = entities.Variable.Type.JSON
        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_feature_variable_json'))
            return None

        return self._get_feature_variable_for_type(
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

    def get_all_feature_variables(self, feature_key, user_id, attributes=None):
        """ Returns dictionary of all variables and their corresponding values in the context of a feature.

    Args:
      feature_key: Key of the feature whose variable's value is being accessed.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Dictionary mapping variable key to variable value. None if:
      - Feature key is invalid.
    """

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_all_feature_variables'))
            return None

        return self._get_all_feature_variables_for_type(
            project_config, feature_key, user_id, attributes,
        )

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

        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('set_forced_variation'))
            return False

        if not validator.is_non_empty_string(experiment_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('experiment_key'))
            return False

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return False

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('set_forced_variation'))
            return False

        return self.decision_service.set_forced_variation(project_config, experiment_key, user_id, variation_key)

    def get_forced_variation(self, experiment_key, user_id):
        """ Gets the forced variation for a given user and experiment.

    Args:
      experiment_key: A string key identifying the experiment.
      user_id: The user ID.

    Returns:
      The forced variation key. None if no forced variation key.
    """

        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('get_forced_variation'))
            return None

        if not validator.is_non_empty_string(experiment_key):
            self.logger.error(enums.Errors.INVALID_INPUT.format('experiment_key'))
            return None

        if not isinstance(user_id, string_types):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_forced_variation'))
            return None

        forced_variation = self.decision_service.get_forced_variation(project_config, experiment_key, user_id)
        return forced_variation.key if forced_variation else None

    def get_optimizely_config(self):
        """ Gets OptimizelyConfig instance for the current project config.

        Returns:
            OptimizelyConfig instance. None if the optimizely instance is invalid or
            project config isn't available.
        """
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('get_optimizely_config'))
            return None

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_optimizely_config'))
            return None

        # Customized Config Manager may not have optimizely_config defined.
        if hasattr(self.config_manager, 'optimizely_config'):
            return self.config_manager.optimizely_config

        return OptimizelyConfigService(project_config).get_config()
