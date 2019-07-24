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
import json
from more_itertools.more import always_iterable

from .entity.conversion_event import ConversionEvent
from .entity.decision import Decision
from .entity.event_batch import EventBatch
from .entity.impression_event import ImpressionEvent
from .entity.snapshot import Snapshot
from .entity.snapshot_event import SnapshotEvent
from .entity.visitor import Visitor
from .log_event import LogEvent
from ..helpers import event_tag_utils
from ..helpers import enums
from ..helpers import validator

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

    visitors = []

    for user_event in always_iterable(user_events):
      visitors.append(cls._create_visitor(user_event, logger))
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

    if len([x for x in visitors if x is not None]) == 0:
      return None

    event_batch.visitors = visitors

    event_batch_json = json.dumps(event_batch.__dict__, default=lambda o: o.__dict__)

    return LogEvent(cls.EVENT_ENDPOINT, event_batch_json, cls.HTTP_VERB, cls.HTTP_HEADERS)

  @classmethod
  def _create_visitor(cls, user_event, logger):
    if not user_event:
      return None

    if isinstance(user_event, ImpressionEvent):
      decision = Decision(
        user_event.experiment.layerId if hasattr(user_event, 'experiment') else None,
        user_event.experiment.id if hasattr(user_event, 'experiment') else None,
        user_event.variation.id if hasattr(user_event, 'variation') else None
      )

      snapshot_event = SnapshotEvent(
        user_event.experiment.layerId if hasattr(user_event, 'experiment') else None,
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
        user_event.event.id if hasattr(user_event, 'event') else None,
        user_event.uuid,
        user_event.event.key if hasattr(user_event, 'event') else None,
        user_event.timestamp,
        revenue,
        value,
        user_event.event_tags
      )

      snapshot = Snapshot([snapshot_event])

      visitor = Visitor([snapshot], user_event.visitor_attributes, user_event.user_id)

      return visitor

    else:
      # include log message for invalid event type
      return

  @staticmethod
  def build_attribute_list(attributes, project_config):
    """ Create Vistor Attribute List.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
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
            attributes_list.append({
              'entity_id': attribute_id,
              'key': attribute_key,
              'type': CUSTOM_ATTRIBUTE_FEATURE_TYPE,
              'value': attribute_value
            })

    # Append Bot Filtering Attribute
    bot_filtering_value = project_config.get_bot_filtering_value()
    if isinstance(bot_filtering_value, bool):
      attributes_list.append({
          'entity_id': enums.ControlAttributes.BOT_FILTERING,
          'key': enums.ControlAttributes.BOT_FILTERING,
          'type': CUSTOM_ATTRIBUTE_FEATURE_TYPE,
          'value': bot_filtering_value
      })

    return attributes_list
