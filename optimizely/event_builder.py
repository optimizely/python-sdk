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
  impressions and conversions using the new endpoints. """

  IMPRESSION_ENDPOINT = 'https://logx.optimizely.com/log/decision'
  CONVERSION_ENDPOINT = 'https://logx.optimizely.com/log/event'
  HTTP_VERB = 'POST'
  HTTP_HEADERS = {'Content-Type': 'application/json'}

  class EventParams(object):
    ACCOUNT_ID = 'accountId'
    PROJECT_ID = 'projectId'
    LAYER_ID = 'layerId'
    EXPERIMENT_ID = 'experimentId'
    VARIATION_ID = 'variationId'
    END_USER_ID = 'visitorId'
    EVENT_ID = 'eventEntityId'
    EVENT_NAME = 'eventName'
    EVENT_METRICS = 'eventMetrics'
    EVENT_FEATURES = 'eventFeatures'
    USER_FEATURES = 'userFeatures'
    DECISION = 'decision'
    LAYER_STATES = 'layerStates'
    REVISION = 'revision'
    TIME = 'timestamp'
    SOURCE_SDK_TYPE = 'clientEngine'
    SOURCE_SDK_VERSION = 'clientVersion'
    ACTION_TRIGGERED = 'actionTriggered'
    IS_GLOBAL_HOLDBACK = 'isGlobalHoldback'
    IS_LAYER_HOLDBACK = 'isLayerHoldback'

  def _add_attributes(self, attributes):
    """ Add attribute(s) information to the event.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
    """

    self.params[self.EventParams.USER_FEATURES] = []
    if not attributes:
      return

    for attribute_key in attributes.keys():
      attribute_value = attributes.get(attribute_key)
      # Omit falsy attribute values
      if attribute_value:
        attribute = self.config.get_attribute(attribute_key)
        if attribute:
          self.params[self.EventParams.USER_FEATURES].append({
            'id': attribute.id,
            'name': attribute_key,
            'type': 'custom',
            'value': attribute_value,
            'shouldIndex': True
          })

  def _add_source(self):
    """ Add source information to the event. """

    self.params[self.EventParams.SOURCE_SDK_TYPE] = 'python-sdk'
    self.params[self.EventParams.SOURCE_SDK_VERSION] = version.__version__

  def _add_revision(self):
    """ Add datafile revision information to the event. """
    self.params[self.EventParams.REVISION] = self.config.get_revision()

  def _add_time(self):
    """ Add time information to the event. """

    self.params[self.EventParams.TIME] = int(round(time.time() * 1000))

  def _add_required_params_for_impression(self, experiment, variation_id):
    """ Add parameters that are required for the impression event to register.

    Args:
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
    """

    self.params[self.EventParams.IS_GLOBAL_HOLDBACK] = False
    self.params[self.EventParams.LAYER_ID] = experiment.layerId
    self.params[self.EventParams.DECISION] = {
      self.EventParams.EXPERIMENT_ID: experiment.id,
      self.EventParams.VARIATION_ID: variation_id,
      self.EventParams.IS_LAYER_HOLDBACK: False
    }

  def _add_required_params_for_conversion(self, event_key, event_tags, decisions):
    """ Add parameters that are required for the conversion event to register.

    Args:
      event_key: Key representing the event which needs to be recorded.
      event_tags: Dict representing metadata associated with the event.
      decisions: List of tuples representing valid experiments IDs and variation IDs.
    """

    self.params[self.EventParams.IS_GLOBAL_HOLDBACK] = False
    self.params[self.EventParams.EVENT_FEATURES] = []
    self.params[self.EventParams.EVENT_METRICS] = []

    if event_tags:
      event_value = event_tag_utils.get_revenue_value(event_tags)
      if event_value is not None:
        self.params[self.EventParams.EVENT_METRICS] = [{
          'name': event_tag_utils.EVENT_VALUE_METRIC,
          'value': event_value
        }]

      for event_tag_id in event_tags.keys():
        event_tag_value = event_tags.get(event_tag_id)
        if event_tag_value is None:
          continue

        event_feature = {
          'name': event_tag_id,
          'type': 'custom',
          'value': event_tag_value,
          'shouldIndex': False,
        }
        self.params[self.EventParams.EVENT_FEATURES].append(event_feature)

    self.params[self.EventParams.LAYER_STATES] = []
    for experiment_id, variation_id in decisions:
      experiment = self.config.get_experiment_from_id(experiment_id)
      self.params[self.EventParams.LAYER_STATES].append({
        self.EventParams.LAYER_ID: experiment.layerId,
        self.EventParams.REVISION: self.config.get_revision(),
        self.EventParams.ACTION_TRIGGERED: True,
        self.EventParams.DECISION: {
          self.EventParams.EXPERIMENT_ID: experiment.id,
          self.EventParams.VARIATION_ID: variation_id,
          self.EventParams.IS_LAYER_HOLDBACK: False
        }
      })

    self.params[self.EventParams.EVENT_ID] = self.config.get_event(event_key).id
    self.params[self.EventParams.EVENT_NAME] = event_key

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
    return Event(self.IMPRESSION_ENDPOINT,
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
    return Event(self.CONVERSION_ENDPOINT,
                 self.params,
                 http_verb=self.HTTP_VERB,
                 headers=self.HTTP_HEADERS)
