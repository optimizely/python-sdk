# Copyright 2016-2017, 2019-2020 Optimizely
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

import math

try:
    import mmh3
except ImportError:
    from .lib import pymmh3 as mmh3


MAX_TRAFFIC_VALUE = 10000
UNSIGNED_MAX_32_BIT_VALUE = 0xFFFFFFFF
MAX_HASH_VALUE = math.pow(2, 32)
HASH_SEED = 1
BUCKETING_ID_TEMPLATE = '{bucketing_id}{parent_id}'
GROUP_POLICIES = ['random']


class Bucketer(object):
    """ Optimizely bucketing algorithm that evenly distributes visitors. """

    def __init__(self):
        """ Bucketer init method to set bucketing seed and logger instance. """

        self.bucket_seed = HASH_SEED

    def _generate_unsigned_hash_code_32_bit(self, bucketing_id):
        """ Helper method to retrieve hash code.

        Args:
            bucketing_id: ID for bucketing.

        Returns:
            Hash code which is a 32 bit unsigned integer.
        """

        # Adjusting MurmurHash code to be unsigned
        return mmh3.hash(bucketing_id, self.bucket_seed) & UNSIGNED_MAX_32_BIT_VALUE

    def _generate_bucket_value(self, bucketing_id):
        """ Helper function to generate bucket value in half-closed interval [0, MAX_TRAFFIC_VALUE).

        Args:
            bucketing_id: ID for bucketing.

        Returns:
            Bucket value corresponding to the provided bucketing ID.
        """

        ratio = float(self._generate_unsigned_hash_code_32_bit(bucketing_id)) / MAX_HASH_VALUE
        return math.floor(ratio * MAX_TRAFFIC_VALUE)

    def find_bucket(self, project_config, bucketing_id, parent_id, traffic_allocations):
        """ Determine entity based on bucket value and traffic allocations.

        Args:
            project_config: Instance of ProjectConfig.
            bucketing_id: ID to be used for bucketing the user.
            parent_id: ID representing group or experiment.
            traffic_allocations: Traffic allocations representing traffic allotted to experiments or variations.

        Returns:
            Entity ID which may represent experiment or variation.
        """

        bucketing_key = BUCKETING_ID_TEMPLATE.format(bucketing_id=bucketing_id, parent_id=parent_id)
        bucketing_number = self._generate_bucket_value(bucketing_key)
        project_config.logger.debug(
            'Assigned bucket %s to user with bucketing ID "%s".' % (bucketing_number, bucketing_id)
        )

        for traffic_allocation in traffic_allocations:
            current_end_of_range = traffic_allocation.get('endOfRange')
            if bucketing_number < current_end_of_range:
                return traffic_allocation.get('entityId')

        return None

    def bucket(self, project_config, experiment, user_id, bucketing_id):
        """ For a given experiment and bucketing ID determines variation to be shown to user.

        Args:
            project_config: Instance of ProjectConfig.
            experiment: Object representing the experiment or rollout rule in which user is to be bucketed.
            user_id: ID for user.
            bucketing_id: ID to be used for bucketing the user.

        Returns:
            Variation in which user with ID user_id will be put in. None if no variation.
        """

        if not experiment:
            return None

        # Determine if experiment is in a mutually exclusive group.
        # This will not affect evaluation of rollout rules.
        if experiment.groupPolicy in GROUP_POLICIES:
            group = project_config.get_group(experiment.groupId)

            if not group:
                return None

            user_experiment_id = self.find_bucket(
                project_config, bucketing_id, experiment.groupId, group.trafficAllocation,
            )
            if not user_experiment_id:
                project_config.logger.info('User "%s" is in no experiment.' % user_id)
                return None

            if user_experiment_id != experiment.id:
                project_config.logger.info(
                    'User "%s" is not in experiment "%s" of group %s.' % (user_id, experiment.key, experiment.groupId)
                )
                return None

            project_config.logger.info(
                'User "%s" is in experiment %s of group %s.' % (user_id, experiment.key, experiment.groupId)
            )

        # Bucket user if not in white-list and in group (if any)
        variation_id = self.find_bucket(project_config, bucketing_id, experiment.id, experiment.trafficAllocation)
        if variation_id:
            variation = project_config.get_variation_from_id(experiment.key, variation_id)
            return variation

        return None
