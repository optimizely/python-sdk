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
import mock

from optimizely import entities
from optimizely import error_handler
from optimizely import exceptions
from optimizely import logger
from optimizely import optimizely
from optimizely.helpers import enums

from . import base


class ConfigTest(base.BaseTest):

  def test_init(self):
    """ Test that on creating object, properties are initiated correctly. """

    self.assertEqual(self.config_dict['accountId'], self.project_config.account_id)
    self.assertEqual(self.config_dict['projectId'], self.project_config.project_id)
    self.assertEqual(self.config_dict['revision'], self.project_config.revision)
    self.assertEqual(self.config_dict['experiments'], self.project_config.experiments)
    self.assertEqual(self.config_dict['events'], self.project_config.events)
    expected_group_id_map = {
      '19228': entities.Group(
        self.config_dict['groups'][0]['id'],
        self.config_dict['groups'][0]['policy'],
        self.config_dict['groups'][0]['experiments'],
        self.config_dict['groups'][0]['trafficAllocation']
      )
    }
    expected_experiment_key_map = {
      'test_experiment': entities.Experiment(
        '111127', 'test_experiment', 'Running', ['11154'], [{
          'key': 'control',
          'id': '111128'
        }, {
          'key': 'variation',
          'id': '111129'
        }], {
            'user_1': 'control',
            'user_2': 'control'
        }, [{
          'entityId': '111128',
          'endOfRange': 4000
        }, {
          'entityId': '',
          'endOfRange': 5000
        }, {
          'entityId': '111129',
          'endOfRange': 9000
        }], '111182'),
      'group_exp_1': entities.Experiment(
        '32222', 'group_exp_1', 'Running', [], [{
          'key': 'group_exp_1_control',
          'id': '28901'
        }, {
          'key': 'group_exp_1_variation',
          'id': '28902'
        }], {
            'user_1': 'group_exp_1_control',
            'user_2': 'group_exp_1_control'
        }, [{
          'entityId': '28901',
          'endOfRange': 3000
        }, {
          'entityId': '28902',
          'endOfRange': 9000
        }], '111183', groupId='19228', groupPolicy='random'
      ),
      'group_exp_2': entities.Experiment(
        '32223', 'group_exp_2', 'Running', [], [{
          'key': 'group_exp_2_control',
          'id': '28905'
        }, {
          'key': 'group_exp_2_variation',
          'id': '28906'
        }], {
            'user_1': 'group_exp_2_control',
            'user_2': 'group_exp_2_control'
        }, [{
          'entityId': '28905',
          'endOfRange': 8000
        }, {
          'entityId': '28906',
          'endOfRange': 10000
        }], '111184', groupId='19228', groupPolicy='random'
      ),
    }
    expected_experiment_id_map = {
      '111127': expected_experiment_key_map.get('test_experiment'),
      '32222': expected_experiment_key_map.get('group_exp_1'),
      '32223': expected_experiment_key_map.get('group_exp_2')
    }
    expected_event_key_map = {
      'test_event': entities.Event('111095', 'test_event', ['111127']),
      'Total Revenue': entities.Event('111096', 'Total Revenue', ['111127'])
    }
    expected_attribute_key_map = {
      'boolean_key': entities.Attribute('111196', 'boolean_key'),
      'double_key': entities.Attribute('111198', 'double_key'),
      'integer_key': entities.Attribute('111197', 'integer_key'),
      'test_attribute': entities.Attribute('111094', 'test_attribute', segmentId='11133')
    }
    expected_audience_id_map = {
      '11154': entities.Audience(
        '11154', 'Test attribute users 1',
        '["and", ["or", ["or", {"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]]',
        conditionStructure=['and', ['or', ['or', 0]]],
        conditionList=[['test_attribute', 'test_value_1']]
      ),
      '11159': entities.Audience(
        '11159', 'Test attribute users 2',
        '["and", ["or", ["or", {"name": "test_attribute", "type": "custom_attribute", "value": "test_value_2"}]]]',
        conditionStructure=['and', ['or', ['or', 0]]],
        conditionList=[['test_attribute', 'test_value_2']]
      )
    }
    expected_variation_key_map = {
      'test_experiment': {
        'control': entities.Variation('111128', 'control'),
        'variation': entities.Variation('111129', 'variation')
      },
      'group_exp_1': {
        'group_exp_1_control': entities.Variation('28901', 'group_exp_1_control'),
        'group_exp_1_variation': entities.Variation('28902', 'group_exp_1_variation')
      },
      'group_exp_2': {
        'group_exp_2_control': entities.Variation('28905', 'group_exp_2_control'),
        'group_exp_2_variation': entities.Variation('28906', 'group_exp_2_variation')
      }
    }
    expected_variation_id_map = {
      'test_experiment': {
        '111128': entities.Variation('111128', 'control'),
        '111129': entities.Variation('111129', 'variation')
      },
      'group_exp_1': {
        '28901': entities.Variation('28901', 'group_exp_1_control'),
        '28902': entities.Variation('28902', 'group_exp_1_variation')
      },
      'group_exp_2': {
        '28905': entities.Variation('28905', 'group_exp_2_control'),
        '28906': entities.Variation('28906', 'group_exp_2_variation')
      }
    }

    self.assertEqual(expected_group_id_map, self.project_config.group_id_map)
    self.assertEqual(expected_experiment_key_map, self.project_config.experiment_key_map)
    self.assertEqual(expected_experiment_id_map, self.project_config.experiment_id_map)
    self.assertEqual(expected_event_key_map, self.project_config.event_key_map)
    self.assertEqual(expected_attribute_key_map, self.project_config.attribute_key_map)
    self.assertEqual(expected_audience_id_map, self.project_config.audience_id_map)
    self.assertEqual(expected_variation_key_map, self.project_config.variation_key_map)
    self.assertEqual(expected_variation_id_map, self.project_config.variation_id_map)

  def test_init__with_v4_datafile(self):
    """ Test that on creating object, properties are initiated correctly for version 4 datafile. """

    # Adding some additional fields like live variables and IP anonymization
    config_dict = {
      'revision': '42',
      'version': '4',
      'anonymizeIP': False,
      'botFiltering': True,
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
          'id': '111128',
          'variables': [{
            'id': '127',
            'value': 'false'
          }]
        }, {
          'key': 'variation',
          'id': '111129',
          'variables': [{
            'id': '127',
            'value': 'true'
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
            'id': '28901',
            'variables': [{
              'id': '128',
              'value': 'prod'
            }, {
              'id': '129',
              'value': '1772'
            }, {
              'id': '130',
              'value': '1.22992'
            }]
          }, {
            'key': 'group_exp_1_variation',
            'id': '28902',
            'variables': [{
              'id': '128',
              'value': 'stage'
            }, {
              'id': '129',
              'value': '112'
            }, {
              'id': '130',
              'value': '1.211'
            }]
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
            'id': '28905',
            'variables': []
          }, {
            'key': 'group_exp_2_variation',
            'id': '28906',
            'variables': []
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
          'endOfRange': 3000
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
      'rollouts': [{
        'id': '211111',
        'experiments': [{
          'key': '211112',
          'status': 'Running',
          'forcedVariations': {},
          'layerId': '211111',
          'audienceIds': ['11154'],
          'trafficAllocation': [{
            'entityId': '211113',
            'endOfRange': 10000
          }],
          'id': '211112',
          'variations': [{
            'id': '211113',
            'key': '211113',
            'variables': [{
              'id': '131',
              'value': '15'
            }]
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
            'key': 'number_of_days',
            'defaultValue': '192',
            'type': 'integer',
          }, {
            'id': '130',
            'key': 'significance_value',
            'defaultValue': '0.00098',
            'type': 'double',
          }]
      }, {
        'id': '91112',
        'key': 'test_feature_in_rollout',
        'rolloutId': '211111',
        'experimentIds': [],
        'variables': [{
          'id': '131',
          'key': 'number_of_projects',
          'defaultValue': '10',
          'type': 'integer',
        }],
      }, {
        'id': '91113',
        'key': 'test_feature_in_group',
        'rolloutId': '',
        'experimentIds': ['32222'],
        'variables': [],
      }],
      'projectId': '111001'
    }

    test_obj = optimizely.Optimizely(json.dumps(config_dict))
    project_config = test_obj.config
    self.assertEqual(config_dict['accountId'], project_config.account_id)
    self.assertEqual(config_dict['projectId'], project_config.project_id)
    self.assertEqual(config_dict['revision'], project_config.revision)
    self.assertEqual(config_dict['experiments'], project_config.experiments)
    self.assertEqual(config_dict['events'], project_config.events)
    self.assertEqual(config_dict['botFiltering'], project_config.bot_filtering)

    expected_group_id_map = {
      '19228': entities.Group(
        config_dict['groups'][0]['id'],
        config_dict['groups'][0]['policy'],
        config_dict['groups'][0]['experiments'],
        config_dict['groups'][0]['trafficAllocation']
      )
    }
    expected_experiment_key_map = {
      'test_experiment': entities.Experiment(
        '111127', 'test_experiment', 'Running', ['11154'], [{
          'key': 'control',
          'id': '111128',
          'variables': [{
            'id': '127',
            'value': 'false'
          }]
        }, {
          'key': 'variation',
          'id': '111129',
          'variables': [{
            'id': '127',
            'value': 'true'
          }]
        }], {
            'user_1': 'control',
            'user_2': 'control'
        }, [{
          'entityId': '111128',
          'endOfRange': 4000
        }, {
          'entityId': '',
          'endOfRange': 5000
        }, {
          'entityId': '111129',
          'endOfRange': 9000
        }], '111182'),
      'group_exp_1': entities.Experiment(
        '32222', 'group_exp_1', 'Running', [], [{
          'key': 'group_exp_1_control',
          'id': '28901',
          'variables': [{
            'id': '128',
            'value': 'prod'
          }, {
            'id': '129',
            'value': '1772'
          }, {
            'id': '130',
            'value': '1.22992'
          }]
        }, {
          'key': 'group_exp_1_variation',
          'id': '28902',
          'variables': [{
            'id': '128',
            'value': 'stage'
          }, {
            'id': '129',
            'value': '112'
          }, {
            'id': '130',
            'value': '1.211'
          }]
        }], {
            'user_1': 'group_exp_1_control',
            'user_2': 'group_exp_1_control'
        }, [{
          'entityId': '28901',
          'endOfRange': 3000
        }, {
          'entityId': '28902',
          'endOfRange': 9000
        }], '111183', groupId='19228', groupPolicy='random'
      ),
      'group_exp_2': entities.Experiment(
        '32223', 'group_exp_2', 'Running', [], [{
          'key': 'group_exp_2_control',
          'id': '28905',
          'variables': []
        }, {
          'key': 'group_exp_2_variation',
          'id': '28906',
          'variables': []
        }], {
            'user_1': 'group_exp_2_control',
            'user_2': 'group_exp_2_control'
        }, [{
          'entityId': '28905',
          'endOfRange': 8000
        }, {
          'entityId': '28906',
          'endOfRange': 10000
        }], '111184', groupId='19228', groupPolicy='random'
      ),
      '211112': entities.Experiment(
        '211112', '211112', 'Running', ['11154'], [{
          'id': '211113',
          'key': '211113',
          'variables': [{
            'id': '131',
            'value': '15',
          }]
        }], {}, [{
          'entityId': '211113',
          'endOfRange': 10000
        }],
        '211111'
      ),
    }
    expected_experiment_id_map = {
      '111127': expected_experiment_key_map.get('test_experiment'),
      '32222': expected_experiment_key_map.get('group_exp_1'),
      '32223': expected_experiment_key_map.get('group_exp_2'),
      '211112': expected_experiment_key_map.get('211112')
    }
    expected_event_key_map = {
      'test_event': entities.Event('111095', 'test_event', ['111127']),
      'Total Revenue': entities.Event('111096', 'Total Revenue', ['111127'])
    }
    expected_attribute_key_map = {
      'test_attribute': entities.Attribute('111094', 'test_attribute', segmentId='11133')
    }
    expected_audience_id_map = {
      '11154': entities.Audience(
        '11154', 'Test attribute users',
        '["and", ["or", ["or", {"name": "test_attribute", "type": "custom_attribute", "value": "test_value"}]]]',
        conditionStructure=['and', ['or', ['or', 0]]],
        conditionList=[['test_attribute', 'test_value']]
      )
    }
    expected_variation_key_map = {
      'test_experiment': {
        'control': entities.Variation('111128', 'control', False, [{'id': '127', 'value': 'false'}]),
        'variation': entities.Variation('111129', 'variation', False, [{'id': '127', 'value': 'true'}])
      },
      'group_exp_1': {
        'group_exp_1_control': entities.Variation(
          '28901', 'group_exp_1_control', False, [
            {'id': '128', 'value': 'prod'}, {'id': '129', 'value': '1772'}, {'id': '130', 'value': '1.22992'}]),
        'group_exp_1_variation': entities.Variation(
          '28902', 'group_exp_1_variation', False, [
            {'id': '128', 'value': 'stage'}, {'id': '129', 'value': '112'}, {'id': '130', 'value': '1.211'}])
      },
      'group_exp_2': {
        'group_exp_2_control': entities.Variation('28905', 'group_exp_2_control'),
        'group_exp_2_variation': entities.Variation('28906', 'group_exp_2_variation')
      },
      '211112': {
        '211113': entities.Variation('211113', '211113', False, [{'id': '131', 'value': '15'}])
      }
    }
    expected_variation_id_map = {
      'test_experiment': {
        '111128': entities.Variation('111128', 'control', False, [{'id': '127', 'value': 'false'}]),
        '111129': entities.Variation('111129', 'variation', False, [{'id': '127', 'value': 'true'}])
      },
      'group_exp_1': {
        '28901': entities.Variation('28901', 'group_exp_1_control', False, [
            {'id': '128', 'value': 'prod'}, {'id': '129', 'value': '1772'}, {'id': '130', 'value': '1.22992'}]),
        '28902': entities.Variation('28902', 'group_exp_1_variation', False, [
            {'id': '128', 'value': 'stage'}, {'id': '129', 'value': '112'}, {'id': '130', 'value': '1.211'}])
      },
      'group_exp_2': {
        '28905': entities.Variation('28905', 'group_exp_2_control'),
        '28906': entities.Variation('28906', 'group_exp_2_variation')
      },
      '211112': {
        '211113': entities.Variation('211113', '211113', False, [{'id': '131', 'value': '15'}])
      }
    }

    expected_feature_key_map = {
      'test_feature_in_experiment': entities.FeatureFlag('91111', 'test_feature_in_experiment', ['111127'], '', {
          'is_working': entities.Variable('127', 'is_working', 'boolean', 'true'),
          'environment': entities.Variable('128', 'environment', 'string', 'devel'),
          'number_of_days': entities.Variable('129', 'number_of_days', 'integer', '192'),
          'significance_value': entities.Variable('130', 'significance_value', 'double', '0.00098')
        }),
      'test_feature_in_rollout': entities.FeatureFlag('91112', 'test_feature_in_rollout', [], '211111', {
          'number_of_projects': entities.Variable('131', 'number_of_projects', 'integer', '10')
        }),
      'test_feature_in_group': entities.FeatureFlag('91113', 'test_feature_in_group', ['32222'], '', {}, '19228')
    }

    expected_rollout_id_map = {
      '211111': entities.Layer('211111', [{
          'key': '211112',
          'status': 'Running',
          'forcedVariations': {},
          'layerId': '211111',
          'audienceIds': ['11154'],
          'trafficAllocation': [{
            'entityId': '211113',
            'endOfRange': 10000
          }],
          'id': '211112',
          'variations': [{
            'id': '211113',
            'key': '211113',
            'variables': [{
              'id': '131',
              'value': '15'
            }]
          }]
        }]
      )
    }

    expected_variation_variable_usage_map = {
      '111128': {
        '127': entities.Variation.VariableUsage('127', 'false')
      },
      '111129': {
        '127': entities.Variation.VariableUsage('127', 'true')
      },
      '28901': {
        '128': entities.Variation.VariableUsage('128', 'prod'),
        '129': entities.Variation.VariableUsage('129', '1772'),
        '130': entities.Variation.VariableUsage('130', '1.22992')
      },
      '28902': {
        '128': entities.Variation.VariableUsage('128', 'stage'),
        '129': entities.Variation.VariableUsage('129', '112'),
        '130': entities.Variation.VariableUsage('130', '1.211')
      },
      '28905': {},
      '28906': {},
      '211113': {
        '131': entities.Variation.VariableUsage('131', '15')
      }
    }

    self.assertEqual(expected_variation_variable_usage_map['28901'],
                     project_config.variation_variable_usage_map['28901'])
    self.assertEqual(expected_group_id_map, project_config.group_id_map)
    self.assertEqual(expected_experiment_key_map, project_config.experiment_key_map)
    self.assertEqual(expected_experiment_id_map, project_config.experiment_id_map)
    self.assertEqual(expected_event_key_map, project_config.event_key_map)
    self.assertEqual(expected_attribute_key_map, project_config.attribute_key_map)
    self.assertEqual(expected_audience_id_map, project_config.audience_id_map)
    self.assertEqual(expected_variation_key_map, project_config.variation_key_map)
    self.assertEqual(expected_variation_id_map, project_config.variation_id_map)
    self.assertEqual(expected_feature_key_map, project_config.feature_key_map)
    self.assertEqual(expected_rollout_id_map, project_config.rollout_id_map)
    self.assertEqual(expected_variation_variable_usage_map, project_config.variation_variable_usage_map)

  def test_variation_has_featureEnabled_false_if_prop_undefined(self):
    """ Test that featureEnabled property by default is set to False, when not given in the data file"""
    variation = {
      'key': 'group_exp_1_variation',
      'id': '28902',
      'variables': [{
        'id': '128',
        'value': 'stage'
      }, {
        'id': '129',
        'value': '112'
      }, {
        'id': '130',
        'value': '1.211'
      }]
    }

    variation_entity = entities.Variation(**variation)

    self.assertEqual(variation['id'], variation_entity.id)
    self.assertEqual(variation['key'], variation_entity.key)
    self.assertEqual(variation['variables'], variation_entity.variables)
    self.assertFalse(variation_entity.featureEnabled)

  def test_get_version(self):
    """ Test that JSON version is retrieved correctly when using get_version. """

    self.assertEqual('2', self.project_config.get_version())

  def test_get_revision(self):
    """ Test that revision is retrieved correctly when using get_revision. """

    self.assertEqual('42', self.project_config.get_revision())

  def test_get_account_id(self):
    """ Test that account ID is retrieved correctly when using get_account_id. """

    self.assertEqual(self.config_dict['accountId'], self.project_config.get_account_id())

  def test_get_project_id(self):
    """ Test that project ID is retrieved correctly when using get_project_id. """

    self.assertEqual(self.config_dict['projectId'], self.project_config.get_project_id())

  def test_get_bot_filtering(self):
    """ Test that bot filtering is retrieved correctly when using get_bot_filtering_value. """

    # Assert bot filtering is None when not provided in data file
    self.assertTrue('botFiltering' not in self.config_dict)
    self.assertIsNone(self.project_config.get_bot_filtering_value())

    # Assert bot filtering is retrieved as provided in the data file
    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    self.assertEqual(
        self.config_dict_with_features['botFiltering'],
        project_config.get_bot_filtering_value()
    )

  def test_get_experiment_from_key__valid_key(self):
    """ Test that experiment is retrieved correctly for valid experiment key. """

    self.assertEqual(entities.Experiment(
      '32222', 'group_exp_1', 'Running', [], [{
        'key': 'group_exp_1_control',
        'id': '28901'
      }, {
        'key': 'group_exp_1_variation',
        'id': '28902'
      }], {
        'user_1': 'group_exp_1_control',
        'user_2': 'group_exp_1_control'
      }, [{
        'entityId': '28901',
        'endOfRange': 3000
      }, {
        'entityId': '28902',
        'endOfRange': 9000
      }], '111183', groupId='19228', groupPolicy='random'),
      self.project_config.get_experiment_from_key('group_exp_1'))

  def test_get_experiment_from_key__invalid_key(self):
    """ Test that None is returned when provided experiment key is invalid. """

    self.assertIsNone(self.project_config.get_experiment_from_key('invalid_key'))

  def test_get_experiment_from_id__valid_id(self):
    """ Test that experiment is retrieved correctly for valid experiment ID. """

    self.assertEqual(entities.Experiment(
      '32222', 'group_exp_1', 'Running', [], [{
        'key': 'group_exp_1_control',
        'id': '28901'
      }, {
        'key': 'group_exp_1_variation',
        'id': '28902'
      }], {
        'user_1': 'group_exp_1_control',
        'user_2': 'group_exp_1_control'
      }, [{
        'entityId': '28901',
        'endOfRange': 3000
      }, {
        'entityId': '28902',
        'endOfRange': 9000
      }], '111183', groupId='19228', groupPolicy='random'),
      self.project_config.get_experiment_from_id('32222'))

  def test_get_experiment_from_id__invalid_id(self):
    """ Test that None is returned when provided experiment ID is invalid. """

    self.assertIsNone(self.project_config.get_experiment_from_id('invalid_id'))

  def test_get_audience__valid_id(self):
    """ Test that audience object is retrieved correctly given a valid audience ID. """

    self.assertEqual(self.project_config.audience_id_map['11154'],
                     self.project_config.get_audience('11154'))

  def test_get_audience__invalid_id(self):
    """ Test that None is returned for an invalid audience ID. """

    self.assertIsNone(self.project_config.get_audience('42'))

  def test_get_variation_from_key__valid_experiment_key(self):
    """ Test that variation is retrieved correctly when valid experiment key and variation key are provided. """

    self.assertEqual(entities.Variation('111128', 'control'),
                     self.project_config.get_variation_from_key('test_experiment', 'control'))

  def test_get_variation_from_key__invalid_experiment_key(self):
    """ Test that None is returned when provided experiment key is invalid. """

    self.assertIsNone(self.project_config.get_variation_from_key('invalid_key', 'control'))

  def test_get_variation_from_key__invalid_variation_key(self):
    """ Test that None is returned when provided variation ID is invalid. """

    self.assertIsNone(self.project_config.get_variation_from_key('test_experiment', 'invalid_key'))

  def test_get_variation_from_id__valid_experiment_key(self):
    """ Test that variation is retrieved correctly when valid experiment key and variation ID are provided. """

    self.assertEqual(entities.Variation('111128', 'control'),
                     self.project_config.get_variation_from_id('test_experiment', '111128'))

  def test_get_variation_from_id__invalid_experiment_key(self):
    """ Test that None is returned when provided experiment key is invalid. """

    self.assertIsNone(self.project_config.get_variation_from_id('invalid_key', '111128'))

  def test_get_variation_from_id__invalid_variation_key(self):
    """ Test that None is returned when provided variation ID is invalid. """

    self.assertIsNone(self.project_config.get_variation_from_id('test_experiment', '42'))

  def test_get_event__valid_key(self):
    """ Test that event is retrieved correctly for valid event key. """

    self.assertEqual(entities.Event('111095', 'test_event', ['111127']),
                     self.project_config.get_event('test_event'))

  def test_get_event__invalid_key(self):
    """ Test that None is returned when provided goal key is invalid. """

    self.assertIsNone(self.project_config.get_event('invalid_key'))

  def test_get_attribute_id__valid_key(self):
    """ Test that attribute ID is retrieved correctly for valid attribute key. """

    self.assertEqual('111094',
                     self.project_config.get_attribute_id('test_attribute'))

  def test_get_attribute_id__invalid_key(self):
    """ Test that None is returned when provided attribute key is invalid. """

    self.assertIsNone(self.project_config.get_attribute_id('invalid_key'))

  def test_get_attribute_id__reserved_key(self):
    """ Test that Attribute Key is returned as ID when provided attribute key is reserved key. """
    self.assertEqual('$opt_user_agent',
                       self.project_config.get_attribute_id('$opt_user_agent'))

  def test_get_attribute_id__unknown_key_with_opt_prefix(self):
    """ Test that Attribute Key is returned as ID when provided attribute key is not
    present in the datafile but has $opt prefix. """
    self.assertEqual('$opt_interesting',
                     self.project_config.get_attribute_id('$opt_interesting'))

  def test_get_group__valid_id(self):
    """ Test that group is retrieved correctly for valid group ID. """

    self.assertEqual(entities.Group(self.config_dict['groups'][0]['id'],
                                    self.config_dict['groups'][0]['policy'],
                                    self.config_dict['groups'][0]['experiments'],
                                    self.config_dict['groups'][0]['trafficAllocation']),
                     self.project_config.get_group('19228'))

  def test_get_group__invalid_id(self):
    """ Test that None is returned when provided group ID is invalid. """

    self.assertIsNone(self.project_config.get_group('42'))

  def test_get_feature_from_key__valid_feature_key(self):
    """ Test that a valid feature is returned given a valid feature key. """
    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    expected_feature = entities.FeatureFlag('91112', 'test_feature_in_rollout', [], '211111', {})
    self.assertEqual(expected_feature, project_config.get_feature_from_key('test_feature_in_rollout'))

  def test_get_feature_from_key__invalid_feature_key(self):
    """ Test that None is returned given an invalid feature key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    self.assertIsNone(project_config.get_feature_from_key('invalid_feature_key'))

  def test_get_rollout_from_id__valid_rollout_id(self):
    """ Test that a valid rollout is returned """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    expected_rollout = entities.Layer('211111', [{
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
    }])
    self.assertEqual(expected_rollout, project_config.get_rollout_from_id('211111'))

  def test_get_rollout_from_id__invalid_rollout_id(self):
    """ Test that None is returned for an unknown Rollout ID """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features),
                                    logger=logger.NoOpLogger())
    project_config = opt_obj.config
    with mock.patch.object(project_config, 'logger') as mock_config_logging:
      self.assertIsNone(project_config.get_rollout_from_id('aabbccdd'))

    mock_config_logging.error.assert_called_once_with('Rollout with ID "aabbccdd" is not in datafile.')

  def test_get_variable_value_for_variation__returns_valid_value(self):
    """ Test that the right value is returned. """
    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    variation = project_config.get_variation_from_id('test_experiment', '111128')
    is_working_variable = project_config.get_variable_for_feature('test_feature_in_experiment', 'is_working')
    environment_variable = project_config.get_variable_for_feature('test_feature_in_experiment', 'environment')
    self.assertEqual('false', project_config.get_variable_value_for_variation(is_working_variable, variation))
    self.assertEqual('prod', project_config.get_variable_value_for_variation(environment_variable, variation))

  def test_get_variable_value_for_variation__invalid_variable(self):
    """ Test that an invalid variable key will return None. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    variation = project_config.get_variation_from_id('test_experiment', '111128')
    self.assertIsNone(project_config.get_variable_value_for_variation(None, variation))

  def test_get_variable_value_for_variation__no_variables_for_variation(self):
    """ Test that a variation with no variables will return None. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    variation = entities.Variation('1111281', 'invalid_variation', [])
    is_working_variable = project_config.get_variable_for_feature('test_feature_in_experiment', 'is_working')
    self.assertIsNone(project_config.get_variable_value_for_variation(is_working_variable, variation))

  def test_get_variable_value_for_variation__no_usage_of_variable(self):
    """ Test that a variable with no usage will return default value for variable. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    variation = project_config.get_variation_from_id('test_experiment', '111128')
    variable_without_usage_variable = project_config.get_variable_for_feature('test_feature_in_experiment',
                                                                              'variable_without_usage')
    self.assertEqual('45', project_config.get_variable_value_for_variation(variable_without_usage_variable, variation))

  def test_get_variable_for_feature__returns_valid_variable(self):
    """ Test that the feature variable is returned. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    variable = project_config.get_variable_for_feature('test_feature_in_experiment', 'is_working')
    self.assertEqual(entities.Variable('127', 'is_working', 'boolean', 'true'), variable)

  def test_get_variable_for_feature__invalid_feature_key(self):
    """ Test that an invalid feature key will return None. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    self.assertIsNone(project_config.get_variable_for_feature('invalid_feature', 'is_working'))

  def test_get_variable_for_feature__invalid_variable_key(self):
    """ Test that an invalid variable key will return None. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config

    self.assertIsNone(project_config.get_variable_for_feature('test_feature_in_experiment', 'invalid_variable_key'))

  # get_forced_variation tests
  def test_get_forced_variation__invalid_user_id(self):
    """ Test invalid user IDs return a null variation. """
    self.project_config.forced_variation_map['test_user'] = {}
    self.project_config.forced_variation_map['test_user']['test_experiment'] = 'test_variation'

    self.assertIsNone(self.project_config.get_forced_variation('test_experiment', None))
    self.assertIsNone(self.project_config.get_forced_variation('test_experiment', ''))

  def test_get_forced_variation__invalid_experiment_key(self):
    """ Test invalid experiment keys return a null variation. """
    self.project_config.forced_variation_map['test_user'] = {}
    self.project_config.forced_variation_map['test_user']['test_experiment'] = 'test_variation'

    self.assertIsNone(self.project_config.get_forced_variation('test_experiment_not_in_datafile', 'test_user'))
    self.assertIsNone(self.project_config.get_forced_variation(None, 'test_user'))
    self.assertIsNone(self.project_config.get_forced_variation('', 'test_user'))

  def test_get_forced_variation_with_none_set_for_user(self):
    """ Test get_forced_variation when none set for user ID in forced variation map. """
    self.project_config.forced_variation_map = {}
    self.project_config.forced_variation_map['test_user'] = {}

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.assertIsNone(self.project_config.get_forced_variation('test_experiment', 'test_user'))
    mock_config_logging.debug.assert_called_once_with(
      'No experiment "test_experiment" mapped to user "test_user" in the forced variation map.'
    )

  def test_get_forced_variation_missing_variation_mapped_to_experiment(self):
    """ Test get_forced_variation when no variation found against given experiment for the user. """
    self.project_config.forced_variation_map = {}
    self.project_config.forced_variation_map['test_user'] = {}
    self.project_config.forced_variation_map['test_user']['test_experiment'] = None

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.assertIsNone(self.project_config.get_forced_variation('test_experiment', 'test_user'))

    mock_config_logging.debug.assert_called_once_with(
      'No variation mapped to experiment "test_experiment" in the forced variation map.'
    )

  # set_forced_variation tests
  def test_set_forced_variation__invalid_user_id(self):
    """ Test invalid user IDs set fail to set a forced variation """

    self.assertFalse(self.project_config.set_forced_variation('test_experiment', None, 'variation'))
    self.assertFalse(self.project_config.set_forced_variation('test_experiment', '', 'variation'))

  def test_set_forced_variation__invalid_experiment_key(self):
    """ Test invalid experiment keys set fail to set a forced variation """

    self.assertFalse(self.project_config.set_forced_variation('test_experiment_not_in_datafile',
                                                              'test_user', 'variation'))
    self.assertFalse(self.project_config.set_forced_variation('', 'test_user', 'variation'))
    self.assertFalse(self.project_config.set_forced_variation(None, 'test_user', 'variation'))

  def test_set_forced_variation__invalid_variation_key(self):
    """ Test invalid variation keys set fail to set a forced variation """

    self.assertFalse(self.project_config.set_forced_variation('test_experiment', 'test_user',
                                                              'variation_not_in_datafile'))
    self.assertTrue(self.project_config.set_forced_variation('test_experiment', 'test_user', None))

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.assertIs(self.project_config.set_forced_variation('test_experiment', 'test_user', ''), False)
    mock_config_logging.debug.assert_called_once_with('Variation key is invalid.')

  def test_set_forced_variation__multiple_sets(self):
    """ Test multiple sets of experiments for one and multiple users work """

    self.assertTrue(self.project_config.set_forced_variation('test_experiment', 'test_user_1', 'variation'))
    self.assertEqual(self.project_config.get_forced_variation('test_experiment', 'test_user_1').key, 'variation')
    # same user, same experiment, different variation
    self.assertTrue(self.project_config.set_forced_variation('test_experiment', 'test_user_1', 'control'))
    self.assertEqual(self.project_config.get_forced_variation('test_experiment', 'test_user_1').key, 'control')
    # same user, different experiment
    self.assertTrue(self.project_config.set_forced_variation('group_exp_1', 'test_user_1', 'group_exp_1_control'))
    self.assertEqual(self.project_config.get_forced_variation('group_exp_1', 'test_user_1').key, 'group_exp_1_control')

    # different user
    self.assertTrue(self.project_config.set_forced_variation('test_experiment', 'test_user_2', 'variation'))
    self.assertEqual(self.project_config.get_forced_variation('test_experiment', 'test_user_2').key, 'variation')
    # different user, different experiment
    self.assertTrue(self.project_config.set_forced_variation('group_exp_1', 'test_user_2', 'group_exp_1_control'))
    self.assertEqual(self.project_config.get_forced_variation('group_exp_1', 'test_user_2').key, 'group_exp_1_control')

    # make sure the first user forced variations are still valid
    self.assertEqual(self.project_config.get_forced_variation('test_experiment', 'test_user_1').key, 'control')
    self.assertEqual(self.project_config.get_forced_variation('group_exp_1', 'test_user_1').key, 'group_exp_1_control')

  def test_set_forced_variation_when_called_to_remove_forced_variation(self):
    """ Test set_forced_variation when no variation is given. """
    # Test case where both user and experiment are present in the forced variation map
    self.project_config.forced_variation_map = {}
    self.project_config.set_forced_variation('test_experiment', 'test_user', 'variation')

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.assertTrue(self.project_config.set_forced_variation('test_experiment', 'test_user', None))
    mock_config_logging.debug.assert_called_once_with(
      'Variation mapped to experiment "test_experiment" has been removed for user "test_user".'
    )

    # Test case where user is present in the forced variation map, but the given experiment isn't
    self.project_config.forced_variation_map = {}
    self.project_config.set_forced_variation('test_experiment', 'test_user', 'variation')

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.assertTrue(self.project_config.set_forced_variation('group_exp_1', 'test_user', None))
    mock_config_logging.debug.assert_called_once_with(
      'Nothing to remove. Variation mapped to experiment "group_exp_1" for user "test_user" does not exist.'
    )


class ConfigLoggingTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            logger=logger.SimpleLogger())
    self.project_config = self.optimizely.config

  def test_get_experiment_from_key__invalid_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_experiment_from_key('invalid_key')

    mock_config_logging.error.assert_called_once_with('Experiment key "invalid_key" is not in datafile.')

  def test_get_audience__invalid_id(self):
    """ Test that message is logged when provided audience ID is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_audience('42')

    mock_config_logging.error.assert_called_once_with('Audience ID "42" is not in datafile.')

  def test_get_variation_from_key__invalid_experiment_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_variation_from_key('invalid_key', 'control')

    mock_config_logging.error.assert_called_once_with('Experiment key "invalid_key" is not in datafile.')

  def test_get_variation_from_key__invalid_variation_key(self):
    """ Test that message is logged when provided variation key is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_variation_from_key('test_experiment', 'invalid_key')

    mock_config_logging.error.assert_called_once_with('Variation key "invalid_key" is not in datafile.')

  def test_get_variation_from_id__invalid_experiment_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_variation_from_id('invalid_key', '111128')

    mock_config_logging.error.assert_called_once_with('Experiment key "invalid_key" is not in datafile.')

  def test_get_variation_from_id__invalid_variation_id(self):
    """ Test that message is logged when provided variation ID is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_variation_from_id('test_experiment', '42')

    mock_config_logging.error.assert_called_once_with('Variation ID "42" is not in datafile.')

  def test_get_event__invalid_key(self):
    """ Test that message is logged when provided event key is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_event('invalid_key')

    mock_config_logging.error.assert_called_once_with('Event "invalid_key" is not in datafile.')

  def test_get_attribute_id__invalid_key(self):
    """ Test that message is logged when provided attribute key is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_attribute_id('invalid_key')

    mock_config_logging.error.assert_called_once_with('Attribute "invalid_key" is not in datafile.')

  def test_get_attribute_id__key_with_opt_prefix_but_not_a_control_attribute(self):
    """ Test that message is logged when provided attribute key has $opt_ in prefix and
    key is not one of the control attributes. """
    self.project_config.attribute_key_map['$opt_abc'] = entities.Attribute('007', '$opt_abc')

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_attribute_id('$opt_abc')

    mock_config_logging.warning.assert_called_once_with(("Attribute $opt_abc unexpectedly has reserved prefix $opt_; "
                                                         "using attribute ID instead of reserved attribute name."))

  def test_get_group__invalid_id(self):
    """ Test that message is logged when provided group ID is invalid. """

    with mock.patch.object(self.project_config, 'logger') as mock_config_logging:
      self.project_config.get_group('42')

    mock_config_logging.error.assert_called_once_with('Group ID "42" is not in datafile.')


class ConfigExceptionTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            error_handler=error_handler.RaiseExceptionErrorHandler)
    self.project_config = self.optimizely.config

  def test_get_experiment_from_key__invalid_key(self):
    """ Test that exception is raised when provided experiment key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidExperimentException,
                            enums.Errors.INVALID_EXPERIMENT_KEY_ERROR,
                            self.project_config.get_experiment_from_key, 'invalid_key')

  def test_get_audience__invalid_id(self):
    """ Test that message is logged when provided audience ID is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidAudienceException,
                            enums.Errors.INVALID_AUDIENCE_ERROR,
                            self.project_config.get_audience, '42')

  def test_get_variation_from_key__invalid_experiment_key(self):
    """ Test that exception is raised when provided experiment key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidExperimentException,
                            enums.Errors.INVALID_EXPERIMENT_KEY_ERROR,
                            self.project_config.get_variation_from_key, 'invalid_key', 'control')

  def test_get_variation_from_key__invalid_variation_key(self):
    """ Test that exception is raised when provided variation key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidVariationException,
                            enums.Errors.INVALID_VARIATION_ERROR,
                            self.project_config.get_variation_from_key, 'test_experiment', 'invalid_key')

  def test_get_variation_from_id__invalid_experiment_key(self):
    """ Test that exception is raised when provided experiment key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidExperimentException,
                            enums.Errors.INVALID_EXPERIMENT_KEY_ERROR,
                            self.project_config.get_variation_from_id, 'invalid_key', '111128')

  def test_get_variation_from_id__invalid_variation_id(self):
    """ Test that exception is raised when provided variation ID is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidVariationException,
                            enums.Errors.INVALID_VARIATION_ERROR,
                            self.project_config.get_variation_from_key, 'test_experiment', '42')

  def test_get_event__invalid_key(self):
    """ Test that exception is raised when provided event key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidEventException,
                            enums.Errors.INVALID_EVENT_KEY_ERROR,
                            self.project_config.get_event, 'invalid_key')

  def test_get_attribute_id__invalid_key(self):
    """ Test that exception is raised when provided attribute key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException,
                            enums.Errors.INVALID_ATTRIBUTE_ERROR,
                            self.project_config.get_attribute_id, 'invalid_key')

  def test_get_group__invalid_id(self):
    """ Test that exception is raised when provided group ID is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidGroupException,
                            enums.Errors.INVALID_GROUP_ID_ERROR,
                            self.project_config.get_group, '42')
