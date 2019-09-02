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

from .user_event import ConversionEvent, ImpressionEvent
from .payload import Decision, EventBatch, Snapshot, SnapshotEvent, Visitor, VisitorAttribute
from .log_event import LogEvent
from optimizely.helpers import enums, event_tag_utils, validator

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
      user_events: An array of UserEvent instances.
      logger: Provides a logger instance.

    Returns:
      LogEvent instance.
    """

    if not isinstance(user_events, list):
      user_events = [user_events]

    visitors = []

    for user_event in user_events:
      visitor = cls._create_visitor(user_event, logger)

      if visitor:
        visitors.append(visitor)

      user_context = user_event.event_context

      event_batch = EventBatch(
        user_context.account_id,
        user_context.project_id,
        user_context.revision,
        user_context.client_name,
        user_context.client_version,
        user_context.anonymize_ip,
        True
      )

    if len(visitors) == 0:
      return None

    event_batch.visitors = visitors

    event_params = event_batch.get_event_params()

    return LogEvent(cls.EVENT_ENDPOINT, event_params, cls.HTTP_VERB, cls.HTTP_HEADERS)

  @classmethod
  def _create_visitor(cls, user_event, logger):
    """ Helper method to create Visitor instance for event_batch. """

    if isinstance(user_event, ImpressionEvent):
      decision = Decision(
        user_event.experiment.layerId,
        user_event.experiment.id,
        user_event.variation.id,
      )

      snapshot_event = SnapshotEvent(
        user_event.experiment.layerId,
        user_event.uuid,
        cls.ACTIVATE_EVENT_KEY,
        user_event.timestamp
      )

      snapshot = Snapshot([snapshot_event], [decision])

      visitor = Visitor([snapshot], user_event.visitor_attributes, user_event.user_id)

      return visitor

    elif isinstance(user_event, ConversionEvent):
      revenue = event_tag_utils.get_revenue_value(user_event.event_tags)
      value = event_tag_utils.get_numeric_value(user_event.event_tags, logger)

      snapshot_event = SnapshotEvent(
        user_event.event.id,
        user_event.uuid,
        user_event.event.key,
        user_event.timestamp,
        revenue,
        value,
        user_event.event_tags
      )

      snapshot = Snapshot([snapshot_event])

      visitor = Visitor([snapshot], user_event.visitor_attributes, user_event.user_id)

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

    if project_config is None:
      return None

    attributes_list = []

    if isinstance(attributes, dict):
      for attribute_key in attributes.keys():
        attribute_value = attributes.get(attribute_key)
        # Omit attribute values that are not supported by the log endpoint.
        if validator.is_attribute_valid(attribute_key, attribute_value):
          attribute_id = project_config.get_attribute_id(attribute_key)
          if attribute_id:
            attributes_list.append(
              VisitorAttribute(
                attribute_id,
                attribute_key,
                CUSTOM_ATTRIBUTE_FEATURE_TYPE,
                attribute_value)
            )

    # Append Bot Filtering Attribute
    bot_filtering_value = project_config.get_bot_filtering_value()
    if isinstance(bot_filtering_value, bool):
      attributes_list.append(
        VisitorAttribute(
           enums.ControlAttributes.BOT_FILTERING,
           enums.ControlAttributes.BOT_FILTERING,
           CUSTOM_ATTRIBUTE_FEATURE_TYPE,
           bot_filtering_value)
      )

    return attributes_list
