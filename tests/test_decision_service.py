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

import mock

from optimizely import entities
from optimizely import user_profile
from optimizely.helpers import enums
from . import base


class DecisionServiceTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.decision_service = self.optimizely.decision_service
    # Set UserProfileService for the purposes of testing
    self.decision_service.user_profile_service = user_profile.UserProfileService()

  def test_get_forced_variation__user_in_forced_variation(self):
    """ Test that expected variation is returned if user is forced in a variation. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.decision_service.get_forced_variation(experiment, 'user_1'))

    mock_logging.assert_called_with(enums.LogLevels.INFO, 'User "user_1" is forced in variation "control".')

  def test_get_forced_variation__user_in_forced_variation__invalid_variation_id(self):
    """ Test that get_forced_variation returns None when variation user is forced in is invalid. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.project_config.ProjectConfig.get_variation_from_key',
                    return_value=None) as mock_get_variation_id:
      self.assertIsNone(self.decision_service.get_forced_variation(experiment, 'user_1'))

    mock_get_variation_id.assert_called_once_with('test_experiment', 'control')

  def test_get_stored_decision__stored_decision_available(self):
    """ Test that stored decision is retrieved as expected. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    profile = user_profile.UserProfile('test_user', experiment_bucket_map={'111127': {'variation_id': '111128'}})
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.decision_service.get_stored_decision(experiment, profile))

    mock_logging.assert_called_with(
      enums.LogLevels.INFO,
      'Found a stored decision. User "test_user" is in variation "control" of experiment "test_experiment".'
    )

  def test_get_stored_decision__no_stored_decision_available(self):
    """ Test that get_stored_decision returns None when no decision is available. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    profile = user_profile.UserProfile('test_user')
    self.assertIsNone(self.decision_service.get_stored_decision(experiment, profile))

  def test_get_variation__user_forced_in_variation(self):
    """ Test that get_variation returns forced variation if user is forced in a variation. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=entities.Variation('111128', 'control')) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision') as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment') as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup') as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.decision_service.get_variation(experiment, 'user_1', None))

    # Assert that forced variation is returned and stored decision or bucketing service are not involved
    mock_get_forced_variation.assert_called_once_with(experiment, 'user_1')
    self.assertEqual(0, mock_get_stored_decision.call_count)
    self.assertEqual(0, mock_audience_check.call_count)
    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_lookup.call_count)
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__user_has_stored_decision(self):
    """ Test that get_variation returns stored decision if user has variation available for given experiment. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision',
                 return_value=entities.Variation('111128', 'control')) as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment') as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch(
        'optimizely.user_profile.UserProfileService.lookup',
        return_value={'user_id': 'test_user',
                      'experiment_bucket_map': {'111127': {'variation_id': '111128'}}}) as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that stored variation is returned and bucketing service is not involved
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_lookup.assert_called_once_with('test_user')
    mock_get_stored_decision.assert_called_once_with(experiment,
                                                     user_profile.UserProfile('test_user',
                                                                              {'111127': {'variation_id': '111128'}}))
    self.assertEqual(0, mock_audience_check.call_count)
    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__user_bucketed_for_new_experiment__user_profile_service_available(self):
    """ Test that get_variation buckets and returns variation if no forced variation or decision available.
    Also, stores decision if user profile service is available. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision',
                 return_value=None) as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=entities.Variation('111129', 'variation')) as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup',
                 return_value={'user_id': 'test_user', 'experiment_bucket_map': {}}) as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that user is bucketed and new decision is stored
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_lookup.assert_called_once_with('test_user')
    self.assertEqual(1, mock_get_stored_decision.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_bucket.assert_called_once_with(experiment, 'test_user')
    mock_save.assert_called_once_with({'user_id': 'test_user',
                                       'experiment_bucket_map': {'111127': {'variation_id': '111129'}}})

  def test_get_variation__user_bucketed_for_new_experiment__user_profile_service_not_available(self):
    """ Test that get_variation buckets and returns variation if
    no forced variation and no user profile service available. """

    # Unset user profile service
    self.decision_service.user_profile_service = None

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision') as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=entities.Variation('111129', 'variation')) as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup') as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that user is bucketed and new decision is not stored as user profile service is not available
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    self.assertEqual(0, mock_lookup.call_count)
    self.assertEqual(0, mock_get_stored_decision.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_bucket.assert_called_once_with(experiment, 'test_user')
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__user_does_not_meet_audience_conditions(self):
    """ Test that get_variation returns None if user is not in experiment. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision',
                 return_value=None) as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=False) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup',
                 return_value={'user_id': 'test_user', 'experiment_bucket_map': {}}) as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertIsNone(self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that user is bucketed and new decision is stored
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_lookup.assert_called_once_with('test_user')
    mock_get_stored_decision.assert_called_once_with(experiment, user_profile.UserProfile('test_user'))
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__user_profile_in_invalid_format(self):
    """ Test that get_variation handles invalid user profile gracefully. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision') as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=entities.Variation('111129', 'variation')) as mock_bucket, \
      mock.patch('optimizely.logger.NoOpLogger.log') as mock_logging, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup',
                 return_value='invalid_profile') as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that user is bucketed and new decision is stored
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_lookup.assert_called_once_with('test_user')
    # Stored decision is not consulted as user profile is invalid
    self.assertEqual(0, mock_get_stored_decision.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_logging.assert_called_with(enums.LogLevels.WARNING, 'User profile has invalid format.')
    mock_bucket.assert_called_once_with(experiment, 'test_user')
    mock_save.assert_called_once_with({'user_id': 'test_user',
                                       'experiment_bucket_map': {'111127': {'variation_id': '111129'}}})

  def test_get_variation__user_profile_lookup_fails(self):
    """ Test that get_variation acts gracefully when lookup fails. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision') as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=entities.Variation('111129', 'variation')) as mock_bucket, \
      mock.patch('optimizely.logger.NoOpLogger.log') as mock_logging, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup',
                 side_effect=Exception('major problem')) as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that user is bucketed and new decision is stored
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_lookup.assert_called_once_with('test_user')
    # Stored decision is not consulted as lookup failed
    self.assertEqual(0, mock_get_stored_decision.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_logging.assert_any_call(
      enums.LogLevels.ERROR,
      'Unable to retrieve user profile for user "test_user" as lookup failed. Error: major problem')
    mock_bucket.assert_called_once_with(experiment, 'test_user')
    mock_save.assert_called_once_with({'user_id': 'test_user',
                                       'experiment_bucket_map': {'111127': {'variation_id': '111129'}}})

  def test_get_variation__user_profile_save_fails(self):
    """ Test that get_variation acts gracefully when save fails. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_decision') as mock_get_stored_decision, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=entities.Variation('111129', 'variation')) as mock_bucket, \
      mock.patch('optimizely.logger.NoOpLogger.log') as mock_logging, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup', return_value=None) as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save',
                 side_effect=Exception('major problem')) as mock_save:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that user is bucketed and new decision is stored
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_lookup.assert_called_once_with('test_user')
    self.assertEqual(0, mock_get_stored_decision.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_logging.assert_any_call(
      enums.LogLevels.ERROR,
      'Unable to save user profile for user "test_user". Error: major problem')
    mock_bucket.assert_called_once_with(experiment, 'test_user')
    mock_save.assert_called_once_with({'user_id': 'test_user',
                                       'experiment_bucket_map': {'111127': {'variation_id': '111129'}}})
