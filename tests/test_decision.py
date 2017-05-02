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

import json
import mock

from optimizely import decision
from . import base


class DecisionServiceTest(base.BaseTest):
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

  def test_get_forced_variation__experiment_in_group__user_in_forced_variation(self):
    """ Test that bucket returns variation ID for variation user is forced in. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value') as mock_generate_bucket_value:
      self.assertEqual(entities.Variation('28905', 'group_exp_2_control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('group_exp_2'), 'user_1'))

    # Confirm that bucket value generation did not happen
    self.assertEqual(0, mock_generate_bucket_value.call_count)

  def test_get_forced_variation__experiment_in_group__user_in_forced_variation(self):
    """ Test that bucket returns variation ID for variation user is forced in. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value') as mock_generate_bucket_value:
      self.assertEqual(entities.Variation('28905', 'group_exp_2_control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('group_exp_2'), 'user_1'))

    # Confirm that bucket value generation did not happen
    self.assertEqual(0, mock_generate_bucket_value.call_count)

  def test_get_forced_variation__experiment_in_group__user_in_forced_variation(self):
    """ Test that expected log messages are logged during forced bucketing. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value'),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('28905', 'group_exp_2_control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('group_exp_2'), 'user_1'))

    # Confirm that bucket value generation did not happen
    mock_logging.assert_called_with(enums.LogLevels.INFO, 'User "user_1" is forced in variation "group_exp_2_control".')

  def test_get_forced_variation__user_in_forced_variation(self):
    """ Test that expected log messages are logged during forced bucketing. """

    with mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value'),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.bucketer.get_forced_variation(self.project_config.get_experiment_from_key('test_experiment'), 'user_1'))

    mock_logging.assert_called_with(enums.LogLevels.INFO, 'User "user_1" is forced in variation "control".')


