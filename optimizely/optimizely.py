# Copyright 2016-2023, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from . import decision_service
from . import entities
from . import event_builder
from . import exceptions
from . import logger as _logging
from . import project_config
from .config_manager import AuthDatafilePollingConfigManager
from .config_manager import BaseConfigManager
from .config_manager import PollingConfigManager
from .config_manager import StaticConfigManager
from .decision.optimizely_decide_option import OptimizelyDecideOption
from .decision.optimizely_decision import OptimizelyDecision
from .decision.optimizely_decision_message import OptimizelyDecisionMessage
from .decision_service import Decision
from .error_handler import NoOpErrorHandler, BaseErrorHandler
from .event import event_factory, user_event_factory
from .event.event_processor import BatchEventProcessor, BaseEventProcessor
from .event_dispatcher import EventDispatcher, CustomEventDispatcher
from .helpers import enums, validator
from .helpers.sdk_settings import OptimizelySdkSettings
from .helpers.enums import DecisionSources
from .notification_center import NotificationCenter
from .notification_center_registry import _NotificationCenterRegistry
from .odp.lru_cache import LRUCache
from .odp.odp_manager import OdpManager
from .optimizely_config import OptimizelyConfig, OptimizelyConfigService
from .optimizely_user_context import OptimizelyUserContext, UserAttributes

if TYPE_CHECKING:
    # prevent circular dependency by skipping import at runtime
    from .user_profile import UserProfileService
    from .helpers.event_tag_utils import EventTags


class Optimizely:
    """ Class encapsulating all SDK functionality. """

    def __init__(
            self,
            datafile: Optional[str] = None,
            event_dispatcher: Optional[CustomEventDispatcher] = None,
            logger: Optional[_logging.Logger] = None,
            error_handler: Optional[BaseErrorHandler] = None,
            skip_json_validation: Optional[bool] = False,
            user_profile_service: Optional[UserProfileService] = None,
            sdk_key: Optional[str] = None,
            config_manager: Optional[BaseConfigManager] = None,
            notification_center: Optional[NotificationCenter] = None,
            event_processor: Optional[BaseEventProcessor] = None,
            datafile_access_token: Optional[str] = None,
            default_decide_options: Optional[list[str]] = None,
            event_processor_options: Optional[dict[str, Any]] = None,
            settings: Optional[OptimizelySdkSettings] = None
    ) -> None:
        """ Optimizely init method for managing Custom projects.

        Args:
          datafile: Optional JSON string representing the project. Must provide at least one of datafile or sdk_key.
          event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
          logger: Optional component which provides a log method to log messages. By default nothing would be logged.
          error_handler: Optional component which provides a handle_error method to handle exceptions.
                         By default all exceptions will be suppressed.
          skip_json_validation: Optional boolean param which allows skipping JSON schema validation upon object
          invocation.
                                By default JSON schema validation will be performed.
          user_profile_service: Optional component which provides methods to store and manage user profiles.
          sdk_key: Optional string uniquely identifying the datafile corresponding to project and environment
          combination.
                   Must provide at least one of datafile or sdk_key.
          config_manager: Optional component which implements optimizely.config_manager.BaseConfigManager.
          notification_center: Optional instance of notification_center.NotificationCenter. Useful when providing own
                               config_manager.BaseConfigManager implementation which can be using the
                               same NotificationCenter instance.
          event_processor: Optional component which processes the given event(s).
                           By default optimizely.event.event_processor.BatchEventProcessor is used
                           which batches events. To simply forward events to the event dispatcher
                           configure and use optimizely.event.event_processor.ForwardingEventProcessor.
          datafile_access_token: Optional string used to fetch authenticated datafile for a secure project environment.
          default_decide_options: Optional list of decide options used with the decide APIs.
          event_processor_options: Optional dict of options to be passed to the default batch event processor.
          settings: Optional instance of OptimizelySdkSettings for sdk configuration.
        """
        self.logger_name = '.'.join([__name__, self.__class__.__name__])
        self.is_valid = True
        self.event_dispatcher = event_dispatcher or EventDispatcher
        self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
        self.error_handler = error_handler or NoOpErrorHandler
        self.config_manager: BaseConfigManager = config_manager  # type: ignore[assignment]
        self.notification_center = notification_center or NotificationCenter(self.logger)
        event_processor_defaults = {
            'batch_size': 1,
            'flush_interval': 30,
            'timeout_interval': 5,
            'start_on_init': True
        }
        if event_processor_options:
            event_processor_defaults.update(event_processor_options)

        self.event_processor = event_processor or BatchEventProcessor(
            self.event_dispatcher,
            logger=self.logger,
            notification_center=self.notification_center,
            **event_processor_defaults  # type: ignore[arg-type]
        )
        self.default_decide_options: list[str]

        if default_decide_options is None:
            self.default_decide_options = []
        else:
            self.default_decide_options = default_decide_options

        if isinstance(self.default_decide_options, list):
            self.default_decide_options = self.default_decide_options[:]
        else:
            self.logger.debug('Provided default decide options is not a list.')
            self.default_decide_options = []

        self.sdk_settings: OptimizelySdkSettings = settings  # type: ignore[assignment]

        try:
            self._validate_instantiation_options()
        except exceptions.InvalidInputException as error:
            self.is_valid = False
            # We actually want to log this error to stderr, so make sure the logger
            # has a handler capable of doing that.
            self.logger = _logging.reset_logger(self.logger_name)
            self.logger.exception(str(error))
            return

        config_manager_options: dict[str, Any] = {
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

        self.odp_manager: OdpManager
        self._setup_odp(self.config_manager.get_sdk_key())

        self.event_builder = event_builder.EventBuilder()
        self.decision_service = decision_service.DecisionService(self.logger, user_profile_service)

    def _validate_instantiation_options(self) -> None:
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

        if not isinstance(self.sdk_settings, OptimizelySdkSettings):
            if self.sdk_settings is not None:
                self.logger.debug('Provided sdk_settings is not an OptimizelySdkSettings instance.')
            self.sdk_settings = OptimizelySdkSettings()

        if self.sdk_settings.segments_cache:
            if not validator.is_segments_cache_valid(self.sdk_settings.segments_cache):
                raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('segments_cache'))

        if self.sdk_settings.odp_segment_manager:
            if not validator.is_segment_manager_valid(self.sdk_settings.odp_segment_manager):
                raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('segment_manager'))

        if self.sdk_settings.odp_event_manager:
            if not validator.is_event_manager_valid(self.sdk_settings.odp_event_manager):
                raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('event_manager'))

    def _validate_user_inputs(
        self, attributes: Optional[UserAttributes] = None, event_tags: Optional[EventTags] = None
    ) -> bool:
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

    def _send_impression_event(
        self, project_config: project_config.ProjectConfig, experiment: Optional[entities.Experiment],
        variation: Optional[entities.Variation], flag_key: str, rule_key: str, rule_type: str,
        enabled: bool, user_id: str, attributes: Optional[UserAttributes]
    ) -> None:
        """ Helper method to send impression event.

        Args:
          project_config: Instance of ProjectConfig.
          experiment: Experiment for which impression event is being sent.
          variation: Variation picked for user for the given experiment.
          flag_key: key for a feature flag.
          rule_key: key for an experiment.
          rule_type: type for the source.
          enabled: boolean representing if feature is enabled
          user_id: ID for user.
          attributes: Dict representing user attributes and values which need to be recorded.
        """
        if not experiment:
            experiment = entities.Experiment.get_default()

        variation_id = variation.id if variation is not None else None
        user_event = user_event_factory.UserEventFactory.create_impression_event(
            project_config, experiment, variation_id, flag_key, rule_key, rule_type, enabled, user_id, attributes
        )

        if user_event is None:
            self.logger.error('Cannot process None event.')
            return

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
        self, project_config: project_config.ProjectConfig, feature_key: str, variable_key: str,
        variable_type: Optional[str], user_id: str, attributes: Optional[UserAttributes]
    ) -> Any:
        """ Helper method to determine value for a certain variable attached to a feature flag based on
        type of variable.

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

        if not isinstance(user_id, str):
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
                f'Requested variable type "{variable_type}", but variable is of '
                f'type "{variable.type}". Use correct API to retrieve value. Returning None.'
            )
            return None

        feature_enabled = False
        source_info = {}
        variable_value = variable.defaultValue

        user_context = OptimizelyUserContext(self, self.logger, user_id, attributes, False)

        decision, _ = self.decision_service.get_variation_for_feature(project_config, feature_flag, user_context)

        if decision.variation:

            feature_enabled = decision.variation.featureEnabled
            if feature_enabled:
                variable_value = project_config.get_variable_value_for_variation(variable, decision.variation)
                self.logger.info(
                    f'Got variable value "{variable_value}" for '
                    f'variable "{variable_key}" of feature flag "{feature_key}".'
                )
            else:
                self.logger.info(
                    f'Feature "{feature_key}" is not enabled for user "{user_id}". '
                    f'Returning the default variable value "{variable_value}".'
                )
        else:
            self.logger.info(
                f'User "{user_id}" is not in any variation or rollout rule. '
                f'Returning default value for variable "{variable_key}" of feature flag "{feature_key}".'
            )

        if decision.source == enums.DecisionSources.FEATURE_TEST:
            source_info = {
                'experiment_key': decision.experiment.key if decision.experiment else None,
                'variation_key': decision.variation.key if decision.variation else None,
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
        self, project_config: project_config.ProjectConfig, feature_key: str,
        user_id: str, attributes: Optional[UserAttributes],
    ) -> Optional[dict[str, Any]]:
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

        if not isinstance(user_id, str):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        if not self._validate_user_inputs(attributes):
            return None

        feature_flag = project_config.get_feature_from_key(feature_key)
        if not feature_flag:
            return None

        feature_enabled = False
        source_info = {}

        user_context = OptimizelyUserContext(self, self.logger, user_id, attributes, False)

        decision, _ = self.decision_service.get_variation_for_feature(project_config, feature_flag, user_context)

        if decision.variation:

            feature_enabled = decision.variation.featureEnabled
            if feature_enabled:
                self.logger.info(
                    f'Feature "{feature_key}" is enabled for user "{user_id}".'
                )
            else:
                self.logger.info(
                    f'Feature "{feature_key}" is not enabled for user "{user_id}".'
                )
        else:
            self.logger.info(
                f'User "{user_id}" is not in any variation or rollout rule. '
                f'Returning default value for all variables of feature flag "{feature_key}".'
            )

        all_variables = {}
        for variable_key, variable in feature_flag.variables.items():
            variable_value = variable.defaultValue
            if feature_enabled:
                variable_value = project_config.get_variable_value_for_variation(variable, decision.variation)
                self.logger.debug(
                    f'Got variable value "{variable_value}" for '
                    f'variable "{variable_key}" of feature flag "{feature_key}".'
                )

            try:
                actual_value = project_config.get_typecast_value(variable_value, variable.type)
            except:
                self.logger.error('Unable to cast value. Returning None.')
                actual_value = None

            all_variables[variable_key] = actual_value

        if decision.source == enums.DecisionSources.FEATURE_TEST:
            source_info = {
                'experiment_key': decision.experiment.key if decision.experiment else None,
                'variation_key': decision.variation.key if decision.variation else None,
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

    def activate(self, experiment_key: str, user_id: str, attributes: Optional[UserAttributes] = None) -> Optional[str]:
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

        if not isinstance(user_id, str):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('activate'))
            return None

        variation_key = self.get_variation(experiment_key, user_id, attributes)

        if not variation_key:
            self.logger.info(f'Not activating user "{user_id}".')
            return None

        experiment = project_config.get_experiment_from_key(experiment_key)
        variation = project_config.get_variation_from_key(experiment_key, variation_key)
        if not variation or not experiment:
            self.logger.info(f'Not activating user "{user_id}".')
            return None

        # Create and dispatch impression event
        self.logger.info(f'Activating user "{user_id}" in experiment "{experiment.key}".')
        self._send_impression_event(project_config, experiment, variation, '', experiment.key,
                                    enums.DecisionSources.EXPERIMENT, True, user_id, attributes)

        return variation.key

    def track(
        self, event_key: str, user_id: str,
        attributes: Optional[UserAttributes] = None,
        event_tags: Optional[EventTags] = None
    ) -> None:
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

        if not isinstance(user_id, str):
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
            self.logger.info(f'Not tracking user "{user_id}" for event "{event_key}".')
            return

        user_event = user_event_factory.UserEventFactory.create_conversion_event(
            project_config, event_key, user_id, attributes, event_tags
        )

        if user_event is None:
            self.logger.error('Cannot process None event.')
            return

        self.event_processor.process(user_event)
        self.logger.info(f'Tracking event "{event_key}" for user "{user_id}".')

        if len(self.notification_center.notification_listeners[enums.NotificationTypes.TRACK]) > 0:
            log_event = event_factory.EventFactory.create_log_event(user_event, self.logger)
            self.notification_center.send_notifications(
                enums.NotificationTypes.TRACK, event_key, user_id, attributes, event_tags, log_event.__dict__,
            )

    def get_variation(
        self, experiment_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[str]:
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

        if not isinstance(user_id, str):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_variation'))
            return None

        experiment = project_config.get_experiment_from_key(experiment_key)
        variation_key = None

        if not experiment:
            self.logger.info(f'Experiment key "{experiment_key}" is invalid. Not activating user "{user_id}".')
            return None

        if not self._validate_user_inputs(attributes):
            return None

        user_context = OptimizelyUserContext(self, self.logger, user_id, attributes, False)

        variation, _ = self.decision_service.get_variation(project_config, experiment, user_context)
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

    def is_feature_enabled(self, feature_key: str, user_id: str, attributes: Optional[UserAttributes] = None) -> bool:
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

        if not isinstance(user_id, str):
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

        user_context = OptimizelyUserContext(self, self.logger, user_id, attributes, False)

        decision, _ = self.decision_service.get_variation_for_feature(project_config, feature, user_context)
        is_source_experiment = decision.source == enums.DecisionSources.FEATURE_TEST
        is_source_rollout = decision.source == enums.DecisionSources.ROLLOUT

        if decision.variation:
            if decision.variation.featureEnabled is True:
                feature_enabled = True

        if (is_source_rollout or not decision.variation) and project_config.get_send_flag_decisions_value():
            self._send_impression_event(
                project_config, decision.experiment, decision.variation, feature.key, decision.experiment.key if
                decision.experiment else '', decision.source, feature_enabled, user_id, attributes
            )

        # Send event if Decision came from an experiment.
        if is_source_experiment and decision.variation and decision.experiment:
            source_info = {
                'experiment_key': decision.experiment.key,
                'variation_key': decision.variation.key,
            }
            self._send_impression_event(
                project_config, decision.experiment, decision.variation, feature.key, decision.experiment.key,
                decision.source, feature_enabled, user_id, attributes
            )

        if feature_enabled:
            self.logger.info(f'Feature "{feature_key}" is enabled for user "{user_id}".')
        else:
            self.logger.info(f'Feature "{feature_key}" is not enabled for user "{user_id}".')

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

    def get_enabled_features(self, user_id: str, attributes: Optional[UserAttributes] = None) -> list[str]:
        """ Returns the list of features that are enabled for the user.

        Args:
          user_id: ID for user.
          attributes: Dict representing user attributes.

        Returns:
          A list of the keys of the features that are enabled for the user.
        """

        enabled_features: list[str] = []
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('get_enabled_features'))
            return enabled_features

        if not isinstance(user_id, str):
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

    def get_feature_variable(
        self, feature_key: str, variable_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Any:
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

    def get_feature_variable_boolean(
        self, feature_key: str, variable_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[bool]:
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

        return self._get_feature_variable_for_type(  # type: ignore[no-any-return]
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

    def get_feature_variable_double(
        self, feature_key: str, variable_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[float]:
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

        return self._get_feature_variable_for_type(  # type: ignore[no-any-return]
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

    def get_feature_variable_integer(
        self, feature_key: str, variable_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[int]:
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

        return self._get_feature_variable_for_type(  # type: ignore[no-any-return]
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

    def get_feature_variable_string(
        self, feature_key: str, variable_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[str]:
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

        return self._get_feature_variable_for_type(  # type: ignore[no-any-return]
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

    def get_feature_variable_json(
        self, feature_key: str, variable_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[dict[str, Any]]:
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

        return self._get_feature_variable_for_type(  # type: ignore[no-any-return]
            project_config, feature_key, variable_key, variable_type, user_id, attributes,
        )

    def get_all_feature_variables(
        self, feature_key: str, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[dict[str, Any]]:
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

    def set_forced_variation(self, experiment_key: str, user_id: str, variation_key: Optional[str]) -> bool:
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

        if not isinstance(user_id, str):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return False

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('set_forced_variation'))
            return False

        return self.decision_service.set_forced_variation(project_config, experiment_key, user_id, variation_key)

    def get_forced_variation(self, experiment_key: str, user_id: str) -> Optional[str]:
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

        if not isinstance(user_id, str):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        project_config = self.config_manager.get_config()
        if not project_config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('get_forced_variation'))
            return None

        forced_variation, _ = self.decision_service.get_forced_variation(project_config, experiment_key, user_id)
        return forced_variation.key if forced_variation else None

    def get_optimizely_config(self) -> Optional[OptimizelyConfig]:
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

        return OptimizelyConfigService(project_config, self.logger).get_config()

    def create_user_context(
        self, user_id: str, attributes: Optional[UserAttributes] = None
    ) -> Optional[OptimizelyUserContext]:
        """
        We do not check for is_valid here as a user context can be created successfully
        even when the SDK is not fully configured.

        Args:
            user_id: string to use as user id for user context
            attributes: dictionary of attributes or None

        Returns:
            UserContext instance or None if the user id or attributes are invalid.
        """
        if not isinstance(user_id, str):
            self.logger.error(enums.Errors.INVALID_INPUT.format('user_id'))
            return None

        if attributes is not None and type(attributes) is not dict:
            self.logger.error(enums.Errors.INVALID_INPUT.format('attributes'))
            return None

        return OptimizelyUserContext(self, self.logger, user_id, attributes, True)

    def _decide(
        self, user_context: Optional[OptimizelyUserContext], key: str,
        decide_options: Optional[list[str]] = None
    ) -> OptimizelyDecision:
        """
        decide calls optimizely decide with feature key provided
        Args:
            user_context: UserContent with userid and attributes
            key: feature key
            decide_options: list of OptimizelyDecideOption

        Returns:
            Decision object
        """

        # raising on user context as it is internal and not provided directly by the user.
        if not isinstance(user_context, OptimizelyUserContext):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('user_context'))

        reasons = []

        # check if SDK is ready
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('decide'))
            reasons.append(OptimizelyDecisionMessage.SDK_NOT_READY)
            return OptimizelyDecision(flag_key=key, user_context=user_context, reasons=reasons)

        # validate that key is a string
        if not isinstance(key, str):
            self.logger.error('Key parameter is invalid')
            reasons.append(OptimizelyDecisionMessage.FLAG_KEY_INVALID.format(key))
            return OptimizelyDecision(flag_key=key, user_context=user_context, reasons=reasons)

        # validate that key maps to a feature flag
        config = self.config_manager.get_config()
        if not config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('decide'))
            reasons.append(OptimizelyDecisionMessage.SDK_NOT_READY)
            return OptimizelyDecision(flag_key=key, user_context=user_context, reasons=reasons)

        feature_flag = config.get_feature_from_key(key)
        if feature_flag is None:
            self.logger.error(f"No feature flag was found for key '{key}'.")
            reasons.append(OptimizelyDecisionMessage.FLAG_KEY_INVALID.format(key))
            return OptimizelyDecision(flag_key=key, user_context=user_context, reasons=reasons)

        # merge decide_options and default_decide_options
        if isinstance(decide_options, list):
            decide_options += self.default_decide_options
        else:
            self.logger.debug('Provided decide options is not an array. Using default decide options.')
            decide_options = self.default_decide_options

        # Create Optimizely Decision Result.
        user_id = user_context.user_id
        attributes = user_context.get_user_attributes()
        variation_key = None
        variation = None
        feature_enabled = False
        rule_key = None
        flag_key = key
        all_variables = {}
        experiment = None
        decision_source = DecisionSources.ROLLOUT
        source_info: dict[str, Any] = {}
        decision_event_dispatched = False

        # Check forced decisions first
        optimizely_decision_context = OptimizelyUserContext.OptimizelyDecisionContext(flag_key=key, rule_key=rule_key)
        forced_decision_response = self.decision_service.validated_forced_decision(config,
                                                                                   optimizely_decision_context,
                                                                                   user_context)
        variation, decision_reasons = forced_decision_response
        reasons += decision_reasons

        if variation:
            decision = Decision(None, variation, enums.DecisionSources.FEATURE_TEST)
        else:
            # Regular decision
            decision, decision_reasons = self.decision_service.get_variation_for_feature(config,
                                                                                         feature_flag,
                                                                                         user_context, decide_options)

            reasons += decision_reasons

        # Fill in experiment and variation if returned (rollouts can have featureEnabled variables as well.)
        if decision.experiment is not None:
            experiment = decision.experiment
            source_info["experiment"] = experiment
            rule_key = experiment.key if experiment else None
        if decision.variation is not None:
            variation = decision.variation
            variation_key = variation.key
            feature_enabled = variation.featureEnabled
            decision_source = decision.source
            source_info["variation"] = variation

        # Send impression event if Decision came from a feature
        # test and decide options doesn't include disableDecisionEvent
        if OptimizelyDecideOption.DISABLE_DECISION_EVENT not in decide_options:
            if decision_source == DecisionSources.FEATURE_TEST or config.send_flag_decisions:
                self._send_impression_event(config, experiment, variation, flag_key, rule_key or '',
                                            decision_source, feature_enabled,
                                            user_id, attributes)

                decision_event_dispatched = True

        # Generate all variables map if decide options doesn't include excludeVariables
        if OptimizelyDecideOption.EXCLUDE_VARIABLES not in decide_options:
            for variable_key, variable in feature_flag.variables.items():
                variable_value = variable.defaultValue
                if feature_enabled:
                    variable_value = config.get_variable_value_for_variation(variable, decision.variation)
                    self.logger.debug(
                        f'Got variable value "{variable_value}" for '
                        f'variable "{variable_key}" of feature flag "{flag_key}".'
                    )

                try:
                    actual_value = config.get_typecast_value(variable_value, variable.type)
                except:
                    self.logger.error('Unable to cast value. Returning None.')
                    actual_value = None

                all_variables[variable_key] = actual_value

        should_include_reasons = OptimizelyDecideOption.INCLUDE_REASONS in decide_options

        # Send notification
        self.notification_center.send_notifications(
            enums.NotificationTypes.DECISION,
            enums.DecisionNotificationTypes.FLAG,
            user_id,
            attributes or {},
            {
                'flag_key': flag_key,
                'enabled': feature_enabled,
                'variables': all_variables,
                'variation_key': variation_key,
                'rule_key': rule_key,
                'reasons': reasons if should_include_reasons else [],
                'decision_event_dispatched': decision_event_dispatched

            },
        )

        return OptimizelyDecision(variation_key=variation_key, enabled=feature_enabled, variables=all_variables,
                                  rule_key=rule_key, flag_key=flag_key,
                                  user_context=user_context, reasons=reasons if should_include_reasons else []
                                  )

    def _decide_all(
        self,
        user_context: Optional[OptimizelyUserContext],
        decide_options: Optional[list[str]] = None
    ) -> dict[str, OptimizelyDecision]:
        """
        decide_all will return a decision for every feature key in the current config
        Args:
            user_context: UserContent object
            decide_options: Array of DecisionOption

        Returns:
            A dictionary of feature key to Decision
        """
        # raising on user context as it is internal and not provided directly by the user.
        if not isinstance(user_context, OptimizelyUserContext):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('user_context'))

        # check if SDK is ready
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('decide_all'))
            return {}

        config = self.config_manager.get_config()
        if not config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('decide'))
            return {}

        keys = []
        for f in config.feature_flags:
            keys.append(f['key'])
        return self._decide_for_keys(user_context, keys, decide_options)

    def _decide_for_keys(
        self,
        user_context: Optional[OptimizelyUserContext],
        keys: list[str],
        decide_options: Optional[list[str]] = None
    ) -> dict[str, OptimizelyDecision]:
        """
        Args:
            user_context: UserContent
            keys: list of feature keys to run decide on.
            decide_options: an array of DecisionOption objects

        Returns:
            An dictionary of feature key to Decision
        """
        # raising on user context as it is internal and not provided directly by the user.
        if not isinstance(user_context, OptimizelyUserContext):
            raise exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('user_context'))

        # check if SDK is ready
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('decide_for_keys'))
            return {}

        # merge decide_options and default_decide_options
        merged_decide_options: list[str] = []
        if isinstance(decide_options, list):
            merged_decide_options = decide_options[:]
            merged_decide_options += self.default_decide_options
        else:
            self.logger.debug('Provided decide options is not an array. Using default decide options.')
            merged_decide_options = self.default_decide_options

        enabled_flags_only = OptimizelyDecideOption.ENABLED_FLAGS_ONLY in merged_decide_options

        decisions = {}
        for key in keys:
            decision = self._decide(user_context, key, decide_options)
            if enabled_flags_only and not decision.enabled:
                continue
            decisions[key] = decision
        return decisions

    def _setup_odp(self, sdk_key: Optional[str]) -> None:
        """
        - Make sure odp manager is instantiated with provided parameters or defaults.
        - Set up listener to update odp_config when datafile is updated.
        - Manually call callback in case datafile was received before the listener was registered.
        """

        # no need to instantiate a cache if a custom cache or segment manager is provided.
        if (
            not self.sdk_settings.odp_disabled and
            not self.sdk_settings.odp_segment_manager and
            not self.sdk_settings.segments_cache
        ):
            self.sdk_settings.segments_cache = LRUCache(
                self.sdk_settings.segments_cache_size,
                self.sdk_settings.segments_cache_timeout_in_secs
            )

        self.odp_manager = OdpManager(
            self.sdk_settings.odp_disabled,
            self.sdk_settings.segments_cache,
            self.sdk_settings.odp_segment_manager,
            self.sdk_settings.odp_event_manager,
            self.sdk_settings.fetch_segments_timeout,
            self.sdk_settings.odp_event_timeout,
            self.sdk_settings.odp_flush_interval,
            self.logger,
        )

        if self.sdk_settings.odp_disabled:
            return

        internal_notification_center = _NotificationCenterRegistry.get_notification_center(sdk_key, self.logger)
        if internal_notification_center:
            internal_notification_center.add_notification_listener(
                enums.NotificationTypes.OPTIMIZELY_CONFIG_UPDATE,
                self._update_odp_config_on_datafile_update
            )

        self._update_odp_config_on_datafile_update()

    def _update_odp_config_on_datafile_update(self) -> None:
        config = None

        if isinstance(self.config_manager, PollingConfigManager):
            # can not use get_config here because callback is fired before _config_ready event is set
            # and that would be a deadlock
            config = self.config_manager._config
        elif self.config_manager:
            config = self.config_manager.get_config()

        if not config:
            return

        self.odp_manager.update_odp_config(
            config.public_key_for_odp,
            config.host_for_odp,
            config.all_segments
        )

    def _identify_user(self, user_id: str) -> None:
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('identify_user'))
            return

        config = self.config_manager.get_config()
        if not config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('identify_user'))
            return

        self.odp_manager.identify_user(user_id)

    def _fetch_qualified_segments(self, user_id: str, options: Optional[list[str]] = None) -> Optional[list[str]]:
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('fetch_qualified_segments'))
            return None

        config = self.config_manager.get_config()
        if not config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('fetch_qualified_segments'))
            return None

        return self.odp_manager.fetch_qualified_segments(user_id, options or [])

    def send_odp_event(
        self,
        action: str,
        identifiers: dict[str, str],
        type: str = enums.OdpManagerConfig.EVENT_TYPE,
        data: Optional[dict[str, str | int | float | bool | None]] = None
    ) -> None:
        """
        Send an event to the ODP server.

        Args:
            action: The event action name. Cannot be None or empty string.
            identifiers: A dictionary for identifiers. The caller must provide at least one key-value pair.
            type: The event type. Default 'fullstack'.
            data: An optional dictionary for associated data. The default event data will be added to this data
            before sending to the ODP server.
        """
        if not self.is_valid:
            self.logger.error(enums.Errors.INVALID_OPTIMIZELY.format('send_odp_event'))
            return

        if action is None or action == "":
            self.logger.error(enums.Errors.ODP_INVALID_ACTION)
            return

        if not identifiers or not isinstance(identifiers, dict):
            self.logger.error('ODP events must have at least one key-value pair in identifiers.')
            return

        if type is None or type == "":
            type = enums.OdpManagerConfig.EVENT_TYPE

        config = self.config_manager.get_config()
        if not config:
            self.logger.error(enums.Errors.INVALID_PROJECT_CONFIG.format('send_odp_event'))
            return

        self.odp_manager.send_event(type, action, identifiers, data or {})

    def close(self) -> None:
        if callable(getattr(self.event_processor, 'stop', None)):
            self.event_processor.stop()  # type: ignore[attr-defined]
        if self.is_valid:
            self.odp_manager.close()
        if callable(getattr(self.config_manager, 'stop', None)):
            self.config_manager.stop()  # type: ignore[attr-defined]
