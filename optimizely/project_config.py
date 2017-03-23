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

import json

from .helpers import condition as condition_helper
from .helpers import enums
from . import entities
from . import exceptions

REVENUE_GOAL_KEY = 'Total Revenue'
V1_CONFIG_VERSION = '1'
V2_CONFIG_VERSION = '2'


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
    self.version = config.get('version')
    self.account_id = config.get('accountId')
    self.project_id = config.get('projectId')
    self.revision = config.get('revision')
    self.groups = config.get('groups', [])
    self.experiments = config.get('experiments', [])
    self.events = config.get('events', [])
    self.attributes = config.get('dimensions', []) \
      if self.version == V1_CONFIG_VERSION else config.get('attributes', [])
    self.audiences = config.get('audiences', [])

    # Utility maps for quick lookup
    self.group_id_map = self._generate_key_map(self.groups, 'id', entities.Group)
    self.experiment_key_map = self._generate_key_map(self.experiments, 'key', entities.Experiment)
    self.event_key_map = self._generate_key_map(self.events, 'key', entities.Event)
    self.attribute_key_map = self._generate_key_map(self.attributes, 'key', entities.Attribute)
    self.audience_id_map = self._generate_key_map(self.audiences, 'id', entities.Audience)
    self.audience_id_map = self._deserialize_audience(self.audience_id_map)
    for group in self.group_id_map.values():
      experiments_in_group_key_map = self._generate_key_map(group.experiments, 'key', entities.Experiment)
      for experiment in experiments_in_group_key_map.values():
        experiment.__dict__.update({
          'groupId': group.id,
          'groupPolicy': group.policy
        })
      self.experiment_key_map.update(experiments_in_group_key_map)

    self.experiment_id_map = {}
    self.variation_key_map = {}
    self.variation_id_map = {}
    for experiment in self.experiment_key_map.values():
      self.experiment_id_map[experiment.id] = experiment
      self.variation_key_map[experiment.key] = self._generate_key_map(
        experiment.variations, 'key', entities.Variation
      )
      self.variation_id_map[experiment.key] = {}
      for variation in self.variation_key_map.get(experiment.key).values():
        self.variation_id_map[experiment.key][variation.id] = variation

  @staticmethod
  def _generate_key_map(list, key, entity_class):
    """ Helper method to generate map from key to entity object for given list of dicts.

    Args:
      list: List consisting of dict.
      key: Key in each dict which will be key in the map.
      entity_class: Class representing the entity.

    Returns:
      Map mapping key to entity object.
    """

    key_map = {}
    for obj in list:
      key_map[obj[key]] = entity_class(**obj)

    return key_map

  @staticmethod
  def _deserialize_audience(audience_map):
    """ Helper method to de-serialize and populate audience map with the condition list and structure.

    Args:
      audience_map: Dict mapping audience ID to audience object.

    Returns:
      Dict additionally consisting of condition list and structure on every audience object.
    """

    for audience in audience_map.values():
      condition_structure, condition_list = condition_helper.loads(audience.conditions)
      audience.__dict__.update({
        'conditionStructure': condition_structure,
        'conditionList': condition_list
      })

    return audience_map

  def get_version(self):
    """ Get version of the datafile.

    Returns:
      Version of the datafile.
    """

    return self.version

  def get_revision(self):
    """ Get revision of the datafile.

    Returns:
      Revision of the datafile.
    """

    return self.revision

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

  def get_experiment_from_key(self, experiment_key):
    """ Get experiment for the provided experiment key.

    Args:
      experiment_key: Experiment key for which experiment is to be determined.

    Returns:
      Experiment corresponding to the provided experiment key.
    """

    experiment = self.experiment_key_map.get(experiment_key)

    if experiment:
      return experiment

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_experiment_from_id(self, experiment_id):
    """ Get experiment for the provided experiment ID.

    Args:
      experiment_id: Experiment ID for which experiment is to be determined.

    Returns:
      Experiment corresponding to the provided experiment ID.
    """

    experiment = self.experiment_id_map.get(experiment_id)

    if experiment:
      return experiment

    self.logger.log(enums.LogLevels.ERROR, 'Experiment ID "%s" is not in datafile.' % experiment_id)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_group(self, group_id):
    """ Get group for the provided group ID.

    Args:
      group_id: Group ID for which group is to be determined.

    Returns:
      Group corresponding to the provided group ID.
    """

    group = self.group_id_map.get(group_id)

    if group:
      return group

    self.logger.log(enums.LogLevels.ERROR, 'Group ID "%s" is not in datafile.' % group_id)
    self.error_handler.handle_error(exceptions.InvalidGroupException(enums.Errors.INVALID_GROUP_ID_ERROR))
    return None

  def get_audience(self, audience_id):
    """ Get audience object for the provided audience ID.

    Args:
      audience_id: ID of the audience.

    Returns:
      Dict representing the audience.
    """

    audience = self.audience_id_map.get(audience_id)
    if audience:
      return audience

    self.logger.log(enums.LogLevels.ERROR, 'Audience ID "%s" is not in datafile.' % audience_id)
    self.error_handler.handle_error(exceptions.InvalidAudienceException((enums.Errors.INVALID_AUDIENCE_ERROR)))

  def get_variation_from_key(self, experiment_key, variation_key):
    """ Get variation given experiment and variation key.

    Args:
      experiment: Key representing parent experiment of variation.
      variation_key: Key representing the variation.

    Returns
      Object representing the variation.
    """

    variation_map = self.variation_key_map.get(experiment_key)

    if variation_map:
      variation = variation_map.get(variation_key)
      if variation:
        return variation
      else:
        self.logger.log(enums.LogLevels.ERROR, 'Variation key "%s" is not in datafile.' % variation_key)
        self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION_ERROR))
        return None

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_variation_from_id(self, experiment_key, variation_id):
    """ Get variation given experiment and variation ID.

    Args:
      experiment: Key representing parent experiment of variation.
      variation_id: ID representing the variation.

    Returns
      Object representing the variation.
    """

    variation_map = self.variation_id_map.get(experiment_key)

    if variation_map:
      variation = variation_map.get(variation_id)
      if variation:
        return variation
      else:
        self.logger.log(enums.LogLevels.ERROR, 'Variation ID "%s" is not in datafile.' % variation_id)
        self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION_ERROR))
        return None

    self.logger.log(enums.LogLevels.ERROR, 'Experiment key "%s" is not in datafile.' % experiment_key)
    self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY_ERROR))
    return None

  def get_event(self, event_key):
    """ Get event for the provided event key.

    Args:
      event_key: Event key for which event is to be determined.

    Returns:
      Event corresponding to the provided event key.
    """

    event = self.event_key_map.get(event_key)

    if event:
      return event

    self.logger.log(enums.LogLevels.ERROR, 'Event "%s" is not in datafile.' % event_key)
    self.error_handler.handle_error(exceptions.InvalidEventException(enums.Errors.INVALID_EVENT_KEY_ERROR))
    return None

  def get_revenue_goal(self):
    """ Get the revenue goal for the project.

    Returns:
      Revenue goal.
    """

    return self.get_event(REVENUE_GOAL_KEY)

  def get_attribute(self, attribute_key):
    """ Get attribute for the provided attribute key.

    Args:
      attribute_key: Attribute key for which attribute is to be fetched.

    Returns:
      Attribute corresponding to the provided attribute key.
    """

    attribute = self.attribute_key_map.get(attribute_key)

    if attribute:
      return attribute

    self.logger.log(enums.LogLevels.ERROR, 'Attribute "%s" is not in datafile.' % attribute_key)
    self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_ERROR))
    return None
