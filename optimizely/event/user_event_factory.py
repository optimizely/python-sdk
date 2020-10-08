# Copyright 2019 Optimizely
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

from . import event_factory
from . import user_event
from optimizely.helpers import enums


class UserEventFactory(object):
    """ UserEventFactory builds impression and conversion events from a given UserEvent. """

    @classmethod
    def create_impression_event(
        cls, project_config, activated_experiment, variation_id, flag_key, rule_key, rule_type, user_id, user_attributes
    ):
        """ Create impression Event to be sent to the logging endpoint.

    Args:
      project_config: Instance of ProjectConfig.
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
      flag_key: key for a feature flag.
      rule_key: key for an experiment.
      rule_type: type for the source.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Event object encapsulating the impression event. None if:
      - activated_experiment is None.
    """

        if not activated_experiment and rule_type is not enums.DecisionSources.ROLLOUT:
            return None

        variation, experiment_key = None, None
        if activated_experiment:
            experiment_key = activated_experiment.key

        if variation_id and experiment_key:
            variation = project_config.get_variation_from_id(experiment_key, variation_id)
        event_context = user_event.EventContext(
            project_config.account_id, project_config.project_id, project_config.revision, project_config.anonymize_ip,
        )

        return user_event.ImpressionEvent(
            event_context,
            user_id,
            activated_experiment,
            event_factory.EventFactory.build_attribute_list(user_attributes, project_config),
            variation,
            flag_key,
            rule_key,
            rule_type,
            project_config.get_bot_filtering_value(),
        )

    @classmethod
    def create_conversion_event(cls, project_config, event_key, user_id, user_attributes, event_tags):
        """ Create conversion Event to be sent to the logging endpoint.

    Args:
      project_config: Instance of ProjectConfig.
      event_key: Key representing the event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing user attributes and values.
      event_tags: Dict representing metadata associated with the event.

    Returns:
      Event object encapsulating the conversion event.
    """

        event_context = user_event.EventContext(
            project_config.account_id, project_config.project_id, project_config.revision, project_config.anonymize_ip,
        )

        return user_event.ConversionEvent(
            event_context,
            project_config.get_event(event_key),
            user_id,
            event_factory.EventFactory.build_attribute_list(user_attributes, project_config),
            event_tags,
            project_config.get_bot_filtering_value(),
        )
