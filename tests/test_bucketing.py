# Copyright 2016-2017, Optimizely
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

import json
import mmh3
import mock
import random

from optimizely import bucketer
from optimizely import entities
from optimizely import logger
from optimizely import optimizely
from optimizely.helpers import enums
from optimizely.lib import pymmh3

from . import base


class BucketerTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.bucketer = bucketer.Bucketer(self.project_config)

  def test_bucket(self):
    """ Test that for provided bucket value correct variation ID is returned. """

    # Variation 1
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    return_value=42) as mock_generate_bucket_value:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.bucketer.bucket(
                         self.project_config.get_experiment_from_key('test_experiment'), 'test_user'
                       ))
    mock_generate_bucket_value.assert_called_once_with('test_user111127')

    # Empty entity ID
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    return_value=4242) as mock_generate_bucket_value:
      self.assertIsNone(self.bucketer.bucket(
        self.project_config.get_experiment_from_key('test_experiment'), 'test_user'
      ))
    mock_generate_bucket_value.assert_called_once_with('test_user111127')

    # Variation 2
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    return_value=5042) as mock_generate_bucket_value:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.bucketer.bucket(self.project_config.get_experiment_from_key('test_experiment'),
                                            'test_user'))
    mock_generate_bucket_value.assert_called_once_with('test_user111127')

    # No matching variation
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    return_value=424242) as mock_generate_bucket_value:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('test_experiment'),
                                             'test_user'))
    mock_generate_bucket_value.assert_called_once_with('test_user111127')

  def test_bucket__invalid_experiment(self):
    """ Test that bucket returns None for unknown experiment. """

    self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('invalid_experiment'),
                                           'test_user'))

  def test_get_forced_variation__user_in_forced_variation(self):
    """ Test that bucket returns variation ID for variation user is forced in. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value') as mock_generate_bucket_value:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('test_experiment'), 'user_1'))

    # Confirm that bucket value generation did not happen
    self.assertEqual(0, mock_generate_bucket_value.call_count)

  def test_get_forced_variation__user_in_forced_variation__invalid_variation_id(self):
    """ Test that bucket returns None when variation user is forced in is invalid. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value') as mock_generate_bucket_value, \
        mock.patch('optimizely.project_config.ProjectConfig.get_variation_from_key',
                   return_value=None) as mock_get_variation_id:
      self.assertIsNone(self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('test_experiment'),
                                             'user_1'))

    mock_get_variation_id.assert_called_once_with('test_experiment', 'control')
    # Confirm that bucket value generation did not happen
    self.assertEqual(0, mock_generate_bucket_value.call_count)

  def test_bucket__experiment_in_group(self):
    """ Test that for provided bucket values correct variation ID is returned. """

    # In group, matching experiment and variation
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 4242]) as mock_generate_bucket_value:
      self.assertEqual(entities.Variation('28902', 'group_exp_1_variation'),
                       self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_1'), 'test_user'))

    self.assertEqual([mock.call('test_user19228'), mock.call('test_user32222')],
                     mock_generate_bucket_value.call_args_list)

    # In group, no matching experiment
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 9500]) as mock_generate_bucket_value:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_1'),
                                             'test_user'))
    self.assertEqual([mock.call('test_user19228'), mock.call('test_user32222')],
                     mock_generate_bucket_value.call_args_list)

    # In group, experiment does not match
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 4242]) as mock_generate_bucket_value:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_2'),
                                             'test_user'))
    mock_generate_bucket_value.assert_called_once_with('test_user19228')

    # In group no matching variation
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 424242]) as mock_generate_bucket_value:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_1'),
                                             'test_user'))
    self.assertEqual([mock.call('test_user19228'), mock.call('test_user32222')],
                     mock_generate_bucket_value.call_args_list)

  def test_get_forced_variation__experiment_in_group__user_in_forced_variation(self):
    """ Test that bucket returns variation ID for variation user is forced in. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value') as mock_generate_bucket_value:
      self.assertEqual(entities.Variation('28905', 'group_exp_2_control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('group_exp_2'), 'user_1'))

    # Confirm that bucket value generation did not happen
    self.assertEqual(0, mock_generate_bucket_value.call_count)

  def test_bucket_number(self):
    """ Test output of _generate_bucket_value for different inputs. """

    def get_bucketing_id(user_id, parent_id=None):
      parent_id = parent_id or 1886780721
      return bucketer.BUCKETING_ID_TEMPLATE.format(user_id=user_id, parent_id=parent_id)

    self.assertEqual(5254, self.bucketer._generate_bucket_value(get_bucketing_id('ppid1')))
    self.assertEqual(4299, self.bucketer._generate_bucket_value(get_bucketing_id('ppid2')))
    self.assertEqual(2434, self.bucketer._generate_bucket_value(get_bucketing_id('ppid2', 1886780722)))
    self.assertEqual(5439, self.bucketer._generate_bucket_value(get_bucketing_id('ppid3')))
    self.assertEqual(6128, self.bucketer._generate_bucket_value(get_bucketing_id(
      'a very very very very very very very very very very very very very very very long ppd string')))

  def test_hash_values(self):
    """ Test that on randomized data, values computed from mmh3 and pymmh3 match. """

    for i in range(10):
      random_value = str(random.random())
      self.assertEqual(mmh3.hash(random_value), pymmh3.hash(random_value))


class BucketerWithLoggingTest(base.BaseTest):
  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            logger=logger.SimpleLogger())
    self.bucketer = bucketer.Bucketer(self.optimizely.config)

  def test_bucket(self):
    """ Test that expected log messages are logged during bucketing. """

    # Variation 1
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=42),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.bucketer.bucket(self.project_config.get_experiment_from_key('test_experiment'),
                                            'test_user'))

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 42 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(
      mock.call(enums.LogLevels.INFO, 'User "test_user" is in variation "control" of experiment test_experiment.'),
      mock_logging.call_args_list[1]
    )

    # Empty entity ID
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=4242), \
         mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(self.bucketer.bucket(
        self.project_config.get_experiment_from_key('test_experiment'), 'test_user'
      ))

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 4242 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(
      mock.call(enums.LogLevels.INFO, 'User "test_user" is in no variation.'),
      mock_logging.call_args_list[1]
    )

    # Variation 2
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=5042),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.bucketer.bucket(self.project_config.get_experiment_from_key('test_experiment'),
                                            'test_user'))
    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 5042 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(
      mock.call(enums.LogLevels.INFO, 'User "test_user" is in variation "variation" of experiment test_experiment.'),
      mock_logging.call_args_list[1]
    )

    # No matching variation
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=424242),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('test_experiment'),
                                             'test_user'))
    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 424242 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "test_user" is in no variation.'),
                     mock_logging.call_args_list[1])

  def test_get_forced_variation__user_in_forced_variation(self):
    """ Test that expected log messages are logged during forced bucketing. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value'),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('test_experiment'), 'user_1'))

    mock_logging.assert_called_with(enums.LogLevels.INFO, 'User "user_1" is forced in variation "control".')

  def test_bucket__experiment_in_group(self):
    """ Test that for provided bucket values correct variation ID is returned. """

    # In group, matching experiment and variation
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 4242]),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('28902', 'group_exp_1_variation'),
                       self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_1'), 'test_user'))
    self.assertEqual(4, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 42 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "test_user" is in experiment group_exp_1 of group 19228.'),
                     mock_logging.call_args_list[1])
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 4242 to user "test_user".'),
                     mock_logging.call_args_list[2])
    self.assertEqual(
      mock.call(enums.LogLevels.INFO,
                'User "test_user" is in variation "group_exp_1_variation" of experiment group_exp_1.'),
      mock_logging.call_args_list[3]
    )

    # In group, but in no experiment
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[8400, 9500]),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_1'), 'test_user'))
    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 8400 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "test_user" is in no experiment.'),
                     mock_logging.call_args_list[1])

    # In group, no matching experiment
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 9500]),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_1'), 'test_user'))
    self.assertEqual(4, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 42 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "test_user" is in experiment group_exp_1 of group 19228.'),
                     mock_logging.call_args_list[1])
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 9500 to user "test_user".'),
                     mock_logging.call_args_list[2])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "test_user" is in no variation.'),
                     mock_logging.call_args_list[3])

    # In group, experiment does not match
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 4242]),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_2'), 'test_user'))
    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 42 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(
      mock.call(enums.LogLevels.INFO, 'User "test_user" is not in experiment "group_exp_2" of group 19228.'),
      mock_logging.call_args_list[1]
    )

    # In group no matching variation
    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value',
                    side_effect=[42, 424242]),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(self.bucketer.bucket(self.project_config.get_experiment_from_key('group_exp_1'), 'test_user'))
    self.assertEqual(4, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 42 to user "test_user".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "test_user" is in experiment group_exp_1 of group 19228.'),
                     mock_logging.call_args_list[1])
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'Assigned bucket 424242 to user "test_user".'),
                     mock_logging.call_args_list[2])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "test_user" is in no variation.'),
                     mock_logging.call_args_list[3])

  def test_get_forced_variation__experiment_in_group__user_in_forced_variation(self):
    """ Test that expected log messages are logged during forced bucketing. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value'),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('28905', 'group_exp_2_control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('group_exp_2'), 'user_1'))

    # Confirm that bucket value generation did not happen
    mock_logging.assert_called_with(enums.LogLevels.INFO, 'User "user_1" is forced in variation "group_exp_2_control".')
