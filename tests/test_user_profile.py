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
