# Copyright 2016-2018, Optimizely
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

from optimizely import decision_service
from optimizely import entities
from optimizely import error_handler
from optimizely import event_builder
from optimizely import exceptions
from optimizely import logger
from optimizely import optimizely
from optimizely import project_config
from optimizely import version
from optimizely.logger import SimpleLogger
from optimizely.notification_center import NotificationCenter
from optimizely.helpers import enums
from . import base


class OptimizelyTest(base.BaseTest):

  strTest = None

  try:
    isinstance("test", basestring)  # attempt to evaluate basestring

    _expected_notification_failure = \
      'Problem calling notify callback. Error: on_custom_event() takes exactly 1 argument (4 given)'

    def isstr(self, s):
      return isinstance(s, basestring)

    strTest = isstr

  except NameError:
    _expected_notification_failure = \
      'Problem calling notify callback. Error: on_custom_event() takes 1 positional argument but 4 were given'

    def isstr(self, s):
      return isinstance(s, str)
    strTest = isstr

  def _validate_event_object(self, event_obj, expected_url, expected_params, expected_verb, expected_headers):
    """ Helper method to validate properties of the event object. """

    self.assertEqual(expected_url, event_obj.url)
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

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      opt_obj = optimizely.Optimizely('invalid_datafile')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided "datafile" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__invalid_event_dispatcher__logs_error(self):
    """ Test that invalid event_dispatcher logs error on init. """

    class InvalidDispatcher(object):
      pass

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), event_dispatcher=InvalidDispatcher)

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided "event_dispatcher" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__invalid_logger__logs_error(self):
    """ Test that invalid logger logs error on init. """

    class InvalidLogger(object):
      pass

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), logger=InvalidLogger)

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided "logger" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__invalid_error_handler__logs_error(self):
    """ Test that invalid error_handler logs error on init. """

    class InvalidErrorHandler(object):
      pass

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), error_handler=InvalidErrorHandler)

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided "error_handler" is in an invalid format.')
    self.assertFalse(opt_obj.is_valid)

  def test_init__v1_datafile__logs_error(self):
    """ Test that v1 datafile logs error on init. """

    self.config_dict['version'] = project_config.V1_CONFIG_VERSION
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      opt_obj = optimizely.Optimizely(json.dumps(self.config_dict))

    mock_logging.assert_called_once_with(
      enums.LogLevels.ERROR,
      'Provided datafile has unsupported version. Please use SDK version 1.1.0 or earlier for datafile version 1.'
    )
    self.assertFalse(opt_obj.is_valid)

  def test_skip_json_validation_true(self):
    """ Test that on setting skip_json_validation to true, JSON schema validation is not performed. """

    with mock.patch('optimizely.helpers.validator.is_datafile_valid') as mock_datafile_validation:
      optimizely.Optimizely(json.dumps(self.config_dict), skip_json_validation=True)

    self.assertEqual(0, mock_datafile_validation.call_count)

  def test_invalid_json_raises_schema_validation_off(self):
    """ Test that invalid JSON logs error if schema validation is turned off. """

    # Not  JSON
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      optimizely.Optimizely('invalid_json', skip_json_validation=True)

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided "datafile" is in an invalid format.')

    # JSON having valid version, but entities have invalid format
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      optimizely.Optimizely({'version': '2', 'events': 'invalid_value', 'experiments': 'invalid_value'},
                            skip_json_validation=True)

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided "datafile" is in an invalid format.')

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
      'anonymize_ip': False
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

    notification_id = self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE,
                                                                           on_activate)
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

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      notification_center = NotificationCenter(SimpleLogger())
      notification_center.add_notification_listener(custom_type, on_custom_event)
      notification_center.send_notifications(custom_type, 1, 2, "5", 6)

    #self.assertTrue(custom_called[0])
    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, self._expected_notification_failure)

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
         mock.patch(
           'optimizely.notification_center.NotificationCenter.send_notifications') \
        as mock_broadcast_activate:
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
         mock.patch(
           'optimizely.notification_center.NotificationCenter.send_notifications') \
        as mock_broadcast_activate:
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
        mock.patch(
          'optimizely.notification_center.NotificationCenter.send_notifications') as mock_event_tracked:
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
        mock.patch(
          'optimizely.notification_center.NotificationCenter.send_notifications') as mock_event_tracked:
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
        mock.patch(
          'optimizely.notification_center.NotificationCenter.send_notifications') as mock_event_tracked:
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
      'anonymize_ip': False
    }
    mock_get_variation.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'),
                                               'test_user', {'test_attribute': 'test_value'})
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
      'anonymize_ip': False
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
      'anonymize_ip': False
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

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(opt_obj.activate('test_experiment', 'test_user'))

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Datafile has invalid format. Failing "activate".')

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
      'anonymize_ip': False
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
      'anonymize_ip': False
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
      'anonymize_ip': False
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
      'anonymize_ip': False
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
      'anonymize_ip': False
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
      'anonymize_ip': False
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

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      opt_obj.track('test_event', 'test_user')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Datafile has invalid format. Failing "track".')

  def test_get_variation__invalid_object(self):
    """ Test that get_variation logs error if Optimizely object is not created correctly. """

    opt_obj = optimizely.Optimizely('invalid_datafile')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertIsNone(opt_obj.get_variation('test_experiment', 'test_user'))

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Datafile has invalid format. Failing "get_variation".')

  def test_is_feature_enabled__returns_false_for_none_feature_key(self):
    """ Test that is_feature_enabled returns false if the provided feature key is None. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertFalse(opt_obj.is_feature_enabled(None, 'test_user'))

    mock_logger.assert_called_once_with(enums.LogLevels.ERROR, enums.Errors.NONE_FEATURE_KEY_PARAMETER)

  def test_is_feature_enabled__returns_false_for_none_user_id(self):
    """ Test that is_feature_enabled returns false if the provided user ID is None. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertFalse(opt_obj.is_feature_enabled('feature_key', None))

    mock_logger.assert_called_once_with(enums.LogLevels.ERROR, enums.Errors.NONE_USER_ID_PARAMETER)

  def test_is_feature_enabled__returns_false_for_invalid_feature(self):
    """ Test that the feature is not enabled for the user if the provided feature key is invalid. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature') as mock_decision, \
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertFalse(opt_obj.is_feature_enabled('invalid_feature', 'user1'))

    self.assertFalse(mock_decision.called)

    # Check that no event is sent
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_is_feature_enabled__returns_true_for_feature_experiment_if_property_featureEnabled_is_true(self):
    """ Test that the feature is enabled for the user if bucketed into variation of an experiment and
    the variation's featureEnabled property is True.
    Also confirm that impression event is dispatched. """

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
    }
    # Check that impression event is sent
    self.assertEqual(1, mock_dispatch_event.call_count)
    self._validate_event_object(mock_dispatch_event.call_args[0][0],
                                'https://logx.optimizely.com/v1/events',
                                expected_params, 'POST', {'Content-Type': 'application/json'})

  def test_is_feature_enabled__returns_false_for_feature_experiment_if_property_featureEnabled_is_false(self):
    """ Test that the feature is disabled for the user if bucketed into variation of an experiment and
    the variation's featureEnabled property is False.
    Also confirm that impression event is not dispatched. """

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

    # Check that impression event is not sent
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_is_feature_enabled__returns_true_for_feature_rollout_if_property_featureEnabled_is_true(self):
    """ Test that the feature is enabled for the user if bucketed into variation of a rollout and
    the variation's featureEnabled property is True.
    Also confirm that no impression event is dispatched. """

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

  def test_is_feature_enabled__returns_false_for_feature_rollout_if_property_featureEnabled_is_false(self):
    """ Test that the feature is disabled for the user if bucketed into variation of a rollout and
    the variation's featureEnabled property is False.
    Also confirm that no impression event is dispatched. """

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

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging, \
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'user_1'))

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR,
                                         'Datafile has invalid format. Failing "is_feature_enabled".')

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

  def test_get_enabled_features_returns_a_sorted_list(self):
    """ Test that get_enabled_features returns a sorted list of enabled feature keys. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

    with mock.patch('optimizely.optimizely.Optimizely.is_feature_enabled',
                    return_value=True) as mock_is_feature_enabled:
      received_features = opt_obj.get_enabled_features('user_1')

    mock_is_feature_enabled.assert_any_call('test_feature_in_experiment', 'user_1', None)
    mock_is_feature_enabled.assert_any_call('test_feature_in_rollout', 'user_1', None)
    mock_is_feature_enabled.assert_any_call('test_feature_in_group', 'user_1', None)
    mock_is_feature_enabled.assert_any_call('test_feature_in_experiment_and_rollout', 'user_1', None)

    expected_sorted_features = [
      'test_feature_in_experiment',
      'test_feature_in_experiment_and_rollout',
      'test_feature_in_group',
      'test_feature_in_rollout'
      ]

    self.assertEqual(expected_sorted_features, received_features)

  def test_get_enabled_features__invalid_object(self):
    """ Test that get_enabled_features returns empty list if Optimizely object is not valid. """

    opt_obj = optimizely.Optimizely('invalid_file')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual([], opt_obj.get_enabled_features('user_1'))

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR,
                                         'Datafile has invalid format. Failing "get_enabled_features".')

  def test_get_feature_variable_boolean(self):
    """ Test that get_feature_variable_boolean returns Boolean value as expected. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertTrue(opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'Value for variable "is_working" of feature flag "test_feature_in_experiment" is true for user "test_user".'
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
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertEqual(10.02, opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'Value for variable "cost" of feature flag "test_feature_in_experiment" is 10.02 for user "test_user".'
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
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertEqual(4243, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'Value for variable "count" of feature flag "test_feature_in_experiment" is 4243 for user "test_user".'
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
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertEqual('staging',
                       opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'Value for variable "environment" of feature flag "test_feature_in_experiment" is staging for user "test_user".'
    )

  def test_get_feature_variable__returns_default_value(self):
    """ Test that get_feature_variable_* returns default value if no variation. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')

    # Boolean
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertTrue(opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "is_working" of feature flag "test_feature_in_experiment".'
    )

    # Double
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertEqual(10.99,
                       opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "cost" of feature flag "test_feature_in_experiment".'
    )

    # Integer
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertEqual(999,
                       opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "count" of feature flag "test_feature_in_experiment".'
    )

    # String
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment, None,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertEqual('devel',
                       opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'))

    mock_logger.assert_called_once_with(
      enums.LogLevels.INFO,
      'User "test_user" is not in any variation or rollout rule. '
      'Returning default value for variable "environment" of feature flag "test_feature_in_experiment".'
    )

  def test_get_feature_variable__returns_none_if_none_feature_key(self):
    """ Test that get_feature_variable_* returns None for None feature key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertIsNone(opt_obj.get_feature_variable_boolean(None, 'variable_key', 'test_user'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_double(None, 'variable_key', 'test_user'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_integer(None, 'variable_key', 'test_user'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_FEATURE_KEY_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_string(None, 'variable_key', 'test_user'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_FEATURE_KEY_PARAMETER)

    self.assertEqual(4, mock_logger.call_count)

  def test_get_feature_variable__returns_none_if_none_variable_key(self):
    """ Test that get_feature_variable_* returns None for None variable key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertIsNone(opt_obj.get_feature_variable_boolean('feature_key', None, 'test_user'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_double('feature_key', None, 'test_user'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_integer('feature_key', None, 'test_user'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_VARIABLE_KEY_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_string('feature_key', None, 'test-User'))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_VARIABLE_KEY_PARAMETER)

    self.assertEqual(4, mock_logger.call_count)

  def test_get_feature_variable__returns_none_if_none_user_id(self):
    """ Test that get_feature_variable_* returns None for None user ID. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertIsNone(opt_obj.get_feature_variable_boolean('feature_key', 'variable_key', None))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_USER_ID_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_double('feature_key', 'variable_key', None))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_USER_ID_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_integer('feature_key', 'variable_key', None))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_USER_ID_PARAMETER)
      self.assertIsNone(opt_obj.get_feature_variable_string('feature_key', 'variable_key', None))
      mock_logger.assert_called_with(enums.LogLevels.ERROR, enums.Errors.NONE_USER_ID_PARAMETER)

    self.assertEqual(4, mock_logger.call_count)

  def test_get_feature_variable__returns_none_if_invalid_feature_key(self):
    """ Test that get_feature_variable_* returns None for invalid feature key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      self.assertIsNone(opt_obj.get_feature_variable_boolean('invalid_feature', 'is_working', 'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_double('invalid_feature', 'cost', 'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_integer('invalid_feature', 'count', 'test_user'))
      self.assertIsNone(opt_obj.get_feature_variable_string('invalid_feature', 'environment', 'test_user'))

    self.assertEqual(4, mock_logger.call_count)
    mock_logger.assert_called_with(40, 'Feature "invalid_feature" is not in datafile.')

  def test_get_feature_variable__returns_none_if_invalid_variable_key(self):
    """ Test that get_feature_variable_* returns None for invalid variable key. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    with mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
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

    self.assertEqual(4, mock_logger.call_count)
    mock_logger.assert_called_with(40, 'Variable with key "invalid_variable" not found in the datafile.')

  def test_get_feature_variable__returns_none_if_type_mismatch(self):
    """ Test that get_feature_variable_* returns None if type mismatch. """

    opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
    mock_experiment = opt_obj.config.get_experiment_from_key('test_experiment')
    mock_variation = opt_obj.config.get_variation_from_id('test_experiment', '111129')
    with mock.patch('optimizely.decision_service.DecisionService.get_variation_for_feature',
                    return_value=decision_service.Decision(mock_experiment,
                                                           mock_variation,
                                                           decision_service.DECISION_SOURCE_EXPERIMENT)), \
         mock.patch('optimizely.logger.NoOpLogger.log') as mock_logger:
      # "is_working" is boolean variable and we are using double method on it.
      self.assertIsNone(opt_obj.get_feature_variable_double('test_feature_in_experiment', 'is_working', 'test_user'))

    mock_logger.assert_called_with(
      enums.LogLevels.WARNING,
      'Requested variable type "double", but variable is of type "boolean". '
      'Use correct API to retrieve value. Returning None.'
    )


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
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict), logger=logger.SimpleLogger())
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
         mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual(variation_key, self.optimizely.activate(experiment_key, user_id))

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'Activating user "%s" in experiment "%s".'
                               % (user_id, experiment_key)),
                     mock_logging.call_args_list[0])
    (debug_level, debug_message) = mock_logging.call_args_list[1][0]
    self.assertEqual(enums.LogLevels.DEBUG, debug_level)
    self.assertRegexpMatches(debug_message,
                             'Dispatching impression event to URL https://logx.optimizely.com/v1/events with params')

  def test_track(self):
    """ Test that expected log messages are logged during track. """

    user_id = 'test_user'
    event_key = 'test_event'
    experiment_key = 'test_experiment'

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment',
                    return_value=False), \
         mock.patch('time.time', return_value=42), \
         mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event'), \
         mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.track(event_key, user_id)

    self.assertEqual(4, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG,
                               'User "%s" is not in the forced variation map.' % user_id),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO,
                               'User "%s" does not meet conditions to be in experiment "%s".'
                               % (user_id, experiment_key)),
                     mock_logging.call_args_list[1])
    self.assertEqual(mock.call(enums.LogLevels.INFO,
                               'Not tracking user "%s" for experiment "%s".' % (user_id, experiment_key)),
                     mock_logging.call_args_list[2])
    self.assertEqual(mock.call(enums.LogLevels.INFO,
                               'There are no valid experiments for event "%s" to track.' % event_key),
                     mock_logging.call_args_list[3])

  def test_activate__experiment_not_running(self):
    """ Test that expected log messages are logged during activate when experiment is not running. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging, \
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'})

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock_logging.call_args_list[0],
                     mock.call(enums.LogLevels.INFO, 'Experiment "test_experiment" is not running.'))
    self.assertEqual(mock_logging.call_args_list[1],
                     mock.call(enums.LogLevels.INFO, 'Not activating user "test_user".'))
    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))

  def test_activate__no_audience_match(self):
    """ Test that expected log messages are logged during activate when audience conditions are not met. """

    experiment_key = 'test_experiment'
    user_id = 'test_user'

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'wrong_test_value'})

    self.assertEqual(3, mock_logging.call_count)

    self.assertEqual(mock_logging.call_args_list[0],
                     mock.call(enums.LogLevels.DEBUG,
                               'User "%s" is not in the forced variation map.' % user_id))
    self.assertEqual(mock_logging.call_args_list[1],
                     mock.call(enums.LogLevels.INFO,
                               'User "%s" does not meet conditions to be in experiment "%s".'
                               % (user_id, experiment_key)))
    self.assertEqual(mock_logging.call_args_list[2],
                     mock.call(enums.LogLevels.INFO, 'Not activating user "%s".' % user_id))

  def test_activate__dispatch_raises_exception(self):
    """ Test that activate logs dispatch failure gracefully. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging, \
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event',
                   side_effect=Exception('Failed to send')):
      self.assertEqual('control', self.optimizely.activate('test_experiment', 'user_1'))

    mock_logging.assert_any_call(enums.LogLevels.ERROR, 'Unable to dispatch impression event. Error: Failed to send')

  def test_track__invalid_attributes(self):
    """ Test that expected log messages are logged during track when attributes are in invalid format. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.track('test_event', 'test_user', attributes='invalid')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')

  def test_track__invalid_event_tag(self):
    """ Test that expected log messages are logged during track when event_tag is in invalid format. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.track('test_event', 'test_user', event_tags='4200')
      mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided event tags are in an invalid format.')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.track('test_event', 'test_user', event_tags=4200)
      mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided event tags are in an invalid format.')

  def test_track__dispatch_raises_exception(self):
    """ Test that track logs dispatch failure gracefully. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging, \
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event',
                   side_effect=Exception('Failed to send')):
      self.optimizely.track('test_event', 'user_1')

    mock_logging.assert_any_call(enums.LogLevels.ERROR, 'Unable to dispatch conversion event. Error: Failed to send')

  def test_get_variation__invalid_attributes(self):
    """ Test that expected log messages are logged during get variation when attributes are in invalid format. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.get_variation('test_experiment', 'test_user', attributes='invalid')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')

  def test_activate__invalid_attributes(self):
    """ Test that expected log messages are logged during activate when attributes are in invalid format. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.activate('test_experiment', 'test_user', attributes='invalid')

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.'),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'Not activating user "test_user".'),
                     mock_logging.call_args_list[1])

  def test_get_variation__experiment_not_running(self):
    """ Test that expected log messages are logged during get variation when experiment is not running. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging, \
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.optimizely.get_variation('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'})

    mock_logging.assert_called_once_with(enums.LogLevels.INFO, 'Experiment "test_experiment" is not running.')
    mock_is_experiment_running.assert_called_once_with(self.project_config.get_experiment_from_key('test_experiment'))

  def test_get_variation__no_audience_match(self):
    """ Test that expected log messages are logged during get variation when audience conditions are not met. """

    experiment_key = 'test_experiment'
    user_id = 'test_user'

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.get_variation(experiment_key,
                                    user_id,
                                    attributes={'test_attribute': 'wrong_test_value'})

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.DEBUG, 'User "%s" is not in the forced variation map.' % user_id), \
                     mock_logging.call_args_list[0])

    self.assertEqual(mock.call(enums.LogLevels.INFO, 'User "%s" does not meet conditions to be in experiment "%s".'
                               % (user_id, experiment_key)),
                     mock_logging.call_args_list[1])

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
