# Copyright 2019, Optimizely
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

from . import base
from optimizely import logger
from optimizely.event.event_factory import EventFactory
from optimizely.event.user_event_factory import UserEventFactory


class UserEventFactoryTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self, 'config_dict_with_multiple_experiments')
        self.logger = logger.NoOpLogger()

    def test_impression_event(self):
        project_config = self.project_config
        experiment = self.project_config.get_experiment_from_key('test_experiment')
        variation = self.project_config.get_variation_from_id(experiment.key, '111128')
        user_id = 'test_user'

        impression_event = UserEventFactory.create_impression_event(project_config, experiment, '111128', 'flag_key',
                                                                    'rule_key', 'rule_type', user_id, None)

        self.assertEqual(self.project_config.project_id, impression_event.event_context.project_id)
        self.assertEqual(self.project_config.revision, impression_event.event_context.revision)
        self.assertEqual(self.project_config.account_id, impression_event.event_context.account_id)
        self.assertEqual(
            self.project_config.anonymize_ip, impression_event.event_context.anonymize_ip,
        )
        self.assertEqual(self.project_config.bot_filtering, impression_event.bot_filtering)
        self.assertEqual(experiment, impression_event.experiment)
        self.assertEqual(variation, impression_event.variation)
        self.assertEqual(user_id, impression_event.user_id)

    def test_impression_event__with_attributes(self):
        project_config = self.project_config
        experiment = self.project_config.get_experiment_from_key('test_experiment')
        variation = self.project_config.get_variation_from_id(experiment.key, '111128')
        user_id = 'test_user'

        user_attributes = {'test_attribute': 'test_value', 'boolean_key': True}

        impression_event = UserEventFactory.create_impression_event(
            project_config, experiment, '111128', 'flag_key', 'rule_key', 'rule_type', user_id, user_attributes
        )

        expected_attrs = EventFactory.build_attribute_list(user_attributes, project_config)

        self.assertEqual(self.project_config.project_id, impression_event.event_context.project_id)
        self.assertEqual(self.project_config.revision, impression_event.event_context.revision)
        self.assertEqual(self.project_config.account_id, impression_event.event_context.account_id)
        self.assertEqual(
            self.project_config.anonymize_ip, impression_event.event_context.anonymize_ip,
        )
        self.assertEqual(self.project_config.bot_filtering, impression_event.bot_filtering)
        self.assertEqual(experiment, impression_event.experiment)
        self.assertEqual(variation, impression_event.variation)
        self.assertEqual(user_id, impression_event.user_id)
        self.assertEqual(
            [x.__dict__ for x in expected_attrs], [x.__dict__ for x in impression_event.visitor_attributes],
        )

    def test_conversion_event(self):
        project_config = self.project_config
        user_id = 'test_user'
        event_key = 'test_event'
        user_attributes = {'test_attribute': 'test_value', 'boolean_key': True}

        conversion_event = UserEventFactory.create_conversion_event(
            project_config, event_key, user_id, user_attributes, None
        )

        expected_attrs = EventFactory.build_attribute_list(user_attributes, project_config)

        self.assertEqual(self.project_config.project_id, conversion_event.event_context.project_id)
        self.assertEqual(self.project_config.revision, conversion_event.event_context.revision)
        self.assertEqual(self.project_config.account_id, conversion_event.event_context.account_id)
        self.assertEqual(
            self.project_config.anonymize_ip, conversion_event.event_context.anonymize_ip,
        )
        self.assertEqual(self.project_config.bot_filtering, conversion_event.bot_filtering)
        self.assertEqual(self.project_config.get_event(event_key), conversion_event.event)
        self.assertEqual(user_id, conversion_event.user_id)
        self.assertEqual(
            [x.__dict__ for x in expected_attrs], [x.__dict__ for x in conversion_event.visitor_attributes],
        )

    def test_conversion_event__with_event_tags(self):
        project_config = self.project_config
        user_id = 'test_user'
        event_key = 'test_event'
        user_attributes = {'test_attribute': 'test_value', 'boolean_key': True}
        event_tags = {"revenue": 4200, "value": 1.234, "non_revenue": "abc"}

        conversion_event = UserEventFactory.create_conversion_event(
            project_config, event_key, user_id, user_attributes, event_tags
        )

        expected_attrs = EventFactory.build_attribute_list(user_attributes, project_config)

        self.assertEqual(self.project_config.project_id, conversion_event.event_context.project_id)
        self.assertEqual(self.project_config.revision, conversion_event.event_context.revision)
        self.assertEqual(self.project_config.account_id, conversion_event.event_context.account_id)
        self.assertEqual(
            self.project_config.anonymize_ip, conversion_event.event_context.anonymize_ip,
        )
        self.assertEqual(self.project_config.bot_filtering, conversion_event.bot_filtering)
        self.assertEqual(self.project_config.get_event(event_key), conversion_event.event)
        self.assertEqual(user_id, conversion_event.user_id)
        self.assertEqual(
            [x.__dict__ for x in expected_attrs], [x.__dict__ for x in conversion_event.visitor_attributes],
        )
        self.assertEqual(event_tags, conversion_event.event_tags)
