import json
import unittest

from optimizely import optimizely


class BaseTestV1(unittest.TestCase):

  def setUp(self):
    self.config_dict = {
      'revision': '42',
      'version': '1',
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
        'audienceIds': ['11154'],
        'trafficAllocation': [{
          'entityId': '111128',
          'endOfRange': 4000
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
        'holdback': 0,
        'experiments': [{
          'id': '32222',
          'key': 'group_exp_1',
          'status': 'Running',
          'audienceIds': [],
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
      'dimensions': [{
        'key': 'test_attribute',
        'id': '111094',
        'segmentId': '11133'
      }],
      'audiences': [{
        'name': 'Test attribute users',
        'conditions': '["and", ["or", ["or", '
                      '{"name": "test_attribute", "type": "custom_dimension", "value": "test_value"}]]]',
        'id': '11154'
      }],
      'projectId': '111001'
    }

    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict))
    self.project_config = self.optimizely.config


class BaseTestV2(unittest.TestCase):

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
        'holdback': 0,
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

    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict))
    self.project_config = self.optimizely.config
