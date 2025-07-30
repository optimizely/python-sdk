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

        impression_event = UserEventFactory.create_impression_event(project_config, experiment, '111128', '',
                                                                    'rule_key', 'rule_type', True, user_id, None, None)

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
        self.assertEqual(self.project_config.region, impression_event.event_context.region)

    def test_impression_event_with_region_eu(self):
        project_config = self.project_config
        experiment = self.project_config.get_experiment_from_key('test_experiment')
        user_id = 'test_user'

        project_config.region = 'EU'

        impression_event = UserEventFactory.create_impression_event(
            project_config, experiment, '111128', '', 'rule_key', 'rule_type', True, user_id, None, None
        )

        self.assertEqual(self.project_config.region, impression_event.event_context.region)
        self.assertEqual('EU', impression_event.event_context.region)

    def test_impression_event__with_attributes(self):
        project_config = self.project_config
        experiment = self.project_config.get_experiment_from_key('test_experiment')
        variation = self.project_config.get_variation_from_id(experiment.key, '111128')
        user_id = 'test_user'

        user_attributes = {'test_attribute': 'test_value', 'boolean_key': True}

        impression_event = UserEventFactory.create_impression_event(
            project_config, experiment, '111128', '', 'rule_key', 'rule_type', True, user_id, user_attributes, None
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
        self.assertEqual(self.project_config.region, impression_event.event_context.region)
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
        self.assertEqual(self.project_config.region, conversion_event.event_context.region)
        self.assertEqual(
            [x.__dict__ for x in expected_attrs], [x.__dict__ for x in conversion_event.visitor_attributes],
        )

    def test_conversion_event_eu(self):
        project_config = self.project_config
        user_id = 'test_user'
        event_key = 'test_event'
        user_attributes = {'test_attribute': 'test_value', 'boolean_key': True}

        project_config.region = 'EU'

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
        self.assertEqual('EU', conversion_event.event_context.region)
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
        self.assertEqual(self.project_config.region, conversion_event.event_context.region)
        self.assertEqual(
            [x.__dict__ for x in expected_attrs], [x.__dict__ for x in conversion_event.visitor_attributes],
        )
        self.assertEqual(event_tags, conversion_event.event_tags)

    def test_create_impression_user_event_with_cmab_uuid(self):
        project_config = self.project_config
        experiment = self.project_config.get_experiment_from_key('test_experiment')
        variation = self.project_config.get_variation_from_id(experiment.key, '111128')
        user_id = 'test_user'
        cmab_uuid = '123e4567-e89b-12d3-a456-426614174000'

        impression_event = UserEventFactory.create_impression_event(
            project_config, experiment, '111128', '', 'rule_key', 'rule_type', True, user_id, None, cmab_uuid
        )

        # Verify basic impression event properties
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

        # Verify CMAB UUID is properly set
        self.assertEqual(cmab_uuid, impression_event.cmab_uuid)

        # Test that the CMAB UUID is included in the event payload when creating a log event
        from optimizely.event.event_factory import EventFactory
        log_event = EventFactory.create_log_event(impression_event, self.logger)

        self.assertIsNotNone(log_event)
        event_params = log_event.params

        # Verify the event structure contains the CMAB UUID in metadata
        self.assertIn('visitors', event_params)
        self.assertEqual(len(event_params['visitors']), 1)

        visitor = event_params['visitors'][0]
        self.assertIn('snapshots', visitor)
        self.assertEqual(len(visitor['snapshots']), 1)

        snapshot = visitor['snapshots'][0]
        self.assertIn('decisions', snapshot)
        self.assertEqual(len(snapshot['decisions']), 1)

        decision = snapshot['decisions'][0]
        self.assertIn('metadata', decision)

        metadata = decision['metadata']
        self.assertIn('cmab_uuid', metadata)
        self.assertEqual(cmab_uuid, metadata['cmab_uuid'])

        # Verify other metadata fields are present
        self.assertEqual('rule_key', metadata['rule_key'])
        self.assertEqual('rule_type', metadata['rule_type'])
        self.assertEqual(True, metadata['enabled'])
        self.assertEqual(variation.key, metadata['variation_key'])

    def test_create_impression_user_event_without_cmab_uuid(self):
        project_config = self.project_config
        experiment = self.project_config.get_experiment_from_key('test_experiment')
        variation = self.project_config.get_variation_from_id(experiment.key, '111128')
        user_id = 'test_user'

        impression_event = UserEventFactory.create_impression_event(
            project_config, experiment, '111128', '', 'rule_key', 'rule_type', True, user_id, None, None
        )

        # Verify basic impression event properties
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

        # Verify CMAB UUID is None when not provided
        self.assertIsNone(impression_event.cmab_uuid)

        # Test that the CMAB UUID is not included in the event payload when creating a log event
        from optimizely.event.event_factory import EventFactory
        log_event = EventFactory.create_log_event(impression_event, self.logger)

        self.assertIsNotNone(log_event)
        event_params = log_event.params

        # Verify the event structure does not contain CMAB UUID in metadata
        self.assertIn('visitors', event_params)
        self.assertEqual(len(event_params['visitors']), 1)

        visitor = event_params['visitors'][0]
        self.assertIn('snapshots', visitor)
        self.assertEqual(len(visitor['snapshots']), 1)

        snapshot = visitor['snapshots'][0]
        self.assertIn('decisions', snapshot)
        self.assertEqual(len(snapshot['decisions']), 1)

        decision = snapshot['decisions'][0]
        self.assertIn('metadata', decision)

        metadata = decision['metadata']

        # Verify CMAB UUID is not present in metadata when not provided
        self.assertNotIn('cmab_uuid', metadata)

        # Verify other metadata fields are still present
        self.assertEqual('rule_key', metadata['rule_key'])
        self.assertEqual('rule_type', metadata['rule_type'])
        self.assertEqual(True, metadata['enabled'])
        self.assertEqual(variation.key, metadata['variation_key'])
