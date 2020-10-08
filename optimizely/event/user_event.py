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

from optimizely import version

CLIENT_NAME = 'python-sdk'


class UserEvent(object):
    """ Class respresenting User Event. """

    def __init__(self, event_context, user_id, visitor_attributes, bot_filtering=None):
        self.event_context = event_context
        self.user_id = user_id
        self.visitor_attributes = visitor_attributes
        self.bot_filtering = bot_filtering
        self.uuid = self._get_uuid()
        self.timestamp = self._get_time()

    def _get_time(self):
        return int(round(time.time() * 1000))

    def _get_uuid(self):
        return str(uuid.uuid4())


class ImpressionEvent(UserEvent):
    """ Class representing Impression Event. """

    def __init__(
        self, event_context, user_id, experiment, visitor_attributes, variation, flag_key, rule_key, rule_type,
        bot_filtering=None,
    ):
        super(ImpressionEvent, self).__init__(event_context, user_id, visitor_attributes, bot_filtering)
        self.experiment = experiment
        self.variation = variation
        self.flag_key = flag_key
        self.rule_key = rule_key
        self.rule_type = rule_type


class ConversionEvent(UserEvent):
    """ Class representing Conversion Event. """

    def __init__(
        self, event_context, event, user_id, visitor_attributes, event_tags, bot_filtering=None,
    ):
        super(ConversionEvent, self).__init__(event_context, user_id, visitor_attributes, bot_filtering)
        self.event = event
        self.event_tags = event_tags


class EventContext(object):
    """ Class respresenting User Event Context. """

    def __init__(self, account_id, project_id, revision, anonymize_ip):
        self.account_id = account_id
        self.project_id = project_id
        self.revision = revision
        self.client_name = CLIENT_NAME
        self.client_version = version.__version__
        self.anonymize_ip = anonymize_ip
