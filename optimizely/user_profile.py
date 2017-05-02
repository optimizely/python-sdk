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
  """ Class encapsulating information representing a user's profile. """

  def __init__(self, user_id, decisions=None, **kwargs):
    self.user_id = user_id
    self.decisions = decisions or {}

  def __dict__(self):
    return {
      'user_id': self.user_id,
      'decisions': self.decisions
    }


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
    return UserProfile(user_id).__dict__()

  def save(self, user_profile):
    """ Save the user profile dict sent to this method.

    Args:
      user_profile: Dict representing the user's profile.
    """
    pass
