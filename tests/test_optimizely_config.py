# Copyright 2020-2021, Optimizely
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

from optimizely import optimizely, project_config
from optimizely import optimizely_config
from optimizely import logger
from . import base


class OptimizelyConfigTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self)
        opt_instance = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        self.project_config = opt_instance.config_manager.get_config()
        self.opt_config_service = optimizely_config.OptimizelyConfigService(self.project_config, logger.SimpleLogger())     # todo - added logger

        self.expected_config = {
            'sdk_key': 'features-test',
            'environment_key': '',
            'attributes': [{'key': 'test_attribute', 'id': '111094'}],
            'events': [{'key': 'test_event', 'experiment_ids': ['111127'], 'id': '111095'}],
            'audiences': [
                {
                    'name': 'Test attribute users 1',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
                    'id': '11154'
                },
                {
                    'name': 'Test attribute users 2',
                    'conditions': '["and", ["or", ["or", '
                    '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
                    'id': '11159'
                },
                {
                    'name': 'Test attribute users 3',
                    'conditions': "[\"and\", [\"or\", [\"or\", {\"match\": \"exact\", \"name\": \
                        \"experiment_attr\", \"type\": \"custom_attribute\", \"value\": \"group_experiment\"}]]]",
                    'id': '11160',
                }
            ],
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
                    'key': 'test_experiment2',
                    'audiences': ''
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
                    'key': 'test_experiment',
                    'audiences': ''
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
                    'key': 'group_exp_1',
                    'audiences': ''
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
                    'key': 'group_exp_2',
                    'audiences': ''
                },
                'group_2_exp_1': {
                    'variations_map': {
                        'var_1': {
                            'variables_map': {

                            },
                            'id': '38901',
                            'key': 'var_1',
                            'feature_enabled': None
                        },
                    },
                    'id': '42222',
                    'key': 'group_2_exp_1',
                    'audiences': '"Test attribute users 3"'
                },
                'group_2_exp_2': {
                    'variations_map': {
                        'var_1': {
                            'variables_map': {

                            },
                            'id': '38905',
                            'key': 'var_1',
                            'feature_enabled': None
                        },
                    },
                    'id': '42223',
                    'key': 'group_2_exp_2',
                    'audiences': '"Test attribute users 3"'
                },
                'group_2_exp_3': {
                    'variations_map': {
                        'var_1': {
                            'variables_map': {

                            },
                            'id': '38906',
                            'key': 'var_1',
                            'feature_enabled': None
                        },
                    },
                    'id': '42224',
                    'key': 'group_2_exp_3',
                    'audiences': '"Test attribute users 3"'
                },
                'test_experiment3': {
                    'variations_map': {
                        'control': {
                            'variables_map': {

                            },
                            'id': '222239',
                            'key': 'control',
                            'feature_enabled': None
                        },
                    },
                    'id': '111134',
                    'key': 'test_experiment3',
                    'audiences': '"Test attribute users 3"'
                },
                'test_experiment4': {
                    'variations_map': {
                        'control': {
                            'variables_map': {

                            },
                            'id': '222240',
                            'key': 'control',
                            'feature_enabled': None
                        },
                    },
                    'id': '111135',
                    'key': 'test_experiment4',
                    'audiences': '"Test attribute users 3"'
                },
                'test_experiment5': {
                    'variations_map': {
                        'control': {
                            'variables_map': {

                            },
                            'id': '222241',
                            'key': 'control',
                            'feature_enabled': None
                        },
                    },
                    'id': '111136',
                    'key': 'test_experiment5',
                    'audiences': '"Test attribute users 3"'
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
                            'key': 'test_experiment',
                            'audiences': ''
                        }
                    },
                    'delivery_rules': [],
                    'experiment_rules': [
                        {
                            'id': '111127',
                            'key': 'test_experiment',
                            'variations_map': {
                                'control': {
                                    'id': '111128',
                                    'key': 'control',
                                    'feature_enabled': False,
                                    'variables_map': {
                                        'is_working': {
                                            'id': '127',
                                            'key': 'is_working',
                                            'type': 'boolean',
                                            'value': 'true'
                                        },
                                        'environment': {
                                            'id': '128',
                                            'key': 'environment',
                                            'type': 'string',
                                            'value': 'devel'
                                        },
                                        'cost': {
                                            'id': '129',
                                            'key': 'cost',
                                            'type': 'double',
                                            'value': '10.99'
                                        },
                                        'count': {
                                            'id': '130',
                                            'key': 'count',
                                            'type': 'integer',
                                            'value': '999'
                                        },
                                        'variable_without_usage': {
                                            'id': '131',
                                            'key': 'variable_without_usage',
                                            'type': 'integer',
                                            'value': '45'
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
                                        }
                                    }
                                },
                                'variation': {
                                    'id': '111129',
                                    'key': 'variation',
                                    'feature_enabled': True,
                                    'variables_map': {
                                        'is_working': {
                                            'id': '127',
                                            'key': 'is_working',
                                            'type': 'boolean',
                                            'value': 'true'
                                        },
                                        'environment': {
                                            'id': '128',
                                            'key': 'environment',
                                            'type': 'string',
                                            'value': 'staging'
                                        },
                                        'cost': {
                                            'id': '129',
                                            'key': 'cost',
                                            'type': 'double',
                                            'value': '10.02'
                                        },
                                        'count': {
                                            'id': '130',
                                            'key': 'count',
                                            'type': 'integer',
                                            'value': '4243'
                                        },
                                        'variable_without_usage': {
                                            'id': '131',
                                            'key': 'variable_without_usage',
                                            'type': 'integer',
                                            'value': '45'
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
                                        }
                                    }
                                }
                            },
                            'audiences': ''
                        }
                    ],
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
                    'delivery_rules': [
                        {
                            'id': '211127',
                            'key': '211127',
                            'variations_map': {
                                '211129': {
                                    'id': '211129',
                                    'key': '211129',
                                    'feature_enabled': True,
                                    'variables_map': {
                                        'is_running': {
                                            'id': '132',
                                            'key': 'is_running',
                                            'type': 'boolean',
                                            'value': 'false'
                                        },
                                        'message': {
                                            'id': '133',
                                            'key': 'message',
                                            'type': 'string',
                                            'value': 'Hello'
                                        },
                                        'price': {
                                            'id': '134',
                                            'key': 'price',
                                            'type': 'double',
                                            'value': '99.99'
                                        },
                                        'count': {
                                            'id': '135',
                                            'key': 'count',
                                            'type': 'integer',
                                            'value': '999'
                                        },
                                        'object': {
                                            'id': '136',
                                            'key': 'object',
                                            'type': 'json',
                                            'value': '{"field": 1}'
                                        }
                                    }
                                },
                                '211229': {
                                    'id': '211229',
                                    'key': '211229',
                                    'feature_enabled': False,
                                    'variables_map': {
                                        'is_running': {
                                            'id': '132',
                                            'key': 'is_running',
                                            'type': 'boolean',
                                            'value': 'false'
                                        },
                                        'message': {
                                            'id': '133',
                                            'key': 'message',
                                            'type': 'string',
                                            'value': 'Hello'
                                        },
                                        'price': {
                                            'id': '134',
                                            'key': 'price',
                                            'type': 'double',
                                            'value': '99.99'
                                        },
                                        'count': {
                                            'id': '135',
                                            'key': 'count',
                                            'type': 'integer',
                                            'value': '999'
                                        },
                                        'object': {
                                            'id': '136',
                                            'key': 'object',
                                            'type': 'json',
                                            'value': '{"field": 1}'
                                        }
                                    }
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211137',
                            'key': '211137',
                            'variations_map': {
                                '211139': {
                                    'id': '211139',
                                    'key': '211139',
                                    'feature_enabled': True,
                                    'variables_map': {
                                        'is_running': {
                                            'id': '132',
                                            'key': 'is_running',
                                            'type': 'boolean',
                                            'value': 'false'
                                        },
                                        'message': {
                                            'id': '133',
                                            'key': 'message',
                                            'type': 'string',
                                            'value': 'Hello'
                                        },
                                        'price': {
                                            'id': '134',
                                            'key': 'price',
                                            'type': 'double',
                                            'value': '99.99'
                                        },
                                        'count': {
                                            'id': '135',
                                            'key': 'count',
                                            'type': 'integer',
                                            'value': '999'
                                        },
                                        'object': {
                                            'id': '136',
                                            'key': 'object',
                                            'type': 'json',
                                            'value': '{"field": 1}'
                                        }
                                    }
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211147',
                            'key': '211147',
                            'variations_map': {
                                '211149': {
                                    'id': '211149',
                                    'key': '211149',
                                    'feature_enabled': True,
                                    'variables_map': {
                                        'is_running': {
                                            'id': '132',
                                            'key': 'is_running',
                                            'type': 'boolean',
                                            'value': 'false'
                                        },
                                        'message': {
                                            'id': '133',
                                            'key': 'message',
                                            'type': 'string',
                                            'value': 'Hello'
                                        },
                                        'price': {
                                            'id': '134',
                                            'key': 'price',
                                            'type': 'double',
                                            'value': '99.99'
                                        },
                                        'count': {
                                            'id': '135',
                                            'key': 'count',
                                            'type': 'integer',
                                            'value': '999'
                                        },
                                        'object': {
                                            'id': '136',
                                            'key': 'object',
                                            'type': 'json',
                                            'value': '{"field": 1}'
                                        }
                                    }
                                }
                            },
                            'audiences': ''
                        }
                    ],
                    'experiment_rules': [],
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
                            'key': 'group_exp_1',
                            'audiences': ''
                        }
                    },
                    'delivery_rules': [],
                    'experiment_rules': [
                        {
                            'id': '32222',
                            'key': 'group_exp_1',
                            'variations_map': {
                                'group_exp_1_control': {
                                    'id': '28901',
                                    'key': 'group_exp_1_control',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                },
                                'group_exp_1_variation': {
                                    'id': '28902',
                                    'key': 'group_exp_1_variation',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        }
                    ],
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
                            'key': 'group_exp_2',
                            'audiences': ''
                        }
                    },
                    'delivery_rules': [
                        {
                            'id': '211127',
                            'key': '211127',
                            'variations_map': {
                                '211129': {
                                    'id': '211129',
                                    'key': '211129',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                },
                                '211229': {
                                    'id': '211229',
                                    'key': '211229',
                                    'feature_enabled': False,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211137',
                            'key': '211137',
                            'variations_map': {
                                '211139': {
                                    'id': '211139',
                                    'key': '211139',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211147',
                            'key': '211147',
                            'variations_map': {
                                '211149': {
                                    'id': '211149',
                                    'key': '211149',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        }
                    ],
                    'experiment_rules': [
                        {
                            'id': '32223',
                            'key': 'group_exp_2',
                            'variations_map': {
                                'group_exp_2_control': {
                                    'id': '28905',
                                    'key': 'group_exp_2_control',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                },
                                'group_exp_2_variation': {
                                    'id': '28906',
                                    'key': 'group_exp_2_variation',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        }
                    ],
                    'id': '91114',
                    'key': 'test_feature_in_experiment_and_rollout'
                },
                'test_feature_in_exclusion_group': {
                    'variables_map': {

                    },
                    'experiments_map': {
                        'group_2_exp_1': {
                            'variations_map': {
                                'var_1': {
                                    'variables_map': {

                                    },
                                    'id': '38901',
                                    'key': 'var_1',
                                    'feature_enabled': None
                                },
                            },
                            'id': '42222',
                            'key': 'group_2_exp_1',
                            'audiences': '"Test attribute users 3"'
                        },
                        'group_2_exp_2': {
                            'variations_map': {
                                'var_1': {
                                    'variables_map': {

                                    },
                                    'id': '38905',
                                    'key': 'var_1',
                                    'feature_enabled': None
                                },
                            },
                            'id': '42223',
                            'key': 'group_2_exp_2',
                            'audiences': '"Test attribute users 3"'
                        },
                        'group_2_exp_3': {
                            'variations_map': {
                                'var_1': {
                                    'variables_map': {

                                    },
                                    'id': '38906',
                                    'key': 'var_1',
                                    'feature_enabled': None
                                },
                            },
                            'id': '42224',
                            'key': 'group_2_exp_3',
                            'audiences': '"Test attribute users 3"'
                        }
                    },
                    'delivery_rules': [
                        {
                            'id': '211127',
                            'key': '211127',
                            'variations_map': {
                                '211129': {
                                    'id': '211129',
                                    'key': '211129',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                },
                                '211229': {
                                    'id': '211229',
                                    'key': '211229',
                                    'feature_enabled': False,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211137',
                            'key': '211137',
                            'variations_map': {
                                '211139': {
                                    'id': '211139',
                                    'key': '211139',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211147',
                            'key': '211147',
                            'variations_map': {
                                '211149': {
                                    'id': '211149',
                                    'key': '211149',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        }
                    ],
                    'experiment_rules': [
                        {
                            'id': '42222',
                            'key': 'group_2_exp_1',
                            'variations_map': {
                                'var_1': {
                                    'id': '38901',
                                    'key': 'var_1',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': '"Test attribute users 3"'
                        },
                        {
                            'id': '42223',
                            'key': 'group_2_exp_2',
                            'variations_map': {
                                'var_1': {
                                    'id': '38905',
                                    'key': 'var_1',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': '"Test attribute users 3"'
                        },
                        {
                            'id': '42224',
                            'key': 'group_2_exp_3',
                            'variations_map': {
                                'var_1': {
                                    'id': '38906',
                                    'key': 'var_1',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': '"Test attribute users 3"'
                        }
                    ],
                    'id': '91115',
                    'key': 'test_feature_in_exclusion_group'
                },
                'test_feature_in_multiple_experiments': {
                    'variables_map': {

                    },
                    'experiments_map': {
                        'test_experiment3': {
                            'variations_map': {
                                'control': {
                                    'variables_map': {

                                    },
                                    'id': '222239',
                                    'key': 'control',
                                    'feature_enabled': None
                                },
                            },
                            'id': '111134',
                            'key': 'test_experiment3',
                            'audiences': '"Test attribute users 3"'
                        },
                        'test_experiment4': {
                            'variations_map': {
                                'control': {
                                    'variables_map': {

                                    },
                                    'id': '222240',
                                    'key': 'control',
                                    'feature_enabled': None
                                },
                            },
                            'id': '111135',
                            'key': 'test_experiment4',
                            'audiences': '"Test attribute users 3"'
                        },
                        'test_experiment5': {
                            'variations_map': {
                                'control': {
                                    'variables_map': {

                                    },
                                    'id': '222241',
                                    'key': 'control',
                                    'feature_enabled': None
                                },
                            },
                            'id': '111136',
                            'key': 'test_experiment5',
                            'audiences': '"Test attribute users 3"'
                        }
                    },
                    'delivery_rules': [
                        {
                            'id': '211127',
                            'key': '211127',
                            'variations_map': {
                                '211129': {
                                    'id': '211129',
                                    'key': '211129',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                },
                                '211229': {
                                    'id': '211229',
                                    'key': '211229',
                                    'feature_enabled': False,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211137',
                            'key': '211137',
                            'variations_map': {
                                '211139': {
                                    'id': '211139',
                                    'key': '211139',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        },
                        {
                            'id': '211147',
                            'key': '211147',
                            'variations_map': {
                                '211149': {
                                    'id': '211149',
                                    'key': '211149',
                                    'feature_enabled': True,
                                    'variables_map': {}
                                }
                            },
                            'audiences': ''
                        }
                    ],
                    'experiment_rules': [
                        {
                            'id': '111134',
                            'key': 'test_experiment3',
                            'variations_map': {
                                'control': {
                                    'id': '222239',
                                    'key': 'control',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': '"Test attribute users 3"'
                        },
                        {
                            'id': '111135',
                            'key': 'test_experiment4',
                            'variations_map': {
                                'control': {
                                    'id': '222240',
                                    'key': 'control',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': '"Test attribute users 3"'
                        },
                        {
                            'id': '111136',
                            'key': 'test_experiment5',
                            'variations_map': {
                                'control': {
                                    'id': '222241',
                                    'key': 'control',
                                    'feature_enabled': None,
                                    'variables_map': {}
                                }
                            },
                            'audiences': '"Test attribute users 3"'
                        }
                    ],
                    'id': '91116',
                    'key': 'test_feature_in_multiple_experiments'
                }
            },
            'revision': '1',
            '_datafile': json.dumps(self.config_dict_with_features)
        }

        self.actual_config = self.opt_config_service.get_config()
        self.actual_config_dict = self.to_dict(self.actual_config)      # TODO - fails here after I add logger, actual_config not a dict?

        self.typed_audiences_config = {
            'version': '2',
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
            'attributes': [],
            'accountId': '10367498574',
            'events': [{'experimentIds': ['10420810910'], 'id': '10404198134', 'key': 'winning'}],
            'revision': '1337',
        }

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

    # TODO - I ADDED
    def test__duplicate_experiment_keys(self):
        """ Test that multiple features don't have the same experiment key. """

        # update the test datafile with an additional feature flag with the same experiment rule key
        new_experiment = {
                    'key': 'test_experiment',    # added duplicate "test_experiment"
                    'status': 'Running',
                    'layerId': '8',
                    "audienceConditions": [
                        "or",
                        "11160"
                    ],
                    'audienceIds': ['11160'],
                    'id': '111137',
                    'forcedVariations': {},
                    'trafficAllocation': [
                        {'entityId': '222242', 'endOfRange': 8000},
                        {'entityId': '', 'endOfRange': 10000}
                    ],
                    'variations': [
                        {
                            'id': '222242',
                            'key': 'control',
                            'variables': [],
                        }
                    ],
                }

        new_feature = {
                    'id': '91117',
                    'key': 'new_feature',
                    'experimentIds': ['111137'],
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
                }

        # add new feature with the same rule key
        self.config_dict_with_features['experiments'].append(new_experiment)
        self.config_dict_with_features['featureFlags'].append(new_feature)

        config_with_duplicate_key = self.config_dict_with_features
        opt_instance = optimizely.Optimizely(json.dumps(config_with_duplicate_key))
        self.project_config = opt_instance.config_manager.get_config()
        self.opt_config_service = optimizely_config.OptimizelyConfigService(self.project_config, logger=logger.SimpleLogger())

        actual_key_map, actual_id_map = self.opt_config_service._get_experiments_maps()

        self.assertIsInstance(actual_key_map, dict)
        for exp in actual_key_map.values():
            self.assertIsInstance(exp, optimizely_config.OptimizelyExperiment)

        # assert on the log message
        # TODO

        # assert we get ID of the duplicated experiment
        assert actual_key_map.get('test_experiment').id == "111137"

        # assert we get one duplicated experiment
        keys_list = list(actual_key_map.keys())
        assert "test_experiment" in keys_list, "Key 'test_experiment' not found in actual key map"
        assert keys_list.count("test_experiment") == 1, "Key 'test_experiment' found more than once in actual key map"

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

    def test__get_datafile_from_bytes(self):
        """ Test that get_datafile returns the expected datafile when provided as bytes. """

        expected_datafile = json.dumps(self.config_dict_with_features)
        bytes_datafile = bytes(expected_datafile, 'utf-8')

        opt_instance = optimizely.Optimizely(bytes_datafile)
        opt_config = opt_instance.config_manager.optimizely_config
        actual_datafile = opt_config.get_datafile()

        self.assertEqual(expected_datafile, actual_datafile)

    def test__get_sdk_key(self):
        """ Test that get_sdk_key returns the expected value. """

        config = optimizely_config.OptimizelyConfig(
            revision='101',
            experiments_map={},
            features_map={},
            sdk_key='testSdkKey',
        )

        expected_value = 'testSdkKey'

        self.assertEqual(expected_value, config.sdk_key)

    def test__get_sdk_key_invalid(self):
        """ Negative Test that tests get_sdk_key does not return the expected value. """

        config = optimizely_config.OptimizelyConfig(
            revision='101',
            experiments_map={},
            features_map={},
            sdk_key='testSdkKey',
        )

        invalid_value = 123

        self.assertNotEqual(invalid_value, config.sdk_key)

    def test__get_environment_key(self):
        """ Test that get_environment_key returns the expected value. """

        config = optimizely_config.OptimizelyConfig(
            revision='101',
            experiments_map={},
            features_map={},
            environment_key='TestEnvironmentKey'
        )

        expected_value = 'TestEnvironmentKey'

        self.assertEqual(expected_value, config.environment_key)

    def test__get_environment_key_invalid(self):
        """ Negative Test that tests get_environment_key does not return the expected value. """

        config = optimizely_config.OptimizelyConfig(
            revision='101',
            experiments_map={},
            features_map={},
            environment_key='testEnvironmentKey'
        )

        invalid_value = 321

        self.assertNotEqual(invalid_value, config.environment_key)

    def test__get_attributes(self):
        """ Test that the get_attributes returns the expected value. """

        config = optimizely_config.OptimizelyConfig(
            revision='101',
            experiments_map={},
            features_map={},
            attributes=[{
                'id': '123',
                'key': '123'
            },
                {
                'id': '234',
                'key': '234'
            }]
        )

        expected_value = [{
            'id': '123',
            'key': '123'
        },
            {
            'id': '234',
            'key': '234'
        }]

        self.assertEqual(expected_value, config.attributes)
        self.assertEqual(len(config.attributes), 2)

    def test__get_events(self):
        """ Test that the get_events returns the expected value. """

        config = optimizely_config.OptimizelyConfig(
            revision='101',
            experiments_map={},
            features_map={},
            events=[{
                'id': '123',
                'key': '123',
                'experiment_ids': {
                    '54321'
                }
            },
                {
                'id': '234',
                'key': '234',
                'experiment_ids': {
                    '3211', '54365'
                }
            }]
        )

        expected_value = [{
            'id': '123',
            'key': '123',
            'experiment_ids': {
                '54321'
            }
        },
            {
            'id': '234',
            'key': '234',
            'experiment_ids': {
                '3211',
                '54365'
            }
        }]

        self.assertEqual(expected_value, config.events)
        self.assertEqual(len(config.events), 2)

    def test_get_audiences(self):
        ''' Test to confirm get_audiences returns proper value '''
        config_dict = self.typed_audiences_config

        proj_conf = project_config.ProjectConfig(
            json.dumps(config_dict),
            logger=None,
            error_handler=None
        )

        config_service = optimizely_config.OptimizelyConfigService(proj_conf)

        for audience in config_service.audiences:
            self.assertIsInstance(audience, optimizely_config.OptimizelyAudience)

        config = config_service.get_config()

        for audience in config.audiences:
            self.assertIsInstance(audience, optimizely_config.OptimizelyAudience)

        self.assertEqual(len(config.audiences), len(config_service.audiences))

    def test_stringify_audience_conditions_all_cases(self):
        audiences_map = {
            '1': 'us',
            '2': 'female',
            '3': 'adult',
            '11': 'fr',
            '12': 'male',
            '13': 'kid'
        }

        config = optimizely_config.OptimizelyConfig(
            revision='101',
            experiments_map={},
            features_map={},
            environment_key='TestEnvironmentKey',
            attributes={},
            events={},
            audiences=None
        )

        audiences_input = [
            [],
            ["or", "1", "2"],
            ["and", "1", "2", "3"],
            ["not", "1"],
            ["or", "1"],
            ["and", "1"],
            ["1"],
            ["1", "2"],
            ["and", ["or", "1", "2"], "3"],
            ["and", ["or", "1", ["and", "2", "3"]], ["and", "11", ["or", "12", "13"]]],
            ["not", ["and", "1", "2"]],
            ["or", "1", "100000"],
            ["and", "and"],
            ["and"],
            ["and", ["or", "1", ["and", "2", "3"]], ["and", "11", ["or", "12", "3"]]]
        ]

        audiences_output = [
            '',
            '"us" OR "female"',
            '"us" AND "female" AND "adult"',
            'NOT "us"',
            '"us"',
            '"us"',
            '"us"',
            '"us" OR "female"',
            '("us" OR "female") AND "adult"',
            '("us" OR ("female" AND "adult")) AND ("fr" AND ("male" OR "kid"))',
            'NOT ("us" AND "female")',
            '"us" OR "100000"',
            '',
            '',
            '("us" OR ("female" AND "adult")) AND ("fr" AND ("male" OR "adult"))'
        ]

        config_service = optimizely_config.OptimizelyConfigService(config)

        for i in range(len(audiences_input)):
            result = config_service.stringify_conditions(audiences_input[i], audiences_map)
            self.assertEqual(audiences_output[i], result)

    def test_optimizely_audience_conversion(self):
        ''' Test to confirm that audience conversion works and has expected output '''
        config_dict = self.typed_audiences_config

        TOTAL_AUDEINCES_ONCE_MERGED = 10

        proj_conf = project_config.ProjectConfig(
            json.dumps(config_dict),
            logger=None,
            error_handler=None
        )

        config_service = optimizely_config.OptimizelyConfigService(proj_conf)

        for audience in config_service.audiences:
            self.assertIsInstance(audience, optimizely_config.OptimizelyAudience)

        self.assertEqual(len(config_service.audiences), TOTAL_AUDEINCES_ONCE_MERGED)

    def test_get_variations_from_experiments_map(self):
        config_dict = self.typed_audiences_config

        proj_conf = project_config.ProjectConfig(
            json.dumps(config_dict),
            logger=None,
            error_handler=None
        )

        config_service = optimizely_config.OptimizelyConfigService(proj_conf)

        experiments_key_map, experiments_id_map = config_service._get_experiments_maps()

        optly_experiment = experiments_id_map['10420810910']

        for variation in optly_experiment.variations_map.values():
            self.assertIsInstance(variation, optimizely_config.OptimizelyVariation)
            if variation.id == '10418551353':
                self.assertEqual(variation.key, 'all_traffic_variation')
            else:
                self.assertEqual(variation.key, 'no_traffic_variation')

    def test_get_delivery_rules(self):
        expected_features_map_dict = self.expected_config.get('features_map')
        actual_features_map_dict = self.actual_config_dict.get('features_map')
        actual_features_map = self.actual_config.features_map

        for optly_feature in actual_features_map.values():
            self.assertIsInstance(optly_feature, optimizely_config.OptimizelyFeature)
            for delivery_rule in optly_feature.delivery_rules:
                self.assertIsInstance(delivery_rule, optimizely_config.OptimizelyExperiment)

        self.assertEqual(expected_features_map_dict, actual_features_map_dict)
