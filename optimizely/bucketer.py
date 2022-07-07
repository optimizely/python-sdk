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
    from typing import Final  # type: ignore


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
        decide_reasons: list[str] = []
        if not experiment:
            return None, decide_reasons

        # Determine if experiment is in a mutually exclusive group.
        # This will not affect evaluation of rollout rules.
        if experiment.groupPolicy in GROUP_POLICIES:
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

            if user_experiment_id != experiment.id:
                message = f'User "{user_id}" is not in experiment "{experiment.key}" of group {experiment.groupId}.'
                project_config.logger.info(message)
                decide_reasons.append(message)
                return None, decide_reasons

            message = f'User "{user_id}" is in experiment {experiment.key} of group {experiment.groupId}.'
            project_config.logger.info(message)
            decide_reasons.append(message)

        # Bucket user if not in white-list and in group (if any)
        variation_id = self.find_bucket(project_config, bucketing_id,
                                        experiment.id, experiment.trafficAllocation)
        if variation_id:
            variation = project_config.get_variation_from_id_by_experiment_id(experiment.id, variation_id)
            return variation, decide_reasons

        else:
            message = 'Bucketed into an empty traffic range. Returning nil.'
            project_config.logger.info(message)
            decide_reasons.append(message)

        return None, decide_reasons
