# Copyright 2020, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from optimizely import optimizely
from optimizely import optimizely_config
from . import base


class OptimizelyConfigTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self)
        opt_instance = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        self.project_config = opt_instance.config_manager.get_config()
        self.opt_config_service = optimizely_config.OptimizelyConfigService(self.project_config)

        self.expected_config = {
            'experiments_map': {
                'test_experiment2': {
                    'variations_map': {
                        'control': {
                            'variables_map': {

                            },
                            'id': '122239',
                            'key': 'control',
                            'feature_enabled': None
                        },
                        'variation': {
                            'variables_map': {

                            },
                            'id': '122240',
                            'key': 'variation',
                            'feature_enabled': None
                        }
                    },
                    'id': '111133',
                    'key': 'test_experiment2'
                },
                'test_experiment': {
                    'variations_map': {
                        'control': {
                            'variables_map': {
                                'environment': {
                                    'key': 'environment',
                                    'type': 'string',
                                    'id': '128',
                                    'value': 'devel'
                                },
                                'count': {
                                    'key': 'count',
                                    'type': 'integer',
                                    'id': '130',
                                    'value': '999'
                                },
                                'is_working': {
                                    'key': 'is_working',
                                    'type': 'boolean',
                                    'id': '127',
                                    'value': 'true'
                                },
                                'cost': {
                                    'key': 'cost',
                                    'type': 'double',
                                    'id': '129',
                                    'value': '10.99'
                                },
                                'object': {
                                    'id': '132',
                                    'key': 'object',
                                    'type': 'json',
                                    'value': '{"test": 12}'
                                },
                                'true_object': {
                                    'id': '133',
                                    'key': 'true_object',
                                    'type': 'json',
                                    'value': '{"true_test": 23.54}'
                                },
                                'variable_without_usage': {
                                    'key': 'variable_without_usage',
                                    'type': 'integer',
                                    'id': '131',
                                    'value': '45'
                                }
                            },
                            'id': '111128',
                            'key': 'control',
                            'feature_enabled': False
                        },
                        'variation': {
                            'variables_map': {
                                'environment': {
                                    'key': 'environment',
                                    'type': 'string',
                                    'id': '128',
                                    'value': 'staging'
                                },
                                'count': {
                                    'key': 'count',
                                    'type': 'integer',
                                    'id': '130',
                                    'value': '4243'
                                },
                                'is_working': {
                                    'key': 'is_working',
                                    'type': 'boolean',
                                    'id': '127',
                                    'value': 'true'
                                },
                                'cost': {
                                    'key': 'cost',
                                    'type': 'double',
                                    'id': '129',
                                    'value': '10.02'
                                },
                                'object': {
                                    'id': '132',
                                    'key': 'object',
                                    'type': 'json',
                                    'value': '{"test": 123}'
                                },
                                'true_object': {
                                    'id': '133',
                                    'key': 'true_object',
                                    'type': 'json',
                                    'value': '{"true_test": 1.4}'
                                },
                                'variable_without_usage': {
                                    'key': 'variable_without_usage',
                                    'type': 'integer',
                                    'id': '131',
                                    'value': '45'
                                }
                            },
                            'id': '111129',
                            'key': 'variation',
                            'feature_enabled': True
                        }
                    },
                    'id': '111127',
                    'key': 'test_experiment'
                },
                'group_exp_1': {
                    'variations_map': {
                        'group_exp_1_variation': {
                            'variables_map': {

                            },
                            'id': '28902',
                            'key': 'group_exp_1_variation',
                            'feature_enabled': None
                        },
                        'group_exp_1_control': {
                            'variables_map': {

                            },
                            'id': '28901',
                            'key': 'group_exp_1_control',
                            'feature_enabled': None
                        }
                    },
                    'id': '32222',
                    'key': 'group_exp_1'
                },
                'group_exp_2': {
                    'variations_map': {
                        'group_exp_2_variation': {
                            'variables_map': {

                            },
                            'id': '28906',
                            'key': 'group_exp_2_variation',
                            'feature_enabled': None
                        },
                        'group_exp_2_control': {
                            'variables_map': {

                            },
                            'id': '28905',
                            'key': 'group_exp_2_control',
                            'feature_enabled': None
                        }
                    },
                    'id': '32223',
                    'key': 'group_exp_2'
                }
            },
            'features_map': {
                'test_feature_in_experiment': {
                    'variables_map': {
                        'environment': {
                            'key': 'environment',
                            'type': 'string',
                            'id': '128',
                            'value': 'devel'
                        },
                        'count': {
                            'key': 'count',
                            'type': 'integer',
                            'id': '130',
                            'value': '999'
                        },
                        'is_working': {
                            'key': 'is_working',
                            'type': 'boolean',
                            'id': '127',
                            'value': 'true'
                        },
                        'cost': {
                            'key': 'cost',
                            'type': 'double',
                            'id': '129',
                            'value': '10.99'
                        },
                        'object': {
                            'id': '132',
                            'key': 'object',
                            'type': 'json',
                            'value': '{"test": 12}'
                        },
                        'true_object': {
                            'id': '133',
                            'key': 'true_object',
                            'type': 'json',
                            'value': '{"true_test": 23.54}'
                        },
                        'variable_without_usage': {
                            'key': 'variable_without_usage',
                            'type': 'integer',
                            'id': '131',
                            'value': '45'
                        }
                    },
                    'experiments_map': {
                        'test_experiment': {
                            'variations_map': {
                                'control': {
                                    'variables_map': {
                                        'environment': {
                                            'key': 'environment',
                                            'type': 'string',
                                            'id': '128',
                                            'value': 'devel'
                                        },
                                        'count': {
                                            'key': 'count',
                                            'type': 'integer',
                                            'id': '130',
                                            'value': '999'
                                        },
                                        'is_working': {
                                            'key': 'is_working',
                                            'type': 'boolean',
                                            'id': '127',
                                            'value': 'true'
                                        },
                                        'cost': {
                                            'key': 'cost',
                                            'type': 'double',
                                            'id': '129',
                                            'value': '10.99'
                                        },
                                        'object': {
                                            'id': '132',
                                            'key': 'object',
                                            'type': 'json',
                                            'value': '{"test": 12}'
                                        },
                                        'true_object': {
                                            'id': '133',
                                            'key': 'true_object',
                                            'type': 'json',
                                            'value': '{"true_test": 23.54}'
                                        },
                                        'variable_without_usage': {
                                            'key': 'variable_without_usage',
                                            'type': 'integer',
                                            'id': '131',
                                            'value': '45'
                                        }
                                    },
                                    'id': '111128',
                                    'key': 'control',
                                    'feature_enabled': False
                                },
                                'variation': {
                                    'variables_map': {
                                        'environment': {
                                            'key': 'environment',
                                            'type': 'string',
                                            'id': '128',
                                            'value': 'staging'
                                        },
                                        'count': {
                                            'key': 'count',
                                            'type': 'integer',
                                            'id': '130',
                                            'value': '4243'
                                        },
                                        'is_working': {
                                            'key': 'is_working',
                                            'type': 'boolean',
                                            'id': '127',
                                            'value': 'true'
                                        },
                                        'cost': {
                                            'key': 'cost',
                                            'type': 'double',
                                            'id': '129',
                                            'value': '10.02'
                                        },
                                        'object': {
                                            'id': '132',
                                            'key': 'object',
                                            'type': 'json',
                                            'value': '{"test": 123}'
                                        },
                                        'true_object': {
                                            'id': '133',
                                            'key': 'true_object',
                                            'type': 'json',
                                            'value': '{"true_test": 1.4}'
                                        },
                                        'variable_without_usage': {
                                            'key': 'variable_without_usage',
                                            'type': 'integer',
                                            'id': '131',
                                            'value': '45'
                                        }
                                    },
                                    'id': '111129',
                                    'key': 'variation',
                                    'feature_enabled': True
                                }
                            },
                            'id': '111127',
                            'key': 'test_experiment'
                        }
                    },
                    'id': '91111',
                    'key': 'test_feature_in_experiment'
                },
                'test_feature_in_rollout': {
                    'variables_map': {
                        'count': {
                            'key': 'count',
                            'type': 'integer',
                            'id': '135',
                            'value': '999'
                        },
                        'message': {
                            'key': 'message',
                            'type': 'string',
                            'id': '133',
                            'value': 'Hello'
                        },
                        'price': {
                            'key': 'price',
                            'type': 'double',
                            'id': '134',
                            'value': '99.99'
                        },
                        'is_running': {
                            'key': 'is_running',
                            'type': 'boolean',
                            'id': '132',
                            'value': 'false'
                        },
                        'object': {
                            'id': '136',
                            'key': 'object',
                            'type': 'json',
                            'value': '{"field": 1}'
                        }
                    },
                    'experiments_map': {

                    },
                    'id': '91112',
                    'key': 'test_feature_in_rollout'
                },
                'test_feature_in_group': {
                    'variables_map': {

                    },
                    'experiments_map': {
                        'group_exp_1': {
                            'variations_map': {
                                'group_exp_1_variation': {
                                    'variables_map': {

                                    },
                                    'id': '28902',
                                    'key': 'group_exp_1_variation',
                                    'feature_enabled': None
                                },
                                'group_exp_1_control': {
                                    'variables_map': {

                                    },
                                    'id': '28901',
                                    'key': 'group_exp_1_control',
                                    'feature_enabled': None
                                }
                            },
                            'id': '32222',
                            'key': 'group_exp_1'
                        }
                    },
                    'id': '91113',
                    'key': 'test_feature_in_group'
                },
                'test_feature_in_experiment_and_rollout': {
                    'variables_map': {

                    },
                    'experiments_map': {
                        'group_exp_2': {
                            'variations_map': {
                                'group_exp_2_variation': {
                                    'variables_map': {

                                    },
                                    'id': '28906',
                                    'key': 'group_exp_2_variation',
                                    'feature_enabled': None
                                },
                                'group_exp_2_control': {
                                    'variables_map': {

                                    },
                                    'id': '28905',
                                    'key': 'group_exp_2_control',
                                    'feature_enabled': None
                                }
                            },
                            'id': '32223',
                            'key': 'group_exp_2'
                        }
                    },
                    'id': '91114',
                    'key': 'test_feature_in_experiment_and_rollout'
                }
            },
            'revision': '1',
            '_datafile': json.dumps(self.config_dict_with_features)
        }

        self.actual_config = self.opt_config_service.get_config()
        self.actual_config_dict = self.to_dict(self.actual_config)

    def to_dict(self, obj):
        return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

    def test__get_config(self):
        """ Test that get_config returns an expected instance of OptimizelyConfig. """

        self.assertIsInstance(self.actual_config, optimizely_config.OptimizelyConfig)
        self.assertEqual(self.expected_config, self.actual_config_dict)

    def test__get_config__invalid_project_config(self):
        """ Test that get_config returns None when invalid project config supplied. """

        opt_service = optimizely_config.OptimizelyConfigService({"key": "invalid"})
        self.assertIsNone(opt_service.get_config())

    def test__get_experiments_maps(self):
        """ Test that get_experiments_map returns expected experiment key and id maps. """

        actual_key_map, actual_id_map = self.opt_config_service._get_experiments_maps()
        expected_key_map = self.expected_config['experiments_map']

        self.assertIsInstance(actual_key_map, dict)
        for exp in actual_key_map.values():
            self.assertIsInstance(exp, optimizely_config.OptimizelyExperiment)

        self.assertEqual(expected_key_map, self.to_dict(actual_key_map))

        expected_id_map = {}
        for exp in expected_key_map.values():
            expected_id_map[exp['id']] = exp

        self.assertEqual(expected_id_map, self.to_dict(actual_id_map))

    def test__get_features_map(self):
        """ Test that get_features_map returns expected features map. """

        exp_key_map, exp_id_map = self.opt_config_service._get_experiments_maps()

        actual_feature_map = self.opt_config_service._get_features_map(exp_id_map)
        expected_feature_map = self.expected_config['features_map']

        self.assertIsInstance(actual_feature_map, dict)
        for feat in actual_feature_map.values():
            self.assertIsInstance(feat, optimizely_config.OptimizelyFeature)

        self.assertEqual(expected_feature_map, self.to_dict(actual_feature_map))

    def test__get_variations_map(self):
        """ Test that get_variations_map returns expected variations map. """

        experiment = self.project_config.experiments[0]
        actual_variations_map = self.opt_config_service._get_variations_map(experiment)

        expected_variations_map = self.expected_config['experiments_map']['test_experiment']['variations_map']

        self.assertIsInstance(actual_variations_map, dict)
        for variation in actual_variations_map.values():
            self.assertIsInstance(variation, optimizely_config.OptimizelyVariation)

        self.assertEqual(expected_variations_map, self.to_dict(actual_variations_map))

    def test__get_variables_map(self):
        """ Test that get_variables_map returns expected variables map. """

        experiment = self.project_config.experiments[0]
        variation = experiment['variations'][0]
        actual_variables_map = self.opt_config_service._get_variables_map(experiment, variation)

        expected_variations_map = self.expected_config['experiments_map']['test_experiment']['variations_map']
        expected_variables_map = expected_variations_map['control']['variables_map']

        self.assertIsInstance(actual_variables_map, dict)
        for variable in actual_variables_map.values():
            self.assertIsInstance(variable, optimizely_config.OptimizelyVariable)

        self.assertEqual(expected_variables_map, self.to_dict(actual_variables_map))

    def test__get_datafile(self):
        """ Test that get_datafile returns the expected datafile. """

        expected_datafile = json.dumps(self.config_dict_with_features)
        actual_datafile = self.actual_config.get_datafile()

        self.assertEqual(expected_datafile, actual_datafile)
