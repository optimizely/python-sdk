import json

from .helpers import condition as condition_helper
from .helpers import enums
from . import exceptions

REVENUE_GOAL_KEY = 'Total Revenue'


class ProjectConfig(object):
  """ Representation of the Optimizely project config. """

  def __init__(self, datafile, logger, error_handler):
    """ ProjectConfig init method to load and set project config data.

    Args:
      datafile: JSON string representing the project.
      logger: Provides a log message to send log messages to.
      error_handler: Provides a handle_error method to handle exceptions.
    """

    config = json.loads(datafile)
    self.logger = logger
    self.error_handler = error_handler
    self.account_id = config.get('accountId')
    self.project_id = config.get('projectId')
    self.revision = config.get('revision')
    self.groups = config.get('groups', [])
    self.experiments = config.get('experiments', [])
    self.events = config.get('events', [])
    self.attributes = config.get('dimensions', [])
    self.audiences = config.get('audiences', [])

    # Utility maps for quick lookup
    self.group_id_map = self._generate_key_map(self.groups, 'id')
    self.experiment_key_map = self._generate_key_map(self.experiments, 'key')
    self.experiment_id_map = self._generate_key_map(self.experiments, 'id')
    self.event_key_map = self._generate_key_map(self.events, 'key')
    self.attribute_key_map = self._generate_key_map(self.attributes, 'key')
    self.audience_id_map = self._generate_key_map(self.audiences, 'id')
    self.audience_id_map = self._deserialize_audience(self.audience_id_map)
    for group in self.group_id_map.values():
      experiments_in_group_map = self._generate_key_map(group['experiments'], 'key')
      for experiment in experiments_in_group_map.values():
        experiment.update({
          'groupId': group['id'],
          'groupPolicy': group['policy']
        })
      self.experiment_key_map.update(experiments_in_group_map)
    self.variation_key_map = {}
    self.variation_id_map = {}
    for experiment_key in self.experiment_key_map.keys():
      self.variation_key_map[experiment_key] = self._generate_key_map(
        self.experiment_key_map.get(experiment_key)['variations'], 'key'
      )
      self.variation_id_map[experiment_key] = self._generate_key_map(
        self.experiment_key_map.get(experiment_key)['variations'], 'id'
      )

  @staticmethod
  def _generate_key_map(list, key):
    """ Helper method to generate map from key to dict in list of dicts.

    Args:
      list: List consisting of dict.
      key: Key in each dict which will be key in the map.

    Returns:
      Map mapping key to dict.
    """

    key_map = {}
    for obj in list:
      key_map[obj[key]] = obj

    return key_map

  @staticmethod
  def _deserialize_audience(audience_map):
    """ Helper method to deserialize and populate audience map with the condition list and structure.

    Args:
      audience_map: Dict mapping audience ID to audience object.

    Returns:
      Dict additionally consisting of condition list and structure for every audience.
    """

    for audience_id in audience_map.keys():
      audience_map[audience_id]['conditionStructure'], audience_map[audience_id]['conditionList'] = \
        condition_helper.loads(audience_map[audience_id]['conditions'])

    return audience_map

  def get_account_id(self):
    """ Get account ID from the config.

    Returns:
      Account ID information from the config.
    """

    return self.account_id

  def get_project_id(self):
    """ Get project ID from the config.

    Returns:
      Project ID information from the config.
    """

    return self.project_id

  def get_experiment_keys(self):
    """ Get list of all experiment keys in the project.

    Returns:
      List of all experiment keys.
    """

    return list(self.experiment_key_map.keys())

  def get_experiment_group_id(self, experiment_key):
    """ Get group ID for the provided experiment key.

    Args:
      experiment_key: Experiment key for which group ID is to be determined.

    Returns:
      Group ID corresponding to the provided experiment key.
    """

    experiment = self.experiment_key_map.get(experiment_key)

    if experiment:
      return experiment.get('groupId')

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_experiment_group_policy(self, experiment_key):
    """ Get group policy for the provided experiment key.

    Args:
      experiment_key: Experiment key for which group policy is to be determined.

    Returns:
      Group policy corresponding to the provided experiment key.
    """

    experiment = self.experiment_key_map.get(experiment_key)

    if experiment:
      return experiment.get('groupPolicy')

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_experiment_id(self, experiment_key):
    """ Get experiment ID for the provided experiment key.

    Args:
      experiment_key: Experiment key for which ID is to be determined.

    Returns:
      Experiment ID corresponding to the provided experiment key.
    """

    experiment = self.experiment_key_map.get(experiment_key)

    if experiment:
      return experiment.get('id')

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_experiment_key(self, experiment_id):
    """ Get experiment key for the provided experiment ID.

    Args:
      experiment_id: Experiment ID for which key is to be determined.

    Returns:
      Experiment key corresponding to the provided experiment ID.
    """

    experiment = self.experiment_id_map.get(experiment_id)

    if experiment:
      return experiment.get('key')

    self.logger.log(enums.LogLevels.ERROR, 'Experiment ID "%s" is not in datafile.' % experiment_id)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_experiment_status(self, experiment_key):
    """ Get experiment status for the provided experiment key.

    Args:
      experiment_key: Experiment key for which status is to be determined.

    Returns:
      Experiment status corresponding to the provided experiment key.
    """

    experiment = self.experiment_key_map.get(experiment_key)

    if experiment:
      return experiment.get('status')

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_experiment_forced_variations(self, experiment_key):
    """ Get dict representing forced variations for the experiment.

    Args:
      experiment_key: Experiment key for which forced variations are to be fetched.

    Returns:
      Dict representing forced variations for the experiment.
    """

    experiment = self.experiment_key_map.get(experiment_key)

    if experiment:
      return experiment.get('forcedVariations', {})

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_audience_ids_for_experiment(self, experiment_key):
    """ Get audience IDs for the experiment.

    Args:
      experiment_key: Experiment key for which audience IDs are to be determined.

    Returns:
      Audience IDs corresponding to the experiment.
    """

    experiment = self.experiment_key_map.get(experiment_key)

    if experiment:
      return experiment.get('audienceIds', [])

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_audience_object_from_id(self, audience_id):
    """ Get audience object for the provided audience ID.

    Args:
      audience_id: ID of the audience.

    Returns:
      Dict representing the audience.
    """

    return self.audience_id_map.get(audience_id)

  def get_variation_key_from_id(self, experiment_key, variation_id):
    """ Get variation key given experiment key and variation ID.

    Args:
      experiment_key: Key representing parent experiment of variation.
      variation_id: ID of the variation.

    Returns
      Variation key.
    """

    variation_map = self.variation_id_map.get(experiment_key)

    if variation_map:
      variation_obj = variation_map.get(variation_id)
      if variation_obj:
        return variation_obj['key']
      else:
        self.logger.log(enums.LogLevels.ERROR, 'Variation ID "%s" is not in datafile.' % variation_id)
        self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION_ERROR))
        return None

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_variation_id(self, experiment_key, variation_key):
    """ Get variation ID given the experiment and variation key.

    Args:
      experiment_key: Parent experiment for the variation.
      variation_key: Variation for which the ID is to be determined.

    Returns:
      Variation ID corresponding to the variation.
    """

    variation_map = self.variation_key_map.get(experiment_key)

    if variation_map:
      variation_obj = variation_map.get(variation_key)
      if variation_obj:
        return variation_obj['id']
      else:
        self.logger.log(enums.LogLevels.ERROR, 'Variation key "%s" is not in datafile.' % variation_key)
        self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION_ERROR))
        return None

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_goal_id(self, goal_key):
    """ Get goal ID for the provided goal key.

    Args:
      goal_key: Goal key for which ID is to be determined.

    Returns:
      Goal ID corresponding to the provided goal key.
    """

    goal = self.event_key_map.get(goal_key)

    if goal:
      return goal.get('id')

    self.logger.log(enums.LogLevels.ERROR, 'Event "%s" is not in datafile.' % goal_key)
    self.error_handler.handle_error(exceptions.InvalidGoalException(enums.Errors.INVALID_EVENT_KEY_ERROR))
    return None

  def get_goal_keys(self):
    """ Get list of all goal keys in the project except 'Total Revenue'.

    Returns:
      List of all goal keys except 'Total Revenue'.
    """

    goal_keys = list(self.event_key_map.keys())
    if REVENUE_GOAL_KEY in goal_keys:
      goal_keys.remove(REVENUE_GOAL_KEY)

    return goal_keys

  def get_revenue_goal_id(self):
    """ Get ID of the revenue goal for the project.

    Returns:
      Revenue goal ID.
    """

    return self.get_goal_id(REVENUE_GOAL_KEY)

  def get_experiment_ids_for_goal(self, goal_key):
    """ Get experiment IDs for the provided goal key.

    Args:
      goal_key: Goal key for which experiment IDs are to be retrieved.

    Returns:
      List of all experiment IDs for the goal.
    """

    goal = self.event_key_map.get(goal_key)

    if goal:
      return goal.get('experimentIds', [])

    self.logger.log(enums.LogLevels.ERROR, 'Event "%s" is not in datafile.' % goal_key)
    self.error_handler.handle_error(exceptions.InvalidGoalException(enums.Errors.INVALID_EVENT_KEY_ERROR))
    return []

  def get_segment_id(self, attribute_key):
    """ Get segment ID for the provided attribute key.

    Args:
      attribute_key: Attribute key for which segment ID is to be determined.

    Returns:
      Segment ID corresponding to the provided attribute key.
    """

    attribute = self.attribute_key_map.get(attribute_key)

    if attribute:
      return attribute.get('segmentId')

    self.logger.log(enums.LogLevels.ERROR, 'Attribute "%s" is not in datafile.' % attribute_key)
    self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_ERROR))
    return None

  def get_traffic_allocation(self, entity_key_map, entity_key):
    """ Given an entity key map and entity key, returns the traffic allocation for that entity.

    Args:
      entity_key_map: Map representing the entity information.
      entity_key: Key for whcih traffic allocation is to be retrieved from the map

    Returns:
      Traffic allocation for the experiment.
    """

    entity = entity_key_map.get(entity_key)

    if entity:
      return entity.get('trafficAllocation')

    return None
