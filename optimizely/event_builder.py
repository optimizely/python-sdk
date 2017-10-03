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

import time
import uuid
from abc import abstractmethod
from abc import abstractproperty

from . import version
from .helpers import event_tag_utils


class Event(object):
  """ Representation of an event which can be sent to the Optimizely logging endpoint. """

  def __init__(self, url, params, http_verb=None, headers=None):
    self.url = url
    self.params = params
    self.http_verb = http_verb or 'GET'
    self.headers = headers


class BaseEventBuilder(object):
  """ Base class which encapsulates methods to build events for tracking impressions and conversions. """

  def __init__(self, config):
    self.config = config
    self.params = {}

  @abstractproperty
  class EventParams(object):
    pass

  def _add_project_id(self):
    """ Add project ID to the event. """

    self.params[self.EventParams.PROJECT_ID] = self.config.get_project_id()

  def _add_account_id(self):
    """ Add account ID to the event. """

    self.params[self.EventParams.ACCOUNT_ID] = self.config.get_account_id()

  def _add_user_id(self, user_id):
    """ Add user ID to the event. """

    self.params[self.EventParams.END_USER_ID] = user_id

  @abstractmethod
  def _add_attributes(self, attributes):
    """ Add attribute(s) information to the event.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
    """
    pass

  @abstractmethod
  def _add_source(self):
    """ Add source information to the event. """
    pass

  @abstractmethod
  def _add_time(self):
    """ Add time information to the event. """
    pass

  def _add_revision(self):
    """ Add datafile revision information to the event. """
    pass

  def _add_common_params(self, user_id, attributes):
    """ Add params which are used same in both conversion and impression events.

    Args:
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.
    """

    self._add_project_id()
    self._add_account_id()
    self._add_user_id(user_id)
    self._add_attributes(attributes)
    self._add_source()
    self._add_revision()
    self._add_time()


class EventBuilder(BaseEventBuilder):
  """ Class which encapsulates methods to build events for tracking
  impressions and conversions using the new V3 event API (batch). """

  EVENTS_URL = 'https://logx.optimizely.com/v1/events'
  HTTP_VERB = 'POST'
  HTTP_HEADERS = {'Content-Type': 'application/json'}

  class EventParams(object):
    ACCOUNT_ID = 'account_id'
    PROJECT_ID = 'project_id'
    EXPERIMENT_ID = 'experiment_id'
    CAMPAIGN_ID = 'campaign_id'
    VARIATION_ID = 'variation_id'
    END_USER_ID = 'visitor_id'
    EVENTS = 'events'
    EVENT_ID = 'entity_id'
    ATTRIBUTES = 'attributes'
    DECISIONS = 'decisions'
    TIME = 'timestamp'
    KEY = 'key'
    TAGS = 'tags'
    UUID = 'uuid'
    USERS = 'visitors'
    SNAPSHOTS = 'snapshots'
    SOURCE_SDK_TYPE = 'client_name'
    SOURCE_SDK_VERSION = 'client_version'
    CUSTOM = 'custom'

  def _add_attributes(self, attributes):
    """ Add attribute(s) information to the event.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
    """

    visitor = self.params[self.EventParams.USERS][0]
    visitor[self.EventParams.ATTRIBUTES] = []

    if not attributes:
      return

    for attribute_key in attributes.keys():
      attribute_value = attributes.get(attribute_key)
      # Omit falsy attribute values
      if attribute_value:
        attribute = self.config.get_attribute(attribute_key)
        if attribute:
          visitor[self.EventParams.ATTRIBUTES].append({
            self.EventParams.EVENT_ID: attribute.id,
            'key': attribute_key,
            'type': self.EventParams.CUSTOM,
            'value': attribute_value,
          })

  def _add_source(self):
    """ Add source information to the event. """

    self.params[self.EventParams.SOURCE_SDK_TYPE] = 'python-sdk'
    self.params[self.EventParams.SOURCE_SDK_VERSION] = version.__version__

  def _add_time(self):
    """ Add time information to the event. """

    self.params[self.EventParams.TIME] = int(round(time.time() * 1000))

  def _add_visitor(self, user_id):
    """ Add user to the event """

    self.params[self.EventParams.USERS] = []
    # Add a single visitor
    visitor = {}
    visitor[self.EventParams.END_USER_ID] = user_id
    visitor[self.EventParams.SNAPSHOTS] = []
    self.params[self.EventParams.USERS].append(visitor)

  def _add_common_params(self, user_id, attributes):
    """ Add params which are used same in both conversion and impression events.

    Args:
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.
    """
    self._add_project_id()
    self._add_account_id()
    self._add_visitor(user_id)
    self._add_attributes(attributes)
    self._add_source()

  def _add_required_params_for_impression(self, experiment, variation_id):
    """ Add parameters that are required for the impression event to register.

    Args:
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
    """
    snapshot = {}

    snapshot[self.EventParams.DECISIONS] = [{
      self.EventParams.EXPERIMENT_ID: experiment.id,
      self.EventParams.VARIATION_ID: variation_id,
      self.EventParams.CAMPAIGN_ID: experiment.layerId
    }]

    snapshot[self.EventParams.EVENTS] = [{
      self.EventParams.EVENT_ID: experiment.layerId,
      self.EventParams.TIME: int(round(time.time() * 1000)),
      self.EventParams.KEY: 'campaign_activated',
      self.EventParams.UUID: str(uuid.uuid4())
    }]

    visitor = self.params[self.EventParams.USERS][0]
    visitor[self.EventParams.SNAPSHOTS].append(snapshot)

  def _add_required_params_for_conversion(self, event_key, event_tags, decisions):
    """ Add parameters that are required for the conversion event to register.

    Args:
      event_key: Key representing the event which needs to be recorded.
      event_tags: Dict representing metadata associated with the event.
      decisions: List of tuples representing valid experiments IDs and variation IDs.
    """

    visitor = self.params[self.EventParams.USERS][0]

    for experiment_id, variation_id in decisions:
      snapshot = {}
      experiment = self.config.get_experiment_from_id(experiment_id)

      if variation_id:
        snapshot[self.EventParams.DECISIONS] = [{
          self.EventParams.EXPERIMENT_ID: experiment_id,
          self.EventParams.VARIATION_ID: variation_id,
          self.EventParams.CAMPAIGN_ID: experiment.layerId
        }]

        event_dict = {
          self.EventParams.EVENT_ID: self.config.get_event(event_key).id,
          self.EventParams.TIME: int(round(time.time() * 1000)),
          self.EventParams.KEY: event_key,
          self.EventParams.UUID: str(uuid.uuid4())
        }

        if event_tags:
          revenue_value = event_tag_utils.get_revenue_value(event_tags)
          if revenue_value is not None:
            event_dict[event_tag_utils.REVENUE_METRIC_TYPE] = revenue_value

          numeric_value = event_tag_utils.get_numeric_value(event_tags, self.config.logger)
          if numeric_value is not None:
            event_dict[event_tag_utils.NUMERIC_METRIC_TYPE] = numeric_value

          if len(event_tags) > 0:
            event_dict[self.EventParams.TAGS] = event_tags

        snapshot[self.EventParams.EVENTS] = [event_dict]
        visitor[self.EventParams.SNAPSHOTS].append(snapshot)

  def create_impression_event(self, experiment, variation_id, user_id, attributes):
    """ Create impression Event to be sent to the logging endpoint.

    Args:
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Event object encapsulating the impression event.
    """

    self.params = {}
    self._add_common_params(user_id, attributes)
    self._add_required_params_for_impression(experiment, variation_id)

    return Event(self.EVENTS_URL,
                 self.params,
                 http_verb=self.HTTP_VERB,
                 headers=self.HTTP_HEADERS)

  def create_conversion_event(self, event_key, user_id, attributes, event_tags, decisions):
    """ Create conversion Event to be sent to the logging endpoint.

    Args:
      event_key: Key representing the event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing user attributes and values.
      event_tags: Dict representing metadata associated with the event.
      decisions: List of tuples representing experiments IDs and variation IDs.

    Returns:
      Event object encapsulating the conversion event.
    """

    self.params = {}
    self._add_common_params(user_id, attributes)
    self._add_required_params_for_conversion(event_key, event_tags, decisions)
    return Event(self.EVENTS_URL,
                 self.params,
                 http_verb=self.HTTP_VERB,
                 headers=self.HTTP_HEADERS)
