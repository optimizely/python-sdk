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
from typing import Any, Optional, Union
from sys import version_info
from . import logger as _logging
from . import decision_service
from .helpers import enums
if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final, TYPE_CHECKING  # type: ignore
    
    if TYPE_CHECKING:
        # prevent circular dependenacy by skipping import at runtime
        from .project_config import ProjectConfig
        from .logger import Logger
        from .entities import Experiment, Variation
        from .decision_service import Decision
        from optimizely.error_handler import BaseErrorHandler


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
        experiment_bucket_map: Optional[dict[str, Union[Decision, dict[str, str]]]] = None,
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
        experiment_data = self.experiment_bucket_map.get(experiment_id)

        if isinstance(experiment_data, decision_service.Decision):
            return experiment_data.variation.id if experiment_data.variation is not None else None
        elif isinstance(experiment_data, dict):
            return experiment_data.get(self.VARIATION_ID_KEY)

        return None

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
    def __init__(self, user_id: str, user_profile_service: Optional[UserProfileService], logger:Optional[_logging.Logger] = None):
        self.user_id = user_id
        self.user_profile_service = user_profile_service
        self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
        self.profile_updated = False
        self.user_profile = UserProfile(user_id, {})
    
    def get_user_profile(self) -> None:
        return self.user_profile

    def load_user_profile(self, reasons: Optional[list[str]]=[], error_handler: Optional[BaseErrorHandler]=None) -> None:
        reasons = reasons if reasons else []
        try:
            user_profile = self.user_profile_service.lookup(self.user_id) if self.user_profile_service else None
            if user_profile is None:
                message = "Unable to get a user profile from the UserProfileService."
                reasons.append(message)
                # self.logger.info(message)
            else:
                if 'user_id' in user_profile and 'experiment_bucket_map' in user_profile:
                    self.user_profile = UserProfile(
                        user_profile['user_id'], 
                        user_profile['experiment_bucket_map']
                    )
                    self.logger.info("User profile loaded successfully.")
                else:
                    missing_keys = [key for key in ['user_id', 'experiment_bucket_map'] if key not in user_profile]
                    message = f"User profile is missing keys: {', '.join(missing_keys)}"
                    reasons.append(message)
        except Exception as exception:
            message = str(exception)
            reasons.append(message)
            self.logger.exception(f'Unable to retrieve user profile for user "{self.user_id}"as lookup failed.')
            # Todo: add error handler
            # error_handler.handle_error()
        
        if self.user_profile is None:
            self.user_profile = UserProfile(self.user_id, {})
            
    def update_user_profile(self, experiment: Experiment, variation: Variation) -> None:
        if experiment.id in self.user_profile.experiment_bucket_map:
            decision = self.user_profile.experiment_bucket_map[experiment.id]
            if isinstance(decision, decision_service.Decision):
                decision = decision_service.Decision(
                    experiment=decision.experiment,
                    variation=variation,
                    source=decision.source
                )
        else:
            decision = decision_service.Decision(experiment=None, variation=variation, source=None)
         
        self.user_profile.experiment_bucket_map[experiment.id] = decision
        self.profile_updated = True
        # self.logger.info(f'Updated variation "{variation.id}" of experiment "{experiment.id}" for user "{self.user_profile.user_id}".')
        
        
    def save_user_profile(self, error_handler: Optional[BaseErrorHandler] = None) -> None:
        if not self.profile_updated:
            return
        try:
            if self.user_profile_service:
                self.user_profile_service.save(self.user_profile.__dict__)
                self.logger.info(f'Saved user profile of user "{self.user_profile.user_id}".')
        except Exception as exception:
            self.logger.warning(f'Failed to save user profile of user "{self.user_profile.user_id}".')
            # error_handler.handle_error(exception)
