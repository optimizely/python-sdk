# Copyright 2017, 2022, Optimizely
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
from typing import Any, Optional
from sys import version_info
from .helpers.validator import is_user_profile_valid
from .entities import Experiment, Variation
from .decision_service import Decision
from optimizely.error_handler import BaseErrorHandler

if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final  # type: ignore


class UserProfile:
    """ Class encapsulating information representing a user's profile.

   user_id: User's identifier.
   experiment_bucket_map: Dict mapping experiment ID to dict consisting of the
                          variation ID identifying the variation for the user.
   """

    USER_ID_KEY: Final = 'user_id'
    EXPERIMENT_BUCKET_MAP_KEY: Final = 'experiment_bucket_map'
    VARIATION_ID_KEY: Final = 'variation_id'

    def __init__(
        self,
        user_id: str,
        experiment_bucket_map: Optional[dict[str, dict[str, Optional[str]]]] = None,
        **kwargs: Any
    ):
        self.user_id = user_id
        self.experiment_bucket_map = experiment_bucket_map or {}

    def __eq__(self, other: object) -> bool:
        return self.__dict__ == other.__dict__

    def get_variation_for_experiment(self, experiment_id: str) -> Optional[str]:
        """ Helper method to retrieve variation ID for given experiment.

    Args:
      experiment_id: ID for experiment for which variation needs to be looked up for.

    Returns:
      Variation ID corresponding to the experiment. None if no decision available.
    """

        return self.experiment_bucket_map.get(experiment_id, {self.VARIATION_ID_KEY: None}).get(self.VARIATION_ID_KEY)

    def save_variation_for_experiment(self, experiment_id: str, variation_id: str) -> None:
        """ Helper method to save new experiment/variation as part of the user's profile.

    Args:
      experiment_id: ID for experiment for which the decision is to be stored.
      variation_id: ID for variation that the user saw.
    """

        self.experiment_bucket_map.update({experiment_id: {self.VARIATION_ID_KEY: variation_id}})


class UserProfileService:
    """ Class encapsulating user profile service functionality.
  Override with your own implementation for storing and retrieving the user profile. """

    def lookup(self, user_id: str) -> dict[str, Any]:
        """ Fetch the user profile dict corresponding to the user ID.

    Args:
      user_id: ID for user whose profile needs to be retrieved.

    Returns:
      Dict representing the user's profile.
    """
        return UserProfile(user_id).__dict__

    def save(self, user_profile: dict[str, Any]) -> None:
        """ Save the user profile dict sent to this method.

    Args:
      user_profile: Dict representing the user's profile.
    """
        pass

class UserProfileTracker:
    def __init__(self, user_id: str, user_profile_service: UserProfileService, logger=None):
        self.user_id = user_id
        self.user_profile_service = user_profile_service
        self.logger = logger
        self.profile_updated = False
        self.user_profile = None
    
    def get_user_profile(self):
        return self.user_profile

    def load_user_profile(self, reasons: Optional[list[str]], error_handler: Optional[BaseErrorHandler]):
        try:
            user_profile = self.user_profile_service.lookup(self.user_id)
            if user_profile is None:
                message = reasons.append("Unable to get a user profile from the UserProfileService.")
                self.logger.info(message)
            elif is_user_profile_valid(user_profile):
                self.user_profile = user_profile
            else:
                message = reasons.append("The UserProfileService returned an invalid user_profile.")
                self.logger.warning(message)
        except Exception as exception:
            message = reasons.append(str(exception))
            self.logger.error(message)
            # Todo: add error handler
            # error_handler.handle_error()
        
        if self.user_profile is None:
            self.user_profile = UserProfile(self.user_id, {})
            
    def update_user_profile(self, experiment: Experiment, variation: Variation):
        decision:Decision = None
        if experiment.id in self.user_profile.experiment_bucket_map:
            decision = self.user_profile.experiment_bucket_map[experiment.id]
            decision.variation = variation
        else:
            decision = Decision(experiment=None, variation=variation, source=None)
         
        self.user_profile.experiment_bucket_map[experiment.id] = decision
        self.profile_updated = True
        # self.logger.info(f'Updated variation "{variation.id}" of experiment "{experiment.id}" for user "{self.user_profile.user_id}".')
        
        
    def save_user_profile(self, error_handler: Optional[BaseErrorHandler]):
        if not self.profile_updated:
            return

        try:
            self.user_profile_service.save(self.user_profile)
            self.logger.info(f'Saved user profile of user "{self.user_profile.user_id}".')
        except Exception as exception:
            self.logger.warning(f'Failed to save user profile of user "{self.user_profile.user_id}".')
            # error_handler.handle_error(exception)
