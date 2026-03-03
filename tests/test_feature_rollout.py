# Copyright 2025, Optimizely
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
import copy
import unittest

from optimizely import entities
from optimizely import optimizely
from optimizely.project_config import ProjectConfig


class FeatureRolloutConfigTest(unittest.TestCase):
    """Tests for Feature Rollout support in ProjectConfig parsing."""

    def _build_datafile(self, experiments=None, rollouts=None, feature_flags=None):
        """Build a minimal valid datafile with the given components."""
        datafile = {
            'version': '4',
            'accountId': '12001',
            'projectId': '111001',
            'revision': '1',
            'experiments': experiments or [],
            'events': [],
            'attributes': [],
            'audiences': [],
            'groups': [],
            'rollouts': rollouts or [],
            'featureFlags': feature_flags or [],
        }
        return datafile

    def test_experiment_type_field_parsed(self):
        """Test that the optional 'type' field is parsed on Experiment entities."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_1',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'var_1', 'endOfRange': 5000}],
                    'variations': [{'key': 'var_1', 'id': 'var_1', 'featureEnabled': True}],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_rule_1',
                            'key': 'rollout_rule_1',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [{'entityId': 'everyone_var', 'endOfRange': 10000}],
                            'variations': [
                                {'key': 'everyone_var', 'id': 'everyone_var', 'featureEnabled': False}
                            ],
                        }
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_1'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_1']
        self.assertEqual(experiment.type, 'feature_rollout')

    def test_experiment_type_field_none_when_missing(self):
        """Test that experiments without 'type' field have type=None."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_ab',
                    'key': 'ab_test_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'var_1', 'endOfRange': 5000}],
                    'variations': [{'key': 'var_1', 'id': 'var_1', 'featureEnabled': True}],
                },
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_ab'],
                    'rolloutId': '',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_ab']
        self.assertIsNone(experiment.type)

    def test_feature_rollout_injects_everyone_else_variation(self):
        """Test that feature_rollout experiments get the everyone else variation injected."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'rollout_var', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'rollout_var', 'id': 'rollout_var', 'featureEnabled': True}
                    ],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_targeted_rule',
                            'key': 'rollout_targeted_rule',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': ['audience_1'],
                            'trafficAllocation': [{'entityId': 'targeted_var', 'endOfRange': 10000}],
                            'variations': [
                                {'key': 'targeted_var', 'id': 'targeted_var', 'featureEnabled': True}
                            ],
                        },
                        {
                            'id': 'rollout_everyone_else',
                            'key': 'rollout_everyone_else',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [
                                {'entityId': 'everyone_else_var', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'everyone_else_var',
                                    'id': 'everyone_else_var',
                                    'featureEnabled': False,
                                }
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_fr'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_fr']

        # Should now have 2 variations: original + everyone else
        self.assertEqual(len(experiment.variations), 2)

        # Verify the everyone else variation was appended
        variation_ids = [v['id'] if isinstance(v, dict) else v.id for v in experiment.variations]
        self.assertIn('everyone_else_var', variation_ids)

        # Verify traffic allocation was appended with endOfRange=10000
        self.assertEqual(len(experiment.trafficAllocation), 2)
        last_allocation = experiment.trafficAllocation[-1]
        self.assertEqual(last_allocation['entityId'], 'everyone_else_var')
        self.assertEqual(last_allocation['endOfRange'], 10000)

    def test_feature_rollout_variation_maps_updated(self):
        """Test that variation maps are properly updated after injection."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'rollout_var', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'rollout_var', 'id': 'rollout_var', 'featureEnabled': True}
                    ],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_everyone_else',
                            'key': 'rollout_everyone_else',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [
                                {'entityId': 'everyone_else_var', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'everyone_else_var',
                                    'id': 'everyone_else_var',
                                    'featureEnabled': False,
                                }
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_fr'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        # Check variation_key_map is updated
        self.assertIn('everyone_else_var', config.variation_key_map['feature_rollout_exp'])

        # Check variation_id_map is updated
        self.assertIn('everyone_else_var', config.variation_id_map['feature_rollout_exp'])

        # Check variation_id_map_by_experiment_id is updated
        self.assertIn('everyone_else_var', config.variation_id_map_by_experiment_id['exp_fr'])

        # Check variation_key_map_by_experiment_id is updated
        self.assertIn('everyone_else_var', config.variation_key_map_by_experiment_id['exp_fr'])

    def test_non_feature_rollout_experiments_unchanged(self):
        """Test that experiments without type=feature_rollout are not modified."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_ab',
                    'key': 'ab_test_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'var_1', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'var_1', 'id': 'var_1', 'featureEnabled': True}
                    ],
                    'type': 'a/b',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_everyone_else',
                            'key': 'rollout_everyone_else',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [
                                {'entityId': 'everyone_else_var', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'everyone_else_var',
                                    'id': 'everyone_else_var',
                                    'featureEnabled': False,
                                }
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_ab'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_ab']

        # Should still have only 1 variation
        self.assertEqual(len(experiment.variations), 1)
        # Should still have only 1 traffic allocation
        self.assertEqual(len(experiment.trafficAllocation), 1)

    def test_feature_rollout_with_no_rollout(self):
        """Test feature_rollout experiment with empty rolloutId is not modified."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'var_1', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'var_1', 'id': 'var_1', 'featureEnabled': True}
                    ],
                    'type': 'feature_rollout',
                },
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_fr'],
                    'rolloutId': '',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_fr']

        # Without a rollout, no injection should occur
        self.assertEqual(len(experiment.variations), 1)
        self.assertEqual(len(experiment.trafficAllocation), 1)

    def test_feature_rollout_with_empty_rollout_experiments(self):
        """Test feature_rollout with a rollout that has no experiments."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'var_1', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'var_1', 'id': 'var_1', 'featureEnabled': True}
                    ],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_empty',
                    'experiments': [],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_fr'],
                    'rolloutId': 'rollout_empty',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_fr']

        # With empty rollout experiments, no injection should occur
        self.assertEqual(len(experiment.variations), 1)
        self.assertEqual(len(experiment.trafficAllocation), 1)

    def test_feature_rollout_multiple_experiments_mixed_types(self):
        """Test a flag with both feature_rollout and regular experiments."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_ab',
                    'key': 'ab_test',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'ab_var', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'ab_var', 'id': 'ab_var', 'featureEnabled': True}
                    ],
                    'type': 'a/b',
                },
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_2',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'fr_var', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'fr_var', 'id': 'fr_var', 'featureEnabled': True}
                    ],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_everyone_else',
                            'key': 'rollout_everyone_else',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [
                                {'entityId': 'everyone_else_var', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'everyone_else_var',
                                    'id': 'everyone_else_var',
                                    'featureEnabled': False,
                                }
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_ab', 'exp_fr'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        # A/B test should not be modified
        ab_experiment = config.experiment_id_map['exp_ab']
        self.assertEqual(len(ab_experiment.variations), 1)
        self.assertEqual(len(ab_experiment.trafficAllocation), 1)

        # Feature rollout should have the everyone else variation injected
        fr_experiment = config.experiment_id_map['exp_fr']
        self.assertEqual(len(fr_experiment.variations), 2)
        self.assertEqual(len(fr_experiment.trafficAllocation), 2)

        variation_ids = [v['id'] if isinstance(v, dict) else v.id for v in fr_experiment.variations]
        self.assertIn('everyone_else_var', variation_ids)

    def test_feature_rollout_everyone_else_is_last_rollout_rule(self):
        """Test that the everyone else variation comes from the LAST rollout rule."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'fr_var', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'fr_var', 'id': 'fr_var', 'featureEnabled': True}
                    ],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'targeted_rule_1',
                            'key': 'targeted_rule_1',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': ['aud_1'],
                            'trafficAllocation': [
                                {'entityId': 'targeted_var_1', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'targeted_var_1',
                                    'id': 'targeted_var_1',
                                    'featureEnabled': True,
                                }
                            ],
                        },
                        {
                            'id': 'targeted_rule_2',
                            'key': 'targeted_rule_2',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': ['aud_2'],
                            'trafficAllocation': [
                                {'entityId': 'targeted_var_2', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'targeted_var_2',
                                    'id': 'targeted_var_2',
                                    'featureEnabled': True,
                                }
                            ],
                        },
                        {
                            'id': 'everyone_else_rule',
                            'key': 'everyone_else_rule',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [
                                {'entityId': 'correct_everyone_var', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'correct_everyone_var',
                                    'id': 'correct_everyone_var',
                                    'featureEnabled': False,
                                }
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_fr'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_fr']

        # Should have injected the correct (last) everyone else variation
        variation_ids = [v['id'] if isinstance(v, dict) else v.id for v in experiment.variations]
        self.assertIn('correct_everyone_var', variation_ids)
        # Should NOT have injected targeted rule variations
        self.assertNotIn('targeted_var_1', variation_ids)
        self.assertNotIn('targeted_var_2', variation_ids)

    def test_feature_rollout_flag_variations_map_includes_injected(self):
        """Test that flag_variations_map includes the injected everyone else variation."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'fr_var', 'endOfRange': 5000}],
                    'variations': [
                        {'key': 'fr_var', 'id': 'fr_var', 'featureEnabled': True}
                    ],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_everyone_else',
                            'key': 'rollout_everyone_else',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [
                                {'entityId': 'everyone_else_var', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'everyone_else_var',
                                    'id': 'everyone_else_var',
                                    'featureEnabled': False,
                                }
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_fr'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        flag_variations = config.flag_variations_map.get('test_flag', [])
        flag_variation_ids = [v.id for v in flag_variations]

        # The injected variation should be available in flag_variations_map
        self.assertIn('everyone_else_var', flag_variation_ids)
        self.assertIn('fr_var', flag_variation_ids)

    def test_experiment_type_ab(self):
        """Test that experiment with type='a/b' is parsed correctly."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_ab',
                    'key': 'ab_test',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'var_1', 'endOfRange': 5000}],
                    'variations': [{'key': 'var_1', 'id': 'var_1', 'featureEnabled': True}],
                    'type': 'a/b',
                },
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_ab'],
                    'rolloutId': '',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        experiment = config.experiment_id_map['exp_ab']
        self.assertEqual(experiment.type, 'a/b')

    def test_feature_rollout_with_variables_on_everyone_else(self):
        """Test that everyone else variation with variable usages gets properly mapped."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_fr',
                    'key': 'feature_rollout_exp',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [{'entityId': 'fr_var', 'endOfRange': 5000}],
                    'variations': [
                        {
                            'key': 'fr_var',
                            'id': 'fr_var',
                            'featureEnabled': True,
                            'variables': [{'id': 'var_100', 'value': 'on'}],
                        }
                    ],
                    'type': 'feature_rollout',
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_everyone_else',
                            'key': 'rollout_everyone_else',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [
                                {'entityId': 'ee_var', 'endOfRange': 10000}
                            ],
                            'variations': [
                                {
                                    'key': 'ee_var',
                                    'id': 'ee_var',
                                    'featureEnabled': False,
                                    'variables': [{'id': 'var_100', 'value': 'off'}],
                                }
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_fr'],
                    'rolloutId': 'rollout_1',
                    'variables': [
                        {'id': 'var_100', 'key': 'toggle', 'defaultValue': 'default', 'type': 'string'},
                    ],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        # Verify the variation variable usage map is populated for the injected variation
        self.assertIn('ee_var', config.variation_variable_usage_map)
        variable_usage = config.variation_variable_usage_map['ee_var']
        self.assertIn('var_100', variable_usage)
        self.assertEqual(variable_usage['var_100'].value, 'off')

    def test_existing_datafile_not_broken(self):
        """Test that existing datafiles without feature_rollout type still work correctly."""
        datafile = self._build_datafile(
            experiments=[
                {
                    'id': 'exp_1',
                    'key': 'regular_exp',
                    'status': 'Running',
                    'forcedVariations': {'user_1': 'control'},
                    'layerId': 'layer_1',
                    'audienceIds': [],
                    'trafficAllocation': [
                        {'entityId': 'control', 'endOfRange': 5000},
                        {'entityId': 'variation', 'endOfRange': 10000},
                    ],
                    'variations': [
                        {'key': 'control', 'id': 'control', 'featureEnabled': False},
                        {'key': 'variation', 'id': 'variation', 'featureEnabled': True},
                    ],
                },
            ],
            rollouts=[
                {
                    'id': 'rollout_1',
                    'experiments': [
                        {
                            'id': 'rollout_rule',
                            'key': 'rollout_rule',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': 'rollout_1',
                            'audienceIds': [],
                            'trafficAllocation': [{'entityId': 'rollout_var', 'endOfRange': 10000}],
                            'variations': [
                                {'key': 'rollout_var', 'id': 'rollout_var', 'featureEnabled': True}
                            ],
                        },
                    ],
                }
            ],
            feature_flags=[
                {
                    'id': 'flag_1',
                    'key': 'test_flag',
                    'experimentIds': ['exp_1'],
                    'rolloutId': 'rollout_1',
                    'variables': [],
                },
            ],
        )

        opt = optimizely.Optimizely(json.dumps(datafile))
        config = opt.config_manager.get_config()

        # Regular experiment should be unchanged
        experiment = config.experiment_id_map['exp_1']
        self.assertEqual(len(experiment.variations), 2)
        self.assertEqual(len(experiment.trafficAllocation), 2)
        self.assertIsNone(experiment.type)

    def test_get_everyone_else_variation_helper(self):
        """Test the _get_everyone_else_variation static method directly."""
        # Create a Layer with multiple experiment dicts
        layer = entities.Layer(
            id='rollout_1',
            experiments=[
                {
                    'id': 'rule_1',
                    'key': 'rule_1',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'rollout_1',
                    'audienceIds': [],
                    'trafficAllocation': [],
                    'variations': [
                        {'key': 'var_1', 'id': 'var_1', 'featureEnabled': True}
                    ],
                },
                {
                    'id': 'everyone_else',
                    'key': 'everyone_else',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'rollout_1',
                    'audienceIds': [],
                    'trafficAllocation': [],
                    'variations': [
                        {'key': 'ee_var', 'id': 'ee_var', 'featureEnabled': False}
                    ],
                },
            ],
        )

        result = ProjectConfig._get_everyone_else_variation(layer)
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'ee_var')
        self.assertEqual(result['key'], 'ee_var')

    def test_get_everyone_else_variation_empty_rollout(self):
        """Test _get_everyone_else_variation returns None for empty rollout."""
        layer = entities.Layer(id='empty_rollout', experiments=[])
        result = ProjectConfig._get_everyone_else_variation(layer)
        self.assertIsNone(result)

    def test_get_everyone_else_variation_no_variations(self):
        """Test _get_everyone_else_variation returns None when last rule has no variations."""
        layer = entities.Layer(
            id='rollout_1',
            experiments=[
                {
                    'id': 'rule_1',
                    'key': 'rule_1',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': 'rollout_1',
                    'audienceIds': [],
                    'trafficAllocation': [],
                    'variations': [],
                },
            ],
        )

        result = ProjectConfig._get_everyone_else_variation(layer)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
