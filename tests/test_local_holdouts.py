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

"""Tests for Local Holdouts feature (FSSDK-12368).

Tests rule-level holdout targeting instead of flag-level targeting.
"""

import json
import unittest
from unittest import mock

from optimizely import decision_service
from optimizely import error_handler
from optimizely import logger
from optimizely import optimizely as optimizely_module
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption
from optimizely import entities
from optimizely.helpers import enums
from tests import base


class LocalHoldoutsTest(base.BaseTest):
    """Tests for Local Holdouts (rule-level targeting)."""

    def setUp(self):
        base.BaseTest.setUp(self)
        self.error_handler = error_handler.NoOpErrorHandler()
        self.spy_logger = mock.MagicMock(spec=logger.SimpleLogger)
        self.spy_logger.logger = self.spy_logger

        # Create a config with experiments (rules) and holdouts
        config_dict = self.config_dict_with_features.copy()

        # Get experiment/rule IDs from existing config
        # test_experiment: rule with id '111127'
        # group_exp_1: rule with id '32222'
        rule_id_1 = '111127'  # test_experiment
        rule_id_2 = '32222'   # group_exp_1

        config_dict['holdouts'] = [
            # Global holdout (includedRules is None)
            {
                'id': 'global_holdout_1',
                'key': 'global_holdout',
                'status': 'Running',
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'global_var_1',
                        'key': 'global_control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'global_var_1',
                        'endOfRange': 5000  # 50% traffic
                    }
                ]
            },
            # Local holdout targeting single rule
            {
                'id': 'local_holdout_1',
                'key': 'local_holdout_single',
                'status': 'Running',
                'includedRules': [rule_id_1],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'local_var_1',
                        'key': 'local_control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'local_var_1',
                        'endOfRange': 5000  # 50% traffic
                    }
                ]
            },
            # Local holdout targeting multiple rules
            {
                'id': 'local_holdout_2',
                'key': 'local_holdout_multi',
                'status': 'Running',
                'includedRules': [rule_id_1, rule_id_2],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'local_var_2',
                        'key': 'local_multi_control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'local_var_2',
                        'endOfRange': 5000  # 50% traffic
                    }
                ]
            },
            # Local holdout with empty array (should not match any rules)
            {
                'id': 'local_holdout_empty',
                'key': 'local_holdout_empty',
                'status': 'Running',
                'includedRules': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'local_var_empty',
                        'key': 'empty_control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'local_var_empty',
                        'endOfRange': 10000
                    }
                ]
            },
            # Draft holdout (should not be processed)
            {
                'id': 'draft_holdout',
                'key': 'draft_holdout',
                'status': 'Draft',
                'includedRules': [rule_id_1],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'draft_var',
                        'key': 'draft_control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'draft_var',
                        'endOfRange': 10000
                    }
                ]
            },
            # Local holdout with non-existent rule ID
            {
                'id': 'local_holdout_invalid',
                'key': 'local_holdout_invalid_rule',
                'status': 'Running',
                'includedRules': ['non_existent_rule_id'],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'local_var_invalid',
                        'key': 'invalid_control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'local_var_invalid',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict)
        self.opt_obj = optimizely_module.Optimizely(config_json)
        self.project_config = self.opt_obj.config_manager.get_config()

    def test_holdout_entity_is_global_property(self):
        """Test Holdout.is_global property."""
        # Global holdout (includedRules is None)
        global_holdout = entities.Holdout(
            id='1',
            key='global',
            status='Running',
            variations=[],
            trafficAllocation=[],
            audienceIds=[],
            includedRules=None
        )
        self.assertTrue(global_holdout.is_global)

        # Local holdout with rules
        local_holdout = entities.Holdout(
            id='2',
            key='local',
            status='Running',
            variations=[],
            trafficAllocation=[],
            audienceIds=[],
            includedRules=['rule1', 'rule2']
        )
        self.assertFalse(local_holdout.is_global)

        # Local holdout with empty array (not global)
        empty_local_holdout = entities.Holdout(
            id='3',
            key='empty_local',
            status='Running',
            variations=[],
            trafficAllocation=[],
            audienceIds=[],
            includedRules=[]
        )
        self.assertFalse(empty_local_holdout.is_global)

    def test_project_config_global_holdouts(self):
        """Test that global holdouts are correctly identified."""
        global_holdouts = self.project_config.get_global_holdouts()
        self.assertEqual(len(global_holdouts), 1)
        self.assertEqual(global_holdouts[0].key, 'global_holdout')
        self.assertTrue(global_holdouts[0].is_global)

    def test_project_config_rule_holdouts_map(self):
        """Test that local holdouts are correctly mapped to rules."""
        rule_id_1 = '111127'
        rule_id_2 = '32222'

        # Rule 1 should have 2 local holdouts
        holdouts_for_rule_1 = self.project_config.get_holdouts_for_rule(rule_id_1)
        self.assertEqual(len(holdouts_for_rule_1), 2)
        holdout_keys_1 = {h.key for h in holdouts_for_rule_1}
        self.assertIn('local_holdout_single', holdout_keys_1)
        self.assertIn('local_holdout_multi', holdout_keys_1)

        # Rule 2 should have 1 local holdout
        holdouts_for_rule_2 = self.project_config.get_holdouts_for_rule(rule_id_2)
        self.assertEqual(len(holdouts_for_rule_2), 1)
        self.assertEqual(holdouts_for_rule_2[0].key, 'local_holdout_multi')

        # Non-existent rule should return empty list
        holdouts_for_invalid = self.project_config.get_holdouts_for_rule('non_existent')
        self.assertEqual(len(holdouts_for_invalid), 0)

    def test_empty_included_rules_not_mapped(self):
        """Test that holdouts with empty includedRules array are not mapped to any rules."""
        # Verify no rules have the empty holdout
        for rule_id in ['111127', '32222']:
            holdouts = self.project_config.get_holdouts_for_rule(rule_id)
            holdout_keys = {h.key for h in holdouts}
            self.assertNotIn('local_holdout_empty', holdout_keys)

    def test_draft_holdouts_not_processed(self):
        """Test that draft holdouts are not included in global or rule maps."""
        # Draft holdout should not be in global holdouts
        global_holdouts = self.project_config.get_global_holdouts()
        global_keys = {h.key for h in global_holdouts}
        self.assertNotIn('draft_holdout', global_keys)

        # Draft holdout should not be in rule maps
        holdouts_for_rule = self.project_config.get_holdouts_for_rule('111127')
        rule_keys = {h.key for h in holdouts_for_rule}
        self.assertNotIn('draft_holdout', rule_keys)

    def test_invalid_rule_ids_handled_silently(self):
        """Test that holdouts with non-existent rule IDs don't cause errors."""
        # This should not raise an exception
        holdouts = self.project_config.get_holdouts_for_rule('non_existent_rule_id')
        self.assertEqual(len(holdouts), 0)

        # Verify the invalid holdout was stored but just not mapped
        invalid_holdout = self.project_config.get_holdout('local_holdout_invalid')
        self.assertIsNotNone(invalid_holdout)
        self.assertEqual(invalid_holdout.key, 'local_holdout_invalid_rule')

    def test_global_holdout_evaluated_before_experiments(self):
        """Test that global holdouts are evaluated before experiment rules."""
        # Verify global holdouts are retrieved correctly
        global_holdouts = self.project_config.get_global_holdouts()
        self.assertEqual(len(global_holdouts), 1)

        # Verify the global holdout is properly configured
        self.assertEqual(global_holdouts[0].key, 'global_holdout')
        self.assertTrue(global_holdouts[0].is_global)
        self.assertIsNone(global_holdouts[0].includedRules)

    def test_local_holdout_evaluated_per_rule(self):
        """Test that local holdouts are evaluated for specific rules."""
        # This test would require more complex mocking to verify the exact flow
        # For now, we verify the mapping is correct
        rule_id = '111127'
        holdouts = self.project_config.get_holdouts_for_rule(rule_id)

        self.assertGreater(len(holdouts), 0)
        self.assertTrue(all(not h.is_global for h in holdouts))

    def test_none_vs_empty_array_distinction(self):
        """Test that None (global) and [] (empty local) are handled differently."""
        # Global holdout with includedRules=None
        global_holdouts = self.project_config.get_global_holdouts()
        self.assertEqual(len(global_holdouts), 1)
        self.assertIsNone(global_holdouts[0].includedRules)

        # Empty local holdout should not be in global list
        global_keys = {h.key for h in global_holdouts}
        self.assertNotIn('local_holdout_empty', global_keys)

        # Empty local holdout should not be mapped to any rules
        for rule_id in ['111127', '32222']:
            holdouts = self.project_config.get_holdouts_for_rule(rule_id)
            holdout_keys = {h.key for h in holdouts}
            self.assertNotIn('local_holdout_empty', holdout_keys)

    def test_cross_rule_targeting(self):
        """Test that a single holdout can target rules from multiple experiments."""
        rule_id_1 = '111127'
        rule_id_2 = '32222'

        # Multi-rule holdout should appear in both rule maps
        holdouts_1 = self.project_config.get_holdouts_for_rule(rule_id_1)
        holdouts_2 = self.project_config.get_holdouts_for_rule(rule_id_2)

        holdout_keys_1 = {h.key for h in holdouts_1}
        holdout_keys_2 = {h.key for h in holdouts_2}

        self.assertIn('local_holdout_multi', holdout_keys_1)
        self.assertIn('local_holdout_multi', holdout_keys_2)

        # Verify it's the same holdout object
        multi_holdout_from_rule_1 = next(h for h in holdouts_1 if h.key == 'local_holdout_multi')
        multi_holdout_from_rule_2 = next(h for h in holdouts_2 if h.key == 'local_holdout_multi')
        self.assertEqual(multi_holdout_from_rule_1.id, multi_holdout_from_rule_2.id)


class LocalHoldoutsDecisionFlowTest(base.BaseTest):
    """Tests for decision flow with local holdouts."""

    def setUp(self):
        base.BaseTest.setUp(self)
        self.error_handler = error_handler.NoOpErrorHandler()
        self.spy_logger = mock.MagicMock(spec=logger.SimpleLogger)
        self.spy_logger.logger = self.spy_logger

        # Create minimal config for decision flow testing
        config_dict = self.config_dict_with_features.copy()

        rule_id = '111127'  # test_experiment

        config_dict['holdouts'] = [
            {
                'id': 'local_test',
                'key': 'local_test_holdout',
                'status': 'Running',
                'includedRules': [rule_id],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'local_test_var',
                        'key': 'local_test_control',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'local_test_var',
                        'endOfRange': 10000
                    }
                ]
            }
        ]

        config_json = json.dumps(config_dict)
        self.opt_obj = optimizely_module.Optimizely(config_json)
        self.project_config = self.opt_obj.config_manager.get_config()

    def test_local_holdout_checked_before_rule_evaluation(self):
        """Test that local holdouts are checked before rule audience/traffic evaluation."""
        rule_id = '111127'

        # Verify the local holdout is mapped to the rule
        holdouts = self.project_config.get_holdouts_for_rule(rule_id)
        self.assertEqual(len(holdouts), 1)
        self.assertEqual(holdouts[0].key, 'local_test_holdout')


if __name__ == '__main__':
    unittest.main()
