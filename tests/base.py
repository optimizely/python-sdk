# Copyright 2016-2020, Optimizely
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
import unittest
from six import PY3

from optimizely import optimizely

if PY3:

    def long(a):
        raise NotImplementedError('Tests should only call `long` if running in PY2')


class BaseTest(unittest.TestCase):
    def assertStrictTrue(self, to_assert):
        self.assertIs(to_assert, True)

    def assertStrictFalse(self, to_assert):
        self.assertIs(to_assert, False)

    def setUp(self, config_dict='config_dict'):
        self.config_dict = {
            'revision': '42',
            'version': '2',
            'events': [
                {'key': 'test_event', 'experimentIds': ['111127'], 'id': '111095'},
                {'key': 'Total Revenue', 'experimentIds': ['111127'], 'id': '111096'},
            ],
            'experiments': [
                {
                    'key': 'test_experiment',
                    'status': 'Running',
                    'forcedVariations': {'user_1': 'control', 'user_2': 'control'},
                    'layerId': '111182',
                    'audienceIds': ['11154'],
                    'trafficAllocation': [
                        {'entityId': '111128', 'endOfRange': 4000},
                        {'entityId': '', 'endOfRange': 5000},
                        {'entityId': '111129', 'endOfRange': 9000},
                    ],
                    'id': '111127',
                    'variations': [{'key': 'control', 'id': '111128'}, {'key': 'variation', 'id': '111129'}],
                }
            ],
            'groups': [
                {
                    'id': '19228',
                    'policy': 'random',
                    'experiments': [
                        {
                            'id': '32222',
                            'key': 'group_exp_1',
                            'status': 'Running',
                            'audienceIds': [],
                            'layerId': '111183',
                            'variations': [
                                {'key': 'group_exp_1_control', 'id': '28901'},
                                {'key': 'group_exp_1_variation', 'id': '28902'},
                            ],
                            'forcedVariations': {'user_1': 'group_exp_1_control', 'user_2': 'group_exp_1_control'},
                            'trafficAllocation': [
                                {'entityId': '28901', 'endOfRange': 3000},
                                {'entityId': '28902', 'endOfRange': 9000},
                            ],
                        },
                        {
                            'id': '32223',
                            'key': 'group_exp_2',
                            'status': 'Running',
                            'audienceIds': [],
                            'layerId': '111184',
                            'variations': [
                                {'key': 'group_exp_2_control', 'id': '28905'},
                                {'key': 'group_exp_2_variation', 'id': '28906'},
                            ],
                            'forcedVariations': {'user_1': 'group_exp_2_control', 'user_2': 'group_exp_2_control'},
                            'trafficAllocation': [
                                {'entityId': '28905', 'endOfRange': 8000},
                                {'entityId': '28906', 'endOfRange': 10000},
                            ],
                        },
                    ],
                    'trafficAllocation': [
                        {'entityId': '32222', "endOfRange": 3000},
                        {'entityId': '32223', 'endOfRange': 7500},
                    ],
                }
            ],
            'accountId': '12001',
            'attributes': [
                {'key': 'test_attribute', 'id': '111094'},
                {'key': 'boolean_key', 'id': '111196'},
                {'key': 'integer_key', 'id': '111197'},
                {'key': 'double_key', 'id': '111198'},
            ],
            'audiences': [
                {
                    'name': 'Test attribute users 1',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
                    'id': '11154',
                },
                {
                    'name': 'Test attribute users 2',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
                    'id': '11159',
                },
            ],
            'projectId': '111001',
        }

        # datafile version 4
        self.config_dict_with_features = {
            'revision': '1',
            'accountId': '12001',
            'projectId': '111111',
            'version': '4',
            'botFiltering': True,
            'events': [{'key': 'test_event', 'experimentIds': ['111127'], 'id': '111095'}],
            'experiments': [
                {
                    'key': 'test_experiment',
                    'status': 'Running',
                    'forcedVariations': {},
                    'layerId': '111182',
                    'audienceIds': [],
                    'trafficAllocation': [
                        {'entityId': '111128', 'endOfRange': 5000},
                        {'entityId': '111129', 'endOfRange': 9000},
                    ],
                    'id': '111127',
                    'variations': [
                        {
                            'key': 'control',
                            'id': '111128',
                            'featureEnabled': False,
                            'variables': [
                                {'id': '127', 'value': 'false'},
                                {'id': '128', 'value': 'prod'},
                                {'id': '129', 'value': '10.01'},
                                {'id': '130', 'value': '4242'},
                                {'id': '132', 'value': '{"test": 122}'},
                                {'id': '133', 'value': '{"true_test": 1.3}'},
                            ],
                        },
                        {
                            'key': 'variation',
                            'id': '111129',
                            'featureEnabled': True,
                            'variables': [
                                {'id': '127', 'value': 'true'},
                                {'id': '128', 'value': 'staging'},
                                {'id': '129', 'value': '10.02'},
                                {'id': '130', 'value': '4243'},
                                {'id': '132', 'value': '{"test": 123}'},
                                {'id': '133', 'value': '{"true_test": 1.4}'},
                            ],
                        },
                    ],
                },
                {
                    'key': 'test_experiment2',
                    'status': 'Running',
                    'layerId': '5',
                    'audienceIds': [],
                    'id': '111133',
                    'forcedVariations': {},
                    'trafficAllocation': [
                        {'entityId': '122239', 'endOfRange': 5000},
                        {'entityId': '122240', 'endOfRange': 10000},
                    ],
                    'variations': [
                        {
                            'id': '122239',
                            'key': 'control',
                            'variables': [],
                        },
                        {
                            'id': '122240',
                            'key': 'variation',
                            'variables': [],
                        },
                    ],
                },
            ],
            'groups': [
                {
                    'id': '19228',
                    'policy': 'random',
                    'experiments': [
                        {
                            'id': '32222',
                            'key': 'group_exp_1',
                            'status': 'Running',
                            'audienceIds': [],
                            'layerId': '111183',
                            'variations': [
                                {'key': 'group_exp_1_control', 'id': '28901'},
                                {'key': 'group_exp_1_variation', 'id': '28902'},
                            ],
                            'forcedVariations': {'user_1': 'group_exp_1_control', 'user_2': 'group_exp_1_control'},
                            'trafficAllocation': [
                                {'entityId': '28901', 'endOfRange': 3000},
                                {'entityId': '28902', 'endOfRange': 9000},
                            ],
                        },
                        {
                            'id': '32223',
                            'key': 'group_exp_2',
                            'status': 'Running',
                            'audienceIds': [],
                            'layerId': '111184',
                            'variations': [
                                {'key': 'group_exp_2_control', 'id': '28905'},
                                {'key': 'group_exp_2_variation', 'id': '28906'},
                            ],
                            'forcedVariations': {'user_1': 'group_exp_2_control', 'user_2': 'group_exp_2_control'},
                            'trafficAllocation': [
                                {'entityId': '28905', 'endOfRange': 8000},
                                {'entityId': '28906', 'endOfRange': 10000},
                            ],
                        },
                    ],
                    'trafficAllocation': [
                        {'entityId': '32222', "endOfRange": 3000},
                        {'entityId': '32223', 'endOfRange': 7500},
                    ],
                }
            ],
            'attributes': [{'key': 'test_attribute', 'id': '111094'}],
            'audiences': [
                {
                    'name': 'Test attribute users 1',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
                    'id': '11154',
                },
                {
                    'name': 'Test attribute users 2',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
                    'id': '11159',
                },
            ],
            'rollouts': [
                {'id': '201111', 'experiments': []},
                {
                    'id': '211111',
                    'experiments': [
                        {
                            'id': '211127',
                            'key': '211127',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': '211111',
                            'audienceIds': ['11154'],
                            'trafficAllocation': [{'entityId': '211129', 'endOfRange': 9000}],
                            'variations': [
                                {
                                    'key': '211129',
                                    'id': '211129',
                                    'featureEnabled': True,
                                    'variables': [
                                        {'id': '132', 'value': 'true'},
                                        {'id': '133', 'value': 'Hello audience'},
                                        {'id': '134', 'value': '39.99'},
                                        {'id': '135', 'value': '399'},
                                        {'id': '136', 'value': '{"field": 12}'},
                                    ],
                                },
                                {
                                    'key': '211229',
                                    'id': '211229',
                                    'featureEnabled': False,
                                    'variables': [
                                        {'id': '132', 'value': 'true'},
                                        {'id': '133', 'value': 'environment'},
                                        {'id': '134', 'value': '49.99'},
                                        {'id': '135', 'value': '499'},
                                        {'id': '136', 'value': '{"field": 123}'},
                                    ],
                                },
                            ],
                        },
                        {
                            'id': '211137',
                            'key': '211137',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': '211111',
                            'audienceIds': ['11159'],
                            'trafficAllocation': [{'entityId': '211139', 'endOfRange': 3000}],
                            'variations': [{'key': '211139', 'id': '211139', 'featureEnabled': True}],
                        },
                        {
                            'id': '211147',
                            'key': '211147',
                            'status': 'Running',
                            'forcedVariations': {},
                            'layerId': '211111',
                            'audienceIds': [],
                            'trafficAllocation': [{'entityId': '211149', 'endOfRange': 6000}],
                            'variations': [{'key': '211149', 'id': '211149', 'featureEnabled': True}],
                        },
                    ],
                },
            ],
            'featureFlags': [
                {
                    'id': '91111',
                    'key': 'test_feature_in_experiment',
                    'experimentIds': ['111127'],
                    'rolloutId': '',
                    'variables': [
                        {'id': '127', 'key': 'is_working', 'defaultValue': 'true', 'type': 'boolean'},
                        {'id': '128', 'key': 'environment', 'defaultValue': 'devel', 'type': 'string'},
                        {'id': '129', 'key': 'cost', 'defaultValue': '10.99', 'type': 'double'},
                        {'id': '130', 'key': 'count', 'defaultValue': '999', 'type': 'integer'},
                        {'id': '131', 'key': 'variable_without_usage', 'defaultValue': '45', 'type': 'integer'},
                        {'id': '132', 'key': 'object', 'defaultValue': '{"test": 12}', 'type': 'string',
                         'subType': 'json'},
                        {'id': '133', 'key': 'true_object', 'defaultValue': '{"true_test": 23.54}', 'type': 'json'},
                    ],
                },
                {
                    'id': '91112',
                    'key': 'test_feature_in_rollout',
                    'experimentIds': [],
                    'rolloutId': '211111',
                    'variables': [
                        {'id': '132', 'key': 'is_running', 'defaultValue': 'false', 'type': 'boolean'},
                        {'id': '133', 'key': 'message', 'defaultValue': 'Hello', 'type': 'string'},
                        {'id': '134', 'key': 'price', 'defaultValue': '99.99', 'type': 'double'},
                        {'id': '135', 'key': 'count', 'defaultValue': '999', 'type': 'integer'},
                        {'id': '136', 'key': 'object', 'defaultValue': '{"field": 1}', 'type': 'string',
                         'subType': 'json'},
                    ],
                },
                {
                    'id': '91113',
                    'key': 'test_feature_in_group',
                    'experimentIds': ['32222'],
                    'rolloutId': '',
                    'variables': [],
                },
                {
                    'id': '91114',
                    'key': 'test_feature_in_experiment_and_rollout',
                    'experimentIds': ['32223'],
                    'rolloutId': '211111',
                    'variables': [],
                },
            ],
        }

        self.config_dict_with_multiple_experiments = {
            'revision': '42',
            'version': '2',
            'events': [
                {'key': 'test_event', 'experimentIds': ['111127', '111130'], 'id': '111095'},
                {'key': 'Total Revenue', 'experimentIds': ['111127'], 'id': '111096'},
            ],
            'experiments': [
                {
                    'key': 'test_experiment',
                    'status': 'Running',
                    'forcedVariations': {'user_1': 'control', 'user_2': 'control'},
                    'layerId': '111182',
                    'audienceIds': ['11154'],
                    'trafficAllocation': [
                        {'entityId': '111128', 'endOfRange': 4000},
                        {'entityId': '', 'endOfRange': 5000},
                        {'entityId': '111129', 'endOfRange': 9000},
                    ],
                    'id': '111127',
                    'variations': [{'key': 'control', 'id': '111128'}, {'key': 'variation', 'id': '111129'}],
                },
                {
                    'key': 'test_experiment_2',
                    'status': 'Running',
                    'forcedVariations': {'user_1': 'control', 'user_2': 'control'},
                    'layerId': '111182',
                    'audienceIds': ['11154'],
                    'trafficAllocation': [
                        {'entityId': '111131', 'endOfRange': 4000},
                        {'entityId': '', 'endOfRange': 5000},
                        {'entityId': '111132', 'endOfRange': 9000},
                    ],
                    'id': '111130',
                    'variations': [{'key': 'control', 'id': '111131'}, {'key': 'variation', 'id': '111132'}],
                },
            ],
            'groups': [
                {
                    'id': '19228',
                    'policy': 'random',
                    'experiments': [
                        {
                            'id': '32222',
                            'key': 'group_exp_1',
                            'status': 'Running',
                            'audienceIds': [],
                            'layerId': '111183',
                            'variations': [
                                {'key': 'group_exp_1_control', 'id': '28901'},
                                {'key': 'group_exp_1_variation', 'id': '28902'},
                            ],
                            'forcedVariations': {'user_1': 'group_exp_1_control', 'user_2': 'group_exp_1_control'},
                            'trafficAllocation': [
                                {'entityId': '28901', 'endOfRange': 3000},
                                {'entityId': '28902', 'endOfRange': 9000},
                            ],
                        },
                        {
                            'id': '32223',
                            'key': 'group_exp_2',
                            'status': 'Running',
                            'audienceIds': [],
                            'layerId': '111184',
                            'variations': [
                                {'key': 'group_exp_2_control', 'id': '28905'},
                                {'key': 'group_exp_2_variation', 'id': '28906'},
                            ],
                            'forcedVariations': {'user_1': 'group_exp_2_control', 'user_2': 'group_exp_2_control'},
                            'trafficAllocation': [
                                {'entityId': '28905', 'endOfRange': 8000},
                                {'entityId': '28906', 'endOfRange': 10000},
                            ],
                        },
                    ],
                    'trafficAllocation': [
                        {'entityId': '32222', "endOfRange": 3000},
                        {'entityId': '32223', 'endOfRange': 7500},
                    ],
                }
            ],
            'accountId': '12001',
            'attributes': [
                {'key': 'test_attribute', 'id': '111094'},
                {'key': 'boolean_key', 'id': '111196'},
                {'key': 'integer_key', 'id': '111197'},
                {'key': 'double_key', 'id': '111198'},
            ],
            'audiences': [
                {
                    'name': 'Test attribute users 1',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
                    'id': '11154',
                },
                {
                    'name': 'Test attribute users 2',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
                    'id': '11159',
                },
            ],
            'projectId': '111001',
        }

        self.config_dict_with_unsupported_version = {
            'version': '5',
            'rollouts': [],
            'projectId': '10431130345',
            'variables': [],
            'featureFlags': [],
            'experiments': [
                {
                    'status': 'Running',
                    'key': 'ab_running_exp_untargeted',
                    'layerId': '10417730432',
                    'trafficAllocation': [{'entityId': '10418551353', 'endOfRange': 10000}],
                    'audienceIds': [],
                    'variations': [
                        {'variables': [], 'id': '10418551353', 'key': 'all_traffic_variation'},
                        {'variables': [], 'id': '10418510624', 'key': 'no_traffic_variation'},
                    ],
                    'forcedVariations': {},
                    'id': '10420810910',
                }
            ],
            'audiences': [],
            'groups': [],
            'attributes': [],
            'accountId': '10367498574',
            'events': [{'experimentIds': ['10420810910'], 'id': '10404198134', 'key': 'winning'}],
            'revision': '1337',
        }

        self.config_dict_with_typed_audiences = {
            'version': '4',
            'rollouts': [
                {
                    'experiments': [
                        {
                            'status': 'Running',
                            'key': '11488548027',
                            'layerId': '11551226731',
                            'trafficAllocation': [{'entityId': '11557362669', 'endOfRange': 10000}],
                            'audienceIds': [
                                '3468206642',
                                '3988293898',
                                '3988293899',
                                '3468206646',
                                '3468206647',
                                '3468206644',
                                '3468206643',
                                '18278344267'
                            ],
                            'variations': [
                                {'variables': [], 'id': '11557362669', 'key': '11557362669', 'featureEnabled': True}
                            ],
                            'forcedVariations': {},
                            'id': '11488548027',
                        }
                    ],
                    'id': '11551226731',
                },
                {
                    'experiments': [
                        {
                            'status': 'Paused',
                            'key': '11630490911',
                            'layerId': '11638870867',
                            'trafficAllocation': [{'entityId': '11475708558', 'endOfRange': 0}],
                            'audienceIds': [],
                            'variations': [
                                {'variables': [], 'id': '11475708558', 'key': '11475708558', 'featureEnabled': False}
                            ],
                            'forcedVariations': {},
                            'id': '11630490911',
                        }
                    ],
                    'id': '11638870867',
                },
                {
                    'experiments': [
                        {
                            'status': 'Running',
                            'key': '11488548028',
                            'layerId': '11551226732',
                            'trafficAllocation': [{'entityId': '11557362670', 'endOfRange': 10000}],
                            'audienceIds': ['0'],
                            'audienceConditions': [
                                'and',
                                ['or', '3468206642', '3988293898'],
                                ['or', '3988293899', '3468206646', '3468206647', '3468206644', '3468206643', '18278344267'],
                            ],
                            'variations': [
                                {'variables': [], 'id': '11557362670', 'key': '11557362670', 'featureEnabled': True}
                            ],
                            'forcedVariations': {},
                            'id': '11488548028',
                        }
                    ],
                    'id': '11551226732',
                },
                {
                    'experiments': [
                        {
                            'status': 'Paused',
                            'key': '11630490912',
                            'layerId': '11638870868',
                            'trafficAllocation': [{'entityId': '11475708559', 'endOfRange': 0}],
                            'audienceIds': [],
                            'variations': [
                                {'variables': [], 'id': '11475708559', 'key': '11475708559', 'featureEnabled': False}
                            ],
                            'forcedVariations': {},
                            'id': '11630490912',
                        }
                    ],
                    'id': '11638870868',
                },
            ],
            'anonymizeIP': False,
            'projectId': '11624721371',
            'variables': [],
            'featureFlags': [
                {'experimentIds': [], 'rolloutId': '11551226731', 'variables': [], 'id': '11477755619', 'key': 'feat'},
                {
                    'experimentIds': ['11564051718'],
                    'rolloutId': '11638870867',
                    'variables': [{'defaultValue': 'x', 'type': 'string', 'id': '11535264366', 'key': 'x'}],
                    'id': '11567102051',
                    'key': 'feat_with_var',
                },
                {
                    'experimentIds': [],
                    'rolloutId': '11551226732',
                    'variables': [],
                    'id': '11567102052',
                    'key': 'feat2',
                },
                {
                    'experimentIds': ['1323241599'],
                    'rolloutId': '11638870868',
                    'variables': [{'defaultValue': '10', 'type': 'integer', 'id': '11535264367', 'key': 'z'}],
                    'id': '11567102053',
                    'key': 'feat2_with_var',
                },
            ],
            'experiments': [
                {
                    'status': 'Running',
                    'key': 'feat_with_var_test',
                    'layerId': '11504144555',
                    'trafficAllocation': [{'entityId': '11617170975', 'endOfRange': 10000}],
                    'audienceIds': [
                        '3468206642',
                        '3988293898',
                        '3988293899',
                        '3468206646',
                        '3468206647',
                        '3468206644',
                        '3468206643',
                        '18278344267'
                    ],
                    'variations': [
                        {
                            'variables': [{'id': '11535264366', 'value': 'xyz'}],
                            'id': '11617170975',
                            'key': 'variation_2',
                            'featureEnabled': True,
                        }
                    ],
                    'forcedVariations': {},
                    'id': '11564051718',
                },
                {
                    'id': '1323241597',
                    'key': 'typed_audience_experiment',
                    'layerId': '1630555627',
                    'status': 'Running',
                    'variations': [{'id': '1423767503', 'key': 'A', 'variables': []}],
                    'trafficAllocation': [{'entityId': '1423767503', 'endOfRange': 10000}],
                    'audienceIds': [
                        '3468206642',
                        '3988293898',
                        '3988293899',
                        '3468206646',
                        '3468206647',
                        '3468206644',
                        '3468206643',
                        '18278344267'
                    ],
                    'forcedVariations': {},
                },
                {
                    'id': '1323241598',
                    'key': 'audience_combinations_experiment',
                    'layerId': '1323241598',
                    'status': 'Running',
                    'variations': [{'id': '1423767504', 'key': 'A', 'variables': []}],
                    'trafficAllocation': [{'entityId': '1423767504', 'endOfRange': 10000}],
                    'audienceIds': ['0'],
                    'audienceConditions': [
                        'and',
                        ['or', '3468206642', '3988293898'],
                        ['or', '3988293899', '3468206646', '3468206647', '3468206644', '3468206643', '18278344267'],
                    ],
                    'forcedVariations': {},
                },
                {
                    'id': '1323241599',
                    'key': 'feat2_with_var_test',
                    'layerId': '1323241600',
                    'status': 'Running',
                    'variations': [
                        {
                            'variables': [{'id': '11535264367', 'value': '150'}],
                            'id': '1423767505',
                            'key': 'variation_2',
                            'featureEnabled': True,
                        }
                    ],
                    'trafficAllocation': [{'entityId': '1423767505', 'endOfRange': 10000}],
                    'audienceIds': ['0'],
                    'audienceConditions': [
                        'and',
                        ['or', '3468206642', '3988293898'],
                        ['or', '3988293899', '3468206646', '3468206647', '3468206644', '3468206643', '18278344267'],
                    ],
                    'forcedVariations': {},
                },
            ],
            'audiences': [
                {
                    'id': '3468206642',
                    'name': 'exactString',
                    'conditions': '["and", ["or", ["or", {"name": "house", '
                                  '"type": "custom_attribute", "value": "Gryffindor"}]]]',
                },
                {
                    'id': '3988293898',
                    'name': '$$dummySubstringString',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
                {
                    'id': '3988293899',
                    'name': '$$dummyExists',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
                {
                    'id': '3468206646',
                    'name': '$$dummyExactNumber',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
                {
                    'id': '3468206647',
                    'name': '$$dummyGtNumber',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
                {
                    'id': '3468206644',
                    'name': '$$dummyLtNumber',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
                {
                    'id': '3468206643',
                    'name': '$$dummyExactBoolean',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
                {
                    'id': '3468206645',
                    'name': '$$dummyMultipleCustomAttrs',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
                {
                    'id': '0',
                    'name': '$$dummy',
                    'conditions': '{ "type": "custom_attribute", '
                                  '"name": "$opt_dummy_attribute", "value": "impossible_value" }',
                },
            ],
            'typedAudiences': [
                {
                    'id': '3988293898',
                    'name': 'substringString',
                    'conditions': [
                        'and',
                        [
                            'or',
                            [
                                'or',
                                {
                                    'name': 'house',
                                    'type': 'custom_attribute',
                                    'match': 'substring',
                                    'value': 'Slytherin',
                                },
                            ],
                        ],
                    ],
                },
                {
                    'id': '3988293899',
                    'name': 'exists',
                    'conditions': [
                        'and',
                        [
                            'or',
                            ['or', {'name': 'favorite_ice_cream', 'type': 'custom_attribute', 'match': 'exists'}],
                        ],
                    ],
                },
                {
                    'id': '3468206646',
                    'name': 'exactNumber',
                    'conditions': [
                        'and',
                        [
                            'or',
                            ['or', {'name': 'lasers', 'type': 'custom_attribute', 'match': 'exact', 'value': 45.5}],
                        ],
                    ],
                },
                {
                    'id': '3468206647',
                    'name': 'gtNumber',
                    'conditions': [
                        'and',
                        ['or', ['or', {'name': 'lasers', 'type': 'custom_attribute', 'match': 'gt', 'value': 70}]],
                    ],
                },
                {
                    'id': '3468206644',
                    'name': 'ltNumber',
                    'conditions': [
                        'and',
                        ['or', ['or', {'name': 'lasers', 'type': 'custom_attribute', 'match': 'lt', 'value': 1.0}]],
                    ],
                },
                {
                    'id': '3468206643',
                    'name': 'exactBoolean',
                    'conditions': [
                        'and',
                        [
                            'or',
                            [
                                'or',
                                {'name': 'should_do_it', 'type': 'custom_attribute', 'match': 'exact', 'value': True},
                            ],
                        ],
                    ],
                },
                {
                    'id': '3468206645',
                    'name': 'multiple_custom_attrs',
                    'conditions': [
                        "and",
                        [
                            "or",
                            [
                                "or",
                                {"type": "custom_attribute", "name": "browser", "value": "chrome"},
                                {"type": "custom_attribute", "name": "browser", "value": "firefox"},
                            ],
                        ],
                    ],
                },
                {
                    "id": "18278344267",
                    "name": "semverReleaseLt1.2.3Gt1.0.0",
                    "conditions": [
                        "and",
                        [
                            "or",
                            [
                                "or",
                                {
                                    "value": "1.2.3",
                                    "type": "custom_attribute",
                                    "name": "android-release",
                                    "match": "semver_lt"
                                }
                            ]
                        ],
                        [
                            "or",
                            [
                                "or",
                                {
                                    "value": "1.0.0",
                                    "type": "custom_attribute",
                                    "name": "android-release",
                                    "match": "semver_gt"
                                }
                            ]
                        ]
                    ]
                }
            ],
            'groups': [],
            'attributes': [
                {'key': 'house', 'id': '594015'},
                {'key': 'lasers', 'id': '594016'},
                {'key': 'should_do_it', 'id': '594017'},
                {'key': 'favorite_ice_cream', 'id': '594018'},
                {'key': 'android-release', 'id': '594019'},

            ],
            'botFiltering': False,
            'accountId': '4879520872',
            'events': [
                {'key': 'item_bought', 'id': '594089', 'experimentIds': ['11564051718', '1323241597']},
                {'key': 'user_signed_up', 'id': '594090', 'experimentIds': ['1323241598', '1323241599']},
            ],
            'revision': '3',
        }

        config = getattr(self, config_dict)
        self.optimizely = optimizely.Optimizely(json.dumps(config))
        self.project_config = self.optimizely.config_manager.get_config()
