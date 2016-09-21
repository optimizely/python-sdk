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
