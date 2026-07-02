# Copyright 2026 Optimizely and contributors
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

"""Level 1 tests for holdout config parsing and data model.

Originally added under FSSDK-12369 to cover holdout config classification.
Updated under FSSDK-12760 to align with the backward-compatible local holdouts
design: local holdouts now live in a new top-level 'localHoldouts' datafile
section. The 'holdouts' section carries ONLY global holdouts — section membership
(not 'includedRules') is the sole signal for scope.

Tests cover:
- isGlobal classification at the entity level (includedRules == None vs list)
- get_global_holdouts() returns entries from the 'holdouts' section
- get_holdouts_for_rule() returns entries from the 'localHoldouts' section
- Backward compatibility:
  * Old datafiles without 'localHoldouts' continue to work unchanged
  * Any 'includedRules' field on entries in the 'holdouts' section is ignored
  * Datafiles missing both 'holdouts' and 'localHoldouts' sections produce
    empty global/local lists
- localHoldouts section: invalid entries (missing includedRules) are logged
  and excluded from evaluation
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


def _build_config(
    holdouts: list,
    base_test: 'base.BaseTest',
    local_holdouts: 'list | None' = None,
) -> 'optimizely_module.Optimizely':
    """Create an Optimizely instance with the given top-level holdout sections.

    Args:
        holdouts: Entries for the top-level 'holdouts' section (treated as global).
        base_test: Test fixture providing config_dict_with_features.
        local_holdouts: Optional entries for the top-level 'localHoldouts' section
            (treated as local). When omitted, the 'localHoldouts' key is NOT added
            to the datafile, exercising backward-compatible behavior.
    """
    config_dict = base_test.config_dict_with_features.copy()
    config_dict['holdouts'] = holdouts
    if local_holdouts is not None:
        config_dict['localHoldouts'] = local_holdouts
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

    def test_get_global_holdouts_returns_all_entries_from_holdouts_section(self):
        """Every entry in the 'holdouts' datafile section is treated as global.

        Section membership is the sole signal for scope — any 'includedRules'
        field on these entries is ignored. Local holdouts must live in the
        separate 'localHoldouts' section.
        """
        self.opt_obj = _build_config(
            holdouts=[
                _make_holdout('h1', 'global_1'),
                _make_holdout('h2', 'global_2', None),
            ],
            base_test=self,
            local_holdouts=[
                _make_holdout('h3', 'local_1', ['rule_x']),
            ],
        )
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
        """If all holdouts live in the localHoldouts section, global list is empty."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h1', 'local_a', ['rule_1']),
                _make_holdout('h2', 'local_b', ['rule_2']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_global_holdouts(), [])

    def test_global_holdouts_ignore_included_rules_on_entries(self):
        """Any 'includedRules' field on entries in the 'holdouts' section is ignored.

        Section membership in 'holdouts' alone determines global scope. Even if the
        datafile incorrectly includes an 'includedRules' field on a global holdout,
        the entity must still be classified as global and never registered against
        any rule's local-holdout map.
        """
        self.opt_obj = _build_config(
            holdouts=[
                _make_holdout('h_global_with_rules', 'g', ['rule_should_be_ignored']),
            ],
            base_test=self,
        )
        config = self.opt_obj.config_manager.get_config()

        global_holdouts = config.get_global_holdouts()
        global_ids = {h.id for h in global_holdouts}
        self.assertIn('h_global_with_rules', global_ids)

        # The ignored rule ID must not be present in the rule map
        self.assertEqual(config.get_holdouts_for_rule('rule_should_be_ignored'), [])

        # The entity itself must report is_global (includedRules was stripped)
        for h in global_holdouts:
            if h.id == 'h_global_with_rules':
                self.assertTrue(h.is_global)
                self.assertIsNone(h.included_rules)


class HoldoutConfigGetHoldoutsForRuleTest(unittest.TestCase):
    """Tests for ProjectConfig.get_holdouts_for_rule()."""

    def setUp(self):
        base.BaseTest.setUp(self)

    def tearDown(self):
        if hasattr(self, 'opt_obj'):
            self.opt_obj.close()

    def test_get_holdouts_for_rule_returns_matching_local_holdouts(self):
        """Holdout targeting rule_x should be returned for rule_x."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h1', 'local_h', ['rule_x', 'rule_y']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        self.assertEqual(len(holdouts), 1)
        self.assertEqual(holdouts[0].id, 'h1')

    def test_get_holdouts_for_rule_returns_empty_for_unknown_rule(self):
        """Rule ID not found in any holdout's includedRules returns empty list."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h1', 'local_h', ['rule_a']),
            ],
        )
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
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h1', 'local_h1', ['rule_x']),
                _make_holdout('h2', 'local_h2', ['rule_x', 'rule_y']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        ids = {h.id for h in holdouts}
        self.assertIn('h1', ids)
        self.assertIn('h2', ids)

    def test_get_holdouts_for_rule_does_not_return_global_holdouts(self):
        """Global holdouts should not appear in get_holdouts_for_rule results."""
        self.opt_obj = _build_config(
            holdouts=[
                _make_holdout('global', 'global_holdout'),
            ],
            base_test=self,
            local_holdouts=[
                _make_holdout('local', 'local_holdout', ['rule_x']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        ids = {h.id for h in holdouts}
        self.assertNotIn('global', ids)
        self.assertIn('local', ids)

    def test_get_holdouts_for_rule_rule_specificity(self):
        """A holdout targeting rule_x must not appear for rule_y."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h1', 'local_for_x', ['rule_x']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_holdouts_for_rule('rule_y'), [])

    def test_get_holdouts_for_rule_cross_flag_targeting(self):
        """One holdout can target rules from multiple different flags."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h1', 'cross_flag_holdout', ['rule_flag_a', 'rule_flag_b']),
            ],
        )
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

    def test_old_datafile_without_local_holdouts_section_works(self):
        """Old datafiles that only emit the 'holdouts' section continue to work.

        Per FSSDK-12760: backward compatibility requires that datafiles produced
        before the 'localHoldouts' section existed are parsed exactly like before.
        Every entry in 'holdouts' is global; no errors, no log noise.
        """
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
        """Legacy holdouts (no localHoldouts section) must not pollute rule map."""
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

    def test_datafile_missing_both_holdouts_sections(self):
        """Datafiles without 'holdouts' or 'localHoldouts' keys produce empty lists."""
        config_dict = self.config_dict_with_features.copy()
        # Explicitly do not set either holdouts key
        self.opt_obj = optimizely_module.Optimizely(json.dumps(config_dict))
        config = self.opt_obj.config_manager.get_config()

        self.assertEqual(config.get_global_holdouts(), [])
        self.assertEqual(config.get_holdouts_for_rule('any_rule'), [])

    def test_is_global_entity_property_independent_of_section(self):
        """The Holdout.is_global entity property still reflects includedRules.

        At the entity level, is_global is computed from the included_rules attribute
        (None → True, [] or non-empty list → False). The new datafile sections affect
        how the entity is BUILT (via includedRules stripping) but not how the property
        itself is computed.
        """
        # Build an entity directly (bypassing project config) — includedRules controls is_global
        h_none = entities.Holdout(
            id='h_none', key='g', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[], includedRules=None,
        )
        h_empty = entities.Holdout(
            id='h_empty', key='l', status='Running',
            variations=HOLDOUT_VARIATION, trafficAllocation=FULL_TRAFFIC,
            audienceIds=[], includedRules=[],
        )
        self.assertTrue(h_none.is_global)
        self.assertFalse(h_empty.is_global)


class LocalHoldoutsSectionTest(unittest.TestCase):
    """Tests for the new top-level 'localHoldouts' datafile section (FSSDK-12760).

    Local holdouts now live in a dedicated 'localHoldouts' section, separate from
    'holdouts' which carries only global holdouts. Older SDK versions (Gen 1/Gen 2)
    will ignore this unknown top-level key entirely — that's the whole point of the
    backward-compatible design — but Gen 3 SDKs must parse it as the source of truth
    for local (rule-scoped) holdouts.
    """

    def setUp(self):
        base.BaseTest.setUp(self)

    def tearDown(self):
        if hasattr(self, 'opt_obj'):
            self.opt_obj.close()

    def test_local_holdouts_section_registers_in_rule_map(self):
        """Entries in 'localHoldouts' are registered under each rule in includedRules."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h_local', 'local_h', ['rule_x']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        self.assertEqual(len(holdouts), 1)
        self.assertEqual(holdouts[0].id, 'h_local')

    def test_local_holdouts_section_entries_excluded_from_global_list(self):
        """Entries in 'localHoldouts' must not appear in get_global_holdouts()."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h_local', 'local_h', ['rule_x']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_global_holdouts(), [])

    def test_local_holdouts_missing_included_rules_logged_and_excluded(self):
        """Entries in 'localHoldouts' without 'includedRules' are invalid.

        SDK must log an error and exclude the entry from evaluation. It must NOT
        fall back to global application (the partition between sections is hard).
        """
        invalid_local = {
            'id': 'h_invalid',
            'key': 'invalid_local',
            'status': 'Running',
            'audienceIds': [],
            'variations': HOLDOUT_VARIATION,
            'trafficAllocation': FULL_TRAFFIC,
            # Note: no 'includedRules' field
        }
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[invalid_local],
        )
        config = self.opt_obj.config_manager.get_config()

        # Invalid entry must not be applied as global
        self.assertEqual(config.get_global_holdouts(), [])
        # Invalid entry must not be applied as local for any rule
        self.assertEqual(config.get_holdouts_for_rule('any_rule'), [])
        # Invalid entry must not be retrievable by ID either
        self.assertIsNone(config.holdout_id_map.get('h_invalid'))

    def test_local_holdouts_missing_included_rules_logs_error(self):
        """Verify an error log is emitted for an invalid local holdout entry."""
        invalid_local = {
            'id': 'h_invalid',
            'key': 'invalid_local',
            'status': 'Running',
            'audienceIds': [],
            'variations': HOLDOUT_VARIATION,
            'trafficAllocation': FULL_TRAFFIC,
        }
        config_dict = self.config_dict_with_features.copy()
        config_dict['localHoldouts'] = [invalid_local]

        # Verify the error is logged through the standard logging framework.
        with self.assertLogs('optimizely.logger', level='ERROR') as captured:
            self.opt_obj = optimizely_module.Optimizely(json.dumps(config_dict))

        matching = [
            msg for msg in captured.output
            if 'h_invalid' in msg and 'includedRules' in msg
        ]
        self.assertGreaterEqual(
            len(matching), 1,
            f'Expected error log for invalid local holdout; got: {captured.output}'
        )

    def test_local_holdouts_with_null_included_rules_logged_and_excluded(self):
        """includedRules=None in 'localHoldouts' is invalid (same as missing).

        Distinct from 'holdouts' section where None signals a global holdout —
        in 'localHoldouts' the field is REQUIRED and a None value is invalid.
        """
        invalid_local = _make_holdout('h_null', 'null_local', included_rules=None)
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[invalid_local],
        )
        config = self.opt_obj.config_manager.get_config()
        self.assertEqual(config.get_holdouts_for_rule('any_rule'), [])
        self.assertEqual(config.get_global_holdouts(), [])

    def test_local_holdouts_empty_included_rules_targets_no_rules(self):
        """includedRules=[] is valid but targets no rules (entity is stored, not invalid).

        An entry with an empty includedRules list is treated as a local holdout
        that simply does not apply to any rule. It is NOT invalid (no error log),
        and it is NOT promoted to global. This matches the existing entity-level
        semantics where [] != None.
        """
        empty_local = _make_holdout('h_empty', 'empty_local', included_rules=[])
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[empty_local],
        )
        config = self.opt_obj.config_manager.get_config()
        # Not in any rule map (no rules to target)
        self.assertEqual(config.get_holdouts_for_rule('any_rule'), [])
        # Not global either
        self.assertEqual(config.get_global_holdouts(), [])
        # But the entity itself was created and tracked in holdout_id_map
        stored = config.holdout_id_map.get('h_empty')
        self.assertIsNotNone(stored)
        self.assertFalse(stored.is_global)

    def test_local_holdouts_excludes_non_running_entries(self):
        """Non-Running entries in 'localHoldouts' must not be evaluated."""
        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[
                _make_holdout('h_running', 'lr', ['rule_x'], status='Running'),
                _make_holdout('h_draft', 'ld', ['rule_x'], status='Draft'),
            ],
        )
        config = self.opt_obj.config_manager.get_config()
        ids = {h.id for h in config.get_holdouts_for_rule('rule_x')}
        self.assertIn('h_running', ids)
        self.assertNotIn('h_draft', ids)

    def test_both_sections_present_partition_correctly(self):
        """When both 'holdouts' and 'localHoldouts' are present, scope is enforced
        by section membership — entries never cross over."""
        self.opt_obj = _build_config(
            holdouts=[
                _make_holdout('g1', 'global_1'),
                _make_holdout('g2', 'global_2'),
            ],
            base_test=self,
            local_holdouts=[
                _make_holdout('l1', 'local_1', ['rule_a']),
                _make_holdout('l2', 'local_2', ['rule_b']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()

        global_ids = {h.id for h in config.get_global_holdouts()}
        self.assertEqual(global_ids, {'g1', 'g2'})

        self.assertEqual({h.id for h in config.get_holdouts_for_rule('rule_a')}, {'l1'})
        self.assertEqual({h.id for h in config.get_holdouts_for_rule('rule_b')}, {'l2'})

    def test_local_holdouts_id_uniqueness_across_sections(self):
        """Entries from both sections are tracked together in holdout_id_map.

        get_holdout(id) must work for both global and local holdouts regardless of
        which section they came from.
        """
        self.opt_obj = _build_config(
            holdouts=[
                _make_holdout('g1', 'global_1'),
            ],
            base_test=self,
            local_holdouts=[
                _make_holdout('l1', 'local_1', ['rule_x']),
            ],
        )
        config = self.opt_obj.config_manager.get_config()

        self.assertIsNotNone(config.get_holdout('g1'))
        self.assertIsNotNone(config.get_holdout('l1'))

    def test_local_holdouts_section_with_real_traffic_allocation(self):
        """Local holdouts in 'localHoldouts' carry real trafficAllocation directly.

        Per spec: no more dummy-zero-allocation workaround — the trafficAllocation
        field is used as-is for bucketing.
        """
        local_h = _make_holdout('h_local', 'local_h', ['rule_x'])
        # Override with a custom traffic allocation
        local_h['trafficAllocation'] = [{'entityId': 'holdout_var_1', 'endOfRange': 5000}]

        self.opt_obj = _build_config(
            holdouts=[],
            base_test=self,
            local_holdouts=[local_h],
        )
        config = self.opt_obj.config_manager.get_config()
        holdouts = config.get_holdouts_for_rule('rule_x')
        self.assertEqual(len(holdouts), 1)
        self.assertEqual(holdouts[0].trafficAllocation,
                         [{'entityId': 'holdout_var_1', 'endOfRange': 5000}])
