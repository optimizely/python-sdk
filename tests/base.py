# Copyright 2016-2018, Optimizely
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

from optimizely import optimizely


class BaseTest(unittest.TestCase):

  def assertStrictTrue(self, to_assert):
    self.assertIs(to_assert, True)

  def assertStrictFalse(self, to_assert):
    self.assertIs(to_assert, False)

  def setUp(self, config_dict='config_dict'):
    self.config_dict = {
      'revision': '42',
      'version': '2',
      'events': [{
        'key': 'test_event',
        'experimentIds': ['111127'],
        'id': '111095'
      }, {
        'key': 'Total Revenue',
        'experimentIds': ['111127'],
        'id': '111096'
      }],
      'experiments': [{
        'key': 'test_experiment',
        'status': 'Running',
        'forcedVariations': {
          'user_1': 'control',
          'user_2': 'control'
        },
        'layerId': '111182',
        'audienceIds': ['11154'],
        'trafficAllocation': [{
          'entityId': '111128',
          'endOfRange': 4000
        }, {
          'entityId': '',
          'endOfRange': 5000
        }, {
          'entityId': '111129',
          'endOfRange': 9000
        }],
        'id': '111127',
        'variations': [{
          'key': 'control',
          'id': '111128'
        }, {
          'key': 'variation',
          'id': '111129'
        }]
      }],
      'groups': [{
        'id': '19228',
        'policy': 'random',
        'experiments': [{
          'id': '32222',
          'key': 'group_exp_1',
          'status': 'Running',
          'audienceIds': [],
          'layerId': '111183',
          'variations': [{
            'key': 'group_exp_1_control',
            'id': '28901'
          }, {
            'key': 'group_exp_1_variation',
            'id': '28902'
          }],
          'forcedVariations': {
            'user_1': 'group_exp_1_control',
            'user_2': 'group_exp_1_control'
          },
          'trafficAllocation': [{
            'entityId': '28901',
            'endOfRange': 3000
          }, {
            'entityId': '28902',
            'endOfRange': 9000
          }]
        }, {
          'id': '32223',
          'key': 'group_exp_2',
          'status': 'Running',
          'audienceIds': [],
          'layerId': '111184',
          'variations': [{
            'key': 'group_exp_2_control',
            'id': '28905'
          }, {
            'key': 'group_exp_2_variation',
            'id': '28906'
          }],
          'forcedVariations': {
            'user_1': 'group_exp_2_control',
            'user_2': 'group_exp_2_control'
          },
          'trafficAllocation': [{
            'entityId': '28905',
            'endOfRange': 8000
          }, {
            'entityId': '28906',
            'endOfRange': 10000
          }]
        }],
        'trafficAllocation': [{
          'entityId': '32222',
          "endOfRange": 3000
        }, {
          'entityId': '32223',
          'endOfRange': 7500
        }]
      }],
      'accountId': '12001',
      'attributes': [{
        'key': 'test_attribute',
        'id': '111094'
      }, {
        'key': 'boolean_key',
        'id': '111196'
      }, {
        'key': 'integer_key',
        'id': '111197'
      }, {
        'key': 'double_key',
        'id': '111198'
      }],
      'audiences': [{
        'name': 'Test attribute users 1',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
        'id': '11154'
      }, {
        'name': 'Test attribute users 2',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
        'id': '11159'
      }],
      'projectId': '111001'
    }

    # datafile version 4
    self.config_dict_with_features = {
      'revision': '1',
      'accountId': '12001',
      'projectId': '111111',
      'version': '4',
      'botFiltering': True,
      'events': [{
        'key': 'test_event',
        'experimentIds': ['111127'],
        'id': '111095'
      }],
      'experiments': [{
        'key': 'test_experiment',
        'status': 'Running',
        'forcedVariations': {},
        'layerId': '111182',
        'audienceIds': [],
        'trafficAllocation': [{
          'entityId': '111128',
          'endOfRange': 5000
        }, {
          'entityId': '111129',
          'endOfRange': 9000
        }],
        'id': '111127',
        'variations': [{
          'key': 'control',
          'id': '111128',
          'featureEnabled': False,
          'variables': [{
            'id': '127', 'value': 'false'
          }, {
            'id': '128', 'value': 'prod'
          }, {
            'id': '129', 'value': '10.01'
          }, {
            'id': '130', 'value': '4242'
          }]
        }, {
          'key': 'variation',
          'id': '111129',
          'featureEnabled': True,
          'variables': [{
            'id': '127', 'value': 'true'
          }, {
            'id': '128', 'value': 'staging'
          }, {
            'id': '129', 'value': '10.02'
          }, {
            'id': '130', 'value': '4243'
          }]
        }]
      }],
      'groups': [{
        'id': '19228',
        'policy': 'random',
        'experiments': [{
          'id': '32222',
          'key': 'group_exp_1',
          'status': 'Running',
          'audienceIds': [],
          'layerId': '111183',
          'variations': [{
            'key': 'group_exp_1_control',
            'id': '28901'
          }, {
            'key': 'group_exp_1_variation',
            'id': '28902'
          }],
          'forcedVariations': {
            'user_1': 'group_exp_1_control',
            'user_2': 'group_exp_1_control'
          },
          'trafficAllocation': [{
            'entityId': '28901',
            'endOfRange': 3000
          }, {
            'entityId': '28902',
            'endOfRange': 9000
          }]
        }, {
          'id': '32223',
          'key': 'group_exp_2',
          'status': 'Running',
          'audienceIds': [],
          'layerId': '111184',
          'variations': [{
            'key': 'group_exp_2_control',
            'id': '28905'
          }, {
            'key': 'group_exp_2_variation',
            'id': '28906'
          }],
          'forcedVariations': {
            'user_1': 'group_exp_2_control',
            'user_2': 'group_exp_2_control'
          },
          'trafficAllocation': [{
            'entityId': '28905',
            'endOfRange': 8000
          }, {
            'entityId': '28906',
            'endOfRange': 10000
          }]
        }],
        'trafficAllocation': [{
          'entityId': '32222',
          "endOfRange": 3000
        }, {
          'entityId': '32223',
          'endOfRange': 7500
        }]
      }],
      'attributes': [{
        'key': 'test_attribute',
        'id': '111094'
      }],
      'audiences': [{
        'name': 'Test attribute users 1',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
        'id': '11154'
      }, {
        'name': 'Test attribute users 2',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
        'id': '11159'
      }],
      'rollouts': [{
        'id': '201111',
        'experiments': []
      }, {
        'id': '211111',
        'experiments': [{
          'id': '211127',
          'key': '211127',
          'status': 'Running',
          'forcedVariations': {},
          'layerId': '211111',
          'audienceIds': ['11154'],
          'trafficAllocation': [{
            'entityId': '211129',
            'endOfRange': 9000
          }],
          'variations': [{
            'key': '211129',
            'id': '211129',
            'featureEnabled': True
          }]
        }, {
          'id': '211137',
          'key': '211137',
          'status': 'Running',
          'forcedVariations': {},
          'layerId': '211111',
          'audienceIds': ['11159'],
          'trafficAllocation': [{
            'entityId': '211139',
            'endOfRange': 3000
          }],
          'variations': [{
            'key': '211139',
            'id': '211139',
            'featureEnabled': True
          }]
        }, {
          'id': '211147',
          'key': '211147',
          'status': 'Running',
          'forcedVariations': {},
          'layerId': '211111',
          'audienceIds': [],
          'trafficAllocation': [{
            'entityId': '211149',
            'endOfRange': 6000
          }],
          'variations': [{
            'key': '211149',
            'id': '211149',
            'featureEnabled': True
          }]
        }]
      }],
      'featureFlags': [{
        'id': '91111',
        'key': 'test_feature_in_experiment',
        'experimentIds': ['111127'],
        'rolloutId': '',
        'variables': [{
            'id': '127',
            'key': 'is_working',
            'defaultValue': 'true',
            'type': 'boolean',
          }, {
            'id': '128',
            'key': 'environment',
            'defaultValue': 'devel',
            'type': 'string',
          }, {
            'id': '129',
            'key': 'cost',
            'defaultValue': '10.99',
            'type': 'double',
          }, {
            'id': '130',
            'key': 'count',
            'defaultValue': '999',
            'type': 'integer',
          }, {
            'id': '131',
            'key': 'variable_without_usage',
            'defaultValue': '45',
            'type': 'integer',
          }]
      }, {
        'id': '91112',
        'key': 'test_feature_in_rollout',
        'experimentIds': [],
        'rolloutId': '211111',
        'variables': [],
      }, {
        'id': '91113',
        'key': 'test_feature_in_group',
        'experimentIds': ['32222'],
        'rolloutId': '',
        'variables': [],
      }, {
        'id': '91114',
        'key': 'test_feature_in_experiment_and_rollout',
        'experimentIds': ['111127'],
        'rolloutId': '211111',
        'variables': [],
      }]
    }

    self.config_dict_with_multiple_experiments = {
      'revision': '42',
      'version': '2',
      'events': [{
        'key': 'test_event',
        'experimentIds': ['111127', '111130'],
        'id': '111095'
      }, {
        'key': 'Total Revenue',
        'experimentIds': ['111127'],
        'id': '111096'
      }],
      'experiments': [{
        'key': 'test_experiment',
        'status': 'Running',
        'forcedVariations': {
          'user_1': 'control',
          'user_2': 'control'
        },
        'layerId': '111182',
        'audienceIds': ['11154'],
        'trafficAllocation': [{
          'entityId': '111128',
          'endOfRange': 4000
        }, {
          'entityId': '',
          'endOfRange': 5000
        }, {
          'entityId': '111129',
          'endOfRange': 9000
        }],
        'id': '111127',
        'variations': [{
          'key': 'control',
          'id': '111128'
        }, {
          'key': 'variation',
          'id': '111129'
        }]
      }, {
        'key': 'test_experiment_2',
        'status': 'Running',
        'forcedVariations': {
          'user_1': 'control',
          'user_2': 'control'
        },
        'layerId': '111182',
        'audienceIds': ['11154'],
        'trafficAllocation': [{
          'entityId': '111131',
          'endOfRange': 4000
        }, {
          'entityId': '',
          'endOfRange': 5000
        }, {
          'entityId': '111132',
          'endOfRange': 9000
        }],
        'id': '111130',
        'variations': [{
          'key': 'control',
          'id': '111131'
        }, {
          'key': 'variation',
          'id': '111132'
        }]
      }],
      'groups': [{
        'id': '19228',
        'policy': 'random',
        'experiments': [{
          'id': '32222',
          'key': 'group_exp_1',
          'status': 'Running',
          'audienceIds': [],
          'layerId': '111183',
          'variations': [{
            'key': 'group_exp_1_control',
            'id': '28901'
          }, {
            'key': 'group_exp_1_variation',
            'id': '28902'
          }],
          'forcedVariations': {
            'user_1': 'group_exp_1_control',
            'user_2': 'group_exp_1_control'
          },
          'trafficAllocation': [{
            'entityId': '28901',
            'endOfRange': 3000
          }, {
            'entityId': '28902',
            'endOfRange': 9000
          }]
        }, {
          'id': '32223',
          'key': 'group_exp_2',
          'status': 'Running',
          'audienceIds': [],
          'layerId': '111184',
          'variations': [{
            'key': 'group_exp_2_control',
            'id': '28905'
          }, {
            'key': 'group_exp_2_variation',
            'id': '28906'
          }],
          'forcedVariations': {
            'user_1': 'group_exp_2_control',
            'user_2': 'group_exp_2_control'
          },
          'trafficAllocation': [{
            'entityId': '28905',
            'endOfRange': 8000
          }, {
            'entityId': '28906',
            'endOfRange': 10000
          }]
        }],
        'trafficAllocation': [{
          'entityId': '32222',
          "endOfRange": 3000
        }, {
          'entityId': '32223',
          'endOfRange': 7500
        }]
      }],
      'accountId': '12001',
      'attributes': [{
        'key': 'test_attribute',
        'id': '111094'
      }, {
        'key': 'boolean_key',
        'id': '111196'
      }, {
        'key': 'integer_key',
        'id': '111197'
      }, {
        'key': 'double_key',
        'id': '111198'
      }],
      'audiences': [{
        'name': 'Test attribute users 1',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
        'id': '11154'
      }, {
        'name': 'Test attribute users 2',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
        'id': '11159'
      }],
      'projectId': '111001'
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
          'trafficAllocation': [
            {
              'entityId': '10418551353',
              'endOfRange': 10000
            }
          ],
          'audienceIds': [],
          'variations': [
            {
              'variables': [],
              'id': '10418551353',
              'key': 'all_traffic_variation'
            },
            {
              'variables': [],
              'id': '10418510624',
              'key': 'no_traffic_variation'
            }
          ],
          'forcedVariations': {},
          'id': '10420810910'
        }
      ],
      'audiences': [],
      'groups': [],
      'attributes': [],
      'accountId': '10367498574',
      'events': [
        {
          'experimentIds': [
            '10420810910'
          ],
          'id': '10404198134',
          'key': 'winning'
        }
      ],
      'revision': '1337'
    }

    config = getattr(self, config_dict)
    self.optimizely = optimizely.Optimizely(json.dumps(config))
    self.project_config = self.optimizely.config
