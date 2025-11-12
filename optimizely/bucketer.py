# Copyright 2016-2017, 2019-2022 Optimizely
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

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import math
from sys import version_info

from .lib import pymmh3 as mmh3


if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final


if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from .project_config import ProjectConfig
    from .entities import Experiment, Variation
    from .helpers.types import TrafficAllocation


MAX_TRAFFIC_VALUE: Final = 10000
UNSIGNED_MAX_32_BIT_VALUE: Final = 0xFFFFFFFF
MAX_HASH_VALUE: Final = math.pow(2, 32)
HASH_SEED: Final = 1
BUCKETING_ID_TEMPLATE: Final = '{bucketing_id}{parent_id}'
GROUP_POLICIES: Final = ['random']


class Bucketer:
    """ Optimizely bucketing algorithm that evenly distributes visitors. """

    def __init__(self) -> None:
        """ Bucketer init method to set bucketing seed and logger instance. """

        self.bucket_seed = HASH_SEED

    def _generate_unsigned_hash_code_32_bit(self, bucketing_id: str) -> int:
        """ Helper method to retrieve hash code.

        Args:
            bucketing_id: ID for bucketing.

        Returns:
            Hash code which is a 32 bit unsigned integer.
        """

        # Adjusting MurmurHash code to be unsigned
        return mmh3.hash(bucketing_id, self.bucket_seed) & UNSIGNED_MAX_32_BIT_VALUE

    def _generate_bucket_value(self, bucketing_id: str) -> int:
        """ Helper function to generate bucket value in half-closed interval [0, MAX_TRAFFIC_VALUE).

        Args:
            bucketing_id: ID for bucketing.

        Returns:
            Bucket value corresponding to the provided bucketing ID.
        """

        ratio = float(self._generate_unsigned_hash_code_32_bit(bucketing_id)) / MAX_HASH_VALUE
        return math.floor(ratio * MAX_TRAFFIC_VALUE)

    def find_bucket(
        self, project_config: ProjectConfig, bucketing_id: str,
        parent_id: Optional[str], traffic_allocations: list[TrafficAllocation]
    ) -> Optional[str]:
        """ Determine entity based on bucket value and traffic allocations.

        Args:
            project_config: Instance of ProjectConfig.
            bucketing_id: ID to be used for bucketing the user.
            parent_id: ID representing group or experiment.
            traffic_allocations: Traffic allocations representing traffic allotted to experiments or variations.

        Returns:
            Entity ID which may represent experiment or variation and
        """
        bucketing_key = BUCKETING_ID_TEMPLATE.format(bucketing_id=bucketing_id, parent_id=parent_id)
        bucketing_number = self._generate_bucket_value(bucketing_key)
        project_config.logger.debug(
            f'Assigned bucket {bucketing_number} to user with bucketing ID "{bucketing_id}".'
        )

        for traffic_allocation in traffic_allocations:
            current_end_of_range = traffic_allocation.get('endOfRange')
            if current_end_of_range is not None and bucketing_number < current_end_of_range:
                return traffic_allocation.get('entityId')

        return None

    def bucket(
        self, project_config: ProjectConfig,
        experiment: Experiment, user_id: str, bucketing_id: str
    ) -> tuple[Optional[Variation], list[str]]:
        """ For a given experiment and bucketing ID determines variation to be shown to user.

        Args:
            project_config: Instance of ProjectConfig.
            experiment: Object representing the experiment or rollout rule in which user is to be bucketed.
            user_id: ID for user.
            bucketing_id: ID to be used for bucketing the user.

        Returns:
            Variation in which user with ID user_id will be put in. None if no variation
            and array of log messages representing decision making.
     */.
        """
        # Check if experiment is None first
        if not experiment:
            message = 'Invalid entity key provided for bucketing. Returning nil.'
            project_config.logger.debug(message)
            return None, []

        if isinstance(experiment, dict):
            # This is a holdout dictionary
            experiment_key = experiment.get('key', '')
            experiment_id = experiment.get('id', '')
        else:
            # This is an Experiment object
            experiment_key = experiment.key
            experiment_id = experiment.id

        if not experiment_key or not experiment_key.strip():
            message = 'Invalid entity key provided for bucketing. Returning nil.'
            project_config.logger.debug(message)
            return None, []

        variation_id, decide_reasons = self.bucket_to_entity_id(project_config, experiment, user_id, bucketing_id)
        if variation_id:
            if isinstance(experiment, dict):
                # For holdouts, find the variation in the holdout's variations array
                variations = experiment.get('variations', [])
                variation = next((v for v in variations if v.get('id') == variation_id), None)
            else:
                # For experiments, use the existing method
                variation = project_config.get_variation_from_id_by_experiment_id(experiment_id, variation_id)
            return variation, decide_reasons

        # No variation found - log message for empty traffic range
        message = 'Bucketed into an empty traffic range. Returning nil.'
        project_config.logger.info(message)
        decide_reasons.append(message)
        return None, decide_reasons

    def bucket_to_entity_id(
        self, project_config: ProjectConfig,
        experiment: Experiment, user_id: str, bucketing_id: str
    ) -> tuple[Optional[str], list[str]]:
        """
        For a given experiment and bucketing ID determines variation ID to be shown to user.

        Args:
            project_config: Instance of ProjectConfig.
            experiment: The experiment object (used for group/groupPolicy logic if needed).
            user_id: The user ID string.
            bucketing_id: The bucketing ID string for the user.

        Returns:
            Tuple of (entity_id or None, list of decide reasons).
        """
        decide_reasons: list[str] = []
        if not experiment:
            return None, decide_reasons

        # Handle both Experiment objects and holdout dictionaries
        if isinstance(experiment, dict):
            # This is a holdout dictionary - holdouts don't have groups
            experiment_key = experiment.get('key', '')
            experiment_id = experiment.get('id', '')
            traffic_allocations = experiment.get('trafficAllocation', [])
            has_cmab = False
            group_policy = None
        else:
            # This is an Experiment object
            experiment_key = experiment.key
            experiment_id = experiment.id
            traffic_allocations = experiment.trafficAllocation
            has_cmab = bool(experiment.cmab)
            group_policy = getattr(experiment, 'groupPolicy', None)

        # Determine if experiment is in a mutually exclusive group.
        # This will not affect evaluation of rollout rules or holdouts.
        if group_policy and group_policy in GROUP_POLICIES:
            group = project_config.get_group(experiment.groupId)

            if not group:
                return None, decide_reasons

            user_experiment_id = self.find_bucket(
                project_config, bucketing_id, experiment.groupId, group.trafficAllocation,
            )

            if not user_experiment_id:
                message = f'User "{user_id}" is in no experiment.'
                project_config.logger.info(message)
                decide_reasons.append(message)
                return None, decide_reasons

            if user_experiment_id != experiment_id:
                message = f'User "{user_id}" is not in experiment "{experiment_key}" of group {experiment.groupId}.'
                project_config.logger.info(message)
                decide_reasons.append(message)
                return None, decide_reasons

            message = f'User "{user_id}" is in experiment {experiment_key} of group {experiment.groupId}.'
            project_config.logger.info(message)
            decide_reasons.append(message)

        if has_cmab:
            if experiment.cmab:
                traffic_allocations = [
                    {
                        "entityId": "$",
                        "endOfRange": experiment.cmab['trafficAllocation']
                    }
                ]

        # Bucket user if not in white-list and in group (if any)
        variation_id = self.find_bucket(project_config, bucketing_id,
                                        experiment_id, traffic_allocations)

        return variation_id, decide_reasons
