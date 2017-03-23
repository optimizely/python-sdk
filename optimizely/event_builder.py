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

from . import exceptions
from . import project_config
from . import version
from .helpers import enums
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

  def __init__(self, config, bucketer):
    self.config = config
    self.bucketer = bucketer
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


class EventBuilderV1(BaseEventBuilder):
  """ Class which encapsulates methods to build events for tracking
  impressions and conversions using the old endpoint. """

  # Attribute mapping format
  ATTRIBUTE_PARAM_FORMAT = '{segment_prefix}{segment_id}'
  # Experiment mapping format
  EXPERIMENT_PARAM_FORMAT = '{experiment_prefix}{experiment_id}'
  # Event API format
  OFFLINE_API_PATH = 'https://{project_id}.log.optimizely.com/event'


  class EventParams(object):
    ACCOUNT_ID = 'd'
    PROJECT_ID = 'a'
    EXPERIMENT_PREFIX = 'x'
    GOAL_ID = 'g'
    GOAL_NAME = 'n'
    END_USER_ID = 'u'
    EVENT_VALUE = 'v'
    SEGMENT_PREFIX = 's'
    SOURCE = 'src'
    TIME = 'time'

  def _add_attributes(self, attributes):
    """ Add attribute(s) information to the event.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
    """

    if not attributes:
      return

    for attribute_key in attributes.keys():
      attribute_value = attributes.get(attribute_key)
      # Omit falsy attribute values
      if attribute_value:
        attribute = self.config.get_attribute(attribute_key)
        if attribute:
          self.params[self.ATTRIBUTE_PARAM_FORMAT.format(
            segment_prefix=self.EventParams.SEGMENT_PREFIX, segment_id=attribute.segmentId)] = attribute_value

  def _add_source(self):
    """ Add source information to the event. """

    self.params[self.EventParams.SOURCE] = 'python-sdk-{version}'.format(version=version.__version__)

  def _add_time(self):
    """ Add time information to the event. """

    self.params[self.EventParams.TIME] = int(time.time())

  def _add_impression_goal(self, experiment):
    """ Add impression goal information to the event.

    Args:
      experiment: Object representing experiment being activated.
    """

    # For tracking impressions, goal ID is set equal to experiment ID of experiment being activated
    self.params[self.EventParams.GOAL_ID] = experiment.id
    self.params[self.EventParams.GOAL_NAME] = 'visitor-event'

  def _add_experiment(self, experiment, variation_id):
    """ Add experiment to variation mapping to the impression event.

    Args:
      experiment: Object representing experiment being activated.
      variation_id: ID for variation which would be presented to user.
    """

    self.params[self.EXPERIMENT_PARAM_FORMAT.format(experiment_prefix=self.EventParams.EXPERIMENT_PREFIX,
                                                    experiment_id=experiment.id)] = variation_id

  def _add_experiment_variation_params(self, user_id, valid_experiments):
    """ Maps experiment and corresponding variation as parameters to be used in the event tracking call.

    Args:
      user_id: ID for user.
      valid_experiments: List of tuples representing valid experiments for the event.
    """

    for experiment in valid_experiments:
      variation = self.bucketer.bucket(experiment, user_id)
      if variation:
        self.params[self.EXPERIMENT_PARAM_FORMAT.format(experiment_prefix=self.EventParams.EXPERIMENT_PREFIX,
                                                        experiment_id=experiment.id)] = variation.id

  def _add_conversion_goal(self, event_key, event_value):
    """ Add conversion goal information to the event.

    Args:
      event_key: Event key representing the event which needs to be recorded.
      event_value: Value associated with the event. Can be used to represent revenue in cents.
    """

    event = self.config.get_event(event_key)

    if not event:
      return

    event_ids = event.id

    if event_value:
      event_ids = '{goal_id},{revenue_goal_id}'.format(goal_id=event.id,
                                                       revenue_goal_id=self.config.get_revenue_goal().id)
      self.params[self.EventParams.EVENT_VALUE] = event_value

    self.params[self.EventParams.GOAL_ID] = event_ids
    self.params[self.EventParams.GOAL_NAME] = event_key

  def create_impression_event(self, experiment, variation_id, user_id, attributes):
    """ Create impression Event to be sent to the logging endpoint.

    Args:
      experiment: Object representing experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Event object encapsulating the impression event.
    """

    self.params = {}
    self._add_common_params(user_id, attributes)
    self._add_impression_goal(experiment)
    self._add_experiment(experiment, variation_id)
    return Event(self.OFFLINE_API_PATH.format(project_id=self.params[self.EventParams.PROJECT_ID]),
                 self.params)

  def create_conversion_event(self, event_key, user_id, attributes, event_tags, valid_experiments):
    """ Create conversion Event to be sent to the logging endpoint.

    Args:
      event_key: Event key representing the event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing user attributes and values.
      event_tags: Dict representing metadata associated with the event.
      valid_experiments: List of tuples representing valid experiments for the event.

    Returns:
      Event object encapsulating the conversion event.
    """

    event_value = event_tag_utils.get_revenue_value(event_tags)

    self.params = {}
    self._add_common_params(user_id, attributes)
    self._add_conversion_goal(event_key, event_value)
    self._add_experiment_variation_params(user_id, valid_experiments)
    return Event(self.OFFLINE_API_PATH.format(project_id=self.params[self.EventParams.PROJECT_ID]),
                 self.params)


class EventBuilderV2(BaseEventBuilder):
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

  def _add_required_params_for_conversion(self, event_key, user_id, event_tags, valid_experiments):
    """ Add parameters that are required for the conversion event to register.

    Args:
      event_key: Key representing the event which needs to be recorded.
      user_id: ID for user.
      event_tags: Dict representing metadata associated with the event.
      valid_experiments: List of tuples representing valid experiments for the event.
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
    for experiment in valid_experiments:
      variation = self.bucketer.bucket(experiment, user_id)
      if variation:
        self.params[self.EventParams.LAYER_STATES].append({
          self.EventParams.LAYER_ID: experiment.layerId,
          self.EventParams.REVISION: self.config.get_revision(),
          self.EventParams.ACTION_TRIGGERED: True,
          self.EventParams.DECISION: {
            self.EventParams.EXPERIMENT_ID: experiment.id,
            self.EventParams.VARIATION_ID: variation.id,
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

  def create_conversion_event(self, event_key, user_id, attributes, event_tags, valid_experiments):
    """ Create conversion Event to be sent to the logging endpoint.

    Args:
      event_key: Key representing the event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing user attributes and values.
      event_tags: Dict representing metadata associated with the event.
      valid_experiments: List of tuples representing valid experiments for the event.

    Returns:
      Event object encapsulating the conversion event.
    """

    self.params = {}
    self._add_common_params(user_id, attributes)
    self._add_required_params_for_conversion(event_key, user_id, event_tags, valid_experiments)
    return Event(self.CONVERSION_ENDPOINT,
                 self.params,
                 http_verb=self.HTTP_VERB,
                 headers=self.HTTP_HEADERS)


def get_event_builder(config, bucketer):
  """ Helper method to get appropriate EventBuilder class based on the version of the datafile.

  Args:
    config: Object representing the project's configuration.
    bucketer: Object representing the bucketer.

  Returns:
    Event builder based on the version of the datafile.

  Raises:
    Exception if provided datafile has unsupported version.
  """

  config_version = config.get_version()
  if config_version == project_config.V1_CONFIG_VERSION:
    return EventBuilderV1(config, bucketer)
  if config_version == project_config.V2_CONFIG_VERSION:
    return EventBuilderV2(config, bucketer)

  raise exceptions.InvalidInputException(enums.Errors.UNSUPPORTED_DATAFILE_VERSION)
