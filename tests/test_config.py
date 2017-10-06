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
        }],
      '111182'),
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

  def test_init__with_more_fields(self):
    """ Test that no issues occur on creating object with datafile consisting of more fields. """

    # Adding some additional fields like live variables and IP anonymization
    config_dict = {
      'revision': '42',
      'version': '3',
      'anonymizeIP': False,
      'variables': [{
        'id': '127',
        'key': 'is_working',
        'defaultValue': 'true',
        'type': 'boolean',
      }],
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
            'variables': []
          }, {
            'key': 'group_exp_1_variation',
            'id': '28902',
            'variables': []
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
      'projectId': '111001'
    }

    test_obj = optimizely.Optimizely(json.dumps(config_dict))
    self.assertTrue(test_obj.is_valid)

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

  def test_get_revenue_goal(self):
    """ Test that revenue goal can be retrieved as expected. """

    self.assertEqual(entities.Event('111096', 'Total Revenue', ['111127']),
                     self.project_config.get_revenue_goal())

  def test_get_attribute__valid_key(self):
    """ Test that attribute is retrieved correctly for valid attribute key. """

    self.assertEqual(entities.Attribute('111094', 'test_attribute'),
                     self.project_config.get_attribute('test_attribute'))

  def test_get_attribute__invalid_key(self):
    """ Test that None is returned when provided attribute key is invalid. """

    self.assertIsNone(self.project_config.get_attribute('invalid_key'))

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
    self.assertTrue(self.project_config.set_forced_variation('test_experiment', 'test_user', ''))
    self.assertTrue(self.project_config.set_forced_variation('test_experiment', 'test_user', None))

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


class ConfigLoggingTest(base.BaseTest):
  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            logger=logger.SimpleLogger())
    self.project_config = self.optimizely.config

  def test_get_experiment_from_key__invalid_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_experiment_from_key('invalid_key')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Experiment key "invalid_key" is not in datafile.')

  def test_get_audience__invalid_id(self):
    """ Test that message is logged when provided audience ID is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_audience('42')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Audience ID "42" is not in datafile.')

  def test_get_variation_from_key__invalid_experiment_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_variation_from_key('invalid_key', 'control')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Experiment key "invalid_key" is not in datafile.')

  def test_get_variation_from_key__invalid_variation_key(self):
    """ Test that message is logged when provided variation key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_variation_from_key('test_experiment', 'invalid_key')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Variation key "invalid_key" is not in datafile.')

  def test_get_variation_from_id__invalid_experiment_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_variation_from_id('invalid_key', '111128')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Experiment key "invalid_key" is not in datafile.')

  def test_get_variation_from_id__invalid_variation_id(self):
    """ Test that message is logged when provided variation ID is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_variation_from_id('test_experiment', '42')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Variation ID "42" is not in datafile.')

  def test_get_event__invalid_key(self):
    """ Test that message is logged when provided event key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_event('invalid_key')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Event "invalid_key" is not in datafile.')

  def test_get_attribute__invalid_key(self):
    """ Test that message is logged when provided attribute key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_attribute('invalid_key')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Attribute "invalid_key" is not in datafile.')

  def test_get_group__invalid_id(self):
    """ Test that message is logged when provided group ID is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_group('42')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Group ID "42" is not in datafile.')


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

  def test_get_attribute__invalid_key(self):
    """ Test that exception is raised when provided attribute key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException,
                            enums.Errors.INVALID_ATTRIBUTE_ERROR,
                            self.project_config.get_attribute, 'invalid_key')

  def test_get_group__invalid_id(self):
    """ Test that exception is raised when provided group ID is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidGroupException,
                            enums.Errors.INVALID_GROUP_ID_ERROR,
                            self.project_config.get_group, '42')
