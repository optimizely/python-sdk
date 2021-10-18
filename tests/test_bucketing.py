# Copyright 2016-2021, Optimizely
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

import json
import mock
import random

from optimizely import bucketer
from optimizely import entities
from optimizely import logger
from optimizely import optimizely
from optimizely.lib import pymmh3 as mmh3

from . import base


class BucketerTest(base.BaseTest):
    def setUp(self, *args, **kwargs):
        base.BaseTest.setUp(self)
        self.bucketer = bucketer.Bucketer()

    def test_bucket(self):
        """ Test that for provided bucket value correct variation ID is returned. """

        # Variation 1
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=42
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertEqual(
                entities.Variation('111128', 'control'),
                variation,
            )
        mock_generate_bucket_value.assert_called_once_with('test_user111127')

        # Empty entity ID
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=4242
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        mock_generate_bucket_value.assert_called_once_with('test_user111127')

        # Variation 2
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=5042
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertEqual(
                entities.Variation('111129', 'variation'),
                variation,
            )
        mock_generate_bucket_value.assert_called_once_with('test_user111127')

        # No matching variation
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=424242
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        mock_generate_bucket_value.assert_called_once_with('test_user111127')

    def test_bucket__invalid_experiment(self):
        """ Test that bucket returns None for unknown experiment. """
        variation, _ = self.bucketer.bucket(
            self.project_config,
            self.project_config.get_experiment_from_key('invalid_experiment'),
            'test_user',
            'test_user',
        )
        self.assertIsNone(
            variation
        )

    def test_bucket__invalid_group(self):
        """ Test that bucket returns None for unknown group. """

        project_config = self.project_config
        experiment = project_config.get_experiment_from_key('group_exp_1')
        # Set invalid group ID for the experiment
        experiment.groupId = 'invalid_group_id'
        variation, _ = self.bucketer.bucket(self.project_config, experiment, 'test_user', 'test_user')
        self.assertIsNone(variation)

    def test_bucket__experiment_in_group(self):
        """ Test that for provided bucket values correct variation ID is returned. """

        # In group, matching experiment and variation
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 4242],
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_1'),
                'test_user',
                'test_user',
            )
            self.assertEqual(
                entities.Variation('28902', 'group_exp_1_variation'),
                variation,
            )

        self.assertEqual(
            [mock.call('test_user19228'), mock.call('test_user32222')], mock_generate_bucket_value.call_args_list,
        )

        # In group, no matching experiment
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 9500],
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_1'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        self.assertEqual(
            [mock.call('test_user19228'), mock.call('test_user32222')], mock_generate_bucket_value.call_args_list,
        )

        # In group, experiment does not match
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 4242],
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_2'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        mock_generate_bucket_value.assert_called_once_with('test_user19228')

        # In group no matching variation
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 424242],
        ) as mock_generate_bucket_value:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_1'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        self.assertEqual(
            [mock.call('test_user19228'), mock.call('test_user32222')], mock_generate_bucket_value.call_args_list,
        )

    def test_bucket_number(self):
        """ Test output of _generate_bucket_value for different inputs. """

        def get_bucketing_id(bucketing_id, parent_id=None):
            parent_id = parent_id or 1886780721
            return bucketer.BUCKETING_ID_TEMPLATE.format(bucketing_id=bucketing_id, parent_id=parent_id)

        self.assertEqual(5254, self.bucketer._generate_bucket_value(get_bucketing_id('ppid1')))
        self.assertEqual(4299, self.bucketer._generate_bucket_value(get_bucketing_id('ppid2')))
        self.assertEqual(
            2434, self.bucketer._generate_bucket_value(get_bucketing_id('ppid2', 1886780722)),
        )
        self.assertEqual(5439, self.bucketer._generate_bucket_value(get_bucketing_id('ppid3')))
        self.assertEqual(
            6128,
            self.bucketer._generate_bucket_value(
                get_bucketing_id(
                    'a very very very very very very very very very very very very very very very long ppd string'
                )
            ),
        )

    def test_hash_values(self):
        """ Test that on randomized data, values computed from mmh3 and pymmh3 match. """

        for i in range(10):
            random_value = str(random.random())
            self.assertEqual(mmh3.hash(random_value), pymmh3.hash(random_value))


class BucketerWithLoggingTest(base.BaseTest):
    def setUp(self, *args, **kwargs):
        base.BaseTest.setUp(self)
        self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict), logger=logger.SimpleLogger())
        self.bucketer = bucketer.Bucketer()

    def test_bucket(self):
        """ Test that expected log messages are logged during bucketing. """

        # Variation 1
        with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=42), mock.patch.object(
            self.project_config, 'logger'
        ) as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertEqual(
                entities.Variation('111128', 'control'),
                variation,
            )

        mock_config_logging.debug.assert_called_once_with('Assigned bucket 42 to user with bucketing ID "test_user".')

        # Empty entity ID
        with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=4242), mock.patch.object(
            self.project_config, 'logger'
        ) as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )

        mock_config_logging.debug.assert_called_once_with('Assigned bucket 4242 to user with bucketing ID "test_user".')

        # Variation 2
        with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=5042), mock.patch.object(
            self.project_config, 'logger'
        ) as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertEqual(
                entities.Variation('111129', 'variation'),
                variation,
            )

        mock_config_logging.debug.assert_called_once_with('Assigned bucket 5042 to user with bucketing ID "test_user".')

        # No matching variation
        with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=424242), mock.patch.object(
            self.project_config, 'logger'
        ) as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )

        mock_config_logging.debug.assert_called_once_with(
            'Assigned bucket 424242 to user with bucketing ID "test_user".'
        )

    def test_bucket__experiment_in_group(self):
        """ Test that for provided bucket values correct variation ID is returned. """

        # In group, matching experiment and variation
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 4242],
        ), mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_1'),
                'test_user',
                'test_user',
            )
            self.assertEqual(
                entities.Variation('28902', 'group_exp_1_variation'),
                variation,
            )
        mock_config_logging.debug.assert_has_calls(
            [
                mock.call('Assigned bucket 42 to user with bucketing ID "test_user".'),
                mock.call('Assigned bucket 4242 to user with bucketing ID "test_user".'),
            ]
        )
        mock_config_logging.info.assert_has_calls(
            [
                mock.call('User "test_user" is in experiment group_exp_1 of group 19228.'),
            ]
        )

        # In group, but in no experiment
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[8400, 9500],
        ), mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_1'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        mock_config_logging.debug.assert_called_once_with('Assigned bucket 8400 to user with bucketing ID "test_user".')
        mock_config_logging.info.assert_called_once_with('User "test_user" is in no experiment.')

        # In group, no matching experiment
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 9500],
        ), mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_1'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        mock_config_logging.debug.assert_has_calls(
            [
                mock.call('Assigned bucket 42 to user with bucketing ID "test_user".'),
                mock.call('Assigned bucket 9500 to user with bucketing ID "test_user".'),
            ]
        )
        mock_config_logging.info.assert_has_calls(
            [
                mock.call('User "test_user" is in experiment group_exp_1 of group 19228.'),
            ]
        )

        # In group, experiment does not match
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 4242],
        ), mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_2'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )
        mock_config_logging.debug.assert_called_once_with('Assigned bucket 42 to user with bucketing ID "test_user".')
        mock_config_logging.info.assert_called_once_with(
            'User "test_user" is not in experiment "group_exp_2" of group 19228.'
        )

        # In group no matching variation
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', side_effect=[42, 424242],
        ), mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation, _ = self.bucketer.bucket(
                self.project_config,
                self.project_config.get_experiment_from_key('group_exp_1'),
                'test_user',
                'test_user',
            )
            self.assertIsNone(
                variation
            )

        mock_config_logging.debug.assert_has_calls(
            [
                mock.call('Assigned bucket 42 to user with bucketing ID "test_user".'),
                mock.call('Assigned bucket 424242 to user with bucketing ID "test_user".'),
            ]
        )
        mock_config_logging.info.assert_has_calls(
            [
                mock.call('User "test_user" is in experiment group_exp_1 of group 19228.'),
            ]
        )
