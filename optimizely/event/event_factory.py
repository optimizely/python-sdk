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

from optimizely.helpers import enums
from optimizely.helpers import event_tag_utils
from optimizely.helpers import validator
from . import log_event
from . import payload
from . import user_event

CUSTOM_ATTRIBUTE_FEATURE_TYPE = 'custom'


class EventFactory(object):
    """ EventFactory builds LogEvent object from a given UserEvent.
  This class serves to separate concerns between events in the SDK and the API used
  to record the events via the Optimizely Events API ("https://developers.optimizely.com/x/events/api/index.html")
  """

    EVENT_ENDPOINT = 'https://logx.optimizely.com/v1/events'
    HTTP_VERB = 'POST'
    HTTP_HEADERS = {'Content-Type': 'application/json'}
    ACTIVATE_EVENT_KEY = 'campaign_activated'

    @classmethod
    def create_log_event(cls, user_events, logger):
        """ Create LogEvent instance.

    Args:
      user_events: A single UserEvent instance or a list of UserEvent instances.
      logger: Provides a logger instance.

    Returns:
      LogEvent instance.
    """

        if not isinstance(user_events, list):
            user_events = [user_events]

        visitors = []

        for event in user_events:
            visitor = cls._create_visitor(event, logger)

            if visitor:
                visitors.append(visitor)

        if len(visitors) == 0:
            return None

        user_context = user_events[0].event_context
        event_batch = payload.EventBatch(
            user_context.account_id,
            user_context.project_id,
            user_context.revision,
            user_context.client_name,
            user_context.client_version,
            user_context.anonymize_ip,
            True,
        )

        event_batch.visitors = visitors

        event_params = event_batch.get_event_params()

        return log_event.LogEvent(cls.EVENT_ENDPOINT, event_params, cls.HTTP_VERB, cls.HTTP_HEADERS)

    @classmethod
    def _create_visitor(cls, event, logger):
        """ Helper method to create Visitor instance for event_batch.

    Args:
      event: Instance of UserEvent.
      logger: Provides a logger instance.

    Returns:
      Instance of Visitor. None if:
      - event is invalid.
    """

        if isinstance(event, user_event.ImpressionEvent):
            experiment_layerId, experiment_id, variation_id, variation_key = '', '', '', ''

            if event.variation:
                variation_id = event.variation.id
                variation_key = event.variation.key

            if event.experiment:
                experiment_layerId = event.experiment.layerId
                experiment_id = event.experiment.id

            metadata = payload.Metadata(event.flag_key, event.rule_key, event.rule_type, variation_key)
            decision = payload.Decision(experiment_layerId, experiment_id, variation_id, metadata)
            snapshot_event = payload.SnapshotEvent(
                experiment_layerId, event.uuid, cls.ACTIVATE_EVENT_KEY, event.timestamp,
            )

            snapshot = payload.Snapshot([snapshot_event], [decision])

            visitor = payload.Visitor([snapshot], event.visitor_attributes, event.user_id)

            return visitor

        elif isinstance(event, user_event.ConversionEvent):
            revenue = event_tag_utils.get_revenue_value(event.event_tags)
            value = event_tag_utils.get_numeric_value(event.event_tags, logger)

            snapshot_event = payload.SnapshotEvent(
                event.event.id, event.uuid, event.event.key, event.timestamp, revenue, value, event.event_tags,
            )

            snapshot = payload.Snapshot([snapshot_event])

            visitor = payload.Visitor([snapshot], event.visitor_attributes, event.user_id)

            return visitor

        else:
            logger.error('Invalid user event.')
            return None

    @staticmethod
    def build_attribute_list(attributes, project_config):
        """ Create Vistor Attribute List.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded or None.
      project_config: Instance of ProjectConfig.

    Returns:
      List consisting of valid attributes for the user. Empty otherwise.
    """

        attributes_list = []

        if project_config is None:
            return attributes_list

        if isinstance(attributes, dict):
            for attribute_key in attributes.keys():
                attribute_value = attributes.get(attribute_key)
                # Omit attribute values that are not supported by the log endpoint.
                if validator.is_attribute_valid(attribute_key, attribute_value):
                    attribute_id = project_config.get_attribute_id(attribute_key)
                    if attribute_id:
                        attributes_list.append(
                            payload.VisitorAttribute(
                                attribute_id, attribute_key, CUSTOM_ATTRIBUTE_FEATURE_TYPE, attribute_value,
                            )
                        )

        # Append Bot Filtering Attribute
        bot_filtering_value = project_config.get_bot_filtering_value()
        if isinstance(bot_filtering_value, bool):
            attributes_list.append(
                payload.VisitorAttribute(
                    enums.ControlAttributes.BOT_FILTERING,
                    enums.ControlAttributes.BOT_FILTERING,
                    CUSTOM_ATTRIBUTE_FEATURE_TYPE,
                    bot_filtering_value,
                )
            )

        return attributes_list
