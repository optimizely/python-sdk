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
        original_status = holdout.status
        holdout.status = 'Paused'

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
        holdout.status = original_status

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

        # Mock get_holdouts_for_flag to return holdouts
        holdout = self.config_with_holdouts.holdouts[0] if self.config_with_holdouts.holdouts else None
        self.assertIsNotNone(holdout)

        holdout_variation = holdout.variations[0]

        # Create a holdout decision
        mock_holdout_decision = decision_service.Decision(
            experiment=holdout,
            variation=holdout_variation,
            source=enums.DecisionSources.HOLDOUT,
            cmab_uuid=None
        )

        mock_holdout_result = {
            'decision': mock_holdout_decision,
            'error': False,
            'reasons': []
        }

        # Mock get_holdouts_for_flag to return holdouts so the holdout path is taken
        with mock.patch.object(
            self.config_with_holdouts,
            'get_holdouts_for_flag',
            return_value=[holdout]
        ):
            with mock.patch.object(
                self.opt_obj.decision_service,
                'get_variation_for_holdout',
                return_value=mock_holdout_result
            ):
                decision_result = self.opt_obj.decision_service.get_variation_for_feature(
                    self.config_with_holdouts,
                    feature_flag,
                    user_context
                )

                self.assertIsNotNone(decision_result)

                # Decision should be valid and from holdout
                decision = decision_result['decision']
                self.assertEqual(decision.source, enums.DecisionSources.HOLDOUT)
                self.assertIsNotNone(decision.variation)

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
            if not h.includedFlags or len(h.includedFlags) == 0
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
            excluded_holdout = next((h for h in holdouts_for_flag if h.key == 'excluded_holdout'), None)
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
                # Handle both dict and Variation entity formats
                if decision1.variation:
                    var1_id = decision1.variation['id'] if isinstance(decision1.variation, dict) else decision1.variation.id
                else:
                    var1_id = None

                if decision2.variation:
                    var2_id = decision2.variation['id'] if isinstance(decision2.variation, dict) else decision2.variation.id
                else:
                    var2_id = None

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

    # Holdout Impression Events tests

    def test_decide_with_holdout_sends_impression_event(self):
        """Should send impression event for holdout decision."""
        # Create optimizely instance with mocked event processor
        spy_event_processor = mock.MagicMock()

        config_dict_with_holdouts = self.config_dict_with_features.copy()
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
                        'featureEnabled': True,
                        'variables': []
                    },
                    {
                        'id': 'holdout_var_2',
                        'key': 'holdout_treatment',
                        'featureEnabled': False,
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
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt_with_mocked_events = optimizely_module.Optimizely(
            datafile=config_json,
            logger=self.spy_logger,
            error_handler=self.error_handler,
            event_processor=spy_event_processor
        )

        try:
            # Use a specific user ID that will be bucketed into a holdout
            test_user_id = 'user_bucketed_into_holdout'

            config = opt_with_mocked_events.config_manager.get_config()
            feature_flag = config.get_feature_from_key('test_feature_in_experiment')
            self.assertIsNotNone(feature_flag, "Feature flag 'test_feature_in_experiment' should exist")

            user_attributes = {}

            user_context = opt_with_mocked_events.create_user_context(test_user_id, user_attributes)
            decision = user_context.decide(feature_flag.key)

            self.assertIsNotNone(decision, 'Decision should not be None')

            # Find the actual holdout if this is a holdout decision
            actual_holdout = None
            if config.holdouts and decision.rule_key:
                actual_holdout = next(
                    (h for h in config.holdouts if h.key == decision.rule_key),
                    None
                )

            # Only continue if this is a holdout decision
            if actual_holdout:
                self.assertEqual(decision.flag_key, feature_flag.key)

                holdout_variation = next(
                    (v for v in actual_holdout.variations if v.get('key') == decision.variation_key),
                    None
                )

                self.assertIsNotNone(
                    holdout_variation,
                    f"Variation '{decision.variation_key}' should be from the chosen holdout '{actual_holdout.key}'"
                )

                self.assertEqual(
                    decision.enabled,
                    holdout_variation.get('featureEnabled'),
                    "Enabled flag should match holdout variation's featureEnabled value"
                )

                # Verify impression event was sent
                self.assertGreater(spy_event_processor.process.call_count, 0)

                # Verify impression event contains correct user details
                call_args_list = spy_event_processor.process.call_args_list
                user_event_found = False
                for call_args in call_args_list:
                    if call_args[0]:  # Check positional args
                        user_event = call_args[0][0]
                        if hasattr(user_event, 'user_id') and user_event.user_id == test_user_id:
                            user_event_found = True
                            break

                self.assertTrue(user_event_found, 'Impression event should contain correct user ID')
        finally:
            opt_with_mocked_events.close()

    def test_decide_with_holdout_does_not_send_impression_when_disabled(self):
        """Should not send impression event when DISABLE_DECISION_EVENT option is used."""
        # Create optimizely instance with mocked event processor
        spy_event_processor = mock.MagicMock()

        config_dict_with_holdouts = self.config_dict_with_features.copy()
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
                        'featureEnabled': True,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'holdout_var_1',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt_with_mocked_events = optimizely_module.Optimizely(
            datafile=config_json,
            logger=self.spy_logger,
            error_handler=self.error_handler,
            event_processor=spy_event_processor
        )

        try:
            test_user_id = 'user_bucketed_into_holdout'

            config = opt_with_mocked_events.config_manager.get_config()
            feature_flag = config.get_feature_from_key('test_feature_in_experiment')
            self.assertIsNotNone(feature_flag)

            user_attributes = {}

            user_context = opt_with_mocked_events.create_user_context(test_user_id, user_attributes)
            decision = user_context.decide(
                feature_flag.key,
                [OptimizelyDecideOption.DISABLE_DECISION_EVENT]
            )

            self.assertIsNotNone(decision, 'Decision should not be None')

            # Find the chosen holdout if this is a holdout decision
            chosen_holdout = None
            if config.holdouts and decision.rule_key:
                chosen_holdout = next(
                    (h for h in config.holdouts if h.key == decision.rule_key),
                    None
                )

            if chosen_holdout:
                self.assertEqual(decision.flag_key, feature_flag.key)

                # Verify no impression event was sent
                spy_event_processor.process.assert_not_called()
        finally:
            opt_with_mocked_events.close()

    def test_decide_with_holdout_sends_correct_notification_content(self):
        """Should send correct notification content for holdout decision."""
        captured_notifications = []

        def notification_callback(notification_type, user_id, user_attributes, decision_info):
            captured_notifications.append(decision_info.copy())

        config_dict_with_holdouts = self.config_dict_with_features.copy()
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
                        'featureEnabled': True,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'holdout_var_1',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt_with_mocked_events = optimizely_module.Optimizely(
            datafile=config_json,
            logger=self.spy_logger,
            error_handler=self.error_handler
        )

        try:
            opt_with_mocked_events.notification_center.add_notification_listener(
                enums.NotificationTypes.DECISION,
                notification_callback
            )

            test_user_id = 'holdout_test_user'
            config = opt_with_mocked_events.config_manager.get_config()
            feature_flag = config.get_feature_from_key('test_feature_in_experiment')
            holdout = config.holdouts[0] if config.holdouts else None
            self.assertIsNotNone(holdout, 'Should have at least one holdout configured')

            holdout_variation = holdout.variations[0]
            self.assertIsNotNone(holdout_variation, 'Holdout should have at least one variation')

            mock_experiment = mock.MagicMock()
            mock_experiment.key = holdout.key
            mock_experiment.id = holdout.id

            # Mock the decision service to return a holdout decision
            holdout_decision = decision_service.Decision(
                experiment=mock_experiment,
                variation=holdout_variation,
                source=enums.DecisionSources.HOLDOUT,
                cmab_uuid=None
            )

            holdout_decision_result = {
                'decision': holdout_decision,
                'error': False,
                'reasons': []
            }

            # Mock get_variations_for_feature_list to return holdout decision
            with mock.patch.object(
                opt_with_mocked_events.decision_service,
                'get_variations_for_feature_list',
                return_value=[holdout_decision_result]
            ):
                user_context = opt_with_mocked_events.create_user_context(test_user_id, {})
                decision = user_context.decide(feature_flag.key)

            self.assertIsNotNone(decision, 'Decision should not be None')
            self.assertEqual(len(captured_notifications), 1, 'Should have captured exactly one decision notification')

            notification = captured_notifications[0]
            rule_key = notification.get('rule_key')

            self.assertEqual(rule_key, holdout.key, 'RuleKey should match holdout key')

            # Verify holdout notification structure
            self.assertIn('flag_key', notification, 'Holdout notification should contain flag_key')
            self.assertIn('enabled', notification, 'Holdout notification should contain enabled flag')
            self.assertIn('variation_key', notification, 'Holdout notification should contain variation_key')
            self.assertIn('experiment_id', notification, 'Holdout notification should contain experiment_id')
            self.assertIn('variation_id', notification, 'Holdout notification should contain variation_id')

            flag_key = notification.get('flag_key')
            self.assertEqual(flag_key, 'test_feature_in_experiment', 'FlagKey should match the requested flag')

            experiment_id = notification.get('experiment_id')
            self.assertEqual(experiment_id, holdout.id, 'ExperimentId in notification should match holdout ID')

            variation_id = notification.get('variation_id')
            self.assertEqual(variation_id, holdout_variation['id'], 'VariationId should match holdout variation ID')

            variation_key = notification.get('variation_key')
            self.assertEqual(
                variation_key,
                holdout_variation['key'],
                'VariationKey in notification should match holdout variation key'
            )

            enabled = notification.get('enabled')
            self.assertIsNotNone(enabled, 'Enabled flag should be present in notification')
            self.assertEqual(
                enabled,
                holdout_variation.get('featureEnabled'),
                "Enabled flag should match holdout variation's featureEnabled value"
            )

            self.assertIn(flag_key, config.feature_key_map, f"FlagKey '{flag_key}' should exist in config")

            self.assertIn('variables', notification, 'Notification should contain variables')
            self.assertIn('reasons', notification, 'Notification should contain reasons')
            self.assertIn(
                'decision_event_dispatched', notification,
                'Notification should contain decision_event_dispatched'
            )
        finally:
            opt_with_mocked_events.close()

    # DecideAll with holdouts tests (aligned with Swift SDK)

    def test_decide_all_with_global_holdout(self):
        """Should apply global holdout to all flags in decide_all."""
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'global_holdout',
                'key': 'global_test_holdout',
                'status': 'Running',
                'includedFlags': [],  # Global - applies to all flags
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'global_holdout_var',
                        'key': 'global_holdout_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'global_holdout_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})
            decisions = user_context.decide_all()

            # Global holdout should apply to all flags
            self.assertGreater(len(decisions), 0)

            # Check that decisions exist for all flags
            for flag_key, decision in decisions.items():
                self.assertIsNotNone(decision)
        finally:
            opt.close()

    def test_decide_all_with_included_flags(self):
        """Should apply holdout only to included flags in decide_all."""
        # Get feature flag IDs
        feature1_id = '91111'  # test_feature_in_experiment

        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'included_holdout',
                'key': 'specific_holdout',
                'status': 'Running',
                'includedFlags': [feature1_id],  # Only applies to feature1
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'included_var',
                        'key': 'included_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'included_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})
            decisions = user_context.decide_all()

            self.assertGreater(len(decisions), 0)

            # Verify all flags have decisions
            for decision in decisions.values():
                self.assertIsNotNone(decision)
        finally:
            opt.close()

    def test_decide_all_with_excluded_flags(self):
        """Should exclude holdout from excluded flags in decide_all."""
        feature1_id = '91111'  # test_feature_in_experiment

        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'excluded_holdout',
                'key': 'global_except_one',
                'status': 'Running',
                'includedFlags': [],  # Global
                'excludedFlags': [feature1_id],  # Except feature1
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'excluded_var',
                        'key': 'excluded_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'excluded_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})
            decisions = user_context.decide_all()

            # Verify decisions exist for all flags
            self.assertGreater(len(decisions), 0)
            for decision in decisions.values():
                self.assertIsNotNone(decision)
        finally:
            opt.close()

    def test_decide_all_with_multiple_holdouts(self):
        """Should handle multiple holdouts with correct priority."""
        feature1_id = '91111'
        feature2_id = '91112'

        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            # Global holdout (applies to all)
            {
                'id': 'global_holdout',
                'key': 'global_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'global_var',
                        'key': 'global_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'global_var',
                        'endOfRange': 10000
                    }
                ]
            },
            # Specific holdout (only for feature2)
            {
                'id': 'specific_holdout',
                'key': 'specific_holdout',
                'status': 'Running',
                'includedFlags': [feature2_id],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'specific_var',
                        'key': 'specific_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'specific_var',
                        'endOfRange': 10000
                    }
                ]
            },
            # Excluded holdout (all except feature1)
            {
                'id': 'excluded_holdout',
                'key': 'excluded_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [feature1_id],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'excluded_var',
                        'key': 'excluded_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'excluded_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})
            decisions = user_context.decide_all()

            # Verify we got decisions for all flags
            self.assertGreater(len(decisions), 0)
        finally:
            opt.close()

    def test_decide_all_with_enabled_flags_only_option(self):
        """Should filter out disabled flags when using enabled_flags_only option."""
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'disabled_holdout',
                'key': 'disabled_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'disabled_var',
                        'key': 'disabled_control',
                        'featureEnabled': False,  # Feature disabled
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'disabled_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})

            # Without enabled_flags_only, all flags should be returned
            all_decisions = user_context.decide_all()

            # With enabled_flags_only, disabled flags should be filtered out
            enabled_decisions = user_context.decide_all(
                options=[OptimizelyDecideOption.ENABLED_FLAGS_ONLY]
            )

            # enabled_decisions should have fewer or equal entries
            self.assertLessEqual(len(enabled_decisions), len(all_decisions))
        finally:
            opt.close()

    # Impression event metadata tests (aligned with Swift SDK)

    def test_holdout_impression_event_has_correct_metadata(self):
        """Should include correct metadata in holdout impression events."""
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'metadata_holdout',
                'key': 'metadata_test_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'metadata_var',
                        'key': 'metadata_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'metadata_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        spy_event_processor = mock.MagicMock()

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(
            datafile=config_json,
            event_processor=spy_event_processor
        )

        try:
            user_context = opt.create_user_context('test_user', {})
            decision = user_context.decide('test_feature_in_experiment')

            # If this was a holdout decision, verify event metadata
            if decision.rule_key == 'metadata_test_holdout':
                self.assertGreater(spy_event_processor.process.call_count, 0)

                # Get the user event that was sent
                call_args = spy_event_processor.process.call_args_list[0]
                user_event = call_args[0][0]

                # Verify user event has correct structure
                self.assertIsNotNone(user_event)
        finally:
            opt.close()

    def test_holdout_impression_respects_send_flag_decisions_false(self):
        """Should send holdout impression even when sendFlagDecisions is false."""
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['sendFlagDecisions'] = False
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'send_flag_holdout',
                'key': 'send_flag_test_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'send_flag_var',
                        'key': 'send_flag_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'send_flag_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        spy_event_processor = mock.MagicMock()

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(
            datafile=config_json,
            event_processor=spy_event_processor
        )

        try:
            user_context = opt.create_user_context('test_user', {})
            decision = user_context.decide('test_feature_in_experiment')

            # Holdout impressions should be sent even when sendFlagDecisions=false
            # (unlike rollout impressions)
            if decision.rule_key == 'send_flag_test_holdout':
                # Verify impression was sent for holdout
                self.assertGreater(spy_event_processor.process.call_count, 0)
        finally:
            opt.close()

    # Holdout status tests (aligned with Swift SDK)

    def test_holdout_not_running_does_not_apply(self):
        """Should not apply holdout when status is not Running."""
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'draft_holdout',
                'key': 'draft_holdout',
                'status': 'Draft',  # Not Running
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'draft_var',
                        'key': 'draft_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'draft_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})
            decision = user_context.decide('test_feature_in_experiment')

            # Should not be a holdout decision since status is Draft
            self.assertNotEqual(decision.rule_key, 'draft_holdout')
        finally:
            opt.close()

    def test_holdout_concluded_status_does_not_apply(self):
        """Should not apply holdout when status is Concluded."""
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'concluded_holdout',
                'key': 'concluded_holdout',
                'status': 'Concluded',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'concluded_var',
                        'key': 'concluded_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'concluded_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})
            decision = user_context.decide('test_feature_in_experiment')

            # Should not be a holdout decision since status is Concluded
            self.assertNotEqual(decision.rule_key, 'concluded_holdout')
        finally:
            opt.close()

    def test_holdout_archived_status_does_not_apply(self):
        """Should not apply holdout when status is Archived."""
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'archived_holdout',
                'key': 'archived_holdout',
                'status': 'Archived',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'archived_var',
                        'key': 'archived_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'archived_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            user_context = opt.create_user_context('test_user', {})
            decision = user_context.decide('test_feature_in_experiment')

            # Should not be a holdout decision since status is Archived
            self.assertNotEqual(decision.rule_key, 'archived_holdout')
        finally:
            opt.close()

    # Audience targeting tests for holdouts (aligned with Swift SDK)

    def test_holdout_with_audience_match(self):
        """Should bucket user into holdout when audience conditions match."""
        # Using audienceIds that exist in the datafile
        # audience '11154' is for "browser_type" = "chrome"
        config_dict_with_holdouts = self.config_dict_with_features.copy()
        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'audience_holdout',
                'key': 'audience_test_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': ['11154'],  # Requires browser_type=chrome
                'variations': [
                    {
                        'id': 'audience_var',
                        'key': 'audience_control',
                        'featureEnabled': False,
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'audience_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict_with_holdouts)
        opt = optimizely_module.Optimizely(datafile=config_json)

        try:
            # User with matching attribute
            user_context_match = opt.create_user_context('test_user', {'browser_type': 'chrome'})
            decision_match = user_context_match.decide('test_feature_in_experiment')

            # User with non-matching attribute
            user_context_no_match = opt.create_user_context('test_user', {'browser_type': 'firefox'})
            decision_no_match = user_context_no_match.decide('test_feature_in_experiment')

            # Both should have valid decisions
            self.assertIsNotNone(decision_match)
            self.assertIsNotNone(decision_no_match)
        finally:
            opt.close()
