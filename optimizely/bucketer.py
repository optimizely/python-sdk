import math
try:
  import mmh3
except ImportError:
  from .lib import pymmh3 as mmh3

from .helpers import enums
from . import exceptions

MAX_TRAFFIC_VALUE = 10000
UNSIGNED_MAX_32_BIT_VALUE = 0xFFFFFFFF
MAX_HASH_VALUE = math.pow(2, 32)
HASH_SEED = 1
BUCKETING_ID_TEMPLATE = '{user_id}{parent_id}'
GROUP_POLICIES = ['random']


class Bucketer(object):
  """ Optimizely bucketing algorithm that evenly distributes visitors. """

  def __init__(self, project_config):
    """ Bucketer init method to set bucketing seed and project config data.

    Args:
      project_config: Project config data to be used in making bucketing decisions.
    """

    self.bucket_seed = HASH_SEED
    self.config = project_config

  def _generate_unsigned_hash_code_32_bit(self, bucketing_id):
    """ Helper method to retrieve hash code.

    Args:
      bucketing_id: ID for bucketing.

    Returns:
      Hash code which is a 32 bit unsigned integer.
    """

    # Adjusting MurmurHash code to be unsigned
    return (mmh3.hash(bucketing_id, self.bucket_seed) & UNSIGNED_MAX_32_BIT_VALUE)

  def _generate_bucket_value(self, bucketing_id):
    """ Helper function to generate bucket value in half-closed interval [0, MAX_TRAFFIC_VALUE).

    Args:
      bucketing_id: ID for bucketing.

    Returns:
      Bucket value corresponding to the provided bucketing ID.
    """

    ratio = float(self._generate_unsigned_hash_code_32_bit(bucketing_id)) / MAX_HASH_VALUE
    return math.floor(ratio * MAX_TRAFFIC_VALUE)

  def _find_bucket(self, user_id, parent_id, traffic_allocations):
    """ Determine entity based on bucket value and traffic allocations.

    Args:
      user_id: ID for user.
      parent_id: ID representing group or experiment.
      traffic_allocations: Traffic allocations representing traffic allotted to experiments or variations.

    Returns:
      Entity ID which may represent experiment or group.
    """

    bucketing_id = BUCKETING_ID_TEMPLATE.format(user_id=user_id, parent_id=parent_id)
    bucketing_number = self._generate_bucket_value(bucketing_id)
    self.config.logger.log(enums.LogLevels.DEBUG, 'Assigned bucket %s to user "%s".' % (bucketing_number, user_id))

    for traffic_allocation in traffic_allocations:
      current_end_of_range = traffic_allocation.get('endOfRange')
      if bucketing_number < current_end_of_range:
        return traffic_allocation.get('entityId')

    return None

  def bucket(self, experiment, user_id):
    """ For a given experiment and bucketing ID determines ID of variation to be shown to user.

    Args:
      experiment: Object representing the experiment for which user is to be bucketed.
      user_id: ID for user.

    Returns:
      Variation ID for variation in which the visitor with ID user_id will be put in. None if no variation.
    """

    if not experiment:
      return None

    # Check if user is white-listed for a variation
    forced_variations = experiment.forcedVariations
    if forced_variations and user_id in forced_variations:
      variation_key = forced_variations.get(user_id)
      variation_id = self.config.get_variation_id(experiment.key, variation_key)
      if variation_id:
        self.config.logger.log(enums.LogLevels.INFO,
                               'User "%s" is forced in variation "%s".' % (user_id, variation_key))
      return variation_id

    # Determine if experiment is in a mutually exclusive group
    if experiment.groupPolicy in GROUP_POLICIES:
      group_traffic_allocations = self.config.get_traffic_allocation(self.config.group_id_map, experiment.groupId)

      if not group_traffic_allocations:
        self.config.logger.log(enums.LogLevels.ERROR, 'Group ID "%s" is not in datafile.' % experiment.groupId)
        self.config.error_handler.handle_error(
          exceptions.InvalidExperimentException(enums.Errors.INVALID_GROUP_ID_ERROR)
        )
        return None

      user_experiment_id = self._find_bucket(user_id, experiment.groupId, group_traffic_allocations)
      if not user_experiment_id:
        self.config.logger.log(enums.LogLevels.INFO, 'User "%s" is in no experiment.' % user_id)
        return None

      if user_experiment_id != experiment.id:
        self.config.logger.log(enums.LogLevels.INFO, 'User "%s" is not in experiment "%s" of group %s.' %
                               (user_id, experiment.key, experiment.groupId))
        return None

      self.config.logger.log(enums.LogLevels.INFO, 'User "%s" is in experiment %s of group %s.' %
                             (user_id, experiment.key, experiment.groupId))

    # Bucket user if not in white-list and in group (if any)
    variation_id = self._find_bucket(user_id, experiment.id, experiment.trafficAllocation)
    if variation_id:
      variation_key = self.config.get_variation_key_from_id(experiment.key, variation_id)
      self.config.logger.log(enums.LogLevels.INFO, 'User "%s" is in variation "%s" of experiment %s.' %
                             (user_id, variation_key, experiment.key))
      return variation_id

    self.config.logger.log(enums.LogLevels.INFO, 'User "%s" is in no variation.' % user_id)
    return None
