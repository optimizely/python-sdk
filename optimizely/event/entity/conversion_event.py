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
from .user_event import UserEvent


class ConversionEvent(UserEvent):
  """ Class representing Conversion Event. """

  def __init__(self, event_context, event, user_id, visitor_attributes, event_tags, bot_filtering=None):
    self.event_context = event_context
    self.event = event
    self.user_id = user_id
    self.visitor_attributes = visitor_attributes
    self.event_tags = event_tags
    self.bot_filtering = bot_filtering
