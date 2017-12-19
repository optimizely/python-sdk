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

from optimizely import entities
from optimizely import optimizely
from optimizely import user_profile
from optimizely.helpers import enums
from . import base


class DecisionServiceTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.decision_service = self.optimizely.decision_service
    # Set UserProfileService for the purposes of testing
    self.decision_service.user_profile_service = user_profile.UserProfileService()

  def test_get_bucketing_id__no_bucketing_id_attribute(self):
    """ Test that _get_bucketing_id returns correct bucketing ID when there is no bucketing ID attribute. """

    # No attributes
    self.assertEqual('test_user', decision_service.DecisionService._get_bucketing_id('test_user', None))

    # With attributes, but no bucketing ID
    self.assertEqual('test_user', decision_service.DecisionService._get_bucketing_id('test_user',
                                                                                     {'random_key': 'random_value'}))

  def test_get_bucketing_id__bucketing_id_attribute(self):
    """ Test that _get_bucketing_id returns correct bucketing ID when there is bucketing ID attribute. """

    self.assertEqual('user_bucket_value',
                     decision_service.DecisionService._get_bucketing_id('test_user',
                                                                        {'$opt_bucketing_id': 'user_bucket_value'}))

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

  def test_get_stored_variation__stored_decision_available(self):
    """ Test that stored decision is retrieved as expected. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    profile = user_profile.UserProfile('test_user', experiment_bucket_map={'111127': {'variation_id': '111128'}})
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logging:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.decision_service.get_stored_variation(experiment, profile))

    mock_logging.assert_called_with(
      enums.LogLevels.INFO,
      'Found a stored decision. User "test_user" is in variation "control" of experiment "test_experiment".'
    )

  def test_get_stored_variation__no_stored_decision_available(self):
    """ Test that get_stored_variation returns None when no decision is available. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    profile = user_profile.UserProfile('test_user')
    self.assertIsNone(self.decision_service.get_stored_variation(experiment, profile))

  def test_get_variation__experiment_not_running(self):
    """ Test that get_variation returns None if experiment is not Running. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    # Mark experiment paused
    experiment.status = 'Paused'
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation') as mock_get_forced_variation, \
      mock.patch('optimizely.logger.NoOpLogger.log') as mock_logging, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation') as mock_get_stored_variation, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment') as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup') as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertIsNone(self.decision_service.get_variation(experiment, 'test_user', None))

    mock_logging.assert_called_once_with(enums.LogLevels.INFO, 'Experiment "test_experiment" is not running.')
    # Assert no calls are made to other services
    self.assertEqual(0, mock_get_forced_variation.call_count)
    self.assertEqual(0, mock_get_stored_variation.call_count)
    self.assertEqual(0, mock_audience_check.call_count)
    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_lookup.call_count)
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__bucketing_id_provided(self):
    """ Test that get_variation calls bucket with correct bucketing ID if provided. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation', return_value=None), \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation', return_value=None), \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True), \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket:
      self.decision_service.get_variation(experiment,
                                          'test_user',
                                          {'random_key': 'random_value',
                                           '$opt_bucketing_id': 'user_bucket_value'})

    # Assert that bucket is called with appropriate bucketing ID
    mock_bucket.assert_called_once_with(experiment, 'test_user', 'user_bucket_value')

  def test_get_variation__user_forced_in_variation(self):
    """ Test that get_variation returns forced variation if user is forced in a variation. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=entities.Variation('111128', 'control')) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation') as mock_get_stored_variation, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment') as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup') as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111128', 'control'),
                       self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that forced variation is returned and stored decision or bucketing service are not involved
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    self.assertEqual(0, mock_get_stored_variation.call_count)
    self.assertEqual(0, mock_audience_check.call_count)
    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_lookup.call_count)
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__user_has_stored_decision(self):
    """ Test that get_variation returns stored decision if user has variation available for given experiment. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation',
                 return_value=entities.Variation('111128', 'control')) as mock_get_stored_variation, \
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
    mock_get_stored_variation.assert_called_once_with(experiment,
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
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation',
                 return_value=None) as mock_get_stored_variation, \
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
    self.assertEqual(1, mock_get_stored_variation.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_bucket.assert_called_once_with(experiment, 'test_user', 'test_user')
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
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation') as mock_get_stored_variation, \
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
    self.assertEqual(0, mock_get_stored_variation.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_bucket.assert_called_once_with(experiment, 'test_user', 'test_user')
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__user_does_not_meet_audience_conditions(self):
    """ Test that get_variation returns None if user is not in experiment. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation',
                 return_value=None) as mock_get_stored_variation, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=False) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup',
                 return_value={'user_id': 'test_user', 'experiment_bucket_map': {}}) as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertIsNone(self.decision_service.get_variation(experiment, 'test_user', None))

    # Assert that user is bucketed and new decision is stored
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_lookup.assert_called_once_with('test_user')
    mock_get_stored_variation.assert_called_once_with(experiment, user_profile.UserProfile('test_user'))
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_save.call_count)

  def test_get_variation__user_profile_in_invalid_format(self):
    """ Test that get_variation handles invalid user profile gracefully. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation') as mock_get_stored_variation, \
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
    self.assertEqual(0, mock_get_stored_variation.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_logging.assert_called_with(enums.LogLevels.WARNING, 'User profile has invalid format.')
    mock_bucket.assert_called_once_with(experiment, 'test_user', 'test_user')
    mock_save.assert_called_once_with({'user_id': 'test_user',
                                       'experiment_bucket_map': {'111127': {'variation_id': '111129'}}})

  def test_get_variation__user_profile_lookup_fails(self):
    """ Test that get_variation acts gracefully when lookup fails. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation') as mock_get_stored_variation, \
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
    self.assertEqual(0, mock_get_stored_variation.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_logging.assert_any_call(
      enums.LogLevels.ERROR,
      'Unable to retrieve user profile for user "test_user" as lookup failed. Error: major problem')
    mock_bucket.assert_called_once_with(experiment, 'test_user', 'test_user')
    mock_save.assert_called_once_with({'user_id': 'test_user',
                                       'experiment_bucket_map': {'111127': {'variation_id': '111129'}}})

  def test_get_variation__user_profile_save_fails(self):
    """ Test that get_variation acts gracefully when save fails. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.decision_service.DecisionService.get_stored_variation') as mock_get_stored_variation, \
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
    self.assertEqual(0, mock_get_stored_variation.call_count)
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_logging.assert_any_call(
      enums.LogLevels.ERROR,
      'Unable to save user profile for user "test_user". Error: major problem')
    mock_bucket.assert_called_once_with(experiment, 'test_user', 'test_user')
    mock_save.assert_called_once_with({'user_id': 'test_user',
                                       'experiment_bucket_map': {'111127': {'variation_id': '111129'}}})

  def test_get_variation__ignore_user_profile_when_specified(self):
    """ Test that we ignore the user profile service if specified. """

    experiment = self.project_config.get_experiment_from_key('test_experiment')
    with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                    return_value=None) as mock_get_forced_variation, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=entities.Variation('111129', 'variation')) as mock_bucket, \
      mock.patch('optimizely.user_profile.UserProfileService.lookup') as mock_lookup, \
      mock.patch('optimizely.user_profile.UserProfileService.save') as mock_save:
      self.assertEqual(entities.Variation('111129', 'variation'),
                       self.decision_service.get_variation(experiment, 'test_user', None, ignore_user_profile=True))

    # Assert that user is bucketed and new decision is NOT stored
    mock_get_forced_variation.assert_called_once_with(experiment, 'test_user')
    mock_audience_check.assert_called_once_with(self.project_config, experiment, None)
    mock_bucket.assert_called_once_with(experiment, 'test_user', 'test_user')
    self.assertEqual(0, mock_lookup.call_count)
    self.assertEqual(0, mock_save.call_count)


@mock.patch('optimizely.logger.NoOpLogger.log')
class FeatureFlagDecisionTests(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    self.project_config = opt_obj.config
    self.decision_service = opt_obj.decision_service

  def test_get_variation_for_rollout__returns_none_if_no_experiments(self, mock_logging):
    """ Test that get_variation_for_rollout returns None if there are no experiments (targeting rules). """

    no_experiment_rollout = self.project_config.get_rollout_from_id('201111')
    self.assertIsNone(self.decision_service.get_variation_for_rollout(no_experiment_rollout, 'test_user'))

    # Assert no log messages were generated
    self.assertEqual(0, mock_logging.call_count)

  def test_get_variation_for_rollout__returns_decision_if_user_in_rollout(self, mock_logging):
    """ Test that get_variation_for_rollout returns Decision with experiment/variation
     if user meets targeting conditions for a rollout rule. """

    rollout = self.project_config.get_rollout_from_id('211111')

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True),\
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=self.project_config.get_variation_from_id('211127', '211129')) as mock_bucket:
      self.assertEqual(decision_service.Decision(self.project_config.get_experiment_from_id('211127'),
                                                 self.project_config.get_variation_from_id('211127', '211129')),
                       self.decision_service.get_variation_for_rollout(rollout, 'test_user'))

    # Check all log messages
    self.assertEqual(
      [mock.call(enums.LogLevels.DEBUG, 'User "test_user" meets conditions for targeting rule 1.'),
       mock.call(enums.LogLevels.DEBUG, 'User "test_user" is in variation 211129 of experiment 211127.')
       ], mock_logging.call_args_list)

    # Check that bucket is called with correct parameters
    mock_bucket.assert_called_once_with(self.project_config.get_experiment_from_id('211127'), 'test_user', 'test_user')

  def test_get_variation_for_rollout__calls_bucket_with_bucketing_id(self, mock_logging):
    """ Test that get_variation_for_rollout calls Bucketer.bucket with bucketing ID when provided. """

    rollout = self.project_config.get_rollout_from_id('211111')

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True),\
      mock.patch('optimizely.bucketer.Bucketer.bucket',
                 return_value=self.project_config.get_variation_from_id('211127', '211129')) as mock_bucket:
      self.assertEqual(decision_service.Decision(self.project_config.get_experiment_from_id('211127'),
                                                 self.project_config.get_variation_from_id('211127', '211129')),
                       self.decision_service.get_variation_for_rollout(rollout,
                                                                       'test_user',
                                                                       {'$opt_bucketing_id': 'user_bucket_value'}))

    # Check all log messages
    self.assertEqual(
      [mock.call(enums.LogLevels.DEBUG, 'User "test_user" meets conditions for targeting rule 1.'),
       mock.call(enums.LogLevels.DEBUG, 'User "test_user" is in variation 211129 of experiment 211127.')
       ], mock_logging.call_args_list)

    # Check that bucket is called with correct parameters
    mock_bucket.assert_called_once_with(self.project_config.get_experiment_from_id('211127'),
                                        'test_user',
                                        'user_bucket_value')

  def test_get_variation_for_rollout__skips_to_everyone_else_rule(self, mock_logging):
    """ Test that if a user is in an audience, but does not qualify
    for the experiment, then it skips to the Everyone Else rule. """

    rollout = self.project_config.get_rollout_from_id('211111')

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check,\
      mock.patch('optimizely.bucketer.Bucketer.bucket', return_value=None):
      self.assertIsNone(self.decision_service.get_variation_for_rollout(rollout, 'test_user'))

    # Check that after first experiment, it skips to the last experiment to check
    self.assertEqual(
      [mock.call(self.project_config, self.project_config.get_experiment_from_key('211127'), None),
       mock.call(self.project_config, self.project_config.get_experiment_from_key('211147'), None)],
      mock_audience_check.call_args_list
    )

    # Check all log messages
    self.assertEqual(
      [mock.call(enums.LogLevels.DEBUG, 'User "test_user" meets conditions for targeting rule 1.'),
       mock.call(enums.LogLevels.DEBUG, 'User "test_user" is not in the traffic group for the targeting else. '
                                        'Checking "Everyone Else" rule now.')
       ], mock_logging.call_args_list)

  def test_get_variation_for_rollout__returns_none_for_user_not_in_rollout(self, mock_logging):
    """ Test that get_variation_for_rollout returns None for the user not in the associated rollout. """

    rollout = self.project_config.get_rollout_from_id('211111')

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=False) as mock_audience_check:
      self.assertIsNone(self.decision_service.get_variation_for_rollout(rollout, 'test_user'))

    # Check that all experiments in rollout layer were checked
    self.assertEqual(
      [mock.call(self.project_config, self.project_config.get_experiment_from_key('211127'), None),
       mock.call(self.project_config, self.project_config.get_experiment_from_key('211137'), None),
       mock.call(self.project_config, self.project_config.get_experiment_from_key('211147'), None)],
      mock_audience_check.call_args_list
    )

    # Check all log messages
    self.assertEqual(
      [mock.call(enums.LogLevels.DEBUG, 'User "test_user" does not meet conditions for targeting rule 1.'),
       mock.call(enums.LogLevels.DEBUG, 'User "test_user" does not meet conditions for targeting rule 2.')],
      mock_logging.call_args_list)

  def test_get_variation_for_feature__returns_variation_for_feature_in_experiment(self, mock_logging):
    """ Test that get_variation_for_feature returns the variation of the experiment the feature is associated with. """

    feature = self.project_config.get_feature_from_key('test_feature_in_experiment')

    expected_variation = self.project_config.get_variation_from_id('test_experiment', '111129')
    with mock.patch(
      'optimizely.decision_service.DecisionService.get_variation',
      return_value=expected_variation) as mock_decision:
      self.assertEqual(expected_variation, self.decision_service.get_variation_for_feature(feature, 'user1'))

    mock_decision.assert_called_once_with(
      self.project_config.get_experiment_from_key('test_experiment'), 'test_user', None
    )

    # Check log message
    mock_logging.assert_called_once_with(enums.LogLevels.DEBUG,
                                         'User "test_user" is in variation variation of experiment test_experiment.')

  def test_get_variation_for_feature__returns_variation_for_feature_in_rollout(self, mock_logging):
    """ Test that get_variation_for_feature returns the variation of
    the experiment in the rollout that the user is bucketed into. """

    feature = self.project_config.get_feature_from_key('test_feature_in_rollout')

    expected_variation = self.project_config.get_variation_from_id('211127', '211129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_rollout',
                    return_value=expected_variation) as mock_get_variation_for_rollout:
      self.assertEqual(expected_variation, self.decision_service.get_variation_for_feature(feature, 'test_user'))

    expected_rollout = self.project_config.get_rollout_from_id('211111')
    mock_get_variation_for_rollout.assert_called_once_with(expected_rollout, 'test_user', None)

    # Assert no log messages were generated
    self.assertEqual(0, mock_logging.call_count)

  def test_get_variation_for_feature__returns_variation_if_user_not_in_experiment_but_in_rollout(self, _):
    """ Test that get_variation_for_feature returns the variation of the experiment in the
    feature's rollout even if the user is not bucketed into the feature's experiment. """

    feature = self.project_config.get_feature_from_key('test_feature_in_experiment_and_rollout')

    expected_variation = self.project_config.get_variation_from_id('211127', '211129')
    with mock.patch(
      'optimizely.helpers.audience.is_user_in_experiment',
      side_effect=[False, True]) as mock_audience_check, \
      mock.patch('optimizely.bucketer.Bucketer.bucket', return_value=expected_variation):
      self.assertEqual(expected_variation, self.decision_service.get_variation_for_feature(feature, 'user1'))

    self.assertEqual(2, mock_audience_check.call_count)
    mock_audience_check.assert_any_call(self.project_config,
                                        self.project_config.get_experiment_from_key('test_experiment'), None)
    mock_audience_check.assert_any_call(self.project_config,
                                        self.project_config.get_experiment_from_key('211127'), None)

  def test_get_variation_for_feature__returns_variation_for_feature_in_group(self, _):
    """ Test that get_variation_for_feature returns the variation of
     the experiment the user is bucketed in the feature's group. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    decision_service = opt_obj.decision_service
    feature = project_config.get_feature_from_key('test_feature_in_group')

    expected_variation = project_config.get_variation_from_id('group_exp_1', '28901')
    with mock.patch(
      'optimizely.decision_service.DecisionService.get_experiment_in_group',
      return_value=project_config.get_experiment_from_key('group_exp_1')) as mock_get_experiment_in_group, \
      mock.patch('optimizely.decision_service.DecisionService.get_variation',
                 return_value=expected_variation) as mock_decision:
      self.assertEqual(expected_variation, decision_service.get_variation_for_feature(feature, 'user1'))

    mock_get_experiment_in_group.assert_called_once_with(project_config.get_group('19228'), 'user1')
    mock_decision.assert_called_once_with(project_config.get_experiment_from_key('group_exp_1'), 'user1', None)

  def test_get_variation_for_feature__returns_none_for_user_not_in_group(self, _):
    """ Test that get_variation_for_feature returns None for
    user not in group and the feature is not part of a rollout. """

    feature = self.project_config.get_feature_from_key('test_feature_in_group')

    with mock.patch('optimizely.decision_service.DecisionService.get_experiment_in_group',
                    return_value=None) as mock_get_experiment_in_group, \
      mock.patch('optimizely.decision_service.DecisionService.get_variation') as mock_decision:
      self.assertIsNone(self.decision_service.get_variation_for_feature(feature, 'user1'))

    mock_get_experiment_in_group.assert_called_once_with(self.project_config.get_group('19228'), 'test_user')
    self.assertFalse(mock_decision.called)

  def test_get_variation_for_feature__returns_none_for_user_not_in_experiment(self, _):
    """ Test that get_variation_for_feature returns None for user not in the associated experiment. """

    feature = self.project_config.get_feature_from_key('test_feature_in_experiment')

    with mock.patch('optimizely.decision_service.DecisionService.get_variation', return_value=None) as mock_decision:
      self.assertIsNone(self.decision_service.get_variation_for_feature(feature, 'user1'))

    mock_decision.assert_called_once_with(
      self.project_config.get_experiment_from_key('test_experiment'), 'test_user', None
    )

  def test_get_variation_for_feature__returns_none_for_user_in_group_experiment_not_associated_with_feature(self, _):
    """ Test that if a user is in the mutex group but the experiment is
    not targeting a feature, then None is returned. """

    feature = self.project_config.get_feature_from_key('test_feature_in_group')

    with mock.patch('optimizely.decision_service.DecisionService.get_experiment_in_group',
                    return_value=self.project_config.get_experiment_from_key('group_exp_2')) as mock_decision:
      self.assertIsNone(self.decision_service.get_variation_for_feature(feature, 'user_1'))

    mock_decision.assert_called_once_with(self.project_config.get_group('19228'), 'test_user')

  def test_get_experiment_in_group(self, mock_logging):
    """ Test that get_experiment_in_group returns the bucketed experiment for the user. """

    group = self.project_config.get_group('19228')
    experiment = self.project_config.get_experiment_from_id('32222')
    with mock.patch('optimizely.bucketer.Bucketer.find_bucket', return_value='32222'):
      self.assertEqual(experiment, self.decision_service.get_experiment_in_group(group, 'test_user'))

    mock_logging.assert_called_with(enums.LogLevels.INFO, 'User with bucketing ID "test_user" is in '
                                                          'experiment group_exp_1 of group 19228.')

  def test_get_experiment_in_group__returns_none_if_user_not_in_group(self, mock_logging):
    """ Test that get_experiment_in_group returns None if the user is not bucketed into the group. """

    group = self.project_config.get_group('19228')
    with mock.patch('optimizely.bucketer.Bucketer.find_bucket', return_value=None):
      self.assertIsNone(self.decision_service.get_experiment_in_group(group, 'test_user'))

    mock_logging.assert_called_with(enums.LogLevels.INFO, 'User with bucketing ID "test_user" is '
                                                          'not in any experiments of group 19228.')
