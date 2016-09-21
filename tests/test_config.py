import json
import mock

from optimizely import entities
from optimizely import error_handler
from optimizely import exceptions
from optimizely import logger
from optimizely import optimizely
from optimizely import project_config
from optimizely.helpers import enums

from . import base


class ConfigTest(base.BaseTestV1):

  def test_init(self):
    """ Test that on creating object, properties are initiated correctly. """

    self.assertEqual(self.config_dict['accountId'], self.project_config.account_id)
    self.assertEqual(self.config_dict['projectId'], self.project_config.project_id)
    self.assertEqual(self.config_dict['revision'], self.project_config.revision)
    self.assertEqual(self.config_dict['experiments'], self.project_config.experiments)
    self.assertEqual(self.config_dict['events'], self.project_config.events)
    expected_group_id_map = {
      '19228': self.config_dict['groups'][0]
    }
    expected_experiment_key_map = {
      'test_experiment': self.config_dict['experiments'][0],
      'group_exp_1': self.config_dict['groups'][0]['experiments'][0],
      'group_exp_2': self.config_dict['groups'][0]['experiments'][1]
    }
    expected_experiment_key_map['group_exp_1']['groupId'] = '19228'
    expected_experiment_key_map['group_exp_1']['groupPolicy'] = 'random'
    expected_experiment_key_map['group_exp_2']['groupId'] = '19228'
    expected_experiment_key_map['group_exp_2']['groupPolicy'] = 'random'
    expected_experiment_id_map = {
      '111127': self.config_dict['experiments'][0],
      '32222': self.config_dict['groups'][0]['experiments'][0],
      '32223': self.config_dict['groups'][0]['experiments'][1]
    }
    expected_experiment_id_map['32222']['groupId'] = '19228'
    expected_experiment_id_map['32222']['groupPolicy'] = 'random'
    expected_experiment_id_map['32223']['groupId'] = '19228'
    expected_experiment_id_map['32223']['groupPolicy'] = 'random'
    expected_event_key_map = {
      'test_event': project_config.Event(id='111095', key='test_event', experimentIds=['111127']),
      'Total Revenue': project_config.Event(id='111096', key='Total Revenue', experimentIds=['111127'])
    }
    expected_attribute_key_map = {
      'test_attribute': project_config.AttributeV1(id='111094', key='test_attribute', segmentId='11133')
    }
    expected_audience_id_map = {
      '11154': self.config_dict['audiences'][0]
    }
    expected_audience_id_map['11154'].update({
      'conditionList': [['test_attribute', 'test_value']],
      'conditionStructure': ['and', ['or', ['or', 0]]]
    })
    expected_variation_key_map = {
      'test_experiment': {
        'control': {
          'key': 'control',
          'id': '111128'
        },
        'variation': {
          'key': 'variation',
          'id': '111129'
        }
      },
      'group_exp_1': {
        'group_exp_1_control': {
          'key': 'group_exp_1_control',
          'id': '28901'
        },
        'group_exp_1_variation': {
          'key': 'group_exp_1_variation',
          'id': '28902'
        }
      },
      'group_exp_2': {
        'group_exp_2_control': {
          'key': 'group_exp_2_control',
          'id': '28905'
        },
        'group_exp_2_variation': {
          'key': 'group_exp_2_variation',
          'id': '28906'
        }
      }
    }
    expected_variation_id_map = {
      'test_experiment': {
        '111128': {
          'key': 'control',
          'id': '111128'
        },
        '111129': {
          'key': 'variation',
          'id': '111129'
        }
      },
      'group_exp_1': {
        '28901': {
          'key': 'group_exp_1_control',
          'id': '28901'
        },
        '28902': {
          'key': 'group_exp_1_variation',
          'id': '28902'
        }
      },
      'group_exp_2': {
        '28905': {
          'key': 'group_exp_2_control',
          'id': '28905'
        },
        '28906': {
          'key': 'group_exp_2_variation',
          'id': '28906'
        }
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

  def test_get_version(self):
    """ Test that JSON version is retrieved correctly when using get_version. """

    self.assertEqual('1', self.project_config.get_version())

  def test_get_account_id(self):
    """ Test that account ID is retrieved correctly when using get_account_id. """

    self.assertEqual(self.config_dict['accountId'], self.project_config.get_account_id())

  def test_get_project_id(self):
    """ Test that project ID is retrieved correctly when using get_project_id. """

    self.assertEqual(self.config_dict['projectId'], self.project_config.get_project_id())

  def test_get_experiment_from_key__valid_key(self):
    """ Test that experiment is retrieved correctly for valid experiment key. """

    self.assertEqual('19228', self.project_config.get_experiment_from_key('group_exp_1'))

  def test_get_experiment_from_key__invalid_key(self):
    """ Test that None is returned when provided experiment key is invalid. """

    self.assertIsNone(self.project_config.get_experiment_from_key('invalid_key'))

  def test_get_experiment_from_id__valid_id(self):
    """ Test that experiment is retrieved correctly for valid experiment ID. """
    pass

  def test_get_experiment_from_id__invalid_id(self):
    """ Test that None is returned when provided experiment ID is invalid. """
    pass

  def test_get_audience_object_from_id__valid_id(self):
    """ Test that audience object is retrieved correctly given a valid audience ID. """

    self.assertEqual(self.project_config.audience_id_map['11154'],
                     self.project_config.get_audience_object_from_id('11154'))

  def test_get_audience_object_from_id__invalid_id(self):
    """ Test that None is returned for an invalid audience ID. """

    self.assertIsNone(self.project_config.get_audience_object_from_id('42'))

  def test_get_variation_key_from_id__valid_experiment_key(self):
    """ Test that variation key is retrieved correctly when valid experiment key and variation ID are provided. """

    self.assertEqual('control',
                     self.project_config.get_variation_key_from_id(self.config_dict['experiments'][0]['key'], '111128'))

  def test_get_variation_key_from_id__invalid_experiment_key(self):
    """ Test that None is returned when provided experiment key is invalid. """

    self.assertIsNone(self.project_config.get_variation_key_from_id('invalid_key', '111128'))

  def test_get_variation_key_from_id__invalid_variation_id(self):
    """ Test that None is returned when provided variation ID is invalid. """

    self.assertIsNone(self.project_config.get_variation_key_from_id(self.config_dict['experiments'][0]['key'],
                                                                    'invalid_id'))

  def test_get_variation_id__valid_experiment_key(self):
    """ Test that variation ID is retrieved correctly when valid experiment key and variation key are provided. """

    self.assertEqual('111128',
                     self.project_config.get_variation_id(self.config_dict['experiments'][0]['key'], 'control'))

  def test_get_variation_id__invalid_experiment_key(self):
    """ Test that None is returned when provided experiment key is invalid. """

    self.assertIsNone(self.project_config.get_variation_id('invalid_key', 'control'))

  def test_get_variation_id__invalid_variation_key(self):
    """ Test that None is returned when provided variation key is invalid. """

    self.assertIsNone(self.project_config.get_variation_id(self.config_dict['experiments'][0]['key'], 'invalid_key'))

  def test_get_event__valid_key(self):
    """ Test that event is retrieved correctly for valid event key. """

    self.assertEqual(entities.Event('111095', 'test_event', ['111127']).__dict__,
                     self.project_config.get_event('test_event').__dict__)

  def test_get_event__invalid_key(self):
    """ Test that None is returned when provided goal key is invalid. """

    self.assertIsNone(self.project_config.get_event('invalid_key'))

  def test_get_revenue_goal(self):
    """ Test that revenue goal can be retrieved as expected. """

    self.assertEqual(entities.Event('111096', 'Total Revenue', ['111127']).__dict__,
                     self.project_config.get_revenue_goal().__dict__)

  def test_get_attribute__valid_key(self):
    """ Test that attribute is retrieved correctly for valid attribute key. """

    self.assertEqual(entities.Attribute('111094', 'test_attribute', segmentId='11133').__dict__,
                     self.project_config.get_attribute('test_attribute').__dict__)

  def test_get_attribute__invalid_key(self):
    """ Test that None is returned when provided attribute key is invalid. """

    self.assertIsNone(self.project_config.get_attribute('invalid_key'))

  def test_get_traffic_allocation__valid_key(self):
    """ Test that trafficAllocation is retrieved correctly for valid experiment key or group ID. """

    self.assertEqual(self.config_dict['groups'][0]['trafficAllocation'],
                     self.project_config.get_traffic_allocation(self.project_config.group_id_map,
                                                                '19228'))

  def test_get_traffic_allocation__invalid_key(self):
    """ Test that None is returned when provided experiment key or group ID is invalid. """

    self.assertIsNone(self.project_config.get_traffic_allocation(self.project_config.group_id_map,
                                                                 'invalid_key'))


class ConfigTestV2(base.BaseTestV2):
  pass

class ConfigLoggingTest(base.BaseTestV1):
  def setUp(self):
    base.BaseTestV1.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            logger=logger.SimpleLogger())
    self.project_config = self.optimizely.config

  def test_get_experiment_from_key__invalid_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_experiment_from_key('invalid_key')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Experiment key "invalid_key" is not in datafile.')

  def test_get_variation_key_from_id__invalid_variation_id(self):
    """ Test that message is logged when provided variation ID is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_variation_key_from_id('test_experiment', 'invalid_id')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Variation ID "invalid_id" is not in datafile.')

  def test_get_variation_id__invalid_experiment_key(self):
    """ Test that message is logged when provided experiment key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_variation_id('invalid_key', 'control')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Experiment key "invalid_key" is not in datafile.')

  def test_get_variation_id__invalid_variation_key(self):
    """ Test that message is logged when provided variation key is invalid. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.project_config.get_variation_id('test_experiment', 'invalid_key')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Variation key "invalid_key" is not in datafile.')

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


class ConfigExceptionTest(base.BaseTestV1):

  def setUp(self):
    base.BaseTestV1.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            error_handler=error_handler.RaiseExceptionErrorHandler)
    self.project_config = self.optimizely.config

  def test_get_experiment_from_key__invalid_key(self):
    """ Test that exception is raised when provided experiment key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidExperimentException,
                            enums.Errors.INVALID_EXPERIMENT_KEY_ERROR,
                            self.project_config.get_experiment_from_key, 'invalid_key')

  def test_get_variation_key_from_id__invalid_variation_id(self):
    """ Test that exception is raised when provided variation ID is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidVariationException,
                            enums.Errors.INVALID_VARIATION_ERROR,
                            self.project_config.get_variation_key_from_id, 'test_experiment', 'invalid_id')

  def test_get_variation_id__invalid_experiment_key(self):
    """ Test that exception is raised when provided experiment key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidExperimentException,
                            enums.Errors.INVALID_EXPERIMENT_KEY_ERROR,
                            self.project_config.get_variation_id, 'invalid_key', 'control')

  def test_get_variation_id__invalid_variation_key(self):
    """ Test that exception is raised when provided experiment key is invalid. """

    self.assertRaisesRegexp(exceptions.InvalidVariationException,
                            enums.Errors.INVALID_VARIATION_ERROR,
                            self.project_config.get_variation_id, 'test_experiment', 'invalid_key')

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
