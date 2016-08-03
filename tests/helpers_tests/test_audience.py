import mock

from tests import base
from optimizely.helpers import audience


class AudienceTest(base.BaseTest):

  def test_is_match__audience_condition_matches(self):
    """ Test that is_match returns True when audience conditions are met. """

    user_attributes = {
      'test_attribute': 'test_value',
      'browser_type': 'firefox',
      'location': 'San Francisco'
    }

    self.assertTrue(audience.is_match(self.optimizely.config.audiences[0], user_attributes))

  def test_is_match__audience_condition_does_not_match(self):
    """ Test that is_match returns False when audience conditions are not met. """

    user_attributes = {
      'test_attribute': 'wrong_test_value',
      'browser_type': 'chrome',
      'location': 'San Francisco'
    }

    self.assertFalse(audience.is_match(self.optimizely.config.audiences[0], user_attributes))

  def test_is_user_in_experiment__no_audience(self):
    """ Test that is_user_in_experiment returns True when experiment is using no audience. """

    user_attributes = {
      'test_attribute': 'test_value',
      'browser_type': 'firefox',
      'location': 'San Francisco'
    }

    with mock.patch('optimizely.project_config.ProjectConfig.get_audience_ids_for_experiment',
                    return_value=[]) as mock_get_audience_ids:
      self.assertTrue(audience.is_user_in_experiment(self.project_config, 'test_experiment', user_attributes))
    mock_get_audience_ids.assert_called_once_with('test_experiment')

  def test_is_user_in_experiment__audience_conditions_are_met(self):
    """ Test that is_user_in_experiment returns True when audience conditions are met. """

    user_attributes = {
      'test_attribute': 'test_value',
      'browser_type': 'firefox',
      'location': 'San Francisco'
    }

    with mock.patch('optimizely.helpers.audience.is_match', return_value=True) as mock_is_match:
      self.assertTrue(audience.is_user_in_experiment(self.project_config, 'test_experiment', user_attributes))
    mock_is_match.assert_called_once_with(self.optimizely.config.audiences[0], user_attributes)

  def test_is_user_in_experiment__audience_conditions_not_met(self):
    """ Test that is_user_in_experiment returns False when audience conditions are not met. """

    user_attributes = {
      'test_attribute': 'wrong_test_value',
      'browser_type': 'chrome',
      'location': 'San Francisco'
    }

    with mock.patch('optimizely.helpers.audience.is_match', return_value=False) as mock_is_match:
      self.assertFalse(audience.is_user_in_experiment(self.project_config, 'test_experiment', user_attributes))
    mock_is_match.assert_called_once_with(self.optimizely.config.audiences[0], user_attributes)
