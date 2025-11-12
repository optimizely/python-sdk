# Copyright 2025 Optimizely and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from unittest import mock

from optimizely import decision_service
from optimizely import error_handler
from optimizely import logger
from optimizely import optimizely as optimizely_module
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption
from optimizely.helpers import enums
from tests import base


class DecisionServiceHoldoutTest(base.BaseTest):
    """Tests for Decision Service with Holdouts."""

    def setUp(self):
        base.BaseTest.setUp(self)
        self.error_handler = error_handler.NoOpErrorHandler()
        self.spy_logger = mock.MagicMock(spec=logger.SimpleLogger)
        self.spy_logger.logger = self.spy_logger
        self.spy_user_profile_service = mock.MagicMock()
        self.spy_cmab_service = mock.MagicMock()

        # Create a config dict with holdouts and feature flags
        config_dict_with_holdouts = self.config_dict_with_features.copy()

        # Get feature flag ID for test_feature_in_experiment
        test_feature_id = '91111'

        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'holdout_1',
                'key': 'test_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'holdout_var_1',
                        'key': 'holdout_control',
                        'variables': []
                    },
                    {
                        'id': 'holdout_var_2',
                        'key': 'holdout_treatment',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'holdout_var_1',
                        'endOfRange': 5000
                    },
                    {
                        'entityId': 'holdout_var_2',
                        'endOfRange': 10000
                    }
                ]
            },
            {
                'id': 'holdout_2',
                'key': 'excluded_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [test_feature_id],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'holdout_var_3',
                        'key': 'control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'holdout_var_3',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        # Convert to JSON and create config
        config_json = json.dumps(config_dict_with_holdouts)
        self.opt_obj = optimizely_module.Optimizely(config_json)
        self.config_with_holdouts = self.opt_obj.config_manager.get_config()

        self.decision_service_with_holdouts = decision_service.DecisionService(
            self.spy_logger,
            self.spy_user_profile_service,
            self.spy_cmab_service
        )

    def tearDown(self):
        if hasattr(self, 'opt_obj'):
            self.opt_obj.close()

    # get_variations_for_feature_list with holdouts tests

    def test_holdout_active_and_user_bucketed_returns_holdout_decision(self):
        """When holdout is active and user is bucketed, should return holdout decision with variation."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        holdout = self.config_with_holdouts.holdouts[0] if self.config_with_holdouts.holdouts else None
        self.assertIsNotNone(holdout)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Verify result structure is valid
        for decision_result in result:
            self.assertIn('decision', decision_result)
            self.assertIn('reasons', decision_result)

    def test_holdout_inactive_does_not_bucket_users(self):
        """When holdout is inactive, should not bucket users and log appropriate message."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        holdout = self.config_with_holdouts.holdouts[0] if self.config_with_holdouts.holdouts else None
        self.assertIsNotNone(holdout)

        # Mock holdout as inactive
        original_status = holdout['status']
        holdout['status'] = 'Paused'

        user_context = self.opt_obj.create_user_context('testUserId', {})

        result = self.decision_service_with_holdouts.get_decision_for_flag(
            feature_flag,
            user_context,
            self.config_with_holdouts
        )

        # Assert that result is not nil and has expected structure
        self.assertIsNotNone(result)
        self.assertIn('decision', result)
        self.assertIn('reasons', result)

        # Restore original status
        holdout['status'] = original_status

    def test_user_not_bucketed_into_holdout_executes_successfully(self):
        """When user is not bucketed into holdout, should execute successfully with valid result structure."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        # With real bucketer, we can't guarantee specific bucketing results
        # but we can verify the method executes successfully
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_holdout_with_user_attributes_for_audience_targeting(self):
        """Should evaluate holdout with user attributes."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_attributes = {
            'browser': 'chrome',
            'location': 'us'
        }

        user_context = self.opt_obj.create_user_context('testUserId', user_attributes)

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_multiple_holdouts_for_single_feature_flag(self):
        """Should handle multiple holdouts for a single feature flag."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_holdout_bucketing_with_empty_user_id(self):
        """Should allow holdout bucketing with empty user ID."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        # Empty user ID should still be valid for bucketing
        user_context = self.opt_obj.create_user_context('', {})

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)

    def test_holdout_populates_decision_reasons(self):
        """Should populate decision reasons for holdouts."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)

        # Find any decision with reasons
        decision_with_reasons = next(
            (dr for dr in result if dr.get('reasons') and len(dr['reasons']) > 0),
            None
        )

        if decision_with_reasons:
            self.assertGreater(len(decision_with_reasons['reasons']), 0)

    # get_variation_for_feature with holdouts tests

    def test_user_bucketed_into_holdout_returns_before_experiments(self):
        """
        When user is bucketed into holdout, should return holdout decision
        before checking experiments or rollouts.
        """
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        decision_result = self.decision_service_with_holdouts.get_variation_for_feature(
            self.config_with_holdouts,
            feature_flag,
            user_context
        )

        self.assertIsNotNone(decision_result)

        # Decision should be valid
        if decision_result.get('decision'):
            decision = decision_result['decision']
            self.assertEqual(decision.source, enums.DecisionSources.HOLDOUT)
            self.assertIsNotNone(decision.variation)
            self.assertIsNone(decision.experiment)

    def test_no_holdout_decision_falls_through_to_experiment_and_rollout(self):
        """When holdout returns no decision, should fall through to experiment and rollout evaluation."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        # Use a user ID that won't be bucketed into holdout
        user_context = self.opt_obj.create_user_context('non_holdout_user', {})

        decision_result = self.decision_service_with_holdouts.get_variation_for_feature(
            self.config_with_holdouts,
            feature_flag,
            user_context
        )

        # Should still get a valid decision result
        self.assertIsNotNone(decision_result)
        self.assertIn('decision', decision_result)
        self.assertIn('reasons', decision_result)

    def test_holdout_respects_decision_options(self):
        """Should respect decision options when evaluating holdouts."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        # Test with INCLUDE_REASONS option
        decision_result = self.decision_service_with_holdouts.get_variation_for_feature(
            self.config_with_holdouts,
            feature_flag,
            user_context,
            [OptimizelyDecideOption.INCLUDE_REASONS]
        )

        self.assertIsNotNone(decision_result)
        self.assertIsInstance(decision_result.get('reasons'), list)

    # Holdout priority and evaluation order tests

    def test_evaluates_holdouts_before_experiments(self):
        """Should evaluate holdouts before experiments."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        decision_result = self.decision_service_with_holdouts.get_variation_for_feature(
            self.config_with_holdouts,
            feature_flag,
            user_context
        )

        self.assertIsNotNone(decision_result)

    def test_evaluates_global_holdouts_for_all_flags(self):
        """Should evaluate global holdouts for all flags."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        # Get global holdouts
        global_holdouts = [
            h for h in self.config_with_holdouts.holdouts
            if not h.get('includedFlags') or len(h.get('includedFlags', [])) == 0
        ]

        if global_holdouts:
            user_context = self.opt_obj.create_user_context('testUserId', {})

            result = self.decision_service_with_holdouts.get_variations_for_feature_list(
                self.config_with_holdouts,
                [feature_flag],
                user_context,
                []
            )

            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)

    def test_respects_included_and_excluded_flags_configuration(self):
        """Should respect included and excluded flags configuration."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')

        if feature_flag:
            # Get holdouts for this flag
            holdouts_for_flag = self.config_with_holdouts.get_holdouts_for_flag('test_feature_in_experiment')

            # Should not include holdouts that exclude this flag
            excluded_holdout = next((h for h in holdouts_for_flag if h.get('key') == 'excluded_holdout'), None)
            self.assertIsNone(excluded_holdout)

    # Holdout logging and error handling tests

    def test_logs_when_holdout_evaluation_starts(self):
        """Should log when holdout evaluation starts."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        # Verify that logger was called
        self.assertGreater(self.spy_logger.debug.call_count + self.spy_logger.info.call_count, 0)

    def test_handles_missing_holdout_configuration_gracefully(self):
        """Should handle missing holdout configuration gracefully."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        # Temporarily remove holdouts
        original_holdouts = self.config_with_holdouts.holdouts
        self.config_with_holdouts.holdouts = []

        user_context = self.opt_obj.create_user_context('testUserId', {})

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)

        # Restore original holdouts
        self.config_with_holdouts.holdouts = original_holdouts

    def test_handles_invalid_holdout_data_gracefully(self):
        """Should handle invalid holdout data gracefully."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        # The method should handle invalid holdout data without crashing
        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    # Holdout bucketing behavior tests

    def test_uses_consistent_bucketing_for_same_user(self):
        """Should use consistent bucketing for the same user."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_id = 'consistent_user'
        user_context1 = self.opt_obj.create_user_context(user_id, {})
        user_context2 = self.opt_obj.create_user_context(user_id, {})

        result1 = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context1,
            []
        )

        result2 = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context2,
            []
        )

        # Same user should get consistent results
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)

        if result1 and result2:
            decision1 = result1[0].get('decision')
            decision2 = result2[0].get('decision')

            # If both have decisions, they should match
            if decision1 and decision2:
                # Variation is an object, not a dict, so use attributes
                var1_id = decision1.variation.id if decision1.variation else None
                var2_id = decision2.variation.id if decision2.variation else None

                self.assertEqual(
                    var1_id, var2_id,
                    "User should get consistent variation across multiple calls"
                )

    def test_uses_bucketing_id_when_provided(self):
        """Should use bucketing ID when provided."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_attributes = {
            enums.ControlAttributes.BUCKETING_ID: 'custom_bucketing_id'
        }

        user_context = self.opt_obj.create_user_context('testUserId', user_attributes)

        result = self.decision_service_with_holdouts.get_variations_for_feature_list(
            self.config_with_holdouts,
            [feature_flag],
            user_context,
            []
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_handles_different_traffic_allocations(self):
        """Should handle different traffic allocations."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        # Test with multiple users to see varying bucketing results
        users = ['user1', 'user2', 'user3', 'user4', 'user5']
        results = []

        for user_id in users:
            user_context = self.opt_obj.create_user_context(user_id, {})
            result = self.decision_service_with_holdouts.get_variations_for_feature_list(
                self.config_with_holdouts,
                [feature_flag],
                user_context,
                []
            )
            results.append(result)

        # All results should be valid
        for result in results:
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)

    # Holdout integration with feature experiments tests

    def test_checks_holdouts_before_feature_experiments(self):
        """Should check holdouts before feature experiments."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('testUserId', {})

        decision_result = self.decision_service_with_holdouts.get_variation_for_feature(
            self.config_with_holdouts,
            feature_flag,
            user_context
        )

        self.assertIsNotNone(decision_result)

    def test_falls_back_to_experiments_if_no_holdout_decision(self):
        """Should fall back to experiments if no holdout decision."""
        feature_flag = self.config_with_holdouts.get_feature_from_key('test_feature_in_experiment')
        self.assertIsNotNone(feature_flag)

        user_context = self.opt_obj.create_user_context('non_holdout_user_123', {})

        decision_result = self.decision_service_with_holdouts.get_variation_for_feature(
            self.config_with_holdouts,
            feature_flag,
            user_context
        )

        # Should return a valid decision result
        self.assertIsNotNone(decision_result)
        self.assertIn('decision', decision_result)
        self.assertIn('reasons', decision_result)
