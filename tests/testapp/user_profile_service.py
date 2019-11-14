# Copyright 2016-2018, Optimizely
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


class BaseUserProfileService(object):
    def __init__(self, user_profiles):
        self.user_profiles = {profile['user_id']: profile for profile in user_profiles} if user_profiles else {}


class NormalService(BaseUserProfileService):
    def lookup(self, user_id):
        return self.user_profiles.get(user_id)

    def save(self, user_profile):
        user_id = user_profile['user_id']
        self.user_profiles[user_id] = user_profile


class LookupErrorService(NormalService):
    def lookup(self, user_id):
        raise IOError


class SaveErrorService(NormalService):
    def save(self, user_profile):
        raise IOError
