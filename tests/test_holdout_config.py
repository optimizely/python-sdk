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

"""Level 1 tests for holdout config parsing and data model (FSSDK-12369).

Tests cover:
- isGlobal classification (includedRules == None vs list)
- get_global_holdouts() returns only global holdouts
- get_holdouts_for_rule() returns local holdouts for a specific rule
- Backward compatibility with old datafiles (no includedRules field)
- Edge cases: empty array vs None, unknown rule IDs, cross-flag targeting
"""

import json
import unittest

from optimizely import entities
from optimizely import optimizely as optimizely_module
from tests import base


HOLDOUT_VARIATION = [
    {'id': 'holdout_var_1', 'key': 'holdout_control', 'variables': []}
]

FULL_TRAFFIC = [{'entityId': 'holdout_var_1', 'endOfRange': 10000}]
NO_TRAFFIC = [{'entityId': 'holdout_var_1', 'endOfRange': 0}]


def _make_holdout(
    holdout_id: str,
    key: str,
    included_rules: object = 'MISSING',
    status: str = 'Running',
) -> dict:
    """Build a holdout datafile dict. Pass included_rules=None for global,
    a list for local, or leave as 'MISSING' to omit the field entirely."""
    h: dict = {
        'id': holdout_id,
        'key': key,
        'status': status,
        'audienceIds': [],
        'variations': HOLDOUT_VARIATION,
        'trafficAllocation': FULL_TRAFFIC,
    }
    if included_rules != 'MISSING':
        h['includedRules'] = included_rules
    return h


def _build_config(holdouts: list, base_test: 'base.BaseTest') -> 'optimizely_module.Optimizely':
    """Create an Optimizely instance with the given holdouts list."""
    config_dict = base_test.config_dict_with_features.copy()
    config_dict['holdouts'] = holdouts
    return optimizely_module.Optimizely(json.dumps(config_dict))


class HoldoutEntityIsGlobalTest(unittest.TestCase):
    """Tests for the Holdout.is_global computed property."""

    def test_is_global_returns_true_when_included_rules_is_none(self):
        """Holdout with includedRules=None should be classified as global."""
        holdout = entities.Holdout(
            id='h1', key='global_holdout', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[], includedRules=None
        )
        self.assertTrue(holdout.is_global)

    def test_is_global_returns_true_when_included_rules_not_provided(self):
        """Holdout with no includedRules kwarg (default None) is global."""
        holdout = entities.Holdout(
            id='h1', key='global_holdout', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[]
        )
        self.assertTrue(holdout.is_global)

    def test_is_global_returns_false_when_included_rules_is_empty_list(self):
        """Empty list [] is a local holdout targeting no rules — NOT global."""
        holdout = entities.Holdout(
            id='h1', key='local_holdout_no_rules', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[], includedRules=[]
        )
        self.assertFalse(holdout.is_global)

    def test_is_global_returns_false_when_included_rules_has_rule_ids(self):
        """Holdout with rule IDs is local — is_global should be False."""
        holdout = entities.Holdout(
            id='h1', key='local_holdout', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[], includedRules=['rule_1', 'rule_2']
        )
        self.assertFalse(holdout.is_global)

    def test_included_rules_stored_correctly(self):
        """included_rules attribute should match the passed includedRules value."""
        holdout_global = entities.Holdout(
            id='h1', key='g', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[], includedRules=None
        )
        holdout_local = entities.Holdout(
            id='h2', key='l', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[], includedRules=['rule_a', 'rule_b']
        )
        self.assertIsNone(holdout_global.included_rules)
        self.assertEqual(holdout_local.included_rules, ['rule_a', 'rule_b'])


class HoldoutConfigGetGlobalHoldoutsTest(unittest.TestCase):
    """Tests for ProjectConfig.get_global_holdouts()."""

    def setUp(self):
        base.BaseTest.setUp(self)

    def tearDown(self):
        if hasattr(self, 'opt_obj'):
            self.opt_obj.close()

    def test_get_global_holdouts_returns_all_global_holdouts(self):
        """All holdouts without includedRules should be returned."""
        self.opt_obj = _build_config([
            _make_holdout('h1', 'global_1'),            # field absent → global
            _make_holdout('h2', 'global_2', None),      # explicitly None → global
            _make_holdout('h3', 'local_1', ['rule_x']), # local
        ], self)
        config = self.opt_obj.config_manager.get_config()
        global_holdouts = config.get_global_holdouts()
        global_ids = {h.id for h in global_holdouts}
        self.assertIn('h1', global_ids)
        self.assertIn('h2', global_ids)
        self.assertNotIn('h3', global_ids)

    def test_get_global_holdouts_returns_empty_when_no_holdouts(self):
        """No holdouts in datafile → empty list."""
        self.opt_obj = _build_config([], self)
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_global_holdouts(), [])

    def test_get_global_holdouts_excludes_non_running_holdouts(self):
        """Draft holdouts are not activated and should not appear."""
        self.opt_obj = _build_config([
            _make_holdout('h_running', 'running_global', status='Running'),
            _make_holdout('h_draft', 'draft_global', status='Draft'),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        global_holdouts = config.get_global_holdouts()
        ids = {h.id for h in global_holdouts}
        self.assertIn('h_running', ids)
        self.assertNotIn('h_draft', ids)

    def test_get_global_holdouts_returns_empty_when_all_local(self):
        """If all holdouts are local, global list is empty."""
        self.opt_obj = _build_config([
            _make_holdout('h1', 'local_a', ['rule_1']),
            _make_holdout('h2', 'local_b', ['rule_2']),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_global_holdouts(), [])


class HoldoutConfigGetHoldoutsForRuleTest(unittest.TestCase):
    """Tests for ProjectConfig.get_holdouts_for_rule()."""

    def setUp(self):
        base.BaseTest.setUp(self)

    def tearDown(self):
        if hasattr(self, 'opt_obj'):
            self.opt_obj.close()

    def test_get_holdouts_for_rule_returns_matching_local_holdouts(self):
        """Holdout targeting rule_x should be returned for rule_x."""
        self.opt_obj = _build_config([
            _make_holdout('h1', 'local_h', ['rule_x', 'rule_y']),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        self.assertEqual(len(holdouts), 1)
        self.assertEqual(holdouts[0].id, 'h1')

    def test_get_holdouts_for_rule_returns_empty_for_unknown_rule(self):
        """Rule ID not found in any holdout's includedRules returns empty list."""
        self.opt_obj = _build_config([
            _make_holdout('h1', 'local_h', ['rule_a']),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        # Silently skip unknown rule IDs
        holdouts = config.get_holdouts_for_rule('nonexistent_rule')
        self.assertEqual(holdouts, [])

    def test_get_holdouts_for_rule_returns_empty_when_no_holdouts(self):
        """No holdouts defined → always returns empty list."""
        self.opt_obj = _build_config([], self)
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_holdouts_for_rule('any_rule'), [])

    def test_get_holdouts_for_rule_multiple_holdouts_for_same_rule(self):
        """Multiple holdouts can target the same rule."""
        self.opt_obj = _build_config([
            _make_holdout('h1', 'local_h1', ['rule_x']),
            _make_holdout('h2', 'local_h2', ['rule_x', 'rule_y']),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        ids = {h.id for h in holdouts}
        self.assertIn('h1', ids)
        self.assertIn('h2', ids)

    def test_get_holdouts_for_rule_does_not_return_global_holdouts(self):
        """Global holdouts should not appear in get_holdouts_for_rule results."""
        self.opt_obj = _build_config([
            _make_holdout('global', 'global_holdout'),          # field absent → global
            _make_holdout('local', 'local_holdout', ['rule_x']),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        ids = {h.id for h in holdouts}
        self.assertNotIn('global', ids)
        self.assertIn('local', ids)

    def test_get_holdouts_for_rule_rule_specificity(self):
        """A holdout targeting rule_x must not appear for rule_y."""
        self.opt_obj = _build_config([
            _make_holdout('h1', 'local_for_x', ['rule_x']),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_holdouts_for_rule('rule_y'), [])

    def test_get_holdouts_for_rule_cross_flag_targeting(self):
        """One holdout can target rules from multiple different flags."""
        self.opt_obj = _build_config([
            _make_holdout('h1', 'cross_flag_holdout', ['rule_flag_a', 'rule_flag_b']),
        ], self)
        config = self.opt_obj.config_manager.get_config()
        for rule_id in ['rule_flag_a', 'rule_flag_b']:
            holdouts = config.get_holdouts_for_rule(rule_id)
            self.assertEqual(len(holdouts), 1)
            self.assertEqual(holdouts[0].id, 'h1')


class HoldoutBackwardCompatibilityTest(unittest.TestCase):
    """Tests for backward compatibility with old datafiles (no includedRules field)."""

    def setUp(self):
        base.BaseTest.setUp(self)

    def tearDown(self):
        if hasattr(self, 'opt_obj'):
            self.opt_obj.close()

    def test_old_datafile_without_included_rules_treated_as_global(self):
        """Datafiles without includedRules field must default to global holdout."""
        # Simulate old datafile — no 'includedRules' key at all
        old_holdout = {
            'id': 'old_h',
            'key': 'legacy_holdout',
            'status': 'Running',
            'audienceIds': [],
            'variations': HOLDOUT_VARIATION,
            'trafficAllocation': FULL_TRAFFIC,
        }
        self.opt_obj = _build_config([old_holdout], self)
        config = self.opt_obj.config_manager.get_config()

        global_holdouts = config.get_global_holdouts()
        self.assertEqual(len(global_holdouts), 1)
        self.assertEqual(global_holdouts[0].id, 'old_h')
        self.assertTrue(global_holdouts[0].is_global)

    def test_old_datafile_holdout_does_not_appear_in_rule_map(self):
        """Legacy holdouts with no includedRules field must not pollute rule map."""
        old_holdout = {
            'id': 'old_h',
            'key': 'legacy_holdout',
            'status': 'Running',
            'audienceIds': [],
            'variations': HOLDOUT_VARIATION,
            'trafficAllocation': FULL_TRAFFIC,
        }
        self.opt_obj = _build_config([old_holdout], self)
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_holdouts_for_rule('any_rule'), [])

    def test_empty_included_rules_is_local_not_global(self):
        """[] (empty array) is a local holdout targeting no rules — not the same as None."""
        holdout_empty = _make_holdout('h_empty', 'empty_local', included_rules=[])
        holdout_none = _make_holdout('h_none', 'global_none', included_rules=None)

        self.opt_obj = _build_config([holdout_empty, holdout_none], self)
        config = self.opt_obj.config_manager.get_config()

        global_holdouts = config.get_global_holdouts()
        global_ids = {h.id for h in global_holdouts}

        # None → global; [] → local (does not appear in global list)
        self.assertIn('h_none', global_ids)
        self.assertNotIn('h_empty', global_ids)
