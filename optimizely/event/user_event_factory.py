# Copyright 2019, 2021-2022, Optimizely
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

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from optimizely.helpers.event_tag_utils import EventTags
from . import event_factory
from . import user_event
from optimizely.helpers import enums


if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from optimizely.optimizely_user_context import UserAttributes
    from optimizely.project_config import ProjectConfig
    from optimizely.entities import Experiment, Variation


class UserEventFactory:
    """ UserEventFactory builds impression and conversion events from a given UserEvent. """

    @classmethod
    def create_impression_event(
        cls,
        project_config: ProjectConfig,
        activated_experiment: Experiment,
        variation_id: Optional[str],
        flag_key: str,
        rule_key: str,
        rule_type: str,
        enabled: bool,
        user_id: str,
        user_attributes: Optional[UserAttributes]
    ) -> Optional[user_event.ImpressionEvent]:
        """ Create impression Event to be sent to the logging endpoint.

    Args:
      project_config: Instance of ProjectConfig.
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
      flag_key: key for a feature flag.
      rule_key: key for an experiment.
      rule_type: type for the source.
      enabled: boolean representing if feature is enabled
      user_id: ID for user.
      user_attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Event object encapsulating the impression event. None if:
      - activated_experiment is None.
    """

        if not activated_experiment and rule_type is not enums.DecisionSources.ROLLOUT:
            return None

        variation: Optional[Variation] = None
        experiment_id = None
        if activated_experiment:
            experiment_id = activated_experiment.id

        if variation_id and flag_key:
            # need this condition when we send events involving forced decisions
            # (F-to-D or E-to-D with any ruleKey/variationKey combinations)
            variation = project_config.get_flag_variation(flag_key, 'id', variation_id)
        elif variation_id and experiment_id:
            variation = project_config.get_variation_from_id_by_experiment_id(experiment_id, variation_id)

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
            enabled,
            project_config.get_bot_filtering_value(),
        )

    @classmethod
    def create_conversion_event(
        cls,
        project_config: ProjectConfig,
        event_key: str,
        user_id: str,
        user_attributes: Optional[UserAttributes],
        event_tags: Optional[EventTags]
    ) -> Optional[user_event.ConversionEvent]:
        """ Create conversion Event to be sent to the logging endpoint.

    Args:
      project_config: Instance of ProjectConfig.
      event_key: Key representing the event which needs to be recorded.
      user_id: ID for user.
      user_attributes: Dict representing user attributes and values.
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
