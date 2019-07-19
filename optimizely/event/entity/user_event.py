# Copyright 2019 Optimizely
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
import time
import uuid


class UserEvent(object):
  """ Class respresenting Event Context. """

  def __init__(self, event_context):
    self.event_context = event_context
    self.uuid = self._get_uuid()
    self.timestamp = self._get_time()

  def _get_time(self):
    return int(round(time.time() * 1000))

  def _get_uuid(self):
    return str(uuid.uuid4())
