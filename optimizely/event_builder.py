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

  def _add_visitor(self, user_id):
    """ Add user ID to the even """
    self.params['visitors'] = []
    # Add a single visitor
    visitor = {}
    visitor[self.EventParams.END_USER_ID] = user_id
    visitor["snapshots"] = []
    self.params['visitors'].append(visitor)

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
    self._add_visitor(user_id)
    self._add_attributes(attributes)
    self._add_source()
    self._add_revision()


class EventBuilder(BaseEventBuilder):
  """ Class which encapsulates methods to build events for tracking
  impressions and conversions using the new endpoints. """

  ENDPOINT = 'https://logx.optimizely.com/v1/events'
  HTTP_VERB = 'POST'
  HTTP_HEADERS = {'Content-Type': 'application/json'}

  class EventParams(object):
    ACCOUNT_ID = 'accountId'
    PROJECT_ID = 'projectId'
    VISITOR_ID = 'visitorId'
    EXPERIMENT_ID = 'experimentId'
    CAMPAIGN_ID = 'campaignId'
    VARIATION_ID = 'variationId'
    END_USER_ID = 'visitorId'
    EVENT = 'events'
    EVENT_ID = 'entityId'
    EVENT_NAME = 'eventName'
    ATTRIBUTES = 'attributes'
    DECISION = 'decisions'
    REVISION = 'revision'
    TIME = 'timestamp'
    KEY = 'key'
    UUID = 'uuid'
    SOURCE_SDK_TYPE = 'clientName'
    SOURCE_SDK_VERSION = 'clientVersion'
    EVENT_METRICS = 'eventMetrics'
    EVENT_FEATURES = 'eventFeatures'

  def _add_attributes(self, attributes):
    """ Add attribute(s) information to the event.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
    """

    if not attributes:
      return

    visitor = next(iter(self.params['visitors'] or []), None)
    visitor[self.EventParams.ATTRIBUTES] = []

    for attribute_key in attributes.keys():
      attribute_value = attributes.get(attribute_key)
      # Omit falsy attribute values
      if attribute_value:
        attribute = self.config.get_attribute(attribute_key)
        if attribute:
          visitor[self.EventParams.ATTRIBUTES].append({
              'entityId': attribute.id,
              'key': attribute_key,
              'type': 'custom',
              'value': attribute_value,
          })


  def _add_snapshot(self):
    self.snapshot = {}

  def _add_attribute(self):
    self.attribute = {}

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

    self.snapshot[self.EventParams.DECISION] = [{
        self.EventParams.EXPERIMENT_ID: experiment.id,
        self.EventParams.VARIATION_ID: variation_id,
        self.EventParams.CAMPAIGN_ID: experiment.layerId
    }]

    self.snapshot[self.EventParams.EVENT] = [{
        self.EventParams.EVENT_ID: experiment.layerId,
        self.EventParams.TIME: int(round(time.time() * 1000)),
        self.EventParams.KEY : 'campaign_activated',
        self.EventParams.UUID : str(uuid.uuid4())
    }]

    visitor_list = next(iter(self.params['visitors'] or []), None)
    visitor_list['snapshots'].append(self.snapshot)

  def _add_required_params_for_conversion(self, event_key, event_tags, decisions):
    """ Add parameters that are required for the conversion event to register.

    Args:
      event_key: Key representing the event which needs to be recorded.
      event_tags: Dict representing metadata associated with the event.
      decisions: List of tuples representing valid experiments IDs and variation IDs.
    """

    event_list = []
    self.snapshot[self.EventParams.EVENT] = []

    visitor = next(iter(self.params['visitors'] or []), None)

    for experiment in valid_experiments:
      variation = self.bucketer.bucket(experiment, user_id)
      if variation:
        self.snapshot[self.EventParams.DECISION] = [{
            self.EventParams.EXPERIMENT_ID: experiment.id,
            self.EventParams.VARIATION_ID: variation.id,
            self.EventParams.CAMPAIGN_ID: experiment.layerId
        }]

        event_dict = {
            self.EventParams.EVENT_ID: self.config.get_event(event_key).id,
            self.EventParams.TIME: int(round(time.time() * 1000)),
            self.EventParams.KEY : event_key,
            self.EventParams.UUID : str(uuid.uuid4())
        }

        if event_tags:
          event_value = event_tag_utils.get_revenue_value(event_tags)
          if event_value is not None:
            event_dict['revenue'] = event_value
            # remove revenue from event_dict
            del event_tags['revenue']

          if len(event_tags) > 0:
            event_dict['tags'] = event_tags

        self.snapshot[self.EventParams.EVENT].append(event_dict)     

      visitor['snapshots'].append(self.snapshot)

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
    self._add_snapshot()
    self._add_required_params_for_impression(experiment, variation_id)
    print self.params
    return Event(self.ENDPOINT,
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
    self._add_snapshot()
    self._add_required_params_for_conversion(event_key, user_id, event_tags, valid_experiments)
    return Event(self.ENDPOINT,
                 self.params,
                 http_verb=self.HTTP_VERB,
                 headers=self.HTTP_HEADERS)
