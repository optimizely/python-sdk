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

  @abstractproperty
  class EventParams(object):
    pass

  def _get_project_id(self):
    """ Get project ID.

    Returns:
      Project ID of the datafile.
    """

    return self.config.get_project_id()

  def _get_revision(self):
    """ Get revision.

    Returns:
      Revision of the datafile.
    """

    return self.config.get_revision()

  def _get_account_id(self):
    """ Get account ID.

    Returns:
      Account ID in the datafile.
    """

    return self.config.get_account_id()

  @abstractmethod
  def _get_attributes(self, attributes):
    """ Get attribute(s) information.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
    """
    pass

  def _get_anonymize_ip(self):
    """ Get IP anonymization bool

    Returns:
      bool 'anonymizeIP' value in the datafile.
    """

    return self.config.get_anonymize_ip_value()

  @abstractmethod
  def _get_time(self):
    """ Get time in milliseconds to be added.

    Returns:
      int Current time in milliseconds.
    """

    return int(round(time.time() * 1000))

  def _get_common_params(self, user_id, attributes):
    """ Get params which are used same in both conversion and impression events.

    Args:
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
     Dict consisting of parameters common to both impression and conversion events.
    """
    commonParams = {}

    commonParams[self.EventParams.PROJECT_ID] = self._get_project_id()
    commonParams[self.EventParams.ACCOUNT_ID] = self._get_account_id()

    visitor = {}
    visitor[self.EventParams.END_USER_ID] = user_id
    visitor[self.EventParams.SNAPSHOTS] = []

    commonParams[self.EventParams.USERS] = []
    commonParams[self.EventParams.USERS].append(visitor)
    commonParams[self.EventParams.USERS][0][self.EventParams.ATTRIBUTES] = self._get_attributes(attributes)

    commonParams[self.EventParams.SOURCE_SDK_TYPE] = 'python-sdk'
    commonParams[self.EventParams.SOURCE_SDK_VERSION] = version.__version__
    commonParams[self.EventParams.ANONYMIZE_IP] = self._get_anonymize_ip()
    commonParams[self.EventParams.REVISION] = self._get_revision()

    return commonParams


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
    ANONYMIZE_IP = 'anonymize_ip'
    REVISION = 'revision'

  def _get_attributes(self, attributes):
    """ Get attribute(s) information.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      List consisting of valid attributes for the user. Empty otherwise.
    """

    params = []

    if not attributes:
      return []

    for attribute_key in attributes.keys():
      attribute_value = attributes.get(attribute_key)
      # Omit falsy attribute values
      if attribute_value:
        attribute = self.config.get_attribute(attribute_key)
        if attribute:
          params.append({
            self.EventParams.EVENT_ID: attribute.id,
            'key': attribute_key,
            'type': self.EventParams.CUSTOM,
            'value': attribute_value,
          })

    return params

  def _get_required_params_for_impression(self, experiment, variation_id):
    """ Get parameters that are required for the impression event to register.

    Args:
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.

    Returns:
      Dict consisting of decisions and events info for impression event.
    """
    snapshot = {}

    snapshot[self.EventParams.DECISIONS] = [{
      self.EventParams.EXPERIMENT_ID: experiment.id,
      self.EventParams.VARIATION_ID: variation_id,
      self.EventParams.CAMPAIGN_ID: experiment.layerId
    }]

    snapshot[self.EventParams.EVENTS] = [{
      self.EventParams.EVENT_ID: experiment.layerId,
      self.EventParams.TIME: self._get_time(),
      self.EventParams.KEY: 'campaign_activated',
      self.EventParams.UUID: str(uuid.uuid4())
    }]

    return snapshot

  def _get_required_params_for_conversion(self, event_key, event_tags, decisions):
    """ Get parameters that are required for the conversion event to register.

    Args:
      event_key: Key representing the event which needs to be recorded.
      event_tags: Dict representing metadata associated with the event.
      decisions: List of tuples representing valid experiments IDs and variation IDs.

    Returns:
      Dict consisting of the decisions and events info for conversion event.
    """

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
          self.EventParams.TIME: self._get_time(),
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

        return snapshot

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

    params = self._get_common_params(user_id, attributes)
    impression_params = self._get_required_params_for_impression(experiment, variation_id)

    params[self.EventParams.USERS][0][self.EventParams.SNAPSHOTS].append(impression_params)

    return Event(self.EVENTS_URL,
                 params,
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

    params = self._get_common_params(user_id, attributes)
    conversion_params = self._get_required_params_for_conversion(event_key, event_tags, decisions)

    params[self.EventParams.USERS][0][self.EventParams.SNAPSHOTS].append(conversion_params)

    return Event(self.EVENTS_URL,
                 params,
                 http_verb=self.HTTP_VERB,
                 headers=self.HTTP_HEADERS)
