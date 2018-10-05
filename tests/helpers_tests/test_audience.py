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

import mock

from tests import base
from optimizely.helpers import audience


class AudienceTest(base.BaseTest):

  def test_is_match__audience_condition_matches(self):
    """ Test that is_user_in_experiment returns True when audience conditions are met. """

    user_attributes = {
      'test_attribute': 'test_value_1',
      'browser_type': 'firefox',
      'location': 'San Francisco'
    }

    self.assertTrue(
      audience.is_user_in_experiment(
        self.project_config, self.project_config.get_experiment_from_key('test_experiment'), user_attributes))

  def test_is_user_in_experiment__audience_condition_does_not_match(self):
    """ Test that is_user_in_experiment returns False when audience conditions are not met. """

    user_attributes = {
      'test_attribute': 'wrong_test_value',
      'browser_type': 'chrome',
      'location': 'San Francisco'
    }

    self.assertFalse(
      audience.is_user_in_experiment(
        self.project_config, self.project_config.get_experiment_from_key('test_experiment'), user_attributes))

  def test_is_user_in_experiment__no_audience(self):
    """ Test that is_user_in_experiment returns True when experiment is using no audience. """

    user_attributes = {
      'test_attribute': 'test_value_1',
      'browser_type': 'firefox',
      'location': 'San Francisco'
    }
    experiment = self.project_config.get_experiment_from_key('test_experiment')
    experiment.audienceIds = []
    self.assertTrue(audience.is_user_in_experiment(self.project_config, experiment, user_attributes))

  def test_is_user_in_experiment__no_attributes(self):
    """ Test that is_user_in_experiment returns False when attributes are empty
    and experiment has an audience. """

    self.assertFalse(audience.is_user_in_experiment(
      self.project_config, self.project_config.get_experiment_from_key('test_experiment'), None)
    )

    self.assertFalse(audience.is_user_in_experiment(
      self.project_config, self.project_config.get_experiment_from_key('test_experiment'), {})
    )

  def test_is_user_in_experiment__audience_conditions_are_met(self):
    """ Test that is_user_in_experiment returns True when Condition Evaluator returns True."""

    user_attributes = {
      'test_attribute': 'test_value_1',
      'browser_type': 'firefox',
      'location': 'San Francisco'
    }

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate', return_value=True) as mock_evaluate:
      self.assertTrue(audience.is_user_in_experiment(self.project_config,
                                                     self.project_config.get_experiment_from_key('test_experiment'),
                                                     user_attributes))
    mock_evaluate.assert_called_once_with(self.optimizely.config.get_audience('11154').conditionList)

  def test_is_user_in_experiment__audience_conditions_not_met(self):
    """ Test that is_user_in_experiment returns False when Condition Evaluator returns False. """

    user_attributes = {
      'test_attribute': 'wrong_test_value',
      'browser_type': 'chrome',
      'location': 'San Francisco'
    }

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate', return_value=False) as mock_evaluate:
      self.assertFalse(audience.is_user_in_experiment(self.project_config,
                                                      self.project_config.get_experiment_from_key('test_experiment'),
                                                      user_attributes))
    mock_evaluate.assert_called_once_with(self.optimizely.config.get_audience('11154').conditionList)
