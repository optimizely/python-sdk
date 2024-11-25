# Copyright 2017, Optimizely
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

import unittest

from optimizely import user_profile
from unittest import mock


class UserProfileTest(unittest.TestCase):
    def setUp(self):
        user_id = 'test_user'
        experiment_bucket_map = {'199912': {'variation_id': '14512525'}}

        self.profile = user_profile.UserProfile(user_id, experiment_bucket_map=experiment_bucket_map)

    def test_get_variation_for_experiment__decision_exists(self):
        """ Test that variation ID is retrieved correctly if a decision exists in the experiment bucket map. """

        self.assertEqual('14512525', self.profile.get_variation_for_experiment('199912'))

    def test_get_variation_for_experiment__no_decision_exists(self):
        """ Test that None is returned if no decision exists in the experiment bucket map. """

        self.assertIsNone(self.profile.get_variation_for_experiment('199924'))

    def test_set_variation_for_experiment__no_previous_decision(self):
        """ Test that decision for new experiment/variation is stored correctly. """

        self.profile.save_variation_for_experiment('1993412', '118822')
        self.assertEqual(
            {'199912': {'variation_id': '14512525'}, '1993412': {'variation_id': '118822'}},
            self.profile.experiment_bucket_map,
        )

    def test_set_variation_for_experiment__previous_decision_available(self):
        """ Test that decision for is updated correctly if new experiment/variation combination is available. """

        self.profile.save_variation_for_experiment('199912', '1224525')
        self.assertEqual({'199912': {'variation_id': '1224525'}}, self.profile.experiment_bucket_map)


class UserProfileServiceTest(unittest.TestCase):
    def test_lookup(self):
        """ Test that lookup returns user profile in expected format. """

        user_profile_service = user_profile.UserProfileService()
        self.assertEqual(
            {'user_id': 'test_user', 'experiment_bucket_map': {}}, user_profile_service.lookup('test_user'),
        )

    def test_save(self):
        """ Test that nothing happens on calling save. """

        user_profile_service = user_profile.UserProfileService()
        self.assertIsNone(user_profile_service.save({'user_id': 'test_user', 'experiment_bucket_map': {}}))


class UserProfileTrackerTest(unittest.TestCase):
    def test_load_user_profile_failure(self):
        """Test that load_user_profile handles exceptions gracefully."""
        mock_user_profile_service = mock.MagicMock()
        mock_logger = mock.MagicMock()

        user_profile_tracker = user_profile.UserProfileTracker(
            user_id="test_user",
            user_profile_service=mock_user_profile_service,
            logger=mock_logger
        )
        mock_user_profile_service.lookup.side_effect = Exception("Lookup failure")

        user_profile_tracker.load_user_profile()

        # Verify that the logger recorded the exception
        mock_logger.exception.assert_called_once_with(
            'Unable to retrieve user profile for user "test_user" as lookup failed.'
        )

        # Verify that the user profile is reset to an empty profile
        self.assertEqual(user_profile_tracker.user_profile.user_id, "test_user")
        self.assertEqual(user_profile_tracker.user_profile.experiment_bucket_map, {})

    def test_load_user_profile__user_profile_invalid(self):
        """Test that load_user_profile handles an invalid user profile format."""
        mock_user_profile_service = mock.MagicMock()
        mock_logger = mock.MagicMock()

        user_profile_tracker = user_profile.UserProfileTracker(
            user_id="test_user",
            user_profile_service=mock_user_profile_service,
            logger=mock_logger
        )

        mock_user_profile_service.lookup.return_value = {"invalid_key": "value"}

        reasons = []
        user_profile_tracker.load_user_profile(reasons=reasons)

        # Verify that the logger recorded a warning for the missing keys
        missing_keys_message = "User profile is missing keys: user_id, experiment_bucket_map"
        self.assertIn(missing_keys_message, reasons)

        # Ensure the logger logs the invalid format
        mock_logger.info.assert_not_called()
        self.assertEqual(user_profile_tracker.user_profile.user_id, "test_user")
        self.assertEqual(user_profile_tracker.user_profile.experiment_bucket_map, {})

        # Verify the reasons list was updated
        self.assertIn(missing_keys_message, reasons)

    def test_save_user_profile_failure(self):
        """Test that save_user_profile handles exceptions gracefully."""
        mock_user_profile_service = mock.MagicMock()
        mock_logger = mock.MagicMock()

        user_profile_tracker = user_profile.UserProfileTracker(
            user_id="test_user",
            user_profile_service=mock_user_profile_service,
            logger=mock_logger
        )

        user_profile_tracker.profile_updated = True
        mock_user_profile_service.save.side_effect = Exception("Save failure")

        user_profile_tracker.save_user_profile()

        mock_logger.warning.assert_called_once_with(
            'Failed to save user profile of user "test_user" for exception:Save failure".'
        )
