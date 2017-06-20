# Copyright 2016-2017, Optimizely
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
import unittest


from optimizely import error_handler
from optimizely import event_builder
from optimizely import logger
from optimizely import optimizely
from optimizely import project_config


class BaseTest(unittest.TestCase):

  def setUp(self):
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
      }],
      'audiences': [{
        'name': 'Test attribute users',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value"}]]]',
        'id': '11154'
      }],
      'projectId': '111001'
    }

    # datafile version 4
    self.config_dict_with_features = {
      'revision': '1',
      'accountId': '12001',
      'projectId': '111111',
      'version': '4',
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
          'variables': [{
            'id': '127', 'value': 'false'
          }, {
            'id': '128', 'value': 'prod'
          }]
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
      'attributes': [{
        'key': 'test_attribute',
        'id': '111094'
      }],
      'audiences': [{
        'name': 'Test attribute users',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value"}]]]',
        'id': '11154'
      }],
      'layers': [{
        'id': '211111',
        'policy': 'ordered',
        'experiments': [{
          'key': 'test_rollout_exp_1',
          'status': 'Running',
          'forcedVariations': {},
          'layerId': '211111',
          'audienceIds': ['11154'],
          'trafficAllocation': [{
            'entityId': '211128',
            'endOfRange': 5000
          }, {
            'entityId': '211129',
            'endOfRange': 9000
          }],
          'id': '211127',
          'variations': [{
            'key': 'control',
            'id': '211128'
          }, {
            'key': 'variation',
            'id': '211129'
          }]
        }]
      }],
      'features': [{
        'id': '91111',
        'key': 'test_feature_1',
        'experimentIds': ['111127'],
        'layerId': '',
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
          }]
      }, {
        'id': '91112',
        'key': 'test_feature_2',
        'experimentIds': [],
        'layerId': '211111',
        'variables': [],
      }, {
        'id': '91113',
        'key': 'test_feature_in_group',
        'experimentIds': ['32222'],
        'layerId': '',
        'variables': [],
      }, {
        'id': '91114',
        'key': 'test_feature_in_experiment_and_rollout',
        'experimentIds': ['111127'],
        'layerId': '211111',
        'variables': [],
      }]
    }

    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict))
    self.project_config = self.optimizely.config


class BaseTestV3(unittest.TestCase):

  def setUp(self):
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
      }],
      'audiences': [{
        'name': 'Test attribute users',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value"}]]]',
        'id': '11154'
      }],
      'projectId': '111001'
    }

    # datafile version 4
    self.config_dict_with_features = {
      'revision': '1',
      'accountId': '12001',
      'projectId': '111111',
      'version': '4',
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
          'variables': [{
            'id': '127', 'value': 'false'
          }, {
            'id': '128', 'value': 'prod'
          }]
        }, {
          'key': 'variation',
          'id': '111129'
        }]
      }],
      'groups': [],
      'attributes': [{
        'key': 'test_attribute',
        'id': '111094'
      }],
      'audiences': [{
        'name': 'Test attribute users',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_attribute", "value": "test_value"}]]]',
        'id': '11154'
      }],
      'layers': [{
        'id': '211111',
        'policy': 'ordered',
        'experiments': [{
          'key': 'test_rollout_exp_1',
          'status': 'Running',
          'forcedVariations': {},
          'layerId': '211111',
          'audienceIds': ['11154'],
          'trafficAllocation': [{
            'entityId': '211128',
            'endOfRange': 5000
          }, {
            'entityId': '211129',
            'endOfRange': 9000
          }],
          'id': '211127',
          'variations': [{
            'key': 'control',
            'id': '211128'
          }, {
            'key': 'variation',
            'id': '211129'
          }]
        }]
      }],
      'features': [{
        'id': '91111',
        'key': 'test_feature_1',
        'experimentIds': ['111127'],
        'layerId': '',
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
          }]
      }, {
        'id': '91112',
        'key': 'test_feature_2',
        'experimentIds': [],
        'layerId': '211111',
        'variables': [],
      }]
    }

    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict))
    self.config = project_config.ProjectConfig(json.dumps(self.config_dict),
                                               logger.SimpleLogger(), error_handler.NoOpErrorHandler())
    self.optimizely.event_builder = event_builder.EventBuilderV3(self.config)
    self.project_config = self.optimizely.config
