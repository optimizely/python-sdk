# Copyright 2016, Optimizely
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

import mock

from tests import base
from optimizely import entities
from optimizely.helpers import experiment


class ExperimentTest(base.BaseTestV1):

  def test_is_experiment_running__status_running(self):
    """ Test that is_experiment_running returns True when experiment has Running status. """

    self.assertTrue(experiment.is_experiment_running(self.project_config.get_experiment_from_key('test_experiment')))

  def test_is_experiment_running__status_not_running(self):
    """ Test that is_experiment_running returns False when experiment does not have running status. """

    with mock.patch('optimizely.project_config.ProjectConfig.get_experiment_from_key',
                    return_value=entities.Experiment(
                      '42', 'test_experiment', 'Some Status', [], [], {},[])) as mock_get_experiment:
      self.assertFalse(experiment.is_experiment_running(self.project_config.get_experiment_from_key('test_experiment')))
    mock_get_experiment.assert_called_once_with('test_experiment')

  def test_is_user_in_forced_variation__no_forced_variation_dict(self):
    """ Test that is_user_in_forced_variation returns False when experiment has no forced variations. """

    self.assertFalse(experiment.is_user_in_forced_variation(None, 'test_user'))
    self.assertFalse(experiment.is_user_in_forced_variation({}, 'test_user'))

  def test_is_user_in_forced_variation__user_not_in_forced_variation(self):
    """ Test that is_user_in_forced_variation returns False when user is not in experiment's forced variations. """

    self.assertFalse(experiment.is_user_in_forced_variation({'user_1': 'control'}, 'test_user'))

  def test_is_user_in_forced_variation__user_in_forced_variation(self):
    """ Test that is_user_in_forced_variation returns True when user is in experiment's forced variations. """

    self.assertTrue(experiment.is_user_in_forced_variation({'user_1': 'control'}, 'user_1'))
