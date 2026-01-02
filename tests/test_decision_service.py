# Copyright 2017-2021, Optimizely
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

from unittest import mock

from optimizely import decision_service
from optimizely import entities
from optimizely import optimizely
from optimizely import optimizely_user_context
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
        bucketing_id, _ = self.decision_service._get_bucketing_id("test_user", None)
        self.assertEqual(
            "test_user",
            bucketing_id
        )

        # With attributes, but no bucketing ID
        bucketing_id, _ = self.decision_service._get_bucketing_id(
            "test_user", {"random_key": "random_value"}
        )
        self.assertEqual(
            "test_user",
            bucketing_id,
        )

    def test_get_bucketing_id__bucketing_id_attribute(self):
        """ Test that _get_bucketing_id returns correct bucketing ID when there is bucketing ID attribute. """
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            bucketing_id, _ = self.decision_service._get_bucketing_id(
                "test_user", {"$opt_bucketing_id": "user_bucket_value"}
            )
            self.assertEqual(
                "user_bucket_value",
                bucketing_id,
            )
            mock_decision_service_logging.debug.assert_not_called()

    def test_get_bucketing_id__bucketing_id_attribute_not_a_string(self):
        """ Test that _get_bucketing_id returns user ID as  bucketing ID when bucketing ID attribute is not a string"""
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            bucketing_id, _ = self.decision_service._get_bucketing_id(
                "test_user", {"$opt_bucketing_id": True}
            )
            self.assertEqual(
                "test_user",
                bucketing_id,
            )
            mock_decision_service_logging.warning.assert_called_once_with(
                "Bucketing ID attribute is not a string. Defaulted to user_id."
            )
            mock_decision_service_logging.reset_mock()

            bucketing_id, _ = self.decision_service._get_bucketing_id(
                "test_user", {"$opt_bucketing_id": 5.9}
            )
            self.assertEqual(
                "test_user",
                bucketing_id,
            )
            mock_decision_service_logging.warning.assert_called_once_with(
                "Bucketing ID attribute is not a string. Defaulted to user_id."
            )
            mock_decision_service_logging.reset_mock()
            bucketing_id, _ = self.decision_service._get_bucketing_id(
                "test_user", {"$opt_bucketing_id": 5}
            )
            self.assertEqual(
                "test_user",
                bucketing_id,
            )
            mock_decision_service_logging.warning.assert_called_once_with(
                "Bucketing ID attribute is not a string. Defaulted to user_id."
            )

    def test_set_forced_variation__invalid_experiment_key(self):
        """ Test invalid experiment keys set fail to set a forced variation """

        self.assertFalse(
            self.decision_service.set_forced_variation(
                self.project_config,
                "test_experiment_not_in_datafile",
                "test_user",
                "variation",
            )
        )
        self.assertFalse(
            self.decision_service.set_forced_variation(
                self.project_config, "", "test_user", "variation"
            )
        )
        self.assertFalse(
            self.decision_service.set_forced_variation(
                self.project_config, None, "test_user", "variation"
            )
        )

    def test_set_forced_variation__invalid_variation_key(self):
        """ Test invalid variation keys set fail to set a forced variation """

        self.assertFalse(
            self.decision_service.set_forced_variation(
                self.project_config,
                "test_experiment",
                "test_user",
                "variation_not_in_datafile",
            )
        )
        self.assertTrue(
            self.decision_service.set_forced_variation(
                self.project_config, "test_experiment", "test_user", None
            )
        )
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            self.assertIs(
                self.decision_service.set_forced_variation(
                    self.project_config, "test_experiment", "test_user", ""
                ),
                False,
            )
        mock_decision_service_logging.debug.assert_called_once_with(
            "Variation key is invalid."
        )

    def test_set_forced_variation__multiple_sets(self):
        """ Test multiple sets of experiments for one and multiple users work """

        self.assertTrue(
            self.decision_service.set_forced_variation(
                self.project_config, "test_experiment", "test_user_1", "variation"
            )
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "test_experiment", "test_user_1"
        )
        self.assertEqual(
            variation.key,
            "variation",
        )
        # same user, same experiment, different variation
        self.assertTrue(
            self.decision_service.set_forced_variation(
                self.project_config, "test_experiment", "test_user_1", "control"
            )
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "test_experiment", "test_user_1"
        )
        self.assertEqual(
            variation.key,
            "control",
        )
        # same user, different experiment
        self.assertTrue(
            self.decision_service.set_forced_variation(
                self.project_config, "group_exp_1", "test_user_1", "group_exp_1_control"
            )
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "group_exp_1", "test_user_1"
        )
        self.assertEqual(
            variation.key,
            "group_exp_1_control",
        )

        # different user
        self.assertTrue(
            self.decision_service.set_forced_variation(
                self.project_config, "test_experiment", "test_user_2", "variation"
            )
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "test_experiment", "test_user_2"
        )
        self.assertEqual(
            variation.key,
            "variation",
        )
        # different user, different experiment
        self.assertTrue(
            self.decision_service.set_forced_variation(
                self.project_config, "group_exp_1", "test_user_2", "group_exp_1_control"
            )
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "group_exp_1", "test_user_2"
        )
        self.assertEqual(
            variation.key,
            "group_exp_1_control",
        )

        # make sure the first user forced variations are still valid
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "test_experiment", "test_user_1"
        )
        self.assertEqual(
            variation.key,
            "control",
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "group_exp_1", "test_user_1"
        )
        self.assertEqual(
            variation.key,
            "group_exp_1_control",
        )

    def test_set_forced_variation_when_called_to_remove_forced_variation(self):
        """ Test set_forced_variation when no variation is given. """
        # Test case where both user and experiment are present in the forced variation map
        self.project_config.forced_variation_map = {}
        self.decision_service.set_forced_variation(
            self.project_config, "test_experiment", "test_user", "variation"
        )

        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            self.assertTrue(
                self.decision_service.set_forced_variation(
                    self.project_config, "test_experiment", "test_user", None
                )
            )
        mock_decision_service_logging.debug.assert_called_once_with(
            'Variation mapped to experiment "test_experiment" has been removed for user "test_user".'
        )

        # Test case where user is present in the forced variation map, but the given experiment isn't
        self.project_config.forced_variation_map = {}
        self.decision_service.set_forced_variation(
            self.project_config, "test_experiment", "test_user", "variation"
        )

        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            self.assertTrue(
                self.decision_service.set_forced_variation(
                    self.project_config, "group_exp_1", "test_user", None
                )
            )
        mock_decision_service_logging.debug.assert_called_once_with(
            'Nothing to remove. Variation mapped to experiment "group_exp_1" for user "test_user" does not exist.'
        )

    def test_get_forced_variation__invalid_user_id(self):
        """ Test invalid user IDs return a null variation. """
        self.decision_service.forced_variation_map["test_user"] = {}
        self.decision_service.forced_variation_map["test_user"][
            "test_experiment"
        ] = "test_variation"

        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "test_experiment", None
        )
        self.assertIsNone(
            variation
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "test_experiment", ""
        )
        self.assertIsNone(
            variation
        )

    def test_get_forced_variation__invalid_experiment_key(self):
        """ Test invalid experiment keys return a null variation. """
        self.decision_service.forced_variation_map["test_user"] = {}
        self.decision_service.forced_variation_map["test_user"][
            "test_experiment"
        ] = "test_variation"
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "test_experiment_not_in_datafile", "test_user"
        )
        self.assertIsNone(
            variation
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, None, "test_user"
        )
        self.assertIsNone(
            variation
        )
        variation, _ = self.decision_service.get_forced_variation(
            self.project_config, "", "test_user"
        )
        self.assertIsNone(
            variation
        )

    def test_get_forced_variation_with_none_set_for_user(self):
        """ Test get_forced_variation when none set for user ID in forced variation map. """
        self.decision_service.forced_variation_map = {}
        self.decision_service.forced_variation_map["test_user"] = {}

        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            variation, _ = self.decision_service.get_forced_variation(
                self.project_config, "test_experiment", "test_user"
            )
            self.assertIsNone(
                variation
            )
        mock_decision_service_logging.debug.assert_called_once_with(
            'No experiment "test_experiment" mapped to user "test_user" in the forced variation map.'
        )

    def test_get_forced_variation_missing_variation_mapped_to_experiment(self):
        """ Test get_forced_variation when no variation found against given experiment for the user. """
        self.decision_service.forced_variation_map = {}
        self.decision_service.forced_variation_map["test_user"] = {}
        self.decision_service.forced_variation_map["test_user"][
            "test_experiment"
        ] = None

        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            variation, _ = self.decision_service.get_forced_variation(
                self.project_config, "test_experiment", "test_user"
            )
            self.assertIsNone(
                variation
            )

        mock_decision_service_logging.debug.assert_called_once_with(
            'No variation mapped to experiment "test_experiment" in the forced variation map.'
        )

    def test_get_whitelisted_variation__user_in_forced_variation(self):
        """ Test that expected variation is returned if user is forced in a variation. """

        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            variation, _ = self.decision_service.get_whitelisted_variation(
                self.project_config, experiment, "user_1"
            )
            self.assertEqual(
                entities.Variation("111128", "control"),
                variation,
            )

        mock_decision_service_logging.info.assert_called_once_with(
            'User "user_1" is forced in variation "control".'
        )

    def test_get_whitelisted_variation__user_in_invalid_variation(self):
        """ Test that get_whitelisted_variation returns None when variation user is whitelisted for is invalid. """

        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch(
                "optimizely.project_config.ProjectConfig.get_variation_from_key",
                return_value=None,
        ) as mock_get_variation_id:
            variation, _ = self.decision_service.get_whitelisted_variation(
                self.project_config, experiment, "user_1"
            )
            self.assertIsNone(
                variation
            )

        mock_get_variation_id.assert_called_once_with("test_experiment", "control")

    def test_get_stored_variation__stored_decision_available(self):
        """ Test that stored decision is retrieved as expected. """

        experiment = self.project_config.get_experiment_from_key("test_experiment")
        profile = user_profile.UserProfile(
            "test_user", experiment_bucket_map={"111127": {"variation_id": "111128"}}
        )
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging:
            variation = self.decision_service.get_stored_variation(
                self.project_config, experiment, profile
            )
            self.assertEqual(
                entities.Variation("111128", "control"),
                variation,
            )

        mock_decision_service_logging.info.assert_called_once_with(
            'Found a stored decision. User "test_user" is in variation "control" of experiment "test_experiment".'
        )

    def test_get_stored_variation__no_stored_decision_available(self):
        """ Test that get_stored_variation returns None when no decision is available. """

        experiment = self.project_config.get_experiment_from_key("test_experiment")
        profile = user_profile.UserProfile("test_user")
        variation = self.decision_service.get_stored_variation(
            self.project_config, experiment, profile
        )
        self.assertIsNone(
            variation
        )

    def test_get_variation__experiment_not_running(self):
        """ Test that get_variation returns None if experiment is not Running. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        experiment = self.project_config.get_experiment_from_key("test_experiment")
        # Mark experiment paused
        experiment.status = "Paused"
        with mock.patch(
                "optimizely.decision_service.DecisionService.get_forced_variation"
        ) as mock_get_forced_variation, mock.patch.object(
            self.decision_service, "logger"
        ) as mock_decision_service_logging, mock.patch(
            "optimizely.decision_service.DecisionService.get_stored_variation"
        ) as mock_get_stored_variation, mock.patch(
            "optimizely.helpers.audience.does_user_meet_audience_conditions"
        ) as mock_audience_check, mock.patch(
            "optimizely.bucketer.Bucketer.bucket"
        ) as mock_bucket, mock.patch(
            "optimizely.user_profile.UserProfileService.lookup"
        ) as mock_lookup, mock.patch(
            "optimizely.user_profile.UserProfileService.save"
        ) as mock_save:
            variation_result = self.decision_service.get_variation(
                self.project_config, experiment, user, None
            )
            variation = variation_result['variation']
            self.assertIsNone(
                variation
            )

        mock_decision_service_logging.info.assert_called_once_with(
            'Experiment "test_experiment" is not running.'
        )
        # Assert no calls are made to other services
        self.assertEqual(0, mock_get_forced_variation.call_count)
        self.assertEqual(0, mock_get_stored_variation.call_count)
        self.assertEqual(0, mock_audience_check.call_count)
        self.assertEqual(0, mock_bucket.call_count)
        self.assertEqual(0, mock_lookup.call_count)
        self.assertEqual(0, mock_save.call_count)

    def test_get_variation__bucketing_id_provided(self):
        """ Test that get_variation calls bucket with correct bucketing ID if provided. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={
                                                                 "random_key": "random_value",
                                                                 "$opt_bucketing_id": "user_bucket_value",
                                                             })
        user_profile_service = user_profile.UserProfileService()
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, user_profile_service)
        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch(
                "optimizely.decision_service.DecisionService.get_forced_variation",
                return_value=[None, []],
        ), mock.patch(
            "optimizely.decision_service.DecisionService.get_stored_variation",
            return_value=None,
        ), mock.patch(
            "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[True, []]
        ), mock.patch(
            "optimizely.bucketer.Bucketer.bucket",
            return_value=[self.project_config.get_variation_from_id("211127", "211129"), []],
        ) as mock_bucket:
            _ = self.decision_service.get_variation(
                self.project_config,
                experiment,
                user,
                user_profile_tracker
            )

        # Assert that bucket is called with appropriate bucketing ID
        mock_bucket.assert_called_once_with(
            self.project_config, experiment, "test_user", "user_bucket_value"
        )

    def test_get_variation__user_whitelisted_for_variation(self):
        """ Test that get_variation returns whitelisted variation if user is whitelisted. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None, logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        user_profile_service = user_profile.UserProfileService()
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, user_profile_service)
        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch(
                "optimizely.decision_service.DecisionService.get_whitelisted_variation",
                return_value=[entities.Variation("111128", "control"), []],
        ) as mock_get_whitelisted_variation, mock.patch(
            "optimizely.decision_service.DecisionService.get_stored_variation"
        ) as mock_get_stored_variation, mock.patch(
            "optimizely.helpers.audience.does_user_meet_audience_conditions"
        ) as mock_audience_check, mock.patch(
            "optimizely.bucketer.Bucketer.bucket"
        ) as mock_bucket, mock.patch(
            "optimizely.user_profile.UserProfileService.lookup"
        ) as mock_lookup, mock.patch(
            "optimizely.user_profile.UserProfileService.save"
        ) as mock_save:
            variation = self.decision_service.get_variation(
                self.project_config, experiment, user, user_profile_tracker
            )['variation']
            self.assertEqual(
                entities.Variation("111128", "control"),
                variation,
            )

        # Assert that forced variation is returned and stored decision or bucketing service are not involved
        mock_get_whitelisted_variation.assert_called_once_with(
            self.project_config, experiment, "test_user"
        )
        self.assertEqual(0, mock_get_stored_variation.call_count)
        self.assertEqual(0, mock_audience_check.call_count)
        self.assertEqual(0, mock_bucket.call_count)
        self.assertEqual(0, mock_lookup.call_count)
        self.assertEqual(0, mock_save.call_count)

    def test_get_variation__user_has_stored_decision(self):
        """ Test that get_variation returns stored decision if user has variation available for given experiment. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None, logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        user_profile_service = user_profile.UserProfileService()
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, user_profile_service)
        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch(
                "optimizely.decision_service.DecisionService.get_whitelisted_variation",
                return_value=[None, []],
        ) as mock_get_whitelisted_variation, mock.patch(
            "optimizely.decision_service.DecisionService.get_stored_variation",
            return_value=entities.Variation("111128", "control"),
        ) as mock_get_stored_variation, mock.patch(
            "optimizely.helpers.audience.does_user_meet_audience_conditions"
        ) as mock_audience_check, mock.patch(
            "optimizely.bucketer.Bucketer.bucket"
        ) as mock_bucket:
            variation = self.decision_service.get_variation(
                self.project_config, experiment, user, user_profile_tracker
            )['variation']
            self.assertEqual(
                entities.Variation("111128", "control"),
                variation,
            )
        # Assert that stored variation is returned and bucketing service is not involved
        mock_get_whitelisted_variation.assert_called_once_with(
            self.project_config, experiment, "test_user"
        )
        mock_get_stored_variation.assert_called_once_with(
            self.project_config,
            experiment,
            user_profile_tracker.user_profile
        )
        self.assertEqual(0, mock_audience_check.call_count)
        self.assertEqual(0, mock_bucket.call_count)

    def test_get_variation__user_bucketed_for_new_experiment__user_profile_tracker_available(
            self,
    ):
        """ Test that get_variation buckets and returns variation if no forced variation or decision available.
    """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        user_profile_service = user_profile.UserProfileService()
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, user_profile_service)
        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging, mock.patch(
            "optimizely.decision_service.DecisionService.get_whitelisted_variation",
            return_value=[None, []],
        ) as mock_get_whitelisted_variation, mock.patch(
            "optimizely.decision_service.DecisionService.get_stored_variation",
            return_value=None,
        ) as mock_get_stored_variation, mock.patch(
            "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[True, []]
        ) as mock_audience_check, mock.patch(
            "optimizely.bucketer.Bucketer.bucket",
            return_value=[entities.Variation("111129", "variation"), []],
        ) as mock_bucket:
            variation = self.decision_service.get_variation(
                self.project_config, experiment, user, user_profile_tracker
            )['variation']
            self.assertEqual(
                entities.Variation("111129", "variation"),
                variation,
            )

        # Assert that user is bucketed and new decision is stored
        mock_get_whitelisted_variation.assert_called_once_with(
            self.project_config, experiment, user.user_id
        )

        self.assertEqual(1, mock_get_stored_variation.call_count)
        mock_audience_check.assert_called_once_with(
            self.project_config,
            experiment.get_audience_conditions_or_ids(),
            enums.ExperimentAudienceEvaluationLogs,
            "test_experiment",
            user,
            mock_decision_service_logging
        )
        mock_bucket.assert_called_once_with(
            self.project_config, experiment, "test_user", "test_user"
        )

    def test_get_variation__user_does_not_meet_audience_conditions(self):
        """ Test that get_variation returns None if user is not in experiment. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, self.decision_service.user_profile_service)
        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging, mock.patch(
            "optimizely.decision_service.DecisionService.get_whitelisted_variation",
            return_value=[None, []],
        ) as mock_get_whitelisted_variation, mock.patch(
            "optimizely.decision_service.DecisionService.get_stored_variation",
            return_value=None,
        ) as mock_get_stored_variation, mock.patch(
            "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[False, []]
        ) as mock_audience_check, mock.patch(
            "optimizely.bucketer.Bucketer.bucket"
        ) as mock_bucket, mock.patch(
            "optimizely.user_profile.UserProfileService.save"
        ) as mock_save:
            variation = self.decision_service.get_variation(
                self.project_config, experiment, user, user_profile_tracker
            )['variation']
            self.assertIsNone(
                variation
            )

        # Assert that user is bucketed and new decision is stored
        mock_get_whitelisted_variation.assert_called_once_with(
            self.project_config, experiment, "test_user"
        )
        mock_get_stored_variation.assert_called_once_with(
            self.project_config, experiment, user_profile_tracker.get_user_profile()
        )
        mock_audience_check.assert_called_once_with(
            self.project_config,
            experiment.get_audience_conditions_or_ids(),
            enums.ExperimentAudienceEvaluationLogs,
            "test_experiment",
            user,
            mock_decision_service_logging
        )
        self.assertEqual(0, mock_bucket.call_count)
        self.assertEqual(0, mock_save.call_count)

    def test_get_variation__ignore_user_profile_when_specified(self):
        """ Test that we ignore the user profile service if specified. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        user_profile_service = user_profile.UserProfileService()
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, user_profile_service)
        experiment = self.project_config.get_experiment_from_key("test_experiment")
        with mock.patch.object(
                self.decision_service, "logger"
        ) as mock_decision_service_logging, mock.patch(
            "optimizely.decision_service.DecisionService.get_whitelisted_variation",
            return_value=[None, []],
        ) as mock_get_whitelisted_variation, mock.patch(
            "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[True, []]
        ) as mock_audience_check, mock.patch(
            "optimizely.bucketer.Bucketer.bucket",
            return_value=[entities.Variation("111129", "variation"), []],
        ) as mock_bucket, mock.patch(
            "optimizely.user_profile.UserProfileService.lookup"
        ) as mock_lookup, mock.patch(
            "optimizely.user_profile.UserProfileService.save"
        ) as mock_save:
            variation = self.decision_service.get_variation(
                self.project_config,
                experiment,
                user,
                user_profile_tracker,
                [],
                options=['IGNORE_USER_PROFILE_SERVICE'],
            )['variation']
            self.assertEqual(
                entities.Variation("111129", "variation"),
                variation,
            )

        # Assert that user is bucketed and new decision is NOT stored
        mock_get_whitelisted_variation.assert_called_once_with(
            self.project_config, experiment, "test_user"
        )
        mock_audience_check.assert_called_once_with(
            self.project_config,
            experiment.get_audience_conditions_or_ids(),
            enums.ExperimentAudienceEvaluationLogs,
            "test_experiment",
            user,
            mock_decision_service_logging
        )
        mock_bucket.assert_called_once_with(
            self.project_config, experiment, "test_user", "test_user"
        )
        self.assertEqual(0, mock_lookup.call_count)
        self.assertEqual(0, mock_save.call_count)

    def test_get_variation_cmab_experiment_user_in_traffic_allocation(self):
        """Test get_variation with CMAB experiment where user is in traffic allocation."""

        # Create a user context
        user = optimizely_user_context.OptimizelyUserContext(
            optimizely_client=None,
            logger=None,
            user_id="test_user",
            user_attributes={}
        )

        # Create a CMAB experiment
        cmab_experiment = entities.Experiment(
            '111150',
            'cmab_experiment',
            'Running',
            '111150',
            [],  # No audience IDs
            {},
            [
                entities.Variation('111151', 'variation_1'),
                entities.Variation('111152', 'variation_2')
            ],
            [
                {'entityId': '111151', 'endOfRange': 5000},
                {'entityId': '111152', 'endOfRange': 10000}
            ],
            cmab={'trafficAllocation': 5000}
        )

        with mock.patch('optimizely.helpers.experiment.is_experiment_running', return_value=True), \
            mock.patch('optimizely.helpers.audience.does_user_meet_audience_conditions', return_value=[True, []]), \
            mock.patch.object(self.decision_service.bucketer, 'bucket_to_entity_id',
                              return_value=['$', []]) as mock_bucket, \
            mock.patch.object(self.decision_service, 'cmab_service') as mock_cmab_service, \
            mock.patch.object(self.project_config, 'get_variation_from_id',
                              return_value=entities.Variation('111151', 'variation_1')), \
            mock.patch.object(self.decision_service,
                              'logger') as mock_logger:

            # Configure CMAB service to return a decision
            mock_cmab_service.get_decision.return_value = (
                {
                    'variation_id': '111151',
                    'cmab_uuid': 'test-cmab-uuid-123'
                },
                []  # reasons list
            )

            # Call get_variation with the CMAB experiment
            variation_result = self.decision_service.get_variation(
                self.project_config,
                cmab_experiment,
                user,
                None
            )
            cmab_uuid = variation_result['cmab_uuid']
            variation = variation_result['variation']
            error = variation_result['error']
            reasons = variation_result['reasons']

            # Verify the variation and cmab_uuid
            self.assertEqual(entities.Variation('111151', 'variation_1'), variation)
            self.assertEqual('test-cmab-uuid-123', cmab_uuid)
            self.assertStrictFalse(error)
            self.assertIn('User "test_user" is in variation "variation_1" of experiment cmab_experiment.', reasons)

            # Verify bucketer was called with correct arguments
            mock_bucket.assert_called_once_with(
                self.project_config,
                cmab_experiment,
                "test_user",
                "test_user"
            )

            # Verify CMAB service was called with correct arguments
            mock_cmab_service.get_decision.assert_called_once_with(
                self.project_config,
                user,
                '111150',  # experiment id
                []  # options (empty list as default)
            )

            # Verify logger was called
            mock_logger.info.assert_any_call('User "test_user" is in variation '
                                             '"variation_1" of experiment cmab_experiment.')

    def test_get_variation_cmab_experiment_user_not_in_traffic_allocation(self):
        """Test get_variation with CMAB experiment where user is not in traffic allocation."""

        # Create a user context
        user = optimizely_user_context.OptimizelyUserContext(
            optimizely_client=None,
            logger=None,
            user_id="test_user",
            user_attributes={}
        )

        # Create a CMAB experiment
        cmab_experiment = entities.Experiment(
            '111150',
            'cmab_experiment',
            'Running',
            '111150',
            [],  # No audience IDs
            {},
            [entities.Variation('111151', 'variation_1')],
            [{'entityId': '111151', 'endOfRange': 10000}],
            cmab={'trafficAllocation': 5000}
        )

        with mock.patch('optimizely.helpers.experiment.is_experiment_running', return_value=True), \
            mock.patch('optimizely.helpers.audience.does_user_meet_audience_conditions', return_value=[True, []]), \
            mock.patch.object(self.decision_service.bucketer, 'bucket_to_entity_id',
                              return_value=[None, []]) as mock_bucket, \
            mock.patch.object(self.decision_service, 'cmab_service') as mock_cmab_service, \
            mock.patch.object(self.decision_service,
                              'logger') as mock_logger:

            # Call get_variation with the CMAB experiment
            variation_result = self.decision_service.get_variation(
                self.project_config,
                cmab_experiment,
                user,
                None
            )
            variation = variation_result['variation']
            cmab_uuid = variation_result['cmab_uuid']
            error = variation_result['error']
            reasons = variation_result['reasons']

            # Verify we get no variation and CMAB service wasn't called
            self.assertIsNone(variation)
            self.assertIsNone(cmab_uuid)
            self.assertStrictFalse(error)
            self.assertIn('User "test_user" not in CMAB experiment "cmab_experiment" due to traffic allocation.',
                          reasons)

            # Verify bucketer was called with correct arguments
            mock_bucket.assert_called_once_with(
                self.project_config,
                cmab_experiment,
                "test_user",
                "test_user"
            )

            # Verify CMAB service wasn't called since user is not in traffic allocation
            mock_cmab_service.get_decision.assert_not_called()

            # Verify logger was called
            mock_logger.info.assert_any_call('User "test_user" not in CMAB '
                                             'experiment "cmab_experiment" due to traffic allocation.')

    def test_get_variation_cmab_experiment_service_error(self):
        """Test get_variation with CMAB experiment when the CMAB service returns an error."""

        # Create a user context
        user = optimizely_user_context.OptimizelyUserContext(
            optimizely_client=None,
            logger=None,
            user_id="test_user",
            user_attributes={}
        )

        # Create a CMAB experiment
        cmab_experiment = entities.Experiment(
            '111150',
            'cmab_experiment',
            'Running',
            '111150',
            [],  # No audience IDs
            {},
            [entities.Variation('111151', 'variation_1')],
            [{'entityId': '111151', 'endOfRange': 10000}],
            cmab={'trafficAllocation': 5000}
        )

        with mock.patch('optimizely.helpers.experiment.is_experiment_running', return_value=True), \
            mock.patch('optimizely.helpers.audience.does_user_meet_audience_conditions', return_value=[True, []]), \
            mock.patch('optimizely.bucketer.Bucketer.bucket_to_entity_id', return_value=['$', []]), \
            mock.patch('optimizely.decision_service.DecisionService._get_decision_for_cmab_experiment',
                       return_value={'error': True, 'result': None, 'reasons': ['CMAB service error']}):

            # Call get_variation with the CMAB experiment
            variation_result = self.decision_service.get_variation(
                self.project_config,
                cmab_experiment,
                user,
                None
            )
            variation = variation_result['variation']
            cmab_uuid = variation_result['cmab_uuid']
            reasons = variation_result['reasons']
            error = variation_result['error']

            # Verify we get no variation due to CMAB service error
            self.assertIsNone(variation)
            self.assertIsNone(cmab_uuid)
            self.assertIn('CMAB service error', reasons)
            self.assertStrictTrue(error)

    def test_get_variation_cmab_experiment_forced_variation(self):
        """Test get_variation with CMAB experiment when user has a forced variation."""

        # Create a user context
        user = optimizely_user_context.OptimizelyUserContext(
            optimizely_client=None,
            logger=None,
            user_id="test_user",
            user_attributes={}
        )

        # Create a CMAB experiment
        cmab_experiment = entities.Experiment(
            '111150',
            'cmab_experiment',
            'Running',
            '111150',
            [],  # No audience IDs
            {},
            [
                entities.Variation('111151', 'variation_1'),
                entities.Variation('111152', 'variation_2')
            ],
            [
                {'entityId': '111151', 'endOfRange': 5000},
                {'entityId': '111152', 'endOfRange': 10000}
            ],
            cmab={'trafficAllocation': 5000}
        )

        forced_variation = entities.Variation('111152', 'variation_2')

        with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                        return_value=[forced_variation, ['User is forced into variation']]), \
            mock.patch('optimizely.bucketer.Bucketer.bucket_to_entity_id') as mock_bucket, \
            mock.patch('optimizely.decision_service.DecisionService._get_decision_for_cmab_experiment'
                       ) as mock_cmab_decision:

            # Call get_variation with the CMAB experiment
            variation_result = self.decision_service.get_variation(
                self.project_config,
                cmab_experiment,
                user,
                None
            )
            variation = variation_result['variation']
            reasons = variation_result['reasons']
            cmab_uuid = variation_result['cmab_uuid']
            error = variation_result['error']

            # Verify we get the forced variation
            self.assertEqual(forced_variation, variation)
            self.assertIsNone(cmab_uuid)
            self.assertIn('User is forced into variation', reasons)
            self.assertStrictFalse(error)

            # Verify CMAB-specific methods weren't called
            mock_bucket.assert_not_called()
            mock_cmab_decision.assert_not_called()

    def test_get_variation_cmab_experiment_with_whitelisted_variation(self):
        """Test get_variation with CMAB experiment when user has a whitelisted variation."""

        # Create a user context
        user = optimizely_user_context.OptimizelyUserContext(
            optimizely_client=None,
            logger=None,
            user_id="test_user",
            user_attributes={}
        )

        # Create a CMAB experiment with forced variations
        cmab_experiment = entities.Experiment(
            '111150',
            'cmab_experiment',
            'Running',
            '111150',
            [],  # No audience IDs
            {'test_user': 'variation_2'},
            [
                entities.Variation('111151', 'variation_1'),
                entities.Variation('111152', 'variation_2')
            ],
            [
                {'entityId': '111151', 'endOfRange': 5000},
                {'entityId': '111152', 'endOfRange': 10000}
            ],
            cmab={'trafficAllocation': 5000}
        )

        whitelisted_variation = entities.Variation('111152', 'variation_2')

        with mock.patch('optimizely.decision_service.DecisionService.get_forced_variation',
                        return_value=[None, []]), \
            mock.patch('optimizely.decision_service.DecisionService.get_whitelisted_variation',
                       return_value=[whitelisted_variation, ['User is whitelisted into variation']]), \
            mock.patch('optimizely.bucketer.Bucketer.bucket_to_entity_id') as mock_bucket, \
            mock.patch('optimizely.decision_service.DecisionService._get_decision_for_cmab_experiment'
                       ) as mock_cmab_decision:

            # Call get_variation with the CMAB experiment
            variation_result = self.decision_service.get_variation(
                self.project_config,
                cmab_experiment,
                user,
                None
            )
            variation = variation_result['variation']
            cmab_uuid = variation_result['cmab_uuid']
            reasons = variation_result['reasons']
            error = variation_result['error']

            # Verify we get the whitelisted variation
            self.assertEqual(whitelisted_variation, variation)
            self.assertIsNone(cmab_uuid)
            self.assertIn('User is whitelisted into variation', reasons)
            self.assertStrictFalse(error)

            # Verify CMAB-specific methods weren't called
            mock_bucket.assert_not_called()
            mock_cmab_decision.assert_not_called()

    def test_get_variation_cmab_experiment_does_not_save_user_profile(self):
        """Test that CMAB experiments do not save bucketing decisions to user profile."""

        # Create a user context
        user = optimizely_user_context.OptimizelyUserContext(
            optimizely_client=None,
            logger=None,
            user_id="test_user",
            user_attributes={}
        )

        # Create a user profile service and tracker
        user_profile_service = user_profile.UserProfileService()
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, user_profile_service)

        # Create a CMAB experiment
        cmab_experiment = entities.Experiment(
            '111150',
            'cmab_experiment',
            'Running',
            '111150',
            [],  # No audience IDs
            {},
            [
                entities.Variation('111151', 'variation_1'),
                entities.Variation('111152', 'variation_2')
            ],
            [
                {'entityId': '111151', 'endOfRange': 5000},
                {'entityId': '111152', 'endOfRange': 10000}
            ],
            cmab={'trafficAllocation': 5000}
        )

        with mock.patch('optimizely.helpers.experiment.is_experiment_running', return_value=True), \
            mock.patch('optimizely.helpers.audience.does_user_meet_audience_conditions', return_value=[True, []]), \
            mock.patch.object(self.decision_service.bucketer, 'bucket_to_entity_id',
                              return_value=['$', []]), \
            mock.patch.object(self.decision_service, 'cmab_service') as mock_cmab_service, \
            mock.patch.object(self.project_config, 'get_variation_from_id',
                              return_value=entities.Variation('111151', 'variation_1')), \
            mock.patch.object(user_profile_tracker, 'update_user_profile') as mock_update_profile, \
                mock.patch.object(self.decision_service, 'logger') as mock_logger:

            # Configure CMAB service to return a decision
            mock_cmab_service.get_decision.return_value = (
                {
                    'variation_id': '111151',
                    'cmab_uuid': 'test-cmab-uuid-123'
                },
                []  # reasons list
            )

            # Call get_variation with the CMAB experiment and user profile tracker
            variation_result = self.decision_service.get_variation(
                self.project_config,
                cmab_experiment,
                user,
                user_profile_tracker
            )
            variation = variation_result['variation']
            cmab_uuid = variation_result['cmab_uuid']

            # Verify the variation and cmab_uuid are returned
            self.assertEqual(entities.Variation('111151', 'variation_1'), variation)
            self.assertEqual('test-cmab-uuid-123', cmab_uuid)

            # Verify user profile was NOT updated for CMAB experiment
            mock_update_profile.assert_not_called()

            # Verify debug log was called to explain CMAB exclusion
            mock_logger.debug.assert_any_call(
                'Skipping user profile service for CMAB experiment "cmab_experiment". '
                'CMAB decisions are dynamic and not stored for sticky bucketing.'
            )

    def test_get_variation_standard_experiment_saves_user_profile(self):
        """Test that standard (non-CMAB) experiments DO save bucketing decisions to user profile."""

        user = optimizely_user_context.OptimizelyUserContext(
            optimizely_client=None,
            logger=None,
            user_id="test_user",
            user_attributes={}
        )

        # Create a user profile service and tracker
        user_profile_service = user_profile.UserProfileService()
        user_profile_tracker = user_profile.UserProfileTracker(user.user_id, user_profile_service)

        # Get a standard (non-CMAB) experiment
        experiment = self.project_config.get_experiment_from_key("test_experiment")

        with mock.patch('optimizely.decision_service.DecisionService.get_whitelisted_variation',
                        return_value=[None, []]), \
            mock.patch('optimizely.decision_service.DecisionService.get_stored_variation',
                       return_value=None), \
            mock.patch('optimizely.helpers.audience.does_user_meet_audience_conditions',
                       return_value=[True, []]), \
            mock.patch('optimizely.bucketer.Bucketer.bucket',
                       return_value=[entities.Variation("111129", "variation"), []]), \
                mock.patch.object(user_profile_tracker, 'update_user_profile') as mock_update_profile:

            # Call get_variation with standard experiment and user profile tracker
            variation_result = self.decision_service.get_variation(
                self.project_config,
                experiment,
                user,
                user_profile_tracker
            )
            variation = variation_result['variation']

            # Verify variation was returned
            self.assertEqual(entities.Variation("111129", "variation"), variation)

            # Verify user profile WAS updated for standard experiment
            mock_update_profile.assert_called_once_with(experiment, variation)


class FeatureFlagDecisionTests(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self)
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        self.project_config = opt_obj.config_manager.get_config()
        self.decision_service = opt_obj.decision_service
        self.mock_decision_logger = mock.patch.object(self.decision_service, "logger")
        self.mock_config_logger = mock.patch.object(self.project_config, "logger")

    def test_get_variation_for_rollout__returns_none_if_no_experiments(self):
        """ Test that get_variation_for_rollout returns None if there are no experiments (targeting rules).
            For this we assign None to the feature parameter.
            There is one rolloutId in the datafile that has no experiments associsted with it.
            rolloutId is tied to feature. That's why we make feature None which means there are no experiments.
        """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})

        with self.mock_config_logger as mock_logging:
            feature = None
            variation_received, _ = self.decision_service.get_variation_for_rollout(
                self.project_config, feature, user
            )

            self.assertEqual(
                decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT, None),
                variation_received,
            )

        # Assert no log messages were generated
        self.assertEqual(0, mock_logging.call_count)

    def test_get_variation_for_rollout__returns_decision_if_user_in_rollout(self):
        """ Test that get_variation_for_rollout returns Decision with experiment/variation
     if user meets targeting conditions for a rollout rule. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_rollout")

        with mock.patch(
                "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[True, []]
        ), self.mock_decision_logger as mock_decision_service_logging, mock.patch(
            "optimizely.bucketer.Bucketer.bucket",
            return_value=[self.project_config.get_variation_from_id("211127", "211129"), []],
        ) as mock_bucket:
            variation_received, _ = self.decision_service.get_variation_for_rollout(
                self.project_config, feature, user
            )
            self.assertEqual(
                decision_service.Decision(
                    self.project_config.get_experiment_from_id("211127"),
                    self.project_config.get_variation_from_id("211127", "211129"),
                    enums.DecisionSources.ROLLOUT,
                    None
                ),
                variation_received,
            )

        # Check all log messages
        mock_decision_service_logging.debug.assert_has_calls([
            mock.call('User "test_user" meets audience conditions for targeting rule 1.'),
            mock.call('User "test_user" bucketed into a targeting rule 1.')])

        # Check that bucket is called with correct parameters
        mock_bucket.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_id("211127"),
            "test_user",
            'test_user',
        )

    def test_get_variation_for_rollout__calls_bucket_with_bucketing_id(self):
        """ Test that get_variation_for_rollout calls Bucketer.bucket with bucketing ID when provided. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"$opt_bucketing_id": "user_bucket_value"})
        feature = self.project_config.get_feature_from_key("test_feature_in_rollout")

        with mock.patch(
                "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[True, []]
        ), self.mock_decision_logger as mock_decision_service_logging, mock.patch(
            "optimizely.bucketer.Bucketer.bucket",
            return_value=[self.project_config.get_variation_from_id("211127", "211129"), []],
        ) as mock_bucket:
            variation_received, _ = self.decision_service.get_variation_for_rollout(
                self.project_config,
                feature,
                user
            )
            self.assertEqual(
                decision_service.Decision(
                    self.project_config.get_experiment_from_id("211127"),
                    self.project_config.get_variation_from_id("211127", "211129"),
                    enums.DecisionSources.ROLLOUT,
                    None
                ),
                variation_received,
            )

        # Check all log messages
        mock_decision_service_logging.debug.assert_has_calls(
            [mock.call('User "test_user" meets audience conditions for targeting rule 1.')]
        )
        # Check that bucket is called with correct parameters
        mock_bucket.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_id("211127"),
            "test_user",
            'user_bucket_value'
        )

    def test_get_variation_for_rollout__skips_to_everyone_else_rule(self):
        """ Test that if a user is in an audience, but does not qualify
    for the experiment, then it skips to the Everyone Else rule. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_rollout")
        everyone_else_exp = self.project_config.get_experiment_from_id("211147")
        variation_to_mock = self.project_config.get_variation_from_id(
            "211147", "211149"
        )

        with mock.patch(
                "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[True, []]
        ) as mock_audience_check, self.mock_decision_logger as mock_decision_service_logging, mock.patch(
            "optimizely.bucketer.Bucketer.bucket", side_effect=[[None, []], [variation_to_mock, []]]
        ):
            variation_received, _ = self.decision_service.get_variation_for_rollout(
                self.project_config, feature, user
            )
            self.assertEqual(
                decision_service.Decision(
                    everyone_else_exp, variation_to_mock, enums.DecisionSources.ROLLOUT, None
                ),
                variation_received,
            )

        # Check that after first experiment, it skips to the last experiment to check
        self.assertEqual(
            [
                mock.call(
                    self.project_config,
                    self.project_config.get_experiment_from_key("211127").get_audience_conditions_or_ids(),
                    enums.RolloutRuleAudienceEvaluationLogs,
                    '1',
                    user,
                    mock_decision_service_logging,
                ),
                mock.call(
                    self.project_config,
                    self.project_config.get_experiment_from_key("211147").get_audience_conditions_or_ids(),
                    enums.RolloutRuleAudienceEvaluationLogs,
                    'Everyone Else',
                    user,
                    mock_decision_service_logging,
                ),
            ],
            mock_audience_check.call_args_list,
        )

        # Check all log messages
        mock_decision_service_logging.debug.assert_has_calls(
            [
                mock.call('User "test_user" meets audience conditions for targeting rule 1.'),
                mock.call('User "test_user" not bucketed into a targeting rule 1. Checking "Everyone Else" rule now.'),
                mock.call('User "test_user" meets audience conditions for targeting rule Everyone Else.'),
                mock.call('User "test_user" bucketed into a targeting rule Everyone Else.'),
            ]
        )

    def test_get_variation_for_rollout__returns_none_for_user_not_in_rollout(self):
        """ Test that get_variation_for_rollout returns None for the user not in the associated rollout. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_rollout")

        with mock.patch(
                "optimizely.helpers.audience.does_user_meet_audience_conditions", return_value=[False, []]
        ) as mock_audience_check, self.mock_decision_logger as mock_decision_service_logging:
            variation_received, _ = self.decision_service.get_variation_for_rollout(
                self.project_config, feature, user
            )
            self.assertEqual(
                decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT, None),
                variation_received,
            )

        # Check that all experiments in rollout layer were checked
        self.assertEqual(
            [
                mock.call(
                    self.project_config,
                    self.project_config.get_experiment_from_key("211127").get_audience_conditions_or_ids(),
                    enums.RolloutRuleAudienceEvaluationLogs,
                    "1",
                    user,
                    mock_decision_service_logging,
                ),
                mock.call(
                    self.project_config,
                    self.project_config.get_experiment_from_key("211137").get_audience_conditions_or_ids(),
                    enums.RolloutRuleAudienceEvaluationLogs,
                    "2",
                    user,
                    mock_decision_service_logging,
                ),
                mock.call(
                    self.project_config,
                    self.project_config.get_experiment_from_key("211147").get_audience_conditions_or_ids(),
                    enums.RolloutRuleAudienceEvaluationLogs,
                    "Everyone Else",
                    user,
                    mock_decision_service_logging,
                ),
            ],
            mock_audience_check.call_args_list,
        )

        # Check all log messages
        mock_decision_service_logging.debug.assert_has_calls(
            [
                mock.call(
                    'User "test_user" does not meet audience conditions for targeting rule 1.'
                ),
                mock.call(
                    'User "test_user" does not meet audience conditions for targeting rule 2.'
                ),
            ]
        )

    def test_get_variation_for_feature__returns_variation_for_feature_in_experiment(
            self,
    ):
        """ Test that get_variation_for_feature returns the variation
        of the experiment the feature is associated with. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_experiment")

        expected_experiment = self.project_config.get_experiment_from_key(
            "test_experiment"
        )
        expected_variation = self.project_config.get_variation_from_id(
            "test_experiment", "111129"
        )
        decision_patch = mock.patch(
            "optimizely.decision_service.DecisionService.get_variation",
            return_value={'variation': expected_variation, 'cmab_uuid': None, 'reasons': [], 'error': False},
        )
        with decision_patch as mock_decision, self.mock_decision_logger:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user, options=None
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                variation_received,
            )

        mock_decision.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_key("test_experiment"),
            user,
            None,
            [],
            None
        )

    def test_get_variation_for_feature__returns_variation_for_feature_in_rollout(self):
        """ Test that get_variation_for_feature returns the variation of
        the experiment in the rollout that the user is bucketed into. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_rollout")

        expected_variation = self.project_config.get_variation_from_id(
            "211127", "211129"
        )
        get_variation_for_rollout_patch = mock.patch(
            "optimizely.decision_service.DecisionService.get_variation_for_rollout",
            return_value=[expected_variation, None],
        )
        with get_variation_for_rollout_patch as mock_get_variation_for_rollout, \
                self.mock_decision_logger as mock_decision_service_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user, False
            )['decision']
            self.assertEqual(
                expected_variation,
                variation_received,
            )

        mock_get_variation_for_rollout.assert_called_once_with(
            self.project_config, feature, user
        )

        # Assert no log messages were generated
        self.assertEqual(1, mock_decision_service_logging.debug.call_count)
        self.assertEqual(1, len(mock_decision_service_logging.method_calls))

    def test_get_variation_for_feature__returns_variation_if_user_not_in_experiment_but_in_rollout(
            self,
    ):
        """ Test that get_variation_for_feature returns the variation of the experiment in the
            feature's rollout even if the user is not bucketed into the feature's experiment. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key(
            "test_feature_in_experiment_and_rollout"
        )

        expected_experiment = self.project_config.get_experiment_from_key("211127")
        expected_variation = self.project_config.get_variation_from_id(
            "211127", "211129"
        )
        with mock.patch(
                "optimizely.helpers.audience.does_user_meet_audience_conditions",
                side_effect=[[False, []], [True, []]],
        ) as mock_audience_check, \
                self.mock_decision_logger as mock_decision_service_logging, mock.patch(
                "optimizely.bucketer.Bucketer.bucket", return_value=[expected_variation, []]):
            decision = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.ROLLOUT,
                    None
                ),
                decision,
            )

        self.assertEqual(2, mock_audience_check.call_count)
        mock_audience_check.assert_any_call(
            self.project_config,
            self.project_config.get_experiment_from_key("group_exp_2").get_audience_conditions_or_ids(),
            enums.ExperimentAudienceEvaluationLogs,
            "group_exp_2",
            user,
            mock_decision_service_logging,
        )

        mock_audience_check.assert_any_call(
            self.project_config,
            self.project_config.get_experiment_from_key("211127").get_audience_conditions_or_ids(),
            enums.RolloutRuleAudienceEvaluationLogs,
            "1",
            user,
            mock_decision_service_logging,
        )

    def test_get_variation_for_feature__returns_variation_for_feature_in_group(self):
        """ Test that get_variation_for_feature returns the variation of
     the experiment the user is bucketed in the feature's group. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_group")

        expected_experiment = self.project_config.get_experiment_from_key("group_exp_1")
        expected_variation = self.project_config.get_variation_from_id(
            "group_exp_1", "28901"
        )
        with mock.patch(
                "optimizely.decision_service.DecisionService.get_variation",
                return_value={'variation': expected_variation, 'cmab_uuid': None, 'reasons': [], 'error': False},
        ) as mock_decision:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user, options=None
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                variation_received,
            )

        mock_decision.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_key("group_exp_1"),
            user,
            None,
            [],
            None
        )

    def test_get_variation_for_feature__returns_none_for_user_not_in_experiment(self):
        """ Test that get_variation_for_feature returns None for user not in the associated experiment. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_experiment")

        with mock.patch(
                "optimizely.decision_service.DecisionService.get_variation",
                return_value={'variation': None, 'cmab_uuid': None, 'reasons': [], 'error': False},
        ) as mock_decision:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT, None),
                variation_received,
            )

        mock_decision.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_key("test_experiment"),
            user,
            None,
            [],
            None
        )

    def test_get_variation_for_feature__returns_none_for_user_in_group_experiment_not_associated_with_feature(
            self,
    ):
        """ Test that if a user is in the mutex group but the experiment is
    not targeting a feature, then None is returned. """

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={})
        feature = self.project_config.get_feature_from_key("test_feature_in_group")
        with mock.patch(
                "optimizely.decision_service.DecisionService.get_variation",
                return_value={'variation': None, 'cmab_uuid': None, 'reasons': [], 'error': False},
        ) as mock_decision:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user, False
            )["decision"]
            self.assertEqual(
                decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT, None),
                variation_received,
            )

        mock_decision.assert_called_once_with(
            self.project_config, self.project_config.get_experiment_from_id("32222"), user, None, [], False
        )

    def test_get_variation_for_feature__returns_variation_for_feature_in_mutex_group_bucket_less_than_2500(
            self,
    ):
        """ Test that if a user is in the mutex group and the user bucket value should be less than 2500."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})
        feature = self.project_config.get_feature_from_key("test_feature_in_exclusion_group")
        expected_experiment = self.project_config.get_experiment_from_key("group_2_exp_1")
        expected_variation = self.project_config.get_variation_from_id(
            "group_2_exp_1", "38901"
        )
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=2400) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']

            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                variation_received,
            )

        mock_config_logging.debug.assert_called_with('Assigned bucket 2400 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with('test_user42222')

    def test_get_variation_for_feature__returns_variation_for_feature_in_mutex_group_bucket_range_2500_5000(
            self,
    ):
        """ Test that if a user is in the mutex group and the user bucket value should be equal to 2500
        or less than 5000."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})

        feature = self.project_config.get_feature_from_key("test_feature_in_exclusion_group")
        expected_experiment = self.project_config.get_experiment_from_key("group_2_exp_2")
        expected_variation = self.project_config.get_variation_from_id(
            "group_2_exp_2", "38905"
        )
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=4000) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                variation_received,
            )
        mock_config_logging.debug.assert_called_with('Assigned bucket 4000 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with('test_user42223')

    def test_get_variation_for_feature__returns_variation_for_feature_in_mutex_group_bucket_range_5000_7500(
            self,
    ):
        """ Test that if a user is in the mutex group and the user bucket value should be equal to 5000
        or less than 7500."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})
        feature = self.project_config.get_feature_from_key("test_feature_in_exclusion_group")
        expected_experiment = self.project_config.get_experiment_from_key("group_2_exp_3")
        expected_variation = self.project_config.get_variation_from_id(
            "group_2_exp_3", "38906"
        )

        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=6500) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:

            decision_result = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )
            decision_received = decision_result['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                decision_received,
            )
        mock_config_logging.debug.assert_called_with('Assigned bucket 6500 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with('test_user42224')

    def test_get_variation_for_feature__returns_variation_for_rollout_in_mutex_group_bucket_greater_than_7500(
            self,
    ):
        """ Test that if a user is in the mutex group and the user bucket value should be greater than  7500."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})
        feature = self.project_config.get_feature_from_key("test_feature_in_exclusion_group")

        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=8000) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']

            self.assertEqual(
                decision_service.Decision(
                    None,
                    None,
                    enums.DecisionSources.ROLLOUT,
                    None
                ),
                variation_received,
            )

        mock_generate_bucket_value.assert_called_with("test_user211147")
        mock_config_logging.debug.assert_called_with(
            'Assigned bucket 8000 to user with bucketing ID "test_user".')

    def test_get_variation_for_feature__returns_variation_for_feature_in_experiment_bucket_less_than_2500(
            self,
    ):
        """ Test that if a user is in the non-mutex group and the user bucket value should be less than 2500."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})
        feature = self.project_config.get_feature_from_key("test_feature_in_multiple_experiments")
        expected_experiment = self.project_config.get_experiment_from_key("test_experiment3")
        expected_variation = self.project_config.get_variation_from_id(
            "test_experiment3", "222239"
        )

        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=2400) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                variation_received,
            )
        mock_config_logging.debug.assert_called_with('Assigned bucket 2400 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with('test_user111134')

    def test_get_variation_for_feature__returns_variation_for_feature_in_experiment_bucket_range_2500_5000(
            self,
    ):
        """ Test that if a user is in the non-mutex group and the user bucket value should be equal to 2500
        or less than 5000."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})
        feature = self.project_config.get_feature_from_key("test_feature_in_multiple_experiments")
        expected_experiment = self.project_config.get_experiment_from_key("test_experiment4")
        expected_variation = self.project_config.get_variation_from_id(
            "test_experiment4", "222240"
        )
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=4000) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                variation_received,
            )
        mock_config_logging.debug.assert_called_with('Assigned bucket 4000 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with('test_user111135')

    def test_get_variation_for_feature__returns_variation_for_feature_in_experiment_bucket_range_5000_7500(
            self,
    ):
        """ Test that if a user is in the non-mutex group and the user bucket value should be equal to 5000
        or less than 7500."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})
        feature = self.project_config.get_feature_from_key("test_feature_in_multiple_experiments")
        expected_experiment = self.project_config.get_experiment_from_key("test_experiment5")
        expected_variation = self.project_config.get_variation_from_id(
            "test_experiment5", "222241"
        )

        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=6500) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.FEATURE_TEST,
                    None
                ),
                variation_received,
            )
        mock_config_logging.debug.assert_called_with('Assigned bucket 6500 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with('test_user111136')

    def test_get_variation_for_feature__returns_variation_for_rollout_in_experiment_bucket_greater_than_7500(
            self,
    ):
        """ Test that if a user is in the non-mutex group and the user bucket value should be greater than  7500."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={"experiment_attr": "group_experiment"})
        feature = self.project_config.get_feature_from_key("test_feature_in_multiple_experiments")

        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=8000) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    None,
                    None,
                    enums.DecisionSources.ROLLOUT,
                    None
                ),
                variation_received,
            )
        mock_generate_bucket_value.assert_called_with("test_user211147")
        mock_config_logging.debug.assert_called_with(
            'Assigned bucket 8000 to user with bucketing ID "test_user".')

    def test_get_variation_for_feature__returns_variation_for_rollout_in_mutex_group_audience_mismatch(
            self,
    ):
        """ Test that if a user is in the mutex group and the user bucket value should be less than 2500 and
        missing target by audience."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={
                                                                 "experiment_attr": "group_experiment_invalid"})
        feature = self.project_config.get_feature_from_key("test_feature_in_exclusion_group")
        expected_experiment = self.project_config.get_experiment_from_id("211147")
        expected_variation = self.project_config.get_variation_from_id(
            "211147", "211149"
        )
        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=2400) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.ROLLOUT,
                    None
                ),
                variation_received,
            )

        mock_config_logging.debug.assert_called_with(
            'Assigned bucket 2400 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with("test_user211147")

    def test_get_variation_for_feature_returns_rollout_in_experiment_bucket_range_2500_5000_audience_mismatch(
            self,
    ):
        """ Test that if a user is in the non-mutex group and the user bucket value should be equal to 2500
        or less than 5000 missing target by audience."""

        user = optimizely_user_context.OptimizelyUserContext(optimizely_client=None,
                                                             logger=None,
                                                             user_id="test_user",
                                                             user_attributes={
                                                                 "experiment_attr": "group_experiment_invalid"})
        feature = self.project_config.get_feature_from_key("test_feature_in_multiple_experiments")
        expected_experiment = self.project_config.get_experiment_from_id("211147")
        expected_variation = self.project_config.get_variation_from_id(
            "211147", "211149"
        )

        with mock.patch(
            'optimizely.bucketer.Bucketer._generate_bucket_value', return_value=4000) as mock_generate_bucket_value, \
                mock.patch.object(self.project_config, 'logger') as mock_config_logging:
            variation_received = self.decision_service.get_variation_for_feature(
                self.project_config, feature, user
            )['decision']
            self.assertEqual(
                decision_service.Decision(
                    expected_experiment,
                    expected_variation,
                    enums.DecisionSources.ROLLOUT,
                    None
                ),
                variation_received,
            )

        mock_config_logging.debug.assert_called_with(
            'Assigned bucket 4000 to user with bucketing ID "test_user".')
        mock_generate_bucket_value.assert_called_with("test_user211147")
