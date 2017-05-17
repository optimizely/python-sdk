# Copyright 2017, Optimizely
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


class UserProfile(object):
  """ Class encapsulating information representing a user's profile.

   user_id: User's identifier.
   experiment_bucket_map: Dict mapping experiment ID to dict consisting of the
                          variation ID identifying the variation for the user.
   """

  def __init__(self, user_id, experiment_bucket_map=None, **kwargs):
    self.user_id = user_id
    self.experiment_bucket_map = experiment_bucket_map or {}


class UserProfileService(object):
  """ Class encapsulating user profile service functionality.
  Override with your own implementation for storing and retrieving the user profile. """

  def lookup(self, user_id):
    """ Fetch the user profile dict corresponding to the user ID.

    Args:
      user_id: ID for user whose profile needs to be retrieved.

    Returns:
      Dict representing the user's profile.
    """
    return dict(UserProfile(user_id))

  def save(self, user_profile):
    """ Save the user profile dict sent to this method.

    Args:
      user_profile: Dict representing the user's profile.
    """
    pass
