import time

from .helpers import audience
from .helpers import experiment
from . import version


# Attribute mapping format
ATTRIBUTE_PARAM_FORMAT = '{segment_prefix}{segment_id}'

# Experiment mapping format
EXPERIMENT_PARAM_FORMAT = '{experiment_prefix}{experiment_id}'

# Event API format
OFFLINE_API_PATH = 'https://{project_id}.log.optimizely.com/event'


class Params(object):
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


class Event(object):
  """ Representation of an event which can be sent to the Optimizely logging endpoint. """

  def __init__(self, params):
    self.params = params

  def get_url(self):
    """ Get URL for sending impression/conversion event.

    Returns:
      URL for the event API.
    """

    return OFFLINE_API_PATH.format(project_id=self.params[Params.PROJECT_ID])

  def get_params(self):
    """ Get params to be sent along to the event endpoint.

    Returns:
      Dict of params representing the impression/conversion event.
    """

    return self.params


class EventBuilder(object):
  """ Class which encapsulates methods to build events for tracking impressions and conversions. """

  def __init__(self, config, bucketer):
    self.config = config
    self.bucketer = bucketer
    self.params = {}

  def _add_project_id(self):
    """ Add project ID to the event. """

    self.params[Params.PROJECT_ID] = self.config.get_project_id()

  def _add_account_id(self):
    """ Add account ID to the event. """

    self.params[Params.ACCOUNT_ID] = self.config.get_account_id()

  def _add_user_id(self, user_id):
    """ Add user ID to the event. """

    self.params[Params.END_USER_ID] = user_id

  def _add_attributes(self, attributes):
    """ Add attribute(s) information to the event.

    Args:
      attributes: Dict representing user attributes and values which need to be recorded.
    """

    if not attributes:
      return

    for attribute_key in list(attributes.keys()):
      attribute_value = attributes[attribute_key]
      # Omit falsy attribute values
      if attribute_value:
        segment_id = self.config.get_segment_id(attribute_key)
        if segment_id:
          self.params[ATTRIBUTE_PARAM_FORMAT.format(
            segment_prefix=Params.SEGMENT_PREFIX, segment_id=segment_id)] = attribute_value

  def _add_source(self):
    """ Add source information to the event. """

    self.params[Params.SOURCE] = 'python-sdk-{version}'.format(version=version.__version__)

  def _add_time(self):
    """ Add time information to the event. """

    self.params[Params.TIME] = int(time.time())

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
    self._add_time()

  def _add_impression_goal(self, experiment_key):
    """ Add impression goal information to the event.

    Args:
      experiment_key: Experiment which is being activated.
    """

    # For tracking impressions, goal ID is set equal to experiment ID of experiment being activated
    self.params[Params.GOAL_ID] = self.config.get_experiment_id(experiment_key)
    self.params[Params.GOAL_NAME] = 'visitor-event'

  def _add_experiment(self, experiment_key, variation_id):
    """ Add experiment to variation mapping to the impression event.

    Args:
      experiment_key: Experiment which is being activated.
      variation_id: ID for variation which would be presented to user.
    """

    experiment_id = self.config.get_experiment_id(experiment_key)
    self.params[EXPERIMENT_PARAM_FORMAT.format(experiment_prefix=Params.EXPERIMENT_PREFIX,
                                               experiment_id=experiment_id)] = variation_id

  def _add_experiment_variation_params(self, event_key, user_id, valid_experiments):
    """ Maps experiment and corresponding variation as parameters to be used in the event tracking call.

    Args:
      event_key: Goal key representing the event which needs to be recorded.
      user_id: ID for user.
      valid_experiments: List of tuples representing valid experiments for the event.
    """

    for experiment in valid_experiments:
        variation_id = self.bucketer.bucket(experiment[1], user_id)
        if variation_id:
          self.params[EXPERIMENT_PARAM_FORMAT.format(experiment_prefix=Params.EXPERIMENT_PREFIX,
                                                     experiment_id=experiment[0])] = variation_id

  def _add_conversion_goal(self, event_key, event_value):
    """ Add conversion goal information to the event.

    Args:
      event_key: Goal key representing the event which needs to be recorded.
      event_value: Value associated with the event. Can be used to represent revenue in cents.
    """

    goal_id = self.config.get_goal_id(event_key)
    event_ids = goal_id

    if event_value:
      event_ids = '{goal_id},{revenue_goal_id}'.format(goal_id=goal_id,
                                                       revenue_goal_id=self.config.get_revenue_goal_id())
      self.params[Params.EVENT_VALUE] = event_value

    self.params[Params.GOAL_ID] = event_ids
    self.params[Params.GOAL_NAME] = event_key

  def create_impression_event(self, experiment_key, variation_id, user_id, attributes):
    """ Create impression Event to be sent to the logging endpoint.

    Args:
      experiment_key: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Event object encapsulating the impression event.
    """

    self.params = {}
    self._add_common_params(user_id, attributes)
    self._add_impression_goal(experiment_key)
    self._add_experiment(experiment_key, variation_id)
    return Event(self.params)

  def create_conversion_event(self, event_key, user_id, attributes, event_value, valid_experiments):
    """ Create conversion Event to be sent to the logging endpoint.

    Args:
      event_key: Goal key representing the event which needs to be recorded.
      user_id: ID for user.
      event_value: Value associated with the event. Can be used to represent revenue in cents.
      valid_experiments: List of tuples representing valid experiments for the event.

    Returns:
      Event object encapsulating the conversion event.
    """

    self.params = {}
    self._add_common_params(user_id, attributes)
    self._add_conversion_goal(event_key, event_value)
    self._add_experiment_variation_params(event_key, user_id, valid_experiments)
    return Event(self.params)
