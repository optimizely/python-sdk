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
from operator import itemgetter

from optimizely import decision_service
from optimizely import entities
from optimizely import error_handler
from optimizely import event_builder
from optimizely import exceptions
from optimizely import logger
from optimizely import optimizely
from optimizely import project_config
from optimizely import version
from optimizely.helpers import enums
from optimizely.notification_center import NotificationCenter
from . import base


class OptimizelyTest(base.BaseTest):

  strTest = None

  try:
    isinstance("test", basestring)  # attempt to evaluate basestring

    _expected_notification_failure = 'Problem calling notify callback.'

    def isstr(self, s):
      return isinstance(s, basestring)

    strTest = isstr

  except NameError:

    def isstr(self, s):
      return isinstance(s, str)
    strTest = isstr

  def _validate_event_object(self, event_obj, expected_url, expected_params, expected_verb, expected_headers):
    """ Helper method to validate properties of the event object. """

    self.assertEqual(expected_url, event_obj.url)

    expected_params['visitors'][0]['attributes'] = \
      sorted(expected_params['visitors'][0]['attributes'], key=itemgetter('key'))
    event_obj.params['visitors'][0]['attributes'] = \
      sorted(event_obj.params['visitors'][0]['attributes'], key=itemgetter('key'))
    self.assertEqual(expected_params, event_obj.params)
    self.assertEqual(expected_verb, event_obj.http_verb)
    self.assertEqual(expected_headers, event_obj.headers)

  def _validate_event_object_event_tags(self, event_obj, expected_event_metric_params, expected_event_features_params):
    """ Helper method to validate properties of the event object related to event tags. """

    # get event metrics from the created event object
    event_metrics = event_obj.params['visitors'][0]['snapshots'][0]['events'][0]['tags']
    self.assertEqual(expected_event_metric_params, event_metrics)

    # get event features from the created event object
    event_features = event_obj.params['visitors'][0]['attributes'][0]
    self.assertEqual(expected_event_features_params, event_features)

  def test_init__invalid_datafile__logs_error(self):
    """ Test that invalid datafile logs error on init. """

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
      opt_obj = optimizely.Optimizely('invalid_datafile')

    mock_client_logger.exception.assert_called_once_with('Provided "datafile" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__null_datafile__logs_error(self):
    """ Test that null datafile logs error on init. """

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
      opt_obj = optimizely.Optimizely(None)

    mock_client_logger.exception.assert_called_once_with('Provided "datafile" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__empty_datafile__logs_error(self):
    """ Test that empty datafile logs error on init. """

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
      opt_obj = optimizely.Optimizely("")

    mock_client_logger.exception.assert_called_once_with('Provided "datafile" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__invalid_event_dispatcher__logs_error(self):
    """ Test that invalid event_dispatcher logs error on init. """

    class InvalidDispatcher(object):
      pass

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), event_dispatcher=InvalidDispatcher)

    mock_client_logger.exception.assert_called_once_with('Provided "event_dispatcher" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__invalid_logger__logs_error(self):
    """ Test that invalid logger logs error on init. """

    class InvalidLogger(object):
      pass

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), logger=InvalidLogger)

    mock_client_logger.exception.assert_called_once_with('Provided "logger" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__invalid_error_handler__logs_error(self):
    """ Test that invalid error_handler logs error on init. """

    class InvalidErrorHandler(object):
      pass

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), error_handler=InvalidErrorHandler)

    mock_client_logger.exception.assert_called_once_with('Provided "error_handler" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__unsupported_datafile_version__logs_error(self):
    """ Test that datafile with unsupported version logs error on init. """

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger),\
      mock.patch('optimizely.error_handler.NoOpErrorHandler.handle_error') as mock_error_handler:
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_unsupported_version))

    mock_client_logger.exception.assert_called_once_with(
      'This version of the Python SDK does not support the given datafile version: "5".'
    )

    args, kwargs = mock_error_handler.call_args
    self.assertIsInstance(args[0], exceptions.UnsupportedDatafileVersionException)
    self.assertEqual(args[0].args[0],
                     'This version of the Python SDK does not support the given datafile version: "5".')

    self.assertFalse(opt_obj.is_valid)

  def test_init_with_supported_datafile_version(self):
    """ Test that datafile with supported version works as expected. """

    self.assertTrue(self.config_dict['version'] in project_config.SUPPORTED_VERSIONS)

    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict))

    mock_client_logger.exception.assert_not_called()
    self.assertTrue(opt_obj.is_valid)

  def test_skip_json_validation_true(self):
    """ Test that on setting skip_json_validation to true, JSON schema validation is not performed. """

    with mock.patch('optimizely.helpers.validator.is_datafile_valid') as mock_datafile_validation:
      optimizely.Optimizely(json.dumps(self.config_dict), skip_json_validation=True)

    self.assertEqual(0, mock_datafile_validation.call_count)

  def test_invalid_json_raises_schema_validation_off(self):
    """ Test that invalid JSON logs error if schema validation is turned off. """

    # Not  JSON
    mock_client_logger = mock.MagicMock()
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger),\
      mock.patch('optimizely.error_handler.NoOpErrorHandler.handle_error') as mock_error_handler:
      opt_obj = optimizely.Optimizely('invalid_json', skip_json_validation=True)

    mock_client_logger.exception.assert_called_once_with('Provided "datafile" is in an invalid format.')
    args, kwargs = mock_error_handler.call_args
    self.assertIsInstance(args[0], exceptions.InvalidInputException)
    self.assertEqual(args[0].args[0],
                     'Provided "datafile" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

    mock_client_logger.reset_mock()
    mock_error_handler.reset_mock()

    # JSON having valid version, but entities have invalid format
    with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger),\
      mock.patch('optimizely.error_handler.NoOpErrorHandler.handle_error') as mock_error_handler:
      opt_obj = optimizely.Optimizely({'version': '2', 'events': 'invalid_value', 'experiments': 'invalid_value'},
                                      skip_json_validation=True)

    mock_client_logger.exception.assert_called_once_with('Provided "datafile" is in an invalid format.')
    args, kwargs = mock_error_handler.call_args
    self.assertIsInstance(args[0], exceptions.InvalidInputException)
    self.assertEqual(args[0].args[0],
                     'Provided "datafile" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_activate(self):
    """ Test that activate calls dispatch_event with right params and returns expected variation. """

    with mock.patch(
        'optimizely.decision_service.DecisionService.get_variation',
        return_value=self.project_config.get_variation_from_id('test_experiment', '111129')) as mock_decision, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111129',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_decision.assert_called_once_with(
      self.project_config.get_experiment_from_key('test_experiment'), 'test_user', None
    )
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_add_activate_remove_clear_listener(self):
    callbackhit = [False]
    """ Test adding a listener activate passes correctly and gets called"""
    def on_activate(experiment, user_id, attributes, variation, event):
      self.assertTrue(isinstance(experiment, entities.Experiment))
      self.assertTrue(self.strTest(user_id))
      if attributes is not None:
        self.assertTrue(isinstance(attributes, dict))
      self.assertTrue(isinstance(variation, entities.Variation))
      self.assertTrue(isinstance(event, event_builder.Event))
      print("Activated experiment {0}".format(experiment.key))
      callbackhit[0] = True

    notification_id = self.optimizely.notification_center.add_notification_listener(
      enums.NotificationTypes.ACTIVATE, on_activate
    )
    with mock.patch(
        'optimizely.decision_service.DecisionService.get_variation',
        return_value=self.project_config.get_variation_from_id('test_experiment', '111129')), \
         mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event'):
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

    self.assertEqual(True, callbackhit[0])
    self.optimizely.notification_center.remove_notification_listener(notification_id)
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.ACTIVATE]))
    self.optimizely.notification_center.clear_all_notifications()
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.ACTIVATE]))

  def test_add_track_remove_clear_listener(self):
    """ Test adding a listener tract passes correctly and gets called"""
    callback_hit = [False]

    def on_track(event_key, user_id, attributes, event_tags, event):
      self.assertTrue(self.strTest(event_key))
      self.assertTrue(self.strTest(user_id))
      if attributes is not None:
        self.assertTrue(isinstance(attributes, dict))
      if event_tags is not None:
        self.assertTrue(isinstance(event_tags, dict))
      self.assertTrue(isinstance(event, event_builder.Event))
      print('Track event with event_key={0}'.format(event_key))
      callback_hit[0] = True

    note_id = self.optimizely.notification_center.add_notification_listener(
      enums.NotificationTypes.TRACK, on_track)

    with mock.patch(
        'optimizely.decision_service.DecisionService.get_variation',
        return_value=self.project_config.get_variation_from_id('test_experiment', '111129')), \
         mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event'):
      self.optimizely.track('test_event', 'test_user')

    self.assertEqual(True, callback_hit[0])

    self.assertEqual(1, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))
    self.optimizely.notification_center.remove_notification_listener(note_id)
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))
    self.optimizely.notification_center.clear_all_notifications()
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))

  def test_add_same_listener(self):
    """ Test adding a same listener """

    def on_track(event_key, user_id, attributes, event_tags, event):
      print('event_key={}', event_key)

    self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track)

    self.assertEqual(1, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))

    self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track)

    self.assertEqual(1, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))

  def test_add_listener_custom_type(self):
    """ Test adding a same listener """
    custom_type = "custom_notification_type"
    custom_called = [False]

    def on_custom_event(test_string):
      custom_called[0] = True
      print('Custom notification event tracked with parameter test_string={}', test_string)

    notification_id = self.optimizely.notification_center.add_notification_listener(custom_type, on_custom_event)

    self.assertEqual(1, len(self.optimizely.notification_center.notifications[custom_type]))

    self.optimizely.notification_center.send_notifications(custom_type, "test")

    self.assertTrue(custom_called[0])

    self.optimizely.notification_center.remove_notification_listener(notification_id)

    self.assertEqual(0, len(self.optimizely.notification_center.notifications[custom_type]))

    self.optimizely.notification_center.clear_notifications(custom_type)

    self.assertEqual(0, len(self.optimizely.notification_center.notifications[custom_type]))

  def test_invalid_notification_send(self):
    """ Test adding a same listener """
    custom_type = "custom_notification_type"
    custom_called = [False]

    def on_custom_event(test_string):
      custom_called[0] = True
      print('Custom notification event tracked with parameter test_string={}', test_string)
    mock_logger = mock.Mock()
    notification_center = NotificationCenter(mock_logger)
    notification_center.add_notification_listener(custom_type, on_custom_event)
    notification_center.send_notifications(custom_type, 1, 2, "5", 6)
    mock_logger.exception.assert_called_once_with('Problem calling notify callback!')

  def test_add_invalid_listener(self):
    """ Test adding a invalid listener """
    not_a_listener = "This is not a listener"
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))

  def test_add_multi_listener(self):
    """ Test adding a 2 listeners """
    def on_track(event_key, *args):
      print("on track 1 called")

    def on_track2(event_key, *args):
      print("on track 2 called")

    self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track)

    self.assertEqual(1, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))
    self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track2)

    self.assertEqual(2, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))

    self.optimizely.notification_center.clear_all_notifications()
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))

  def test_remove_listener(self):
    """ Test remove listener that isn't added"""
    self.optimizely.notification_center.remove_notification_listener(5)
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.TRACK]))
    self.assertEqual(0, len(self.optimizely.notification_center.notifications[enums.NotificationTypes.ACTIVATE]))

  def test_activate_listener(self):
    """ Test that activate calls broadcast activate with proper parameters. """

    with mock.patch(
        'optimizely.decision_service.DecisionService.get_variation',
        return_value=self.project_config.get_variation_from_id('test_experiment', '111129')), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch, \
      mock.patch('optimizely.notification_center.NotificationCenter.send_notifications') as mock_broadcast_activate:
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

    mock_broadcast_activate.assert_called_once_with(enums.NotificationTypes.ACTIVATE,
                                                    self.project_config.get_experiment_from_key('test_experiment'),
                                                    'test_user', None,
                                                    self.project_config.get_variation_from_id('test_experiment',
                                                                                              '111129'),
                                                    mock_dispatch.call_args[0][0])

  def test_activate_listener_with_attr(self):
    """ Test that activate calls broadcast activate with proper parameters. """

    with mock.patch(
        'optimizely.decision_service.DecisionService.get_variation',
        return_value=self.project_config.get_variation_from_id('test_experiment', '111129')), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch, \
      mock.patch('optimizely.notification_center.NotificationCenter.send_notifications') as mock_broadcast_activate:
      self.assertEqual('variation',
                       self.optimizely.activate('test_experiment', 'test_user', {'test_attribute': 'test_value'}))

    mock_broadcast_activate.assert_called_once_with(enums.NotificationTypes.ACTIVATE,
                                                    self.project_config.get_experiment_from_key('test_experiment'),
                                                    'test_user', {'test_attribute': 'test_value'},
                                                    self.project_config.get_variation_from_id(
                                                      'test_experiment', '111129'
                                                    ),
                                                    mock_dispatch.call_args[0][0]
                                                    )

  def test_track_listener(self):
    """ Test that track calls notification broadcaster. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch, \
      mock.patch('optimizely.notification_center.NotificationCenter.send_notifications') as mock_event_tracked:
      self.optimizely.track('test_event', 'test_user')

      mock_event_tracked.assert_called_once_with(enums.NotificationTypes.TRACK, "test_event",
                                                 'test_user', None, None, mock_dispatch.call_args[0][0])

  def test_track_listener_with_attr(self):
    """ Test that track calls notification broadcaster. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch, \
      mock.patch('optimizely.notification_center.NotificationCenter.send_notifications') as mock_event_tracked:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'})

      mock_event_tracked.assert_called_once_with(enums.NotificationTypes.TRACK, "test_event", 'test_user',
                                                 {'test_attribute': 'test_value'},
                                                 None, mock_dispatch.call_args[0][0])

  def test_track_listener_with_attr_with_event_tags(self):
    """ Test that track calls notification broadcaster. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch, \
      mock.patch('optimizely.notification_center.NotificationCenter.send_notifications') as mock_event_tracked:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'},
                            event_tags={'value': 1.234, 'non-revenue': 'abc'})

      mock_event_tracked.assert_called_once_with(enums.NotificationTypes.TRACK, "test_event", 'test_user',
                                                 {'test_attribute': 'test_value'},
                                                 {'value': 1.234, 'non-revenue': 'abc'},
                                                 mock_dispatch.call_args[0][0])

  def test_is_feature_enabled__callback_listener(self):
    """ Test that the feature is enabled for the user if bucketed into variation of an experiment.
    Also confirm that impression event is dispatched. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    feature = project_config.get_feature_from_key('test_feature_in_experiment')

    access_callback = [False]

    def on_activate(experiment, user_id, attributes, variation, event):
      access_callback[0] = True

    opt_obj.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate)

    mock_experiment = project_config.get_experiment_from_key('test_experiment')
    mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      mock_experiment,
                      mock_variation,
                      decision_service.DECISION_SOURCE_EXPERIMENT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)
    self.assertTrue(access_callback[0])

  def test_is_feature_enabled_rollout_callback_listener(self):
    """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is dispatched. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    feature = project_config.get_feature_from_key('test_feature_in_experiment')

    access_callback = [False]

    def on_activate(experiment, user_id, attributes, variation, event):
      access_callback[0] = True

    opt_obj.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate)

    mock_experiment = project_config.get_experiment_from_key('test_experiment')
    mock_variation = project_config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      mock_experiment,
                      mock_variation,
                      decision_service.DECISION_SOURCE_ROLLOUT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)

    # Check that impression event is not sent
    self.assertEqual(0, mock_dispatch_event.call_count)
    self.assertEqual(False, access_callback[0])

  def test_activate__with_attributes__audience_match(self):
    """ Test that activate calls dispatch_event with right params and returns expected
    variation when attributes are provided and audience conditions are met. """

    with mock.patch(
        'optimizely.decision_service.DecisionService.get_variation',
        return_value=self.project_config.get_variation_from_id('test_experiment', '111129')) \
        as mock_get_variation, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user',
                                                             {'test_attribute': 'test_value'}))
    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111129',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_activate__with_attributes_of_different_types(self):
    """ Test that activate calls dispatch_event with right params and returns expected
    variation when different types of attributes are provided and audience conditions are met. """

    with mock.patch(
        'optimizely.bucketer.Bucketer.bucket',
        return_value=self.project_config.get_variation_from_id('test_experiment', '111129')) \
        as mock_bucket, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:

      attributes = {
          'test_attribute': 'test_value_1',
          'boolean_key': False,
          'integer_key': 0,
          'double_key': 0.0
        }

      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user', attributes))

    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': False,
          'entity_id': '111196',
          'key': 'boolean_key'
        }, {
          'type': 'custom',
          'value': 0.0,
          'entity_id': '111198',
          'key': 'double_key'
        }, {
          'type': 'custom',
          'value': 0,
          'entity_id': '111197',
          'key': 'integer_key'
        }, {
          'type': 'custom',
          'value': 'test_value_1',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111129',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }

    mock_bucket.assert_called_once_with(
      self.project_config.get_experiment_from_key('test_experiment'), 'test_user', 'test_user'
    )
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_activate__with_attributes__audience_match__forced_bucketing(self):
    """ Test that activate calls dispatch_event with right params and returns expected
    variation when attributes are provided and audience conditions are met after a
    set_forced_variation is called. """

    with mock.patch('time.time', return_value=42), \
         mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
         mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'control'))
      self.assertEqual('control', self.optimizely.activate('test_experiment', 'test_user',
                                                           {'test_attribute': 'test_value'}))

    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111128',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }

    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_activate__with_attributes__audience_match__bucketing_id_provided(self):
    """ Test that activate calls dispatch_event with right params and returns expected variation
    when attributes (including bucketing ID) are provided and audience conditions are met. """

    with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129')) \
            as mock_get_variation, \
            mock.patch('time.time', return_value=42), \
            mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
            mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user',
                                                             {'test_attribute': 'test_value',
                                                              '$opt_bucketing_id': 'user_bucket_value'}))
    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'user_bucket_value',
          'entity_id': '$opt_bucketing_id',
          'key': '$opt_bucketing_id'
        }, {
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111129',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value',
                                                             '$opt_bucketing_id': 'user_bucket_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_activate__with_attributes__no_audience_match(self):
    """ Test that activate returns None when audience conditions do not match. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=False) as mock_audience_check:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user',
                                                 attributes={'test_attribute': 'test_value'}))
    mock_audience_check.assert_called_once_with(self.project_config,
                                                self.project_config.get_experiment_from_key('test_experiment'),
                                                {'test_attribute': 'test_value'})

  def test_activate__with_attributes__invalid_attributes(self):
    """ Test that activate returns None and does not bucket or dispatch event when attributes are invalid. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user', attributes='invalid'))

    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_activate__experiment_not_running(self):
    """ Test that activate returns None and does not dispatch event when experiment is not Running. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check, \
      mock.patch('optimizely.helpers.experiment.is_experiment_running',
                 return_value=False) as mock_is_experiment_running, \
      mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user',
                                                 attributes={'test_attribute': 'test_value'}))

    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))
    self.assertEqual(0, mock_audience_check.call_count)
    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_activate__whitelisting_overrides_audience_check(self):
    """ Test that during activate whitelist overrides audience check if user is in the whitelist. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=False) as mock_audience_check, \
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=True) as mock_is_experiment_running:
      self.assertEqual('control', self.optimizely.activate('test_experiment', 'user_1'))
    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))
    self.assertEqual(0, mock_audience_check.call_count)

  def test_activate__bucketer_returns_none(self):
    """ Test that activate returns None and does not dispatch event when user is in no variation. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True), \
      mock.patch('optimizely.bucketer.Bucketer.bucket', return_value=None) as mock_bucket, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user',
                                                 attributes={'test_attribute': 'test_value'}))
    mock_bucket.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                        'test_user',
                                        'test_user')
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_activate__invalid_object(self):
    """ Test that activate logs error if Optimizely object is not created correctly. """

    opt_obj = optimizely.Optimizely('invalid_datafile')

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
      self.assertIsNone(opt_obj.activate('test_experiment', 'test_user'))

    mock_client_logging.error.assert_called_once_with('Datafile has invalid format. Failing "activate".')

  def test_track__with_attributes(self):
    """ Test that track calls dispatch_event with right params when attributes are provided. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'})

    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111128',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111095',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'test_event',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_track__with_attributes__bucketing_id_provided(self):
    """ Test that track calls dispatch_event with right params when
    attributes (including bucketing ID) are provided. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
            mock.patch('time.time', return_value=42), \
            mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
            mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value',
                                                                   '$opt_bucketing_id': 'user_bucket_value'})

    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'user_bucket_value',
          'entity_id': '$opt_bucketing_id',
          'key': '$opt_bucketing_id'
        }, {
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111128',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111095',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'test_event',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value',
                                                             '$opt_bucketing_id': 'user_bucket_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_track__with_attributes__no_audience_match(self):
    """ Test that track does not call dispatch_event when audience conditions do not match. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_bucket, \
      mock.patch('time.time', return_value=42), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'wrong_test_value'})

    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_track__with_attributes__invalid_attributes(self):
    """ Test that track does not bucket or dispatch event if attributes are invalid. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes='invalid')

    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_track__with_event_tags(self):
    """ Test that track calls dispatch_event with right params when event tags are provided. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'},
                            event_tags={'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'})

    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111128',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'entity_id': '111095',
            'key': 'test_event',
            'revenue': 4200,
            'tags': {
              'non-revenue': 'abc',
              'revenue': 4200,
              'value': 1.234,
            },
            'timestamp': 42000,
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'value': 1.234,
          }]
        }],
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_track__with_event_tags_revenue(self):
    """ Test that track calls dispatch_event with right params when only revenue
        event tags are provided only. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'},
                            event_tags={'revenue': 4200, 'non-revenue': 'abc'})

    expected_params = {
      'visitors': [{
        'attributes': [{
          'entity_id': '111094',
          'type': 'custom',
          'value': 'test_value',
          'key': 'test_attribute'
        }],
        'visitor_id': 'test_user',
        'snapshots': [{
          'decisions': [{
            'variation_id': '111128',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'entity_id': '111095',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'tags': {
              'non-revenue': 'abc',
              'revenue': 4200
            },
            'timestamp': 42000,
            'revenue': 4200,
            'key': 'test_event'
          }]
        }]
      }],
      'client_name': 'python-sdk',
      'project_id': '111001',
      'client_version': version.__version__,
      'account_id': '12001',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_track__with_event_tags_numeric_metric(self):
    """ Test that track calls dispatch_event with right params when only numeric metric
        event tags are provided. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
      mock.patch('time.time', return_value=42), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'},
                            event_tags={'value': 1.234, 'non-revenue': 'abc'})

    expected_event_metrics_params = {
      'non-revenue': 'abc',
      'value': 1.234
    }

    expected_event_features_params = {
      'entity_id': '111094',
      'type': 'custom',
      'value': 'test_value',
      'key': 'test_attribute'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object_event_tags(mock_dispatch_event.call_args[0][0],
                                           expected_event_metrics_params,
                                           expected_event_features_params)

  def test_track__with_event_tags__forced_bucketing(self):
    """ Test that track calls dispatch_event with right params when event_value information is provided
    after a forced bucket. """

    with mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'},
                            event_tags={'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'})

    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111129',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'entity_id': '111095',
            'key': 'test_event',
            'revenue': 4200,
            'tags': {
              'non-revenue': 'abc',
              'revenue': 4200,
              'value': 1.234
            },
            'timestamp': 42000,
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'value': 1.234,
          }]
        }],
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '42'
    }

    self.assertEqual(1, mock_dispatch_event.call_count)

    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_track__with_invalid_event_tags(self):
    """ Test that track calls dispatch_event with right params when invalid event tags are provided. """

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111128'
                    )) as mock_get_variation, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'},
                            event_tags={'revenue': '4200', 'value': True})

    expected_params = {
      'visitors': [{
        'attributes': [{
          'entity_id': '111094',
          'type': 'custom',
          'value': 'test_value',
          'key': 'test_attribute'
        }],
        'visitor_id': 'test_user',
        'snapshots': [{
          'decisions': [{
            'variation_id': '111128',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111095',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'test_event',
            'tags': {
              'value': True,
              'revenue': '4200'
            }
          }]
        }]
      }],
      'client_name': 'python-sdk',
      'project_id': '111001',
      'client_version': version.__version__,
      'account_id': '12001',
      'anonymize_ip': False,
      'revision': '42'
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value'})
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0], 'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_track__experiment_not_running(self):
    """ Test that track does not call dispatch_event when experiment is not running. """

    with mock.patch('optimizely.helpers.experiment.is_experiment_running',
                    return_value=False) as mock_is_experiment_running, \
      mock.patch('time.time', return_value=42), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user')

    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_track_invalid_event_key(self):
    """ Test that track does not call dispatch_event when event does not exist. """
    dispatch_event_patch = mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event')
    with dispatch_event_patch as mock_dispatch_event, \
          mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
      self.optimizely.track('aabbcc_event', 'test_user')

    self.assertEqual(0, mock_dispatch_event.call_count)
    mock_client_logging.info.assert_called_with(
      'Not tracking user "test_user" for event "aabbcc_event".'
    )

  def test_track__whitelisted_user_overrides_audience_check(self):
    """ Test that track does not check for user in audience when user is in whitelist. """

    with mock.patch('optimizely.helpers.experiment.is_experiment_running',
                    return_value=True) as mock_is_experiment_running, \
      mock.patch('optimizely.helpers.audience.is_user_in_experiment',
                 return_value=False) as mock_audience_check, \
      mock.patch('time.time', return_value=42), \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'user_1')

    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))
    self.assertEqual(1, mock_dispatch_event.call_count)
    self.assertEqual(0, mock_audience_check.call_count)

  def test_track__invalid_object(self):
    """ Test that track logs error if Optimizely object is not created correctly. """

    opt_obj = optimizely.Optimizely('invalid_datafile')

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
      opt_obj.track('test_event', 'test_user')

    mock_client_logging.error.assert_called_once_with('Datafile has invalid format. Failing "track".')

  def test_track__invalid_experiment_key(self):
    """ Test that None is returned and expected log messages are logged during track \
    when exp_key is in invalid format. """

    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, \
         mock.patch('optimizely.helpers.validator.is_non_empty_string', return_value=False) as mock_validator:
      self.assertIsNone(self.optimizely.track(99, 'test_user'))

    mock_validator.assert_any_call(99)

    mock_client_logging.error.assert_called_once_with('Provided "event_key" is in an invalid format.')

  def test_track__invalid_user_id(self):
    """ Test that None is returned and expected log messages are logged during track \
    when user_id is in invalid format. """

    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, \
         mock.patch('optimizely.helpers.validator.is_non_empty_string', side_effect=[True, False]) as mock_validator:
      self.assertIsNone(self.optimizely.track('test_event', 99))

    mock_validator.assert_any_call(99)

    mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

  def test_get_variation__invalid_object(self):
    """ Test that get_variation logs error if Optimizely object is not created correctly. """

    opt_obj = optimizely.Optimizely('invalid_datafile')

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
      self.assertIsNone(opt_obj.get_variation('test_experiment', 'test_user'))

    mock_client_logging.error.assert_called_once_with('Datafile has invalid format. Failing "get_variation".')

  def test_get_variation_unknown_experiment_key(self):
    """ Test that get_variation retuns None when invalid experiment key is given. """
    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
      self.optimizely.get_variation('aabbccdd', 'test_user', None)

    mock_client_logging.info.assert_called_with(
      'Experiment key "aabbccdd" is invalid. Not activating user "test_user".'
    )

  def test_is_feature_enabled__returns_false_for_invalid_feature_key(self):
    """ Test that is_feature_enabled returns false if the provided feature key is invalid. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging,\
         mock.patch('optimizely.helpers.validator.is_non_empty_string', return_value=False) as mock_validator:
      self.assertFalse(opt_obj.is_feature_enabled(None, 'test_user'))

    mock_validator.assert_any_call(None)
    mock_client_logging.error.assert_called_with('Provided "feature_key" is in an invalid format.')

  def test_is_feature_enabled__returns_false_for_invalid_user_id(self):
    """ Test that is_feature_enabled returns false if the provided user ID is invalid. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging,\
         mock.patch('optimizely.helpers.validator.is_non_empty_string', side_effect=[True, False]) as mock_validator:
      self.assertFalse(opt_obj.is_feature_enabled('feature_key', 1.2))

    mock_validator.assert_any_call(1.2)
    mock_client_logging.error.assert_called_with('Provided "user_id" is in an invalid format.')

  def test_is_feature_enabled__returns_false_for__invalid_attributes(self):
    """ Test that is_feature_enabled returns false if attributes are in an invalid format. """
    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging, \
            mock.patch('optimizely.helpers.validator.are_attributes_valid', return_value=False) as mock_validator:
      self.assertFalse(opt_obj.is_feature_enabled('feature_key', 'test_user', attributes='invalid'))

    mock_validator.assert_called_once_with('invalid')
    mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')

  def test_is_feature_enabled__returns_false_for_invalid_feature(self):
    """ Test that the feature is not enabled for the user if the provided feature key is invalid. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature') as mock_decision, \
            mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertFalse(opt_obj.is_feature_enabled('invalid_feature', 'user1'))

    self.assertFalse(mock_decision.called)

    # Check that no event is sent
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_is_feature_enabled__returns_true_for_feature_experiment_if_feature_enabled_for_variation(self):
    """ Test that the feature is enabled for the user if bucketed into variation of an experiment and
    the variation's featureEnabled property is True. Also confirm that impression event is dispatched. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    feature = project_config.get_feature_from_key('test_feature_in_experiment')

    mock_experiment = project_config.get_experiment_from_key('test_experiment')
    mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

    # Assert that featureEnabled property is True
    self.assertTrue(mock_variation.featureEnabled)

    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      mock_experiment,
                      mock_variation,
                      decision_service.DECISION_SOURCE_EXPERIMENT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)

    expected_params = {
      'account_id': '12001',
      'project_id': '111111',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': True,
          'entity_id': '$opt_bot_filtering',
          'key': '$opt_bot_filtering'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111129',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '1'
    }
    # Check that impression event is sent
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0],
                                'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_is_feature_enabled__returns_false_for_feature_experiment_if_feature_disabled_for_variation(self):
    """ Test that the feature is disabled for the user if bucketed into variation of an experiment and
    the variation's featureEnabled property is False. Also confirm that impression event is dispatched. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    feature = project_config.get_feature_from_key('test_feature_in_experiment')

    mock_experiment = project_config.get_experiment_from_key('test_experiment')
    mock_variation = project_config.get_variation_from_id('test_experiment', '111128')

    # Assert that featureEnabled property is False
    self.assertFalse(mock_variation.featureEnabled)

    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      mock_experiment,
                      mock_variation,
                      decision_service.DECISION_SOURCE_EXPERIMENT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)

    # Check that impression event is sent
    expected_params = {
      'account_id': '12001',
      'project_id': '111111',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': True,
          'entity_id': '$opt_bot_filtering',
          'key': '$opt_bot_filtering'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111128',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42000,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
          }]
        }]
      }],
      'client_version': version.__version__,
      'client_name': 'python-sdk',
      'anonymize_ip': False,
      'revision': '1'
    }
    # Check that impression event is sent
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0],
                                'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_is_feature_enabled__returns_true_for_feature_rollout_if_feature_enabled(self):
    """ Test that the feature is enabled for the user if bucketed into variation of a rollout and
    the variation's featureEnabled property is True. Also confirm that no impression event is dispatched. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    feature = project_config.get_feature_from_key('test_feature_in_experiment')

    mock_experiment = project_config.get_experiment_from_key('test_experiment')
    mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

    # Assert that featureEnabled property is True
    self.assertTrue(mock_variation.featureEnabled)

    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      mock_experiment,
                      mock_variation,
                      decision_service.DECISION_SOURCE_ROLLOUT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)

    # Check that impression event is not sent
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_is_feature_enabled__returns_false_for_feature_rollout_if_feature_disabled(self):
    """ Test that the feature is disabled for the user if bucketed into variation of a rollout and
    the variation's featureEnabled property is False. Also confirm that no impression event is dispatched. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    feature = project_config.get_feature_from_key('test_feature_in_experiment')

    mock_experiment = project_config.get_experiment_from_key('test_experiment')
    mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

    # Set featureEnabled property to False
    mock_variation.featureEnabled = False

    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      mock_experiment,
                      mock_variation,
                      decision_service.DECISION_SOURCE_ROLLOUT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)

    # Check that impression event is not sent
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_is_feature_enabled__returns_false_when_user_is_not_bucketed_into_any_variation(self):
    """ Test that the feature is not enabled for the user if user is neither bucketed for
    Feature Experiment nor for Feature Rollout.
    Also confirm that impression event is not dispatched. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    project_config = opt_obj.config
    feature = project_config.get_feature_from_key('test_feature_in_experiment')
    # Test with decision_service.DECISION_SOURCE_EXPERIMENT
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      None,
                      None,
                      decision_service.DECISION_SOURCE_EXPERIMENT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)

    # Check that impression event is not sent
    self.assertEqual(0, mock_dispatch_event.call_count)

    # Test with decision_service.DECISION_SOURCE_ROLLOUT
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(
                      None,
                      None,
                      decision_service.DECISION_SOURCE_ROLLOUT
                    )) as mock_decision, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event, \
      mock.patch('uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'), \
      mock.patch('time.time', return_value=42):
      self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

    mock_decision.assert_called_once_with(feature, 'test_user', None)

    # Check that impression event is not sent
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_is_feature_enabled__invalid_object(self):
    """ Test that is_feature_enabled returns False if Optimizely object is not valid. """

    opt_obj = optimizely.Optimizely('invalid_file')

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging, \
      mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'user_1'))

    mock_client_logging.error.assert_called_once_with('Datafile has invalid format. Failing "is_feature_enabled".')

    # Check that no event is sent
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_get_enabled_features(self):
    """ Test that get_enabled_features only returns features that are enabled for the specified user. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    def side_effect(*args, **kwargs):
      feature_key = args[0]
      if feature_key == 'test_feature_in_experiment' or feature_key == 'test_feature_in_rollout':
        return True

      return False

    with mock.patch('optimizely.optimizely.Optimizely.is_feature_enabled',
                    side_effect=side_effect) as mock_is_feature_enabled:
      received_features = opt_obj.get_enabled_features('user_1')

    expected_enabled_features = ['test_feature_in_experiment', 'test_feature_in_rollout']
    self.assertEqual(sorted(expected_enabled_features), sorted(received_features))
    mock_is_feature_enabled.assert_any_call('test_feature_in_experiment', 'user_1', None)
    mock_is_feature_enabled.assert_any_call('test_feature_in_rollout', 'user_1', None)
    mock_is_feature_enabled.assert_any_call('test_feature_in_group', 'user_1', None)
    mock_is_feature_enabled.assert_any_call('test_feature_in_experiment_and_rollout', 'user_1', None)

  def test_get_enabled_features_invalid_user_id(self):
    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, \
            mock.patch('optimizely.helpers.validator.is_non_empty_string', return_value=False) as mock_validator:
      self.optimizely.get_enabled_features(1.2)

    mock_validator.assert_any_call(1.2)
    mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

  def test_get_enabled_features__invalid_attributes(self):
    """ Test that get_enabled_features returns empty list if attributes are in an invalid format. """
    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, \
            mock.patch('optimizely.helpers.validator.are_attributes_valid', return_value=False) as mock_validator:
      self.assertEqual([], self.optimizely.get_enabled_features('test_user', attributes='invalid'))

    mock_validator.assert_called_once_with('invalid')
    mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')

  def test_get_enabled_features__invalid_object(self):
    """ Test that get_enabled_features returns empty list if Optimizely object is not valid. """

    opt_obj = optimizely.Optimizely('invalid_file')

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
      self.assertEqual([], opt_obj.get_enabled_features('user_1'))

    mock_client_logging.error.assert_called_once_with('Datafile has invalid format. Failing "get_enabled_features".')

  def test_get_feature_variable_boolean(self):
    """ Test that get_feature_variable_boolean returns Boolean value as expected. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logging:
      self.assertTrue(opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user'))

    mock_config_logging.info.assert_called_once_with(
      'Value for variable "is_working" for variation "variation" is "true".'
    )

  def test_get_feature_variable_double(self):
    """ Test that get_feature_variable_double returns Double value as expected. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logging:
      self.assertEqual(10.02, opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'))

    mock_config_logging.info.assert_called_once_with(
      'Value for variable "cost" for variation "variation" is "10.02".'
    )

  def test_get_feature_variable_integer(self):
    """ Test that get_feature_variable_integer returns Integer value as expected. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logging:
      self.assertEqual(4243, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'))

    mock_config_logging.info.assert_called_once_with(
      'Value for variable "count" for variation "variation" is "4243".'
    )

  def test_get_feature_variable_string(self):
    """ Test that get_feature_variable_string returns String value as expected. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logging:
      self.assertEqual(
        'staging',
        opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user')
      )

    mock_config_logging.info.assert_called_once_with(
      'Value for variable "environment" for variation "variation" is "staging".'
    )

  def test_get_feature_variable__returns_default_value_if_variable_usage_not_in_variation(self):
    """ Test that get_feature_variable_* returns default value if variable usage not present in variation. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')

    # Empty variable usage map for the mocked variation
    opt_obj.config.variation_variable_usage_map['111129'] = None

    # Boolean
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logger:
      self.assertTrue(opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user'))

    mock_config_logger.info.assert_called_once_with(
      'Variable "is_working" is not used in variation "variation". Assigning default value "true".'
    )
    mock_config_logger.info.reset_mock()

    # Double
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logger:
      self.assertEqual(10.99,
                       opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'))

    mock_config_logger.info.assert_called_once_with(
      'Variable "cost" is not used in variation "variation". Assigning default value "10.99".'
    )
    mock_config_logger.info.reset_mock()

    # Integer
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logger:
      self.assertEqual(999,
                       opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'))

    mock_config_logger.info.assert_called_once_with(
      'Variable "count" is not used in variation "variation". Assigning default value "999".'
    )
    mock_config_logger.info.reset_mock()

    # String
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj.config, 'logger') as mock_config_logger:
      self.assertEqual('devel',
                       opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'))

    mock_config_logger.info.assert_called_once_with(
      'Variable "environment" is not used in variation "variation". Assigning default value "devel".'
    )
    mock_config_logger.info.reset_mock()

  def test_get_feature_variable__returns_default_value_if_no_variation(self):
    """ Test that get_feature_variable_* returns default value if no variation. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')

    # Boolean
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      self.assertTrue(opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user'))

    mock_client_logger.info.assert_called_once_with(
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "is_working" of feature flag "test_feature_in_experiment".'
    )
    mock_client_logger.info.reset_mock()

    # Double
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      self.assertEqual(10.99,
                       opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'))

    mock_client_logger.info.assert_called_once_with(
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "cost" of feature flag "test_feature_in_experiment".'
    )
    mock_client_logger.info.reset_mock()

    # Integer
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      self.assertEqual(999,
                       opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'))

    mock_client_logger.info.assert_called_once_with(
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "count" of feature flag "test_feature_in_experiment".'
    )
    mock_client_logger.info.reset_mock()

    # String
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      self.assertEqual('devel',
                       opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'))

    mock_client_logger.info.assert_called_once_with(
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "environment" of feature flag "test_feature_in_experiment".'
    )

  def test_get_feature_variable__returns_none_if_none_feature_key(self):
    """ Test that get_feature_variable_* returns None for None feature key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      # Check for booleans
      self.assertIsNone(opt_obj.get_feature_variable_boolean(None, 'variable_key', 'test_user'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for doubles
      self.assertIsNone(opt_obj.get_feature_variable_double(None, 'variable_key', 'test_user'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for integers
      self.assertIsNone(opt_obj.get_feature_variable_integer(None, 'variable_key', 'test_user'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for strings
      self.assertIsNone(opt_obj.get_feature_variable_string(None, 'variable_key', 'test_user'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

  def test_get_feature_variable__returns_none_if_none_variable_key(self):
    """ Test that get_feature_variable_* returns None for None variable key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      # Check for booleans
      self.assertIsNone(opt_obj.get_feature_variable_boolean('feature_key', None, 'test_user'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for doubles
      self.assertIsNone(opt_obj.get_feature_variable_double('feature_key', None, 'test_user'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for integers
      self.assertIsNone(opt_obj.get_feature_variable_integer('feature_key', None, 'test_user'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for strings
      self.assertIsNone(opt_obj.get_feature_variable_string('feature_key', None, 'test-User'))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      mock_client_logger.reset_mock()

  def test_get_feature_variable__returns_none_if_none_user_id(self):
    """ Test that get_feature_variable_* returns None for None user ID. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      # Check for booleans
      self.assertIsNone(opt_obj.get_feature_variable_boolean('feature_key', 'variable_key', None))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_USER_ID_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for doubles
      self.assertIsNone(opt_obj.get_feature_variable_double('feature_key', 'variable_key', None))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_USER_ID_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for integers
      self.assertIsNone(opt_obj.get_feature_variable_integer('feature_key', 'variable_key', None))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_USER_ID_PARAMETER)
      mock_client_logger.reset_mock()

      # Check for strings
      self.assertIsNone(opt_obj.get_feature_variable_string('feature_key', 'variable_key', None))
      mock_client_logger.error.assert_called_with(enums.Errors.NONE_USER_ID_PARAMETER)
      mock_client_logger.reset_mock()

  def test_get_feature_variable__invalid_attributes(self):
    """ Test that get_feature_variable_* returns None for invalid attributes. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch.object(opt_obj, 'logger') as mock_client_logging, \
            mock.patch('optimizely.helpers.validator.are_attributes_valid', return_value=False) as mock_validator:

      # get_feature_variable_boolean
      self.assertIsNone(
        opt_obj.get_feature_variable_boolean('test_feature_in_experiment',
                                             'is_working', 'test_user', attributes='invalid')
      )
      mock_validator.assert_called_once_with('invalid')
      mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
      mock_validator.reset_mock()
      mock_client_logging.reset_mock()

      # get_feature_variable_double
      self.assertIsNone(
        opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user', attributes='invalid')
      )
      mock_validator.assert_called_once_with('invalid')
      mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
      mock_validator.reset_mock()
      mock_client_logging.reset_mock()

      # get_feature_variable_integer
      self.assertIsNone(
        opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user', attributes='invalid')
      )
      mock_validator.assert_called_once_with('invalid')
      mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
      mock_validator.reset_mock()
      mock_client_logging.reset_mock()

      # get_feature_variable_string
      self.assertIsNone(
        opt_obj.get_feature_variable_string('test_feature_in_experiment',
                                            'environment', 'test_user', attributes='invalid')
      )
      mock_validator.assert_called_once_with('invalid')
      mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
      mock_validator.reset_mock()
      mock_client_logging.reset_mock()

  def test_get_feature_variable__returns_none_if_invalid_feature_key(self):
    """ Test that get_feature_variable_* returns None for invalid feature key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch.object(opt_obj.config, 'logger') as mock_config_logger:
      self.assertIsNone(opt_obj.get_feature_variable_boolean('invalid_feature', 'is_working', 'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_double('invalid_feature', 'cost', 'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_integer('invalid_feature', 'count', 'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_string('invalid_feature', 'environment', 'test_user'))

    self.assertEqual(4, mock_config_logger.error.call_count)
    mock_config_logger.error.assert_has_calls([
      mock.call('Feature "invalid_feature" is not in datafile.'),
      mock.call('Feature "invalid_feature" is not in datafile.'),
      mock.call('Feature "invalid_feature" is not in datafile.'),
      mock.call('Feature "invalid_feature" is not in datafile.')
    ])

  def test_get_feature_variable__returns_none_if_invalid_variable_key(self):
    """ Test that get_feature_variable_* returns None for invalid variable key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch.object(opt_obj.config, 'logger') as mock_config_logger:
      self.assertIsNone(opt_obj.get_feature_variable_boolean('test_feature_in_experiment',
                                                             'invalid_variable',
                                                             'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_double('test_feature_in_experiment',
                                                            'invalid_variable',
                                                            'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_integer('test_feature_in_experiment',
                                                             'invalid_variable',
                                                             'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_string('test_feature_in_experiment',
                                                            'invalid_variable',
                                                            'test_user'))
    self.assertEqual(4, mock_config_logger.error.call_count)
    mock_config_logger.error.assert_has_calls([
      mock.call('Variable with key "invalid_variable" not found in the datafile.'),
      mock.call('Variable with key "invalid_variable" not found in the datafile.'),
      mock.call('Variable with key "invalid_variable" not found in the datafile.'),
      mock.call('Variable with key "invalid_variable" not found in the datafile.')
    ])

  def test_get_feature_variable__returns_none_if_type_mismatch(self):
    """ Test that get_feature_variable_* returns None if type mismatch. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      # "is_working" is boolean variable and we are using double method on it.
      self.assertIsNone(opt_obj.get_feature_variable_double('test_feature_in_experiment', 'is_working', 'test_user'))

    mock_client_logger.warning.assert_called_with(
      'Requested variable type "double", but variable is of type "boolean". '
      'Use correct API to retrieve value. Returning None.'
    )

  def test_get_feature_variable__returns_none_if_unable_to_cast(self):
    """ Test that get_feature_variable_* returns None if unable_to_cast_value """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch('optimizely.project_config.ProjectConfig.get_typecast_value',
                    side_effect=ValueError()),\
         mock.patch.object(opt_obj, 'logger') as mock_client_logger:
      self.assertEqual(None, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'))

    mock_client_logger.error.assert_called_with('Unable to cast value. Returning None.')


class OptimizelyWithExceptionTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            error_handler=error_handler.RaiseExceptionErrorHandler)

  def test_activate__with_attributes__invalid_attributes(self):
    """ Test that activate raises exception if attributes are in invalid format. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException, enums.Errors.INVALID_ATTRIBUTE_FORMAT,
                            self.optimizely.activate, 'test_experiment', 'test_user', attributes='invalid')

  def test_track__with_attributes__invalid_attributes(self):
    """ Test that track raises exception if attributes are in invalid format. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException, enums.Errors.INVALID_ATTRIBUTE_FORMAT,
                            self.optimizely.track, 'test_event', 'test_user', attributes='invalid')

  def test_track__with_event_tag__invalid_event_tag(self):
    """ Test that track raises exception if event_tag is in invalid format. """

    self.assertRaisesRegexp(exceptions.InvalidEventTagException, enums.Errors.INVALID_EVENT_TAG_FORMAT,
                            self.optimizely.track, 'test_event', 'test_user', event_tags=4200)

  def test_get_variation__with_attributes__invalid_attributes(self):
    """ Test that get variation raises exception if attributes are in invalid format. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException, enums.Errors.INVALID_ATTRIBUTE_FORMAT,
                            self.optimizely.get_variation, 'test_experiment', 'test_user', attributes='invalid')


class OptimizelyWithLoggingTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(
      json.dumps(self.config_dict),
      logger=logger.SimpleLogger()
    )
    self.project_config = self.optimizely.config

  def test_activate(self):
    """ Test that expected log messages are logged during activate. """

    variation_key = 'variation'
    experiment_key = 'test_experiment'
    user_id = 'test_user'

    with mock.patch('optimizely.decision_service.DecisionService.get_variation',
                    return_value=self.project_config.get_variation_from_id(
                      'test_experiment', '111129')), \
         mock.patch('time.time', return_value=42), \
         mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event'), \
         mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
      self.assertEqual(variation_key, self.optimizely.activate(experiment_key, user_id))

    mock_client_logging.info.assert_called_once_with(
      'Activating user "test_user" in experiment "test_experiment".'
    )
    debug_message = mock_client_logging.debug.call_args_list[0][0][0]
    self.assertRegexpMatches(
      debug_message,
      'Dispatching impression event to URL https://logx.optimizely.com/v1/events with params'
    )

  def test_track(self):
    """ Test that expected log messages are logged during track. """

    user_id = 'test_user'
    event_key = 'test_event'
    mock_client_logger = mock.patch.object(self.optimizely, 'logger')
    mock_config_logger = mock.patch.object(self.optimizely.config, 'logger')
    mock_decision_logger = mock.patch.object(self.optimizely.decision_service, 'logger')
    with mock.patch('optimizely.helpers.audience.is_user_in_experiment',
                    return_value=False), \
         mock.patch('time.time', return_value=42), \
         mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event'), \
         mock_decision_logger as mock_decision_logging, \
         mock_config_logger as mock_config_logging, \
         mock_client_logger as mock_client_logging:
      self.optimizely.track(event_key, user_id)

    mock_config_logging.debug.assert_called_once_with(
      'User "test_user" is not in the forced variation map.'
    )
    mock_decision_logging.info.assert_called_once_with(
      'User "test_user" does not meet conditions to be in experiment "test_experiment".'
    )
    mock_client_logging.info.assert_has_calls([
      mock.call('Not tracking user "test_user" for experiment "test_experiment".'),
      mock.call('There are no valid experiments for event "test_event" to track.')
    ])

  def test_activate__experiment_not_running(self):
    """ Test that expected log messages are logged during activate when experiment is not running. """

    mock_client_logger = mock.patch.object(self.optimizely, 'logger')
    mock_decision_logger = mock.patch.object(self.optimizely.decision_service, 'logger')
    with mock_client_logger as mock_client_logging, \
        mock_decision_logger as mock_decision_logging, \
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'})

    mock_decision_logging.info.assert_called_once_with('Experiment "test_experiment" is not running.')
    mock_client_logging.info.assert_called_once_with('Not activating user "test_user".')
    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))

  def test_activate__no_audience_match(self):
    """ Test that expected log messages are logged during activate when audience conditions are not met. """

    mock_client_logger = mock.patch.object(self.optimizely, 'logger')
    mock_config_logger = mock.patch.object(self.optimizely.config, 'logger')
    mock_decision_logger = mock.patch.object(self.optimizely.decision_service, 'logger')

    with mock_decision_logger as mock_decision_logging, \
         mock_config_logger as mock_config_logging, \
         mock_client_logger as mock_client_logging:
      self.optimizely.activate(
        'test_experiment',
        'test_user',
        attributes={'test_attribute': 'wrong_test_value'}
      )

    mock_config_logging.debug.assert_called_once_with(
      'User "test_user" is not in the forced variation map.'
    )
    mock_decision_logging.info.assert_called_once_with(
      'User "test_user" does not meet conditions to be in experiment "test_experiment".'
    )
    mock_client_logging.info.assert_called_once_with('Not activating user "test_user".')

  def test_activate__dispatch_raises_exception(self):
    """ Test that activate logs dispatch failure gracefully. """

    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, \
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event',
                   side_effect=Exception('Failed to send')):
      self.assertEqual('control', self.optimizely.activate('test_experiment', 'user_1'))

    mock_client_logging.exception.assert_called_once_with('Unable to dispatch impression event!')

  def test_track__invalid_attributes(self):
    """ Test that expected log messages are logged during track when attributes are in invalid format. """

    mock_logger = mock.patch.object(self.optimizely, 'logger')
    with mock_logger as mock_logging:
      self.optimizely.track('test_event', 'test_user', attributes='invalid')

    mock_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')

  def test_track__invalid_event_tag(self):
    """ Test that expected log messages are logged during track when event_tag is in invalid format. """

    mock_client_logger = mock.patch.object(self.optimizely, 'logger')
    with mock_client_logger as mock_client_logging:
      self.optimizely.track('test_event', 'test_user', event_tags='4200')
      mock_client_logging.error.assert_called_once_with(
        'Provided event tags are in an invalid format.'
      )

    with mock_client_logger as mock_client_logging:
      self.optimizely.track('test_event', 'test_user', event_tags=4200)
      mock_client_logging.error.assert_called_once_with(
        'Provided event tags are in an invalid format.'
      )

  def test_track__dispatch_raises_exception(self):
    """ Test that track logs dispatch failure gracefully. """
    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, \
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event',
                   side_effect=Exception('Failed to send')):
      self.optimizely.track('test_event', 'user_1')

    mock_client_logging.exception.assert_called_once_with('Unable to dispatch conversion event!')

  def test_get_variation__invalid_attributes(self):
    """ Test that expected log messages are logged during get variation when attributes are in invalid format. """
    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
      self.optimizely.get_variation('test_experiment', 'test_user', attributes='invalid')

    mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')

  def test_get_variation__invalid_experiment_key(self):
    """ Test that None is returned and expected log messages are logged during get_variation \
    when exp_key is in invalid format. """

    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging,\
         mock.patch('optimizely.helpers.validator.is_non_empty_string', return_value=False) as mock_validator:
      self.assertIsNone(self.optimizely.get_variation(99, 'test_user'))

    mock_validator.assert_any_call(99)
    mock_client_logging.error.assert_called_once_with('Provided "experiment_key" is in an invalid format.')

  def test_get_variation__invalid_user_id(self):
    """ Test that None is returned and expected log messages are logged during get_variation \
    when user_id is in invalid format. """

    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging,\
         mock.patch('optimizely.helpers.validator.is_non_empty_string', side_effect=[True, False]) as mock_validator:
      self.assertIsNone(self.optimizely.get_variation('test_experiment', 99))

    mock_validator.assert_any_call(99)
    mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

  def test_activate__invalid_experiment_key(self):
    """ Test that None is returned and expected log messages are logged during activate \
    when exp_key is in invalid format. """

    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging,\
         mock.patch('optimizely.helpers.validator.is_non_empty_string', return_value=False) as mock_validator:
      self.assertIsNone(self.optimizely.activate(99, 'test_user'))

    mock_validator.assert_any_call(99)

    mock_client_logging.error.assert_called_once_with('Provided "experiment_key" is in an invalid format.')

  def test_activate__invalid_user_id(self):
    """ Test that None is returned and expected log messages are logged during activate \
    when user_id is in invalid format. """

    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging,\
         mock.patch('optimizely.helpers.validator.is_non_empty_string', side_effect=[True, False]) as mock_validator:
      self.assertIsNone(self.optimizely.activate('test_experiment', 99))

    mock_validator.assert_any_call(99)

    mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

  def test_activate__invalid_attributes(self):
    """ Test that expected log messages are logged during activate when attributes are in invalid format. """
    with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
      self.optimizely.activate('test_experiment', 'test_user', attributes='invalid')

    mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
    mock_client_logging.info.assert_called_once_with('Not activating user "test_user".')

  def test_get_variation__experiment_not_running(self):
    """ Test that expected log messages are logged during get variation when experiment is not running. """

    with mock.patch.object(self.optimizely.decision_service, 'logger') as mock_decision_logging, \
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.optimizely.get_variation('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'})

    mock_decision_logging.info.assert_called_once_with('Experiment "test_experiment" is not running.')
    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))

  def test_get_variation__no_audience_match(self):
    """ Test that expected log messages are logged during get variation when audience conditions are not met. """

    experiment_key = 'test_experiment'
    user_id = 'test_user'

    mock_config_logger = mock.patch.object(self.optimizely.config, 'logger')
    mock_decision_logger = mock.patch.object(self.optimizely.decision_service, 'logger')
    with mock_decision_logger as mock_decision_logging, \
           mock_config_logger as mock_config_logging:
      self.optimizely.get_variation(
        experiment_key,
        user_id,
        attributes={'test_attribute': 'wrong_test_value'}
      )

    mock_config_logging.debug.assert_called_once_with(
      'User "test_user" is not in the forced variation map.'
    )
    mock_decision_logging.info.assert_called_once_with(
      'User "test_user" does not meet conditions to be in experiment "test_experiment".'
    )

  def test_get_variation__forced_bucketing(self):
    """ Test that the expected forced variation is called for a valid experiment and attributes """

    self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
    self.assertEqual('variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'))
    variation_key = self.optimizely.get_variation('test_experiment',
                                                  'test_user',
                                                  attributes={'test_attribute': 'test_value'})
    self.assertEqual('variation', variation_key)

  def test_get_variation__experiment_not_running__forced_bucketing(self):
    """ Test that the expected forced variation is called if an experiment is not running """

    with mock.patch('optimizely.helpers.experiment.is_experiment_running',
                    return_value=False) as mock_is_experiment_running:
      self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation')
      self.assertEqual('variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'))
      variation_key = self.optimizely.get_variation('test_experiment',
                                                    'test_user',
                                                    attributes={'test_attribute': 'test_value'})
      self.assertIsNone(variation_key)
      mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))

  def test_get_variation__whitelisted_user_forced_bucketing(self):
    """ Test that the expected forced variation is called if a user is whitelisted """

    self.assertTrue(self.optimizely.set_forced_variation('group_exp_1', 'user_1', 'group_exp_1_variation'))
    forced_variation = self.optimizely.get_forced_variation('group_exp_1', 'user_1')
    self.assertEqual('group_exp_1_variation', forced_variation)
    variation_key = self.optimizely.get_variation('group_exp_1',
                                                  'user_1',
                                                  attributes={'test_attribute': 'test_value'})
    self.assertEqual('group_exp_1_variation', variation_key)

  def test_get_variation__user_profile__forced_bucketing(self):
    """ Test that the expected forced variation is called if a user profile exists """
    with mock.patch('optimizely.decision_service.DecisionService.get_stored_variation',
                    return_value=entities.Variation('111128', 'control')) as mock_get_stored_variation:
      self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
      self.assertEqual('variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'))
      variation_key = self.optimizely.get_variation('test_experiment',
                                                    'test_user',
                                                    attributes={'test_attribute': 'test_value'})
      self.assertEqual('variation', variation_key)

  def test_get_variation__invalid_attributes__forced_bucketing(self):
    """ Test that the expected forced variation is called if the user does not pass audience evaluation """

    self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
    self.assertEqual('variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'))
    variation_key = self.optimizely.get_variation('test_experiment',
                                                  'test_user',
                                                  attributes={'test_attribute': 'test_value_invalid'})
    self.assertEqual('variation', variation_key)
