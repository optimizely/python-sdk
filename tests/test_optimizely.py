# Copyright 2016-2020, Optimizely
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

from optimizely import config_manager
from optimizely import decision_service
from optimizely import entities
from optimizely import error_handler
from optimizely import event_builder
from optimizely import exceptions
from optimizely import logger
from optimizely import optimizely
from optimizely import optimizely_config
from optimizely import project_config
from optimizely import version
from optimizely.event.event_factory import EventFactory
from optimizely.helpers import enums
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

        self.assertEqual(expected_url, event_obj.get('url'))

        event_params = event_obj.get('params')

        expected_params['visitors'][0]['attributes'] = sorted(
            expected_params['visitors'][0]['attributes'], key=itemgetter('key')
        )
        event_params['visitors'][0]['attributes'] = sorted(
            event_params['visitors'][0]['attributes'], key=itemgetter('key')
        )
        self.assertEqual(expected_params, event_params)
        self.assertEqual(expected_verb, event_obj.get('http_verb'))
        self.assertEqual(expected_headers, event_obj.get('headers'))

    def _validate_event_object_event_tags(
        self, event_obj, expected_event_metric_params, expected_event_features_params
    ):
        """ Helper method to validate properties of the event object related to event tags. """

        event_params = event_obj.get('params')

        # get event metrics from the created event object
        event_metrics = event_params['visitors'][0]['snapshots'][0]['events'][0]['tags']
        self.assertEqual(expected_event_metric_params, event_metrics)

        # get event features from the created event object
        event_features = event_params['visitors'][0]['attributes'][0]
        self.assertEqual(expected_event_features_params, event_features)

    def test_init__invalid_datafile__logs_error(self):
        """ Test that invalid datafile logs error on init. """

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely('invalid_datafile')

        mock_client_logger.error.assert_called_once_with('Provided "datafile" is in an invalid format.')
        self.assertIsNone(opt_obj.config_manager.get_config())

    def test_init__null_datafile__logs_error(self):
        """ Test that null datafile logs error on init. """

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely(None)

        mock_client_logger.error.assert_called_once_with('Provided "datafile" is in an invalid format.')
        self.assertIsNone(opt_obj.config_manager.get_config())

    def test_init__empty_datafile__logs_error(self):
        """ Test that empty datafile logs error on init. """

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely("")

        mock_client_logger.error.assert_called_once_with('Provided "datafile" is in an invalid format.')
        self.assertIsNone(opt_obj.config_manager.get_config())

    def test_init__invalid_config_manager__logs_error(self):
        """ Test that invalid config_manager logs error on init. """

        class InvalidConfigManager(object):
            pass

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        mock_client_logger.exception.assert_called_once_with('Provided "config_manager" is in an invalid format.')
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

    def test_init__invalid_event_processor__logs_error(self):
        """ Test that invalid event_processor logs error on init. """

        class InvalidProcessor(object):
            pass

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), event_processor=InvalidProcessor)

        mock_client_logger.exception.assert_called_once_with('Provided "event_processor" is in an invalid format.')
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

    def test_init__invalid_notification_center__logs_error(self):
        """ Test that invalid notification_center logs error on init. """

        class InvalidNotificationCenter(object):
            pass

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely(
                json.dumps(self.config_dict), notification_center=InvalidNotificationCenter(),
            )

        mock_client_logger.exception.assert_called_once_with('Provided "notification_center" is in an invalid format.')
        self.assertFalse(opt_obj.is_valid)

    def test_init__unsupported_datafile_version__logs_error(self):
        """ Test that datafile with unsupported version logs error on init. """

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger), mock.patch(
            'optimizely.error_handler.NoOpErrorHandler.handle_error'
        ) as mock_error_handler:
            opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_unsupported_version))

        mock_client_logger.error.assert_called_once_with(
            'This version of the Python SDK does not support the given datafile version: "5".'
        )

        args, kwargs = mock_error_handler.call_args
        self.assertIsInstance(args[0], exceptions.UnsupportedDatafileVersionException)
        self.assertEqual(
            args[0].args[0], 'This version of the Python SDK does not support the given datafile version: "5".',
        )
        self.assertIsNone(opt_obj.config_manager.get_config())

    def test_init_with_supported_datafile_version(self):
        """ Test that datafile with supported version works as expected. """

        self.assertTrue(self.config_dict['version'] in project_config.SUPPORTED_VERSIONS)

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely(json.dumps(self.config_dict))

        mock_client_logger.exception.assert_not_called()
        self.assertTrue(opt_obj.is_valid)

    def test_init__datafile_only(self):
        """ Test that if only datafile is provided then StaticConfigManager is used. """

        opt_obj = optimizely.Optimizely(datafile=json.dumps(self.config_dict))
        self.assertIs(type(opt_obj.config_manager), config_manager.StaticConfigManager)

    def test_init__sdk_key_only(self):
        """ Test that if only sdk_key is provided then PollingConfigManager is used. """

        with mock.patch('optimizely.config_manager.PollingConfigManager._set_config'), mock.patch(
            'threading.Thread.start'
        ):
            opt_obj = optimizely.Optimizely(sdk_key='test_sdk_key')

        self.assertIs(type(opt_obj.config_manager), config_manager.PollingConfigManager)

    def test_init__sdk_key_and_datafile(self):
        """ Test that if both sdk_key and datafile is provided then PollingConfigManager is used. """

        with mock.patch('optimizely.config_manager.PollingConfigManager._set_config'), mock.patch(
            'threading.Thread.start'
        ):
            opt_obj = optimizely.Optimizely(datafile=json.dumps(self.config_dict), sdk_key='test_sdk_key')

        self.assertIs(type(opt_obj.config_manager), config_manager.PollingConfigManager)

    def test_init__sdk_key_and_datafile_access_token(self):
        """
            Test that if both sdk_key and datafile_access_token is provided then AuthDatafilePollingConfigManager
            is used.
        """

        with mock.patch('optimizely.config_manager.AuthDatafilePollingConfigManager._set_config'), mock.patch(
            'threading.Thread.start'
        ):
            opt_obj = optimizely.Optimizely(datafile_access_token='test_datafile_access_token', sdk_key='test_sdk_key')

        self.assertIs(type(opt_obj.config_manager), config_manager.AuthDatafilePollingConfigManager)

    def test_invalid_json_raises_schema_validation_off(self):
        """ Test that invalid JSON logs error if schema validation is turned off. """

        # Not  JSON
        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger), mock.patch(
            'optimizely.error_handler.NoOpErrorHandler.handle_error'
        ) as mock_error_handler:
            opt_obj = optimizely.Optimizely('invalid_json', skip_json_validation=True)

        mock_client_logger.error.assert_called_once_with('Provided "datafile" is in an invalid format.')
        args, kwargs = mock_error_handler.call_args
        self.assertIsInstance(args[0], exceptions.InvalidInputException)
        self.assertEqual(args[0].args[0], 'Provided "datafile" is in an invalid format.')
        self.assertIsNone(opt_obj.config_manager.get_config())

        mock_client_logger.reset_mock()
        mock_error_handler.reset_mock()

        # JSON having valid version, but entities have invalid format
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger), mock.patch(
            'optimizely.error_handler.NoOpErrorHandler.handle_error'
        ) as mock_error_handler:
            opt_obj = optimizely.Optimizely(
                {'version': '2', 'events': 'invalid_value', 'experiments': 'invalid_value'}, skip_json_validation=True,
            )

        mock_client_logger.error.assert_called_once_with('Provided "datafile" is in an invalid format.')
        args, kwargs = mock_error_handler.call_args
        self.assertIsInstance(args[0], exceptions.InvalidInputException)
        self.assertEqual(args[0].args[0], 'Provided "datafile" is in an invalid format.')
        self.assertIsNone(opt_obj.config_manager.get_config())

    def test_activate(self):
        """ Test that activate calls process with right params and returns expected variation. """

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ) as mock_decision, mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        mock_decision.assert_called_once_with(
            self.project_config, self.project_config.get_experiment_from_key('test_experiment'), 'test_user', None,
        )
        self.assertEqual(1, mock_process.call_count)

        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_add_activate_remove_clear_listener(self):
        callbackhit = [False]
        """ Test adding a listener activate passes correctly and gets called"""

        def on_activate(experiment, user_id, attributes, variation, event):
            self.assertTrue(isinstance(experiment, entities.Experiment))
            self.assertTrue(self.strTest(user_id))
            if attributes is not None:
                self.assertTrue(isinstance(attributes, dict))
            self.assertTrue(isinstance(variation, entities.Variation))
            # self.assertTrue(isinstance(event, event_builder.Event))
            print("Activated experiment {0}".format(experiment.key))
            callbackhit[0] = True

        notification_id = self.optimizely.notification_center.add_notification_listener(
            enums.NotificationTypes.ACTIVATE, on_activate
        )
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process'):
            self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

        self.assertEqual(True, callbackhit[0])
        self.optimizely.notification_center.remove_notification_listener(notification_id)
        self.assertEqual(
            0, len(self.optimizely.notification_center.notification_listeners[enums.NotificationTypes.ACTIVATE]),
        )
        self.optimizely.notification_center.clear_all_notifications()
        self.assertEqual(
            0, len(self.optimizely.notification_center.notification_listeners[enums.NotificationTypes.ACTIVATE]),
        )

    def test_add_track_remove_clear_listener(self):
        """ Test adding a listener track passes correctly and gets called"""
        callback_hit = [False]

        def on_track(event_key, user_id, attributes, event_tags, event):
            self.assertTrue(self.strTest(event_key))
            self.assertTrue(self.strTest(user_id))
            if attributes is not None:
                self.assertTrue(isinstance(attributes, dict))
            if event_tags is not None:
                self.assertTrue(isinstance(event_tags, dict))

            self.assertTrue(isinstance(event, dict))
            callback_hit[0] = True

        note_id = self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process'):
            self.optimizely.track('test_event', 'test_user')

        self.assertEqual(True, callback_hit[0])

        self.assertEqual(
            1, len(self.optimizely.notification_center.notification_listeners[enums.NotificationTypes.TRACK]),
        )
        self.optimizely.notification_center.remove_notification_listener(note_id)
        self.assertEqual(
            0, len(self.optimizely.notification_center.notification_listeners[enums.NotificationTypes.TRACK]),
        )
        self.optimizely.notification_center.clear_all_notifications()
        self.assertEqual(
            0, len(self.optimizely.notification_center.notification_listeners[enums.NotificationTypes.TRACK]),
        )

    def test_activate_and_decision_listener(self):
        """ Test that activate calls broadcast activate and decision with proper parameters. """

        def on_activate(event_key, user_id, attributes, event_tags, event):
            pass

        self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast:
            self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(mock_broadcast.call_count, 2)

        mock_broadcast.assert_has_calls(
            [
                mock.call(
                    enums.NotificationTypes.DECISION,
                    'ab-test',
                    'test_user',
                    {},
                    {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
                ),
                mock.call(
                    enums.NotificationTypes.ACTIVATE,
                    self.project_config.get_experiment_from_key('test_experiment'),
                    'test_user',
                    None,
                    self.project_config.get_variation_from_id('test_experiment', '111129'),
                    log_event.__dict__,
                ),
            ]
        )

    def test_activate_and_decision_listener_with_attr(self):
        """ Test that activate calls broadcast activate and decision with proper parameters. """

        def on_activate(event_key, user_id, attributes, event_tags, event):
            pass

        self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast:
            self.assertEqual(
                'variation', self.optimizely.activate('test_experiment', 'test_user', {'test_attribute': 'test_value'}),
            )

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(mock_broadcast.call_count, 2)

        mock_broadcast.assert_has_calls(
            [
                mock.call(
                    enums.NotificationTypes.DECISION,
                    'ab-test',
                    'test_user',
                    {'test_attribute': 'test_value'},
                    {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
                ),
                mock.call(
                    enums.NotificationTypes.ACTIVATE,
                    self.project_config.get_experiment_from_key('test_experiment'),
                    'test_user',
                    {'test_attribute': 'test_value'},
                    self.project_config.get_variation_from_id('test_experiment', '111129'),
                    log_event.__dict__,
                ),
            ]
        )

    def test_decision_listener__user_not_in_experiment(self):
        """ Test that activate calls broadcast decision with variation_key 'None' \
    when user not in experiment. """

        with mock.patch('optimizely.decision_service.DecisionService.get_variation', return_value=None,), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(None, self.optimizely.activate('test_experiment', 'test_user'))

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'ab-test',
            'test_user',
            {},
            {'experiment_key': 'test_experiment', 'variation_key': None},
        )

    def test_track_listener(self):
        """ Test that track calls notification broadcaster. """

        def on_track(event_key, user_id, attributes, event_tags, event):
            pass

        self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111128'),
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_event_tracked:
            self.optimizely.track('test_event', 'test_user')

            log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

            mock_event_tracked.assert_called_once_with(
                enums.NotificationTypes.TRACK, "test_event", 'test_user', None, None, log_event.__dict__,
            )

    def test_track_listener_with_attr(self):
        """ Test that track calls notification broadcaster. """

        def on_track(event_key, user_id, attributes, event_tags, event):
            pass

        self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111128'),
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_event_tracked:
            self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'})

            log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

            mock_event_tracked.assert_called_once_with(
                enums.NotificationTypes.TRACK,
                "test_event",
                'test_user',
                {'test_attribute': 'test_value'},
                None,
                log_event.__dict__,
            )

    def test_track_listener_with_attr_with_event_tags(self):
        """ Test that track calls notification broadcaster. """

        def on_track(event_key, user_id, attributes, event_tags, event):
            pass

        self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111128'),
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_event_tracked:
            self.optimizely.track(
                'test_event',
                'test_user',
                attributes={'test_attribute': 'test_value'},
                event_tags={'value': 1.234, 'non-revenue': 'abc'},
            )

            log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

            mock_event_tracked.assert_called_once_with(
                enums.NotificationTypes.TRACK,
                "test_event",
                'test_user',
                {'test_attribute': 'test_value'},
                {'value': 1.234, 'non-revenue': 'abc'},
                log_event.__dict__,
            )

    def test_is_feature_enabled__callback_listener(self):
        """ Test that the feature is enabled for the user if bucketed into variation of an experiment.
    Also confirm that impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        feature = project_config.get_feature_from_key('test_feature_in_experiment')

        access_callback = [False]

        def on_activate(experiment, user_id, attributes, variation, event):
            access_callback[0] = True

        opt_obj.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate)

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ) as mock_decision, mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process'):
            self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

        mock_decision.assert_called_once_with(opt_obj.config_manager.get_config(), feature, 'test_user', None)
        self.assertTrue(access_callback[0])

    def test_is_feature_enabled_rollout_callback_listener(self):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        feature = project_config.get_feature_from_key('test_feature_in_experiment')

        access_callback = [False]

        def on_activate(experiment, user_id, attributes, variation, event):
            access_callback[0] = True

        opt_obj.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate)

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ) as mock_decision, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

        mock_decision.assert_called_once_with(project_config, feature, 'test_user', None)

        # Check that impression event is not sent
        self.assertEqual(0, mock_process.call_count)
        self.assertEqual(False, access_callback[0])

    def test_activate__with_attributes__audience_match(self):
        """ Test that activate calls process with right params and returns expected
    variation when attributes are provided and audience conditions are met. """

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ) as mock_get_variation, mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertEqual(
                'variation', self.optimizely.activate('test_experiment', 'test_user', {'test_attribute': 'test_value'}),
            )
        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'}
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        mock_get_variation.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_key('test_experiment'),
            'test_user',
            {'test_attribute': 'test_value'},
        )
        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_activate__with_attributes_of_different_types(self):
        """ Test that activate calls process with right params and returns expected
    variation when different types of attributes are provided and audience conditions are met. """

        with mock.patch(
            'optimizely.bucketer.Bucketer.bucket',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ) as mock_bucket, mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:

            attributes = {
                'test_attribute': 'test_value_1',
                'boolean_key': False,
                'integer_key': 0,
                'double_key': 0.0,
            }

            self.assertEqual(
                'variation', self.optimizely.activate('test_experiment', 'test_user', attributes),
            )

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': False, 'entity_id': '111196', 'key': 'boolean_key'},
                        {'type': 'custom', 'value': 0.0, 'entity_id': '111198', 'key': 'double_key'},
                        {'type': 'custom', 'value': 0, 'entity_id': '111197', 'key': 'integer_key'},
                        {'type': 'custom', 'value': 'test_value_1', 'entity_id': '111094', 'key': 'test_attribute'},
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        mock_bucket.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_key('test_experiment'),
            'test_user',
            'test_user',
        )
        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_activate__with_attributes__typed_audience_match(self):
        """ Test that activate calls process with right params and returns expected
    variation when attributes are provided and typed audience conditions are met. """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            # Should be included via exact match string audience with id '3468206642'
            self.assertEqual(
                'A', opt_obj.activate('typed_audience_experiment', 'test_user', {'house': 'Gryffindor'}),
            )
        expected_attr = {
            'type': 'custom',
            'value': 'Gryffindor',
            'entity_id': '594015',
            'key': 'house',
        }

        self.assertTrue(expected_attr in [x.__dict__ for x in mock_process.call_args[0][0].visitor_attributes])

        mock_process.reset()

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            # Should be included via exact match number audience with id '3468206646'
            self.assertEqual(
                'A', opt_obj.activate('typed_audience_experiment', 'test_user', {'lasers': 45.5}),
            )
        expected_attr = {
            'type': 'custom',
            'value': 45.5,
            'entity_id': '594016',
            'key': 'lasers',
        }

        self.assertTrue(expected_attr in [x.__dict__ for x in mock_process.call_args[0][0].visitor_attributes])

    def test_activate__with_attributes__typed_audience_mismatch(self):
        """ Test that activate returns None when typed audience conditions do not match. """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.assertIsNone(opt_obj.activate('typed_audience_experiment', 'test_user', {'house': 'Hufflepuff'}))
        self.assertEqual(0, mock_process.call_count)

    def test_activate__with_attributes__complex_audience_match(self):
        """ Test that activate calls process with right params and returns expected
    variation when attributes are provided and complex audience conditions are met. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            # Should be included via substring match string audience with id '3988293898', and
            # exact match number audience with id '3468206646'
            user_attr = {'house': 'Welcome to Slytherin!', 'lasers': 45.5}
            self.assertEqual(
                'A', opt_obj.activate('audience_combinations_experiment', 'test_user', user_attr),
            )

        expected_attr_1 = {
            'type': 'custom',
            'value': 'Welcome to Slytherin!',
            'entity_id': '594015',
            'key': 'house',
        }

        expected_attr_2 = {
            'type': 'custom',
            'value': 45.5,
            'entity_id': '594016',
            'key': 'lasers',
        }

        self.assertTrue(expected_attr_1 in [x.__dict__ for x in mock_process.call_args[0][0].visitor_attributes])

        self.assertTrue(expected_attr_2 in [x.__dict__ for x in mock_process.call_args[0][0].visitor_attributes])

    def test_activate__with_attributes__complex_audience_mismatch(self):
        """ Test that activate returns None when complex audience conditions do not match. """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:

            user_attr = {'house': 'Hufflepuff', 'lasers': 45.5}
            self.assertIsNone(opt_obj.activate('audience_combinations_experiment', 'test_user', user_attr))

        self.assertEqual(0, mock_process.call_count)

    def test_activate__with_attributes__audience_match__forced_bucketing(self):
        """ Test that activate calls process with right params and returns expected
    variation when attributes are provided and audience conditions are met after a
    set_forced_variation is called. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'control'))
            self.assertEqual(
                'control', self.optimizely.activate('test_experiment', 'test_user', {'test_attribute': 'test_value'}),
            )

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'}
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111128', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_activate__with_attributes__audience_match__bucketing_id_provided(self):
        """ Test that activate calls process with right params and returns expected variation
    when attributes (including bucketing ID) are provided and audience conditions are met. """

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ) as mock_get_variation, mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertEqual(
                'variation',
                self.optimizely.activate(
                    'test_experiment',
                    'test_user',
                    {'test_attribute': 'test_value', '$opt_bucketing_id': 'user_bucket_value'},
                ),
            )
        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {
                            'type': 'custom',
                            'value': 'user_bucket_value',
                            'entity_id': '$opt_bucketing_id',
                            'key': '$opt_bucketing_id',
                        },
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'},
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        mock_get_variation.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_key('test_experiment'),
            'test_user',
            {'test_attribute': 'test_value', '$opt_bucketing_id': 'user_bucket_value'},
        )
        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_activate__with_attributes__no_audience_match(self):
        """ Test that activate returns None when audience conditions do not match. """

        with mock.patch('optimizely.helpers.audience.does_user_meet_audience_conditions',
                        return_value=False) as mock_audience_check:
            self.assertIsNone(
                self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},)
            )
        expected_experiment = self.project_config.get_experiment_from_key('test_experiment')
        mock_audience_check.assert_called_once_with(
            self.project_config,
            expected_experiment.get_audience_conditions_or_ids(),
            enums.ExperimentAudienceEvaluationLogs,
            'test_experiment',
            {'test_attribute': 'test_value'},
            self.optimizely.logger,
        )

    def test_activate__with_attributes__invalid_attributes(self):
        """ Test that activate returns None and does not bucket or process event when attributes are invalid. """

        with mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user', attributes='invalid'))

        self.assertEqual(0, mock_bucket.call_count)
        self.assertEqual(0, mock_process.call_count)

    def test_activate__experiment_not_running(self):
        """ Test that activate returns None and does not process event when experiment is not Running. """

        with mock.patch(
            'optimizely.helpers.audience.does_user_meet_audience_conditions', return_value=True
        ) as mock_audience_check, mock.patch(
            'optimizely.helpers.experiment.is_experiment_running', return_value=False
        ) as mock_is_experiment_running, mock.patch(
            'optimizely.bucketer.Bucketer.bucket'
        ) as mock_bucket, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertIsNone(
                self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},)
            )

        mock_is_experiment_running.assert_called_once_with(
            self.project_config.get_experiment_from_key('test_experiment')
        )
        self.assertEqual(0, mock_audience_check.call_count)
        self.assertEqual(0, mock_bucket.call_count)
        self.assertEqual(0, mock_process.call_count)

    def test_activate__whitelisting_overrides_audience_check(self):
        """ Test that during activate whitelist overrides audience check if user is in the whitelist. """

        with mock.patch(
            'optimizely.helpers.audience.does_user_meet_audience_conditions', return_value=False
        ) as mock_audience_check, mock.patch(
            'optimizely.helpers.experiment.is_experiment_running', return_value=True
        ) as mock_is_experiment_running:
            self.assertEqual('control', self.optimizely.activate('test_experiment', 'user_1'))
        mock_is_experiment_running.assert_called_once_with(
            self.project_config.get_experiment_from_key('test_experiment')
        )
        self.assertEqual(0, mock_audience_check.call_count)

    def test_activate__bucketer_returns_none(self):
        """ Test that activate returns None and does not process event when user is in no variation. """

        with mock.patch(
            'optimizely.helpers.audience.does_user_meet_audience_conditions',
            return_value=True), mock.patch(
            'optimizely.bucketer.Bucketer.bucket',
            return_value=None) as mock_bucket, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertIsNone(
                self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},)
            )
        mock_bucket.assert_called_once_with(
            self.project_config,
            self.project_config.get_experiment_from_key('test_experiment'),
            'test_user',
            'test_user',
        )
        self.assertEqual(0, mock_process.call_count)

    def test_activate__invalid_object(self):
        """ Test that activate logs error if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.activate('test_experiment', 'test_user'))

        mock_client_logging.error.assert_called_once_with('Optimizely instance is not valid. Failing "activate".')

    def test_activate__invalid_config(self):
        """ Test that activate logs error if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_datafile')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.activate('test_experiment', 'test_user'))

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "activate".'
        )

    def test_track__with_attributes(self):
        """ Test that track calls process with right params when attributes are provided. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'})

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'}
                    ],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_track__with_attributes__typed_audience_match(self):
        """ Test that track calls process with right params when attributes are provided
    and it's a typed audience match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            # Should be included via substring match string audience with id '3988293898'
            opt_obj.track('item_bought', 'test_user', {'house': 'Welcome to Slytherin!'})

        self.assertEqual(1, mock_process.call_count)

        expected_attr = {
            'type': 'custom',
            'value': 'Welcome to Slytherin!',
            'entity_id': '594015',
            'key': 'house',
        }

        self.assertTrue(expected_attr in [x.__dict__ for x in mock_process.call_args[0][0].visitor_attributes])

    def test_track__with_attributes__typed_audience_mismatch(self):
        """ Test that track calls process even if audience conditions do not match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            opt_obj.track('item_bought', 'test_user', {'house': 'Welcome to Hufflepuff!'})

        self.assertEqual(1, mock_process.call_count)

    def test_track__with_attributes__complex_audience_match(self):
        """ Test that track calls process with right params when attributes are provided
    and it's a complex audience match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            # Should be included via exact match string audience with id '3468206642', and
            # exact match boolean audience with id '3468206643'
            user_attr = {'house': 'Gryffindor', 'should_do_it': True}
            opt_obj.track('user_signed_up', 'test_user', user_attr)

        self.assertEqual(1, mock_process.call_count)

        expected_attr_1 = {
            'type': 'custom',
            'value': 'Gryffindor',
            'entity_id': '594015',
            'key': 'house',
        }

        self.assertTrue(expected_attr_1 in [x.__dict__ for x in mock_process.call_args[0][0].visitor_attributes])

        expected_attr_2 = {
            'type': 'custom',
            'value': True,
            'entity_id': '594017',
            'key': 'should_do_it',
        }

        self.assertTrue(expected_attr_2 in [x.__dict__ for x in mock_process.call_args[0][0].visitor_attributes])

    def test_track__with_attributes__complex_audience_mismatch(self):
        """ Test that track calls process even when complex audience conditions do not match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            # Should be excluded - exact match boolean audience with id '3468206643' does not match,
            # so the overall conditions fail
            user_attr = {'house': 'Gryffindor', 'should_do_it': False}
            opt_obj.track('user_signed_up', 'test_user', user_attr)

        self.assertEqual(1, mock_process.call_count)

    def test_track__with_attributes__bucketing_id_provided(self):
        """ Test that track calls process with right params when
    attributes (including bucketing ID) are provided. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.optimizely.track(
                'test_event',
                'test_user',
                attributes={'test_attribute': 'test_value', '$opt_bucketing_id': 'user_bucket_value'},
            )

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {
                            'type': 'custom',
                            'value': 'user_bucket_value',
                            'entity_id': '$opt_bucketing_id',
                            'key': '$opt_bucketing_id',
                        },
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'},
                    ],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_track__with_attributes__no_audience_match(self):
        """ Test that track calls process even if audience conditions do not match. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.optimizely.track(
                'test_event', 'test_user', attributes={'test_attribute': 'wrong_test_value'},
            )

        self.assertEqual(1, mock_process.call_count)

    def test_track__with_attributes__invalid_attributes(self):
        """ Test that track does not bucket or process event if attributes are invalid. """

        with mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.optimizely.track('test_event', 'test_user', attributes='invalid')

        self.assertEqual(0, mock_bucket.call_count)
        self.assertEqual(0, mock_process.call_count)

    def test_track__with_event_tags(self):
        """ Test that track calls process with right params when event tags are provided. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.optimizely.track(
                'test_event',
                'test_user',
                attributes={'test_attribute': 'test_value'},
                event_tags={'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'},
            )

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'}
                    ],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'entity_id': '111095',
                                    'key': 'test_event',
                                    'revenue': 4200,
                                    'tags': {'non-revenue': 'abc', 'revenue': 4200, 'value': 1.234},
                                    'timestamp': 42000,
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'value': 1.234,
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }
        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_track__with_event_tags_revenue(self):
        """ Test that track calls process with right params when only revenue
        event tags are provided only. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.optimizely.track(
                'test_event',
                'test_user',
                attributes={'test_attribute': 'test_value'},
                event_tags={'revenue': 4200, 'non-revenue': 'abc'},
            )

        expected_params = {
            'visitors': [
                {
                    'attributes': [
                        {'entity_id': '111094', 'type': 'custom', 'value': 'test_value', 'key': 'test_attribute'}
                    ],
                    'visitor_id': 'test_user',
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'tags': {'non-revenue': 'abc', 'revenue': 4200},
                                    'timestamp': 42000,
                                    'revenue': 4200,
                                    'key': 'test_event',
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'project_id': '111001',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'account_id': '12001',
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_track__with_event_tags_numeric_metric(self):
        """ Test that track calls process with right params when only numeric metric
        event tags are provided. """

        with mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.optimizely.track(
                'test_event',
                'test_user',
                attributes={'test_attribute': 'test_value'},
                event_tags={'value': 1.234, 'non-revenue': 'abc'},
            )

        expected_event_metrics_params = {'non-revenue': 'abc', 'value': 1.234}

        expected_event_features_params = {
            'entity_id': '111094',
            'type': 'custom',
            'value': 'test_value',
            'key': 'test_attribute',
        }

        self.assertEqual(1, mock_process.call_count)

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self._validate_event_object_event_tags(
            log_event.__dict__, expected_event_metrics_params, expected_event_features_params,
        )

    def test_track__with_event_tags__forced_bucketing(self):
        """ Test that track calls process with right params when event_value information is provided
    after a forced bucket. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
            self.optimizely.track(
                'test_event',
                'test_user',
                attributes={'test_attribute': 'test_value'},
                event_tags={'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'},
            )

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'}
                    ],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'entity_id': '111095',
                                    'key': 'test_event',
                                    'revenue': 4200,
                                    'tags': {'non-revenue': 'abc', 'revenue': 4200, 'value': 1.234},
                                    'timestamp': 42000,
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'value': 1.234,
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_track__with_invalid_event_tags(self):
        """ Test that track calls process with right params when invalid event tags are provided. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.optimizely.track(
                'test_event',
                'test_user',
                attributes={'test_attribute': 'test_value'},
                event_tags={'revenue': '4200', 'value': True},
            )

        expected_params = {
            'visitors': [
                {
                    'attributes': [
                        {'entity_id': '111094', 'type': 'custom', 'value': 'test_value', 'key': 'test_attribute'}
                    ],
                    'visitor_id': 'test_user',
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                    'tags': {'value': True, 'revenue': '4200'},
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'project_id': '111001',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'account_id': '12001',
            'anonymize_ip': False,
            'revision': '42',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_track__experiment_not_running(self):
        """ Test that track calls process even if experiment is not running. """

        with mock.patch(
            'optimizely.helpers.experiment.is_experiment_running', return_value=False
        ) as mock_is_experiment_running, mock.patch('time.time', return_value=42), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.optimizely.track('test_event', 'test_user')

        # Assert that experiment is running is not performed
        self.assertEqual(0, mock_is_experiment_running.call_count)
        self.assertEqual(1, mock_process.call_count)

    def test_track_invalid_event_key(self):
        """ Test that track does not call process when event does not exist. """

        with mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.optimizely.track('aabbcc_event', 'test_user')

        self.assertEqual(0, mock_process.call_count)
        mock_client_logging.info.assert_called_with('Not tracking user "test_user" for event "aabbcc_event".')

    def test_track__whitelisted_user_overrides_audience_check(self):
        """ Test that event is tracked when user is whitelisted. """

        with mock.patch('time.time', return_value=42), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            self.optimizely.track('test_event', 'user_1')

        self.assertEqual(1, mock_process.call_count)

    def test_track__invalid_object(self):
        """ Test that track logs error if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.track('test_event', 'test_user'))

        mock_client_logging.error.assert_called_once_with('Optimizely instance is not valid. Failing "track".')

    def test_track__invalid_config(self):
        """ Test that track logs error if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_datafile')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            opt_obj.track('test_event', 'test_user')

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "track".'
        )

    def test_track__invalid_experiment_key(self):
        """ Test that None is returned and expected log messages are logged during track \
    when exp_key is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.is_non_empty_string', return_value=False
        ) as mock_validator:
            self.assertIsNone(self.optimizely.track(99, 'test_user'))

        mock_validator.assert_any_call(99)

        mock_client_logging.error.assert_called_once_with('Provided "event_key" is in an invalid format.')

    def test_track__invalid_user_id(self):
        """ Test that None is returned and expected log messages are logged during track \
    when user_id is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.assertIsNone(self.optimizely.track('test_event', 99))
        mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

    def test_get_variation(self):
        """ Test that get_variation returns valid variation and broadcasts decision with proper parameters. """

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('optimizely.notification_center.NotificationCenter.send_notifications') as mock_broadcast:
            self.assertEqual(
                'variation', self.optimizely.get_variation('test_experiment', 'test_user'),
            )

        self.assertEqual(mock_broadcast.call_count, 1)

        mock_broadcast.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'ab-test',
            'test_user',
            {},
            {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
        )

    def test_get_variation_with_experiment_in_feature(self):
        """ Test that get_variation returns valid variation and broadcasts decision listener with type feature-test when
     get_variation returns feature experiment variation."""

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('optimizely.notification_center.NotificationCenter.send_notifications') as mock_broadcast:
            self.assertEqual('variation', opt_obj.get_variation('test_experiment', 'test_user'))

        self.assertEqual(mock_broadcast.call_count, 1)

        mock_broadcast.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-test',
            'test_user',
            {},
            {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
        )

    def test_get_variation__returns_none(self):
        """ Test that get_variation returns no variation and broadcasts decision with proper parameters. """

        with mock.patch('optimizely.decision_service.DecisionService.get_variation', return_value=None,), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast:
            self.assertEqual(
                None,
                self.optimizely.get_variation(
                    'test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},
                ),
            )

        self.assertEqual(mock_broadcast.call_count, 1)

        mock_broadcast.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'ab-test',
            'test_user',
            {'test_attribute': 'test_value'},
            {'experiment_key': 'test_experiment', 'variation_key': None},
        )

    def test_get_variation__invalid_object(self):
        """ Test that get_variation logs error if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.get_variation('test_experiment', 'test_user'))

        mock_client_logging.error.assert_called_once_with('Optimizely instance is not valid. Failing "get_variation".')

    def test_get_variation__invalid_config(self):
        """ Test that get_variation logs error if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_datafile')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.get_variation('test_experiment', 'test_user'))

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "get_variation".'
        )

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

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.is_non_empty_string', return_value=False
        ) as mock_validator:
            self.assertFalse(opt_obj.is_feature_enabled(None, 'test_user'))

        mock_validator.assert_any_call(None)
        mock_client_logging.error.assert_called_with('Provided "feature_key" is in an invalid format.')

    def test_is_feature_enabled__returns_false_for_invalid_user_id(self):
        """ Test that is_feature_enabled returns false if the provided user ID is invalid. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertFalse(opt_obj.is_feature_enabled('feature_key', 1.2))
        mock_client_logging.error.assert_called_with('Provided "user_id" is in an invalid format.')

    def test_is_feature_enabled__returns_false_for__invalid_attributes(self):
        """ Test that is_feature_enabled returns false if attributes are in an invalid format. """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.are_attributes_valid', return_value=False
        ) as mock_validator:
            self.assertFalse(opt_obj.is_feature_enabled('feature_key', 'test_user', attributes='invalid'))

        mock_validator.assert_called_once_with('invalid')
        mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')

    def test_is_feature_enabled__in_rollout__typed_audience_match(self):
        """ Test that is_feature_enabled returns True for feature rollout with typed audience match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        # Should be included via exists match audience with id '3988293899'
        self.assertTrue(opt_obj.is_feature_enabled('feat', 'test_user', {'favorite_ice_cream': 'chocolate'}))

        # Should be included via less-than match audience with id '3468206644'
        self.assertTrue(opt_obj.is_feature_enabled('feat', 'test_user', {'lasers': -3}))

    def test_is_feature_enabled__in_rollout__typed_audience_mismatch(self):
        """ Test that is_feature_enabled returns False for feature rollout with typed audience mismatch. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        self.assertIs(opt_obj.is_feature_enabled('feat', 'test_user', {}), False)

    def test_is_feature_enabled__in_rollout__complex_audience_match(self):
        """ Test that is_feature_enabled returns True for feature rollout with complex audience match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        # Should be included via substring match string audience with id '3988293898', and
        # exists audience with id '3988293899'
        user_attr = {'house': '...Slytherinnn...sss.', 'favorite_ice_cream': 'matcha'}
        self.assertStrictTrue(opt_obj.is_feature_enabled('feat2', 'test_user', user_attr))

    def test_is_feature_enabled__in_rollout__complex_audience_mismatch(self):
        """ Test that is_feature_enabled returns False for feature rollout with complex audience mismatch. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))
        # Should be excluded - substring match string audience with id '3988293898' does not match,
        # and no audience in the other branch of the 'and' matches either
        self.assertStrictFalse(opt_obj.is_feature_enabled('feat2', 'test_user', {'house': 'Lannister'}))

    def test_is_feature_enabled__returns_false_for_invalid_feature(self):
        """ Test that the feature is not enabled for the user if the provided feature key is invalid. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature'
        ) as mock_decision, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process:
            self.assertFalse(opt_obj.is_feature_enabled('invalid_feature', 'user1'))

        self.assertFalse(mock_decision.called)

        # Check that no event is sent
        self.assertEqual(0, mock_process.call_count)

    def test_is_feature_enabled__returns_true_for_feature_experiment_if_feature_enabled_for_variation(self,):
        """ Test that the feature is enabled for the user if bucketed into variation of an experiment and
    the variation's featureEnabled property is True. Also confirm that impression event is processed and
    decision listener is called with proper parameters """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        feature = project_config.get_feature_from_key('test_feature_in_experiment')

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        # Assert that featureEnabled property is True
        self.assertTrue(mock_variation.featureEnabled)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ) as mock_decision, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

        mock_decision.assert_called_once_with(opt_obj.config_manager.get_config(), feature, 'test_user', None)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'feature',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )
        expected_params = {
            'account_id': '12001',
            'project_id': '111111',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {
                            'type': 'custom',
                            'value': True,
                            'entity_id': '$opt_bot_filtering',
                            'key': '$opt_bot_filtering',
                        }
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '1',
        }

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        # Check that impression event is sent
        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_is_feature_enabled__returns_false_for_feature_experiment_if_feature_disabled_for_variation(self,):
        """ Test that the feature is disabled for the user if bucketed into variation of an experiment and
    the variation's featureEnabled property is False. Also confirm that impression event is processed and
    decision is broadcasted with proper parameters """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        feature = project_config.get_feature_from_key('test_feature_in_experiment')

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111128')

        # Assert that featureEnabled property is False
        self.assertFalse(mock_variation.featureEnabled)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ) as mock_decision, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

        mock_decision.assert_called_once_with(opt_obj.config_manager.get_config(), feature, 'test_user', None)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'feature',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'feature-test',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'control'},
            },
        )
        # Check that impression event is sent
        expected_params = {
            'account_id': '12001',
            'project_id': '111111',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {
                            'type': 'custom',
                            'value': True,
                            'entity_id': '$opt_bot_filtering',
                            'key': '$opt_bot_filtering',
                        }
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111128', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42000,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_version': version.__version__,
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '1',
        }
        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], self.optimizely.logger)

        # Check that impression event is sent
        self.assertEqual(1, mock_process.call_count)
        self._validate_event_object(
            log_event.__dict__,
            'https://logx.optimizely.com/v1/events',
            expected_params,
            'POST',
            {'Content-Type': 'application/json'},
        )

    def test_is_feature_enabled__returns_true_for_feature_rollout_if_feature_enabled(self,):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout and
    the variation's featureEnabled property is True. Also confirm that no impression event is processed and
    decision is broadcasted with proper parameters """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        feature = project_config.get_feature_from_key('test_feature_in_experiment')

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        # Assert that featureEnabled property is True
        self.assertTrue(mock_variation.featureEnabled)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ) as mock_decision, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            self.assertTrue(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

        mock_decision.assert_called_once_with(opt_obj.config_manager.get_config(), feature, 'test_user', None)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'feature',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'rollout',
                'source_info': {},
            },
        )

        # Check that impression event is not sent
        self.assertEqual(0, mock_process.call_count)

    def test_is_feature_enabled__returns_false_for_feature_rollout_if_feature_disabled(self,):
        """ Test that the feature is disabled for the user if bucketed into variation of a rollout and
    the variation's featureEnabled property is False. Also confirm that no impression event is processed and
    decision is broadcasted with proper parameters """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        feature = project_config.get_feature_from_key('test_feature_in_experiment')

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        # Set featureEnabled property to False
        mock_variation.featureEnabled = False

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ) as mock_decision, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

        mock_decision.assert_called_once_with(opt_obj.config_manager.get_config(), feature, 'test_user', None)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'feature',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'source_info': {},
            },
        )

        # Check that impression event is not sent
        self.assertEqual(0, mock_process.call_count)

    def test_is_feature_enabled__returns_false_when_user_is_not_bucketed_into_any_variation(self,):
        """ Test that the feature is not enabled for the user if user is neither bucketed for
    Feature Experiment nor for Feature Rollout.
    Also confirm that impression event is not processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        feature = project_config.get_feature_from_key('test_feature_in_experiment')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ) as mock_decision, mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'test_user'))

        # Check that impression event is not sent
        self.assertEqual(0, mock_process.call_count)

        mock_decision.assert_called_once_with(opt_obj.config_manager.get_config(), feature, 'test_user', None)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'feature',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'source_info': {},
            },
        )

        # Check that impression event is not sent
        self.assertEqual(0, mock_process.call_count)

    def test_is_feature_enabled__invalid_object(self):
        """ Test that is_feature_enabled returns False and logs error if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'user_1'))

        mock_client_logging.error.assert_called_once_with(
            'Optimizely instance is not valid. Failing "is_feature_enabled".'
        )

    def test_is_feature_enabled__invalid_config(self):
        """ Test that is_feature_enabled returns False if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_file')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging, mock.patch(
            'optimizely.event_dispatcher.EventDispatcher.dispatch_event'
        ) as mock_dispatch_event:
            self.assertFalse(opt_obj.is_feature_enabled('test_feature_in_experiment', 'user_1'))

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "is_feature_enabled".'
        )

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

        with mock.patch(
            'optimizely.optimizely.Optimizely.is_feature_enabled', side_effect=side_effect,
        ) as mock_is_feature_enabled:
            received_features = opt_obj.get_enabled_features('user_1')

        expected_enabled_features = [
            'test_feature_in_experiment',
            'test_feature_in_rollout',
        ]
        self.assertEqual(sorted(expected_enabled_features), sorted(received_features))
        mock_is_feature_enabled.assert_any_call('test_feature_in_experiment', 'user_1', None)
        mock_is_feature_enabled.assert_any_call('test_feature_in_rollout', 'user_1', None)
        mock_is_feature_enabled.assert_any_call('test_feature_in_group', 'user_1', None)
        mock_is_feature_enabled.assert_any_call('test_feature_in_experiment_and_rollout', 'user_1', None)

    def test_get_enabled_features__broadcasts_decision_for_each_feature(self):
        """ Test that get_enabled_features only returns features that are enabled for the specified user \
    and broadcasts decision for each feature. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        mock_variation_2 = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111128')

        def side_effect(*args, **kwargs):
            feature = args[1]
            if feature.key == 'test_feature_in_experiment':
                return decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST)
            elif feature.key == 'test_feature_in_rollout':
                return decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT)
            elif feature.key == 'test_feature_in_experiment_and_rollout':
                return decision_service.Decision(mock_experiment, mock_variation_2, enums.DecisionSources.FEATURE_TEST,)
            else:
                return decision_service.Decision(mock_experiment, mock_variation_2, enums.DecisionSources.ROLLOUT)

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature', side_effect=side_effect,
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            received_features = opt_obj.get_enabled_features('user_1')

        expected_enabled_features = [
            'test_feature_in_experiment',
            'test_feature_in_rollout',
        ]

        self.assertEqual(sorted(expected_enabled_features), sorted(received_features))

        mock_broadcast_decision.assert_has_calls(
            [
                mock.call(
                    enums.NotificationTypes.DECISION,
                    'feature',
                    'user_1',
                    {},
                    {
                        'feature_key': 'test_feature_in_experiment',
                        'feature_enabled': True,
                        'source': 'feature-test',
                        'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
                    },
                ),
                mock.call(
                    enums.NotificationTypes.DECISION,
                    'feature',
                    'user_1',
                    {},
                    {
                        'feature_key': 'test_feature_in_group',
                        'feature_enabled': False,
                        'source': 'rollout',
                        'source_info': {},
                    },
                ),
                mock.call(
                    enums.NotificationTypes.DECISION,
                    'feature',
                    'user_1',
                    {},
                    {
                        'feature_key': 'test_feature_in_rollout',
                        'feature_enabled': True,
                        'source': 'rollout',
                        'source_info': {},
                    },
                ),
                mock.call(
                    enums.NotificationTypes.DECISION,
                    'feature',
                    'user_1',
                    {},
                    {
                        'feature_key': 'test_feature_in_experiment_and_rollout',
                        'feature_enabled': False,
                        'source': 'feature-test',
                        'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'control'},
                    },
                ),
            ],
            any_order=True,
        )

    def test_get_enabled_features_invalid_user_id(self):
        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.assertEqual([], self.optimizely.get_enabled_features(1.2))

        mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

    def test_get_enabled_features__invalid_attributes(self):
        """ Test that get_enabled_features returns empty list if attributes are in an invalid format. """
        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.are_attributes_valid', return_value=False
        ) as mock_validator:
            self.assertEqual(
                [], self.optimizely.get_enabled_features('test_user', attributes='invalid'),
            )

        mock_validator.assert_called_once_with('invalid')
        mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')

    def test_get_enabled_features__invalid_object(self):
        """ Test that get_enabled_features returns empty list if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertEqual([], opt_obj.get_enabled_features('test_user'))

        mock_client_logging.error.assert_called_once_with(
            'Optimizely instance is not valid. ' 'Failing "get_enabled_features".'
        )

    def test_get_enabled_features__invalid_config(self):
        """ Test that get_enabled_features returns empty list if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_file')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertEqual([], opt_obj.get_enabled_features('user_1'))

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "get_enabled_features".'
        )

    def test_get_feature_variable_boolean(self):
        """ Test that get_feature_variable_boolean returns Boolean value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user')
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "is_working" for variation "variation" is "true".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'is_working',
                'variable_value': True,
                'variable_type': 'boolean',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )

    def test_get_feature_variable_double(self):
        """ Test that get_feature_variable_double returns Double value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                10.02, opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "cost" for variation "variation" is "10.02".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'cost',
                'variable_value': 10.02,
                'variable_type': 'double',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )

    def test_get_feature_variable_integer(self):
        """ Test that get_feature_variable_integer returns Integer value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                4243, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "count" for variation "variation" is "4243".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'count',
                'variable_value': 4243,
                'variable_type': 'integer',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )

    def test_get_feature_variable_string(self):
        """ Test that get_feature_variable_string returns String value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                'staging',
                opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "environment" for variation "variation" is "staging".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'environment',
                'variable_value': 'staging',
                'variable_type': 'string',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )

    def test_get_feature_variable_json(self):
        """ Test that get_feature_variable_json returns dictionary object as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                {"test": 123},
                opt_obj.get_feature_variable_json('test_feature_in_experiment', 'object', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "object" for variation "variation" is "{"test": 123}".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'object',
                'variable_value': {"test": 123},
                'variable_type': 'json',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )

    def test_get_all_feature_variables(self):
        """ Test that get_all_feature_variables returns dictionary object as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        expected_results = {
            'cost': 10.02,
            'count': 4243,
            'environment': 'staging',
            'is_working': True,
            'object': {'test': 123},
            'true_object': {'true_test': 1.4},
            'variable_without_usage': 45}
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                expected_results,
                opt_obj.get_all_feature_variables('test_feature_in_experiment', 'test_user'),
            )

        self.assertEqual(7, mock_config_logging.info.call_count)

        mock_config_logging.info.assert_has_calls(
            [
                mock.call('Value for variable "count" for variation "variation" is "4243".'),
                mock.call('Value for variable "is_working" for variation "variation" is "true".'),
                mock.call('Variable "variable_without_usage" is not used in variation "variation". \
Assigning default value "45".'),
                mock.call('Value for variable "object" for variation "variation" is "{"test": 123}".'),
                mock.call('Value for variable "true_object" for variation "variation" is "{"true_test": 1.4}".'),
                mock.call('Value for variable "environment" for variation "variation" is "staging".'),
                mock.call('Value for variable "cost" for variation "variation" is "10.02".')
            ], any_order=True
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'all-feature-variables',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_values': {'count': 4243, 'is_working': True, 'true_object': {'true_test': 1.4},
                                    'variable_without_usage': 45, 'object': {'test': 123}, 'environment': 'staging',
                                    'cost': 10.02},
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )

    def test_get_feature_variable(self):
        """ Test that get_feature_variable returns variable value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        # Boolean
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(opt_obj.get_feature_variable('test_feature_in_experiment', 'is_working', 'test_user'))

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "is_working" for variation "variation" is "true".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'is_working',
                'variable_value': True,
                'variable_type': 'boolean',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )
        # Double
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                10.02, opt_obj.get_feature_variable('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "cost" for variation "variation" is "10.02".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'cost',
                'variable_value': 10.02,
                'variable_type': 'double',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )
        # Integer
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                4243, opt_obj.get_feature_variable('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "count" for variation "variation" is "4243".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'count',
                'variable_value': 4243,
                'variable_type': 'integer',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )
        # String
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                'staging', opt_obj.get_feature_variable('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "environment" for variation "variation" is "staging".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'environment',
                'variable_value': 'staging',
                'variable_type': 'string',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )
        # JSON
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                {"test": 123}, opt_obj.get_feature_variable('test_feature_in_experiment', 'object', 'test_user'),
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "object" for variation "variation" is "{"test": 123}".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': True,
                'source': 'feature-test',
                'variable_key': 'object',
                'variable_value': {"test": 123},
                'variable_type': 'json',
                'source_info': {'experiment_key': 'test_experiment', 'variation_key': 'variation'},
            },
        )

    def test_get_feature_variable_boolean_for_feature_in_rollout(self):
        """ Test that get_feature_variable_boolean returns Boolean value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211129')
        user_attributes = {'test_attribute': 'test_value'}

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable_boolean(
                    'test_feature_in_rollout', 'is_running', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "is_running" for variation "211129" is "true".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'is_running',
                'variable_value': True,
                'variable_type': 'boolean',
                'source_info': {},
            },
        )

    def test_get_feature_variable_double_for_feature_in_rollout(self):
        """ Test that get_feature_variable_double returns Double value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211129')
        user_attributes = {'test_attribute': 'test_value'}

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable_double(
                    'test_feature_in_rollout', 'price', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "price" for variation "211129" is "39.99".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'price',
                'variable_value': 39.99,
                'variable_type': 'double',
                'source_info': {},
            },
        )

    def test_get_feature_variable_integer_for_feature_in_rollout(self):
        """ Test that get_feature_variable_integer returns Double value as expected \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211129')
        user_attributes = {'test_attribute': 'test_value'}

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable_integer(
                    'test_feature_in_rollout', 'count', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with('Value for variable "count" for variation "211129" is "399".')

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'count',
                'variable_value': 399,
                'variable_type': 'integer',
                'source_info': {},
            },
        )

    def test_get_feature_variable_string_for_feature_in_rollout(self):
        """ Test that get_feature_variable_double returns Double value as expected
        and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211129')
        user_attributes = {'test_attribute': 'test_value'}

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable_string(
                    'test_feature_in_rollout', 'message', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "message" for variation "211129" is "Hello audience".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'message',
                'variable_value': 'Hello audience',
                'variable_type': 'string',
                'source_info': {},
            },
        )

    def test_get_feature_variable_json_for_feature_in_rollout(self):
        """ Test that get_feature_variable_json returns dictionary object as expected
        and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211129')
        user_attributes = {'test_attribute': 'test_value'}

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable_json(
                    'test_feature_in_rollout', 'object', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "object" for variation "211129" is "{"field": 12}".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'object',
                'variable_value': {"field": 12},
                'variable_type': 'json',
                'source_info': {},
            },
        )

    def test_get_all_feature_variables_for_feature_in_rollout(self):
        """ Test that get_all_feature_variables returns dictionary object as expected
        and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211129')
        user_attributes = {'test_attribute': 'test_value'}

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_all_feature_variables(
                    'test_feature_in_rollout', 'test_user', attributes=user_attributes,
                )
            )

        self.assertEqual(5, mock_config_logging.info.call_count)

        mock_config_logging.info.assert_has_calls(
            [
                mock.call('Value for variable "count" for variation "211129" is "399".'),
                mock.call('Value for variable "message" for variation "211129" is "Hello audience".'),
                mock.call('Value for variable "object" for variation "211129" is "{"field": 12}".'),
                mock.call('Value for variable "price" for variation "211129" is "39.99".'),
                mock.call('Value for variable "is_running" for variation "211129" is "true".'),
            ], any_order=True
        )
        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'all-feature-variables',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'variable_values': {'count': 399, 'message': 'Hello audience', 'object': {'field': 12},
                                    'price': 39.99, 'is_running': True},
                'source': 'rollout',
                'source_info': {},
            },
        )

    def test_get_feature_variable_for_feature_in_rollout(self):
        """ Test that get_feature_variable returns value as expected and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211129')
        user_attributes = {'test_attribute': 'test_value'}

        # Boolean
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable(
                    'test_feature_in_rollout', 'is_running', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "is_running" for variation "211129" is "true".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'is_running',
                'variable_value': True,
                'variable_type': 'boolean',
                'source_info': {},
            },
        )
        # Double
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable(
                    'test_feature_in_rollout', 'price', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "price" for variation "211129" is "39.99".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'price',
                'variable_value': 39.99,
                'variable_type': 'double',
                'source_info': {},
            },
        )
        # Integer
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable(
                    'test_feature_in_rollout', 'count', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with('Value for variable "count" for variation "211129" is "399".')

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'count',
                'variable_value': 399,
                'variable_type': 'integer',
                'source_info': {},
            },
        )
        # String
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable(
                    'test_feature_in_rollout', 'message', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "message" for variation "211129" is "Hello audience".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'message',
                'variable_value': 'Hello audience',
                'variable_type': 'string',
                'source_info': {},
            },
        )

        # JSON
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logging, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable(
                    'test_feature_in_rollout', 'object', 'test_user', attributes=user_attributes,
                )
            )

        mock_config_logging.info.assert_called_once_with(
            'Value for variable "object" for variation "211129" is "{"field": 12}".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {'test_attribute': 'test_value'},
            {
                'feature_key': 'test_feature_in_rollout',
                'feature_enabled': True,
                'source': 'rollout',
                'variable_key': 'object',
                'variable_value': {"field": 12},
                'variable_type': 'json',
                'source_info': {},
            },
        )

    def test_get_feature_variable__returns_default_value_if_variable_usage_not_in_variation(self,):
        """ Test that get_feature_variable_* returns default value if variable usage not present in variation. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')

        # Empty variable usage map for the mocked variation
        opt_obj.config_manager.get_config().variation_variable_usage_map['111129'] = None

        # Boolean
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertTrue(
                opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user')
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "is_working" is not used in variation "variation". Assigning default value "true".'
        )
        mock_config_logger.info.reset_mock()

        # Double
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertEqual(
                10.99, opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "cost" is not used in variation "variation". Assigning default value "10.99".'
        )
        mock_config_logger.info.reset_mock()

        # Integer
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertEqual(
                999, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "count" is not used in variation "variation". Assigning default value "999".'
        )
        mock_config_logger.info.reset_mock()

        # String
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertEqual(
                'devel', opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "environment" is not used in variation "variation". Assigning default value "devel".'
        )
        mock_config_logger.info.reset_mock()

        # JSON
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertEqual(
                {"test": 12}, opt_obj.get_feature_variable_json('test_feature_in_experiment', 'object', 'test_user'),
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "object" is not used in variation "variation". Assigning default value "{"test": 12}".'
        )
        mock_config_logger.info.reset_mock()

        # Non-typed
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertTrue(opt_obj.get_feature_variable('test_feature_in_experiment', 'is_working', 'test_user'))

        mock_config_logger.info.assert_called_once_with(
            'Variable "is_working" is not used in variation "variation". Assigning default value "true".'
        )
        mock_config_logger.info.reset_mock()

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertEqual(
                10.99, opt_obj.get_feature_variable('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "cost" is not used in variation "variation". Assigning default value "10.99".'
        )
        mock_config_logger.info.reset_mock()

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertEqual(
                999, opt_obj.get_feature_variable('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "count" is not used in variation "variation". Assigning default value "999".'
        )
        mock_config_logger.info.reset_mock()

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertEqual(
                'devel', opt_obj.get_feature_variable('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_config_logger.info.assert_called_once_with(
            'Variable "environment" is not used in variation "variation". Assigning default value "devel".'
        )
        mock_config_logger.info.reset_mock()

    def test_get_feature_variable__returns_default_value_if_no_variation(self):
        """ Test that get_feature_variable_* returns default value if no variation \
    and broadcasts decision with proper parameters. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        # Boolean
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(
                opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user')
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "is_working" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'is_working',
                'variable_value': True,
                'variable_type': 'boolean',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        # Double
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                10.99, opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "cost" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'cost',
                'variable_value': 10.99,
                'variable_type': 'double',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        # Integer
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                999, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "count" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'count',
                'variable_value': 999,
                'variable_type': 'integer',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        # String
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                'devel', opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "environment" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'environment',
                'variable_value': 'devel',
                'variable_type': 'string',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        # JSON
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                {"test": 12}, opt_obj.get_feature_variable_json('test_feature_in_experiment', 'object', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "object" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'object',
                'variable_value': {"test": 12},
                'variable_type': 'json',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        # Non-typed
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertTrue(opt_obj.get_feature_variable('test_feature_in_experiment', 'is_working', 'test_user'))

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "is_working" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'is_working',
                'variable_value': True,
                'variable_type': 'boolean',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                10.99, opt_obj.get_feature_variable('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "cost" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'cost',
                'variable_value': 10.99,
                'variable_type': 'double',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                999, opt_obj.get_feature_variable('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "count" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'count',
                'variable_value': 999,
                'variable_type': 'integer',
                'source_info': {},
            },
        )

        mock_client_logger.info.reset_mock()

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(None, None, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision:
            self.assertEqual(
                'devel', opt_obj.get_feature_variable('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'User "test_user" is not in any variation or rollout rule. '
            'Returning default value for variable "environment" of feature flag "test_feature_in_experiment".'
        )

        mock_broadcast_decision.assert_called_once_with(
            enums.NotificationTypes.DECISION,
            'feature-variable',
            'test_user',
            {},
            {
                'feature_key': 'test_feature_in_experiment',
                'feature_enabled': False,
                'source': 'rollout',
                'variable_key': 'environment',
                'variable_value': 'devel',
                'variable_type': 'string',
                'source_info': {},
            },
        )

    def test_get_feature_variable__returns_none_if_none_feature_key(self):
        """ Test that get_feature_variable_* returns None for None feature key. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            # Check for booleans
            self.assertIsNone(opt_obj.get_feature_variable_boolean(None, 'variable_key', 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "feature_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for doubles
            self.assertIsNone(opt_obj.get_feature_variable_double(None, 'variable_key', 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "feature_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for integers
            self.assertIsNone(opt_obj.get_feature_variable_integer(None, 'variable_key', 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "feature_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for strings
            self.assertIsNone(opt_obj.get_feature_variable_string(None, 'variable_key', 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "feature_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for json
            self.assertIsNone(opt_obj.get_feature_variable_json(None, 'variable_key', 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "feature_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for non-typed
            self.assertIsNone(opt_obj.get_feature_variable(None, 'variable_key', 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "feature_key" is in an invalid format.')
            mock_client_logger.reset_mock()

    def test_get_feature_variable__returns_none_if_none_variable_key(self):
        """ Test that get_feature_variable_* returns None for None variable key. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            # Check for booleans
            self.assertIsNone(opt_obj.get_feature_variable_boolean('feature_key', None, 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "variable_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for doubles
            self.assertIsNone(opt_obj.get_feature_variable_double('feature_key', None, 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "variable_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for integers
            self.assertIsNone(opt_obj.get_feature_variable_integer('feature_key', None, 'test_user'))
            mock_client_logger.error.assert_called_with('Provided "variable_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for strings
            self.assertIsNone(opt_obj.get_feature_variable_string('feature_key', None, 'test-User'))
            mock_client_logger.error.assert_called_with('Provided "variable_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for json
            self.assertIsNone(opt_obj.get_feature_variable_json('feature_key', None, 'test-User'))
            mock_client_logger.error.assert_called_with('Provided "variable_key" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for non-typed
            self.assertIsNone(opt_obj.get_feature_variable('feature_key', None, 'test-User'))
            mock_client_logger.error.assert_called_with('Provided "variable_key" is in an invalid format.')
            mock_client_logger.reset_mock()

    def test_get_feature_variable__returns_none_if_none_user_id(self):
        """ Test that get_feature_variable_* returns None for None user ID. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            # Check for booleans
            self.assertIsNone(opt_obj.get_feature_variable_boolean('feature_key', 'variable_key', None))
            mock_client_logger.error.assert_called_with('Provided "user_id" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for doubles
            self.assertIsNone(opt_obj.get_feature_variable_double('feature_key', 'variable_key', None))
            mock_client_logger.error.assert_called_with('Provided "user_id" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for integers
            self.assertIsNone(opt_obj.get_feature_variable_integer('feature_key', 'variable_key', None))
            mock_client_logger.error.assert_called_with('Provided "user_id" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for strings
            self.assertIsNone(opt_obj.get_feature_variable_string('feature_key', 'variable_key', None))
            mock_client_logger.error.assert_called_with('Provided "user_id" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for json
            self.assertIsNone(opt_obj.get_feature_variable_json('feature_key', 'variable_key', None))
            mock_client_logger.error.assert_called_with('Provided "user_id" is in an invalid format.')
            mock_client_logger.reset_mock()

            # Check for non-typed
            self.assertIsNone(opt_obj.get_feature_variable('feature_key', 'variable_key', None))
            mock_client_logger.error.assert_called_with('Provided "user_id" is in an invalid format.')
            mock_client_logger.reset_mock()

    def test_get_feature_variable__invalid_attributes(self):
        """ Test that get_feature_variable_* returns None for invalid attributes. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.are_attributes_valid', return_value=False
        ) as mock_validator:

            # get_feature_variable_boolean
            self.assertIsNone(
                opt_obj.get_feature_variable_boolean(
                    'test_feature_in_experiment', 'is_working', 'test_user', attributes='invalid',
                )
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            # get_feature_variable_double
            self.assertIsNone(
                opt_obj.get_feature_variable_double(
                    'test_feature_in_experiment', 'cost', 'test_user', attributes='invalid',
                )
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            # get_feature_variable_integer
            self.assertIsNone(
                opt_obj.get_feature_variable_integer(
                    'test_feature_in_experiment', 'count', 'test_user', attributes='invalid',
                )
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            # get_feature_variable_string
            self.assertIsNone(
                opt_obj.get_feature_variable_string(
                    'test_feature_in_experiment', 'environment', 'test_user', attributes='invalid',
                )
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            # get_feature_variable_json
            self.assertIsNone(
                opt_obj.get_feature_variable_json(
                    'test_feature_in_experiment', 'object', 'test_user', attributes='invalid',
                )
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            # get_feature_variable
            self.assertIsNone(
                opt_obj.get_feature_variable(
                    'test_feature_in_experiment', 'is_working', 'test_user', attributes='invalid',
                )
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            self.assertIsNone(
                opt_obj.get_feature_variable('test_feature_in_experiment', 'cost', 'test_user', attributes='invalid',)
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            self.assertIsNone(
                opt_obj.get_feature_variable('test_feature_in_experiment', 'count', 'test_user', attributes='invalid',)
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

            self.assertIsNone(
                opt_obj.get_feature_variable(
                    'test_feature_in_experiment', 'environment', 'test_user', attributes='invalid',
                )
            )
            mock_validator.assert_called_once_with('invalid')
            mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
            mock_validator.reset_mock()
            mock_client_logging.reset_mock()

    def test_get_feature_variable__returns_none_if_invalid_feature_key(self):
        """ Test that get_feature_variable_* returns None for invalid feature key. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        with mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertIsNone(opt_obj.get_feature_variable_boolean('invalid_feature', 'is_working', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable_double('invalid_feature', 'cost', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable_integer('invalid_feature', 'count', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable_string('invalid_feature', 'environment', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable_json('invalid_feature', 'object', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable('invalid_feature', 'is_working', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable('invalid_feature', 'cost', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable('invalid_feature', 'count', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable('invalid_feature', 'environment', 'test_user'))
            self.assertIsNone(opt_obj.get_feature_variable('invalid_feature', 'object', 'test_user'))

        self.assertEqual(10, mock_config_logger.error.call_count)
        mock_config_logger.error.assert_has_calls(
            [
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
                mock.call('Feature "invalid_feature" is not in datafile.'),
            ]
        )

    def test_get_feature_variable__returns_none_if_invalid_variable_key(self):
        """ Test that get_feature_variable_* returns None for invalid variable key. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        with mock.patch.object(opt_obj.config_manager.get_config(), 'logger') as mock_config_logger:
            self.assertIsNone(
                opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'invalid_variable', 'test_user')
            )
            self.assertIsNone(
                opt_obj.get_feature_variable_double('test_feature_in_experiment', 'invalid_variable', 'test_user')
            )
            self.assertIsNone(
                opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'invalid_variable', 'test_user')
            )
            self.assertIsNone(
                opt_obj.get_feature_variable_string('test_feature_in_experiment', 'invalid_variable', 'test_user')
            )
            self.assertIsNone(
                opt_obj.get_feature_variable_json('test_feature_in_experiment', 'invalid_variable', 'test_user')
            )
            self.assertIsNone(
                opt_obj.get_feature_variable('test_feature_in_experiment', 'invalid_variable', 'test_user')
            )

        self.assertEqual(6, mock_config_logger.error.call_count)
        mock_config_logger.error.assert_has_calls(
            [
                mock.call('Variable with key "invalid_variable" not found in the datafile.'),
                mock.call('Variable with key "invalid_variable" not found in the datafile.'),
                mock.call('Variable with key "invalid_variable" not found in the datafile.'),
                mock.call('Variable with key "invalid_variable" not found in the datafile.'),
                mock.call('Variable with key "invalid_variable" not found in the datafile.'),
                mock.call('Variable with key "invalid_variable" not found in the datafile.'),
            ]
        )

    def test_get_feature_variable__returns_default_value_if_feature_not_enabled(self):
        """ Test that get_feature_variable_* returns default value if feature is not enabled for the user. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111128')

        # Boolean
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:

            self.assertTrue(
                opt_obj.get_feature_variable_boolean('test_feature_in_experiment', 'is_working', 'test_user')
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "true".'
        )

        # Double
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                10.99, opt_obj.get_feature_variable_double('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "10.99".'
        )

        # Integer
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                999, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "999".'
        )

        # String
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'devel', opt_obj.get_feature_variable_string('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "devel".'
        )

        # JSON
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                {"test": 12}, opt_obj.get_feature_variable_json('test_feature_in_experiment', 'object', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "{"test": 12}".'
        )

        # Non-typed
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:

            self.assertTrue(opt_obj.get_feature_variable('test_feature_in_experiment', 'is_working', 'test_user'))

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "true".'
        )

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                10.99, opt_obj.get_feature_variable('test_feature_in_experiment', 'cost', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "10.99".'
        )

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                999, opt_obj.get_feature_variable('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "999".'
        )

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'devel', opt_obj.get_feature_variable('test_feature_in_experiment', 'environment', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_experiment" for variation "control" is not enabled. '
            'Returning the default variable value "devel".'
        )

    def test_get_feature_variable__returns_default_value_if_feature_not_enabled_in_rollout(self,):
        """ Test that get_feature_variable_* returns default value if feature is not enabled for the user. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('211127')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('211127', '211229')

        # Boolean
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertFalse(opt_obj.get_feature_variable_boolean('test_feature_in_rollout', 'is_running', 'test_user'))

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "false".'
        )

        # Double
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                99.99, opt_obj.get_feature_variable_double('test_feature_in_rollout', 'price', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "99.99".'
        )

        # Integer
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                999, opt_obj.get_feature_variable_integer('test_feature_in_rollout', 'count', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "999".'
        )

        # String
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'Hello', opt_obj.get_feature_variable_string('test_feature_in_rollout', 'message', 'test_user'),
            )
        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "Hello".'
        )

        # JSON
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                {"field": 1}, opt_obj.get_feature_variable_json('test_feature_in_rollout', 'object', 'test_user'),
            )
        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "{"field": 1}".'
        )

        # Non-typed
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertFalse(opt_obj.get_feature_variable('test_feature_in_rollout', 'is_running', 'test_user'))

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "false".'
        )

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                99.99, opt_obj.get_feature_variable('test_feature_in_rollout', 'price', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "99.99".'
        )

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                999, opt_obj.get_feature_variable('test_feature_in_rollout', 'count', 'test_user'),
            )

        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "999".'
        )

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'Hello', opt_obj.get_feature_variable('test_feature_in_rollout', 'message', 'test_user'),
            )
        mock_client_logger.info.assert_called_once_with(
            'Feature "test_feature_in_rollout" for variation "211229" is not enabled. '
            'Returning the default variable value "Hello".'
        )

    def test_get_feature_variable__returns_none_if_type_mismatch(self):
        """ Test that get_feature_variable_* returns None if type mismatch. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            # "is_working" is boolean variable and we are using double method on it.
            self.assertIsNone(
                opt_obj.get_feature_variable_double('test_feature_in_experiment', 'is_working', 'test_user')
            )

        mock_client_logger.warning.assert_called_with(
            'Requested variable type "double", but variable is of type "boolean". '
            'Use correct API to retrieve value. Returning None.'
        )

    def test_get_feature_variable__returns_none_if_unable_to_cast(self):
        """ Test that get_feature_variable_* returns None if unable_to_cast_value """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        mock_experiment = opt_obj.config_manager.get_config().get_experiment_from_key('test_experiment')
        mock_variation = opt_obj.config_manager.get_config().get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.FEATURE_TEST),
        ), mock.patch(
            'optimizely.project_config.ProjectConfig.get_typecast_value', side_effect=ValueError(),
        ), mock.patch.object(
            opt_obj, 'logger'
        ) as mock_client_logger:
            self.assertEqual(
                None, opt_obj.get_feature_variable_integer('test_feature_in_experiment', 'count', 'test_user'),
            )
            self.assertEqual(
                None, opt_obj.get_feature_variable('test_feature_in_experiment', 'count', 'test_user'),
            )

        mock_client_logger.error.assert_called_with('Unable to cast value. Returning None.')

    def test_get_feature_variable_returns__variable_value__typed_audience_match(self):
        """ Test that get_feature_variable_* return variable value with typed audience match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        # Should be included in the feature test via greater-than match audience with id '3468206647'
        with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'xyz', opt_obj.get_feature_variable_string('feat_with_var', 'x', 'user1', {'lasers': 71}),
            )
            mock_client_logger.info.assert_called_once_with(
                'Got variable value "xyz" for variable "x" of feature flag "feat_with_var".'
            )

        with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'xyz', opt_obj.get_feature_variable('feat_with_var', 'x', 'user1', {'lasers': 71}),
            )
            mock_client_logger.info.assert_called_once_with(
                'Got variable value "xyz" for variable "x" of feature flag "feat_with_var".'
            )

        # Should be included in the feature test via exact match boolean audience with id '3468206643'
        with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'xyz', opt_obj.get_feature_variable_string('feat_with_var', 'x', 'user1', {'should_do_it': True}),
            )
            mock_client_logger.info.assert_called_once_with(
                'Got variable value "xyz" for variable "x" of feature flag "feat_with_var".'
            )

        with mock.patch.object(opt_obj, 'logger') as mock_client_logger:
            self.assertEqual(
                'xyz', opt_obj.get_feature_variable('feat_with_var', 'x', 'user1', {'should_do_it': True}),
            )
            mock_client_logger.info.assert_called_once_with(
                'Got variable value "xyz" for variable "x" of feature flag "feat_with_var".'
            )

        """ Test that get_feature_variable_* return default value with typed audience mismatch. """

    def test_get_feature_variable_returns__default_value__typed_audience_match(self):

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        self.assertEqual(
            'x', opt_obj.get_feature_variable_string('feat_with_var', 'x', 'user1', {'lasers': 50}),
        )
        self.assertEqual(
            'x', opt_obj.get_feature_variable('feat_with_var', 'x', 'user1', {'lasers': 50}),
        )

    def test_get_feature_variable_returns__variable_value__complex_audience_match(self):
        """ Test that get_feature_variable_* return variable value with complex audience match. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        # Should be included via exact match string audience with id '3468206642', and
        # greater than audience with id '3468206647'
        user_attr = {'house': 'Gryffindor', 'lasers': 700}
        self.assertEqual(
            150, opt_obj.get_feature_variable_integer('feat2_with_var', 'z', 'user1', user_attr),
        )
        self.assertEqual(150, opt_obj.get_feature_variable('feat2_with_var', 'z', 'user1', user_attr))

    def test_get_feature_variable_returns__default_value__complex_audience_match(self):
        """ Test that get_feature_variable_* return default value with complex audience mismatch. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_typed_audiences))

        # Should be excluded - no audiences match with no attributes
        self.assertEqual(10, opt_obj.get_feature_variable_integer('feat2_with_var', 'z', 'user1', {}))
        self.assertEqual(10, opt_obj.get_feature_variable('feat2_with_var', 'z', 'user1', {}))

    def test_get_optimizely_config__invalid_object(self):
        """ Test that get_optimizely_config logs error if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.get_optimizely_config())

        mock_client_logging.error.assert_called_once_with(
            'Optimizely instance is not valid. Failing "get_optimizely_config".')

    def test_get_optimizely_config__invalid_config(self):
        """ Test that get_optimizely_config logs error if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_datafile')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.get_optimizely_config())

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "get_optimizely_config".'
        )

    def test_get_optimizely_config_returns_instance_of_optimizely_config(self):
        """ Test that get_optimizely_config returns an instance of OptimizelyConfig. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        opt_config = opt_obj.get_optimizely_config()
        self.assertIsInstance(opt_config, optimizely_config.OptimizelyConfig)

    def test_get_optimizely_config_with_custom_config_manager(self):
        """ Test that get_optimizely_config returns a valid instance of OptimizelyConfig
        when a custom config manager is used. """

        some_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        return_config = some_obj.config_manager.get_config()

        class SomeConfigManager(object):
            def get_config(self):
                return return_config

        opt_obj = optimizely.Optimizely(config_manager=SomeConfigManager())
        self.assertIsInstance(
            opt_obj.get_optimizely_config(),
            optimizely_config.OptimizelyConfig
        )

        with mock.patch('optimizely.optimizely_config.OptimizelyConfigService.get_config') as mock_opt_service:
            opt_obj = optimizely.Optimizely(config_manager=SomeConfigManager())
            opt_obj.get_optimizely_config()

        self.assertEqual(1, mock_opt_service.call_count)


class OptimizelyWithExceptionTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self)
        self.optimizely = optimizely.Optimizely(
            json.dumps(self.config_dict), error_handler=error_handler.RaiseExceptionErrorHandler,
        )

    def test_activate__with_attributes__invalid_attributes(self):
        """ Test that activate raises exception if attributes are in invalid format. """

        self.assertRaisesRegexp(
            exceptions.InvalidAttributeException,
            enums.Errors.INVALID_ATTRIBUTE_FORMAT,
            self.optimizely.activate,
            'test_experiment',
            'test_user',
            attributes='invalid',
        )

    def test_track__with_attributes__invalid_attributes(self):
        """ Test that track raises exception if attributes are in invalid format. """

        self.assertRaisesRegexp(
            exceptions.InvalidAttributeException,
            enums.Errors.INVALID_ATTRIBUTE_FORMAT,
            self.optimizely.track,
            'test_event',
            'test_user',
            attributes='invalid',
        )

    def test_track__with_event_tag__invalid_event_tag(self):
        """ Test that track raises exception if event_tag is in invalid format. """

        self.assertRaisesRegexp(
            exceptions.InvalidEventTagException,
            enums.Errors.INVALID_EVENT_TAG_FORMAT,
            self.optimizely.track,
            'test_event',
            'test_user',
            event_tags=4200,
        )

    def test_get_variation__with_attributes__invalid_attributes(self):
        """ Test that get variation raises exception if attributes are in invalid format. """

        self.assertRaisesRegexp(
            exceptions.InvalidAttributeException,
            enums.Errors.INVALID_ATTRIBUTE_FORMAT,
            self.optimizely.get_variation,
            'test_experiment',
            'test_user',
            attributes='invalid',
        )


class OptimizelyWithLoggingTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self)
        self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict), logger=logger.SimpleLogger())
        self.project_config = self.optimizely.config_manager.get_config()

    def test_activate(self):
        """ Test that expected log messages are logged during activate. """

        variation_key = 'variation'
        experiment_key = 'test_experiment'
        user_id = 'test_user'

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('time.time', return_value=42), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ), mock.patch.object(
            self.optimizely, 'logger'
        ) as mock_client_logging:
            self.assertEqual(variation_key, self.optimizely.activate(experiment_key, user_id))

        mock_client_logging.info.assert_called_once_with('Activating user "test_user" in experiment "test_experiment".')

    def test_track(self):
        """ Test that expected log messages are logged during track. """

        user_id = 'test_user'
        event_key = 'test_event'
        mock_client_logger = mock.patch.object(self.optimizely, 'logger')

        event_builder.Event('logx.optimizely.com', {'event_key': event_key})
        with mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ), mock_client_logger as mock_client_logging:
            self.optimizely.track(event_key, user_id)

        mock_client_logging.info.assert_has_calls(
            [mock.call('Tracking event "%s" for user "%s".' % (event_key, user_id))]
        )

    def test_activate__experiment_not_running(self):
        """ Test that expected log messages are logged during activate when experiment is not running. """

        mock_client_logger = mock.patch.object(self.optimizely, 'logger')
        mock_decision_logger = mock.patch.object(self.optimizely.decision_service, 'logger')
        with mock_client_logger as mock_client_logging, mock_decision_logger as mock_decision_logging, mock.patch(
            'optimizely.helpers.experiment.is_experiment_running', return_value=False
        ) as mock_is_experiment_running:
            self.optimizely.activate(
                'test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},
            )

        mock_decision_logging.info.assert_called_once_with('Experiment "test_experiment" is not running.')
        mock_client_logging.info.assert_called_once_with('Not activating user "test_user".')
        mock_is_experiment_running.assert_called_once_with(
            self.project_config.get_experiment_from_key('test_experiment')
        )

    def test_activate__no_audience_match(self):
        """ Test that expected log messages are logged during activate when audience conditions are not met. """

        mock_client_logger = mock.patch.object(self.optimizely, 'logger')
        mock_decision_logger = mock.patch.object(self.optimizely.decision_service, 'logger')

        with mock_decision_logger as mock_decision_logging, mock_client_logger as mock_client_logging:
            self.optimizely.activate(
                'test_experiment', 'test_user', attributes={'test_attribute': 'wrong_test_value'},
            )

        mock_decision_logging.debug.assert_any_call('User "test_user" is not in the forced variation map.')
        mock_decision_logging.info.assert_called_with(
            'User "test_user" does not meet conditions to be in experiment "test_experiment".'
        )
        mock_client_logging.info.assert_called_once_with('Not activating user "test_user".')

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
            mock_client_logging.error.assert_called_once_with('Provided event tags are in an invalid format.')

        with mock_client_logger as mock_client_logging:
            self.optimizely.track('test_event', 'test_user', event_tags=4200)
            mock_client_logging.error.assert_called_once_with('Provided event tags are in an invalid format.')

    def test_get_variation__invalid_attributes(self):
        """ Test that expected log messages are logged during get variation when attributes are in invalid format. """
        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.optimizely.get_variation('test_experiment', 'test_user', attributes='invalid')

        mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')

    def test_get_variation__invalid_experiment_key(self):
        """ Test that None is returned and expected log messages are logged during get_variation \
    when exp_key is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.is_non_empty_string', return_value=False
        ) as mock_validator:
            self.assertIsNone(self.optimizely.get_variation(99, 'test_user'))

        mock_validator.assert_any_call(99)
        mock_client_logging.error.assert_called_once_with('Provided "experiment_key" is in an invalid format.')

    def test_get_variation__invalid_user_id(self):
        """ Test that None is returned and expected log messages are logged during get_variation \
    when user_id is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.assertIsNone(self.optimizely.get_variation('test_experiment', 99))
        mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

    def test_activate__invalid_experiment_key(self):
        """ Test that None is returned and expected log messages are logged during activate \
    when exp_key is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.is_non_empty_string', return_value=False
        ) as mock_validator:
            self.assertIsNone(self.optimizely.activate(99, 'test_user'))

        mock_validator.assert_any_call(99)

        mock_client_logging.error.assert_called_once_with('Provided "experiment_key" is in an invalid format.')

    def test_activate__invalid_user_id(self):
        """ Test that None is returned and expected log messages are logged during activate \
    when user_id is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.assertIsNone(self.optimizely.activate('test_experiment', 99))

        mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

    def test_activate__empty_user_id(self):
        """ Test that expected log messages are logged during activate. """

        variation_key = 'variation'
        experiment_key = 'test_experiment'
        user_id = ''

        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation',
            return_value=self.project_config.get_variation_from_id('test_experiment', '111129'),
        ), mock.patch('time.time', return_value=42), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ), mock.patch.object(
            self.optimizely, 'logger'
        ) as mock_client_logging:
            self.assertEqual(variation_key, self.optimizely.activate(experiment_key, user_id))

        mock_client_logging.info.assert_called_once_with('Activating user "" in experiment "test_experiment".')

    def test_activate__invalid_attributes(self):
        """ Test that expected log messages are logged during activate when attributes are in invalid format. """
        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.optimizely.activate('test_experiment', 'test_user', attributes='invalid')

        mock_client_logging.error.assert_called_once_with('Provided attributes are in an invalid format.')
        mock_client_logging.info.assert_called_once_with('Not activating user "test_user".')

    def test_get_variation__experiment_not_running(self):
        """ Test that expected log messages are logged during get variation when experiment is not running. """

        with mock.patch.object(self.optimizely.decision_service, 'logger') as mock_decision_logging, mock.patch(
            'optimizely.helpers.experiment.is_experiment_running', return_value=False
        ) as mock_is_experiment_running:
            self.optimizely.get_variation(
                'test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},
            )

        mock_decision_logging.info.assert_called_once_with('Experiment "test_experiment" is not running.')
        mock_is_experiment_running.assert_called_once_with(
            self.project_config.get_experiment_from_key('test_experiment')
        )

    def test_get_variation__no_audience_match(self):
        """ Test that expected log messages are logged during get variation when audience conditions are not met. """

        experiment_key = 'test_experiment'
        user_id = 'test_user'

        mock_decision_logger = mock.patch.object(self.optimizely.decision_service, 'logger')
        with mock_decision_logger as mock_decision_logging:
            self.optimizely.get_variation(
                experiment_key, user_id, attributes={'test_attribute': 'wrong_test_value'},
            )

        mock_decision_logging.debug.assert_any_call('User "test_user" is not in the forced variation map.')
        mock_decision_logging.info.assert_called_with(
            'User "test_user" does not meet conditions to be in experiment "test_experiment".'
        )

    def test_get_variation__forced_bucketing(self):
        """ Test that the expected forced variation is called for a valid experiment and attributes """

        self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
        self.assertEqual(
            'variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'),
        )
        variation_key = self.optimizely.get_variation(
            'test_experiment', 'test_user', attributes={'test_attribute': 'test_value'}
        )
        self.assertEqual('variation', variation_key)

    def test_get_variation__experiment_not_running__forced_bucketing(self):
        """ Test that the expected forced variation is called if an experiment is not running """

        with mock.patch(
            'optimizely.helpers.experiment.is_experiment_running', return_value=False
        ) as mock_is_experiment_running:
            self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation')
            self.assertEqual(
                'variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'),
            )
            variation_key = self.optimizely.get_variation(
                'test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},
            )
            self.assertIsNone(variation_key)
            mock_is_experiment_running.assert_called_once_with(
                self.project_config.get_experiment_from_key('test_experiment')
            )

    def test_get_variation__whitelisted_user_forced_bucketing(self):
        """ Test that the expected forced variation is called if a user is whitelisted """

        self.assertTrue(self.optimizely.set_forced_variation('group_exp_1', 'user_1', 'group_exp_1_variation'))
        forced_variation = self.optimizely.get_forced_variation('group_exp_1', 'user_1')
        self.assertEqual('group_exp_1_variation', forced_variation)
        variation_key = self.optimizely.get_variation(
            'group_exp_1', 'user_1', attributes={'test_attribute': 'test_value'}
        )
        self.assertEqual('group_exp_1_variation', variation_key)

    def test_get_variation__user_profile__forced_bucketing(self):
        """ Test that the expected forced variation is called if a user profile exists """
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_stored_variation',
            return_value=entities.Variation('111128', 'control'),
        ):
            self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
            self.assertEqual(
                'variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'),
            )
            variation_key = self.optimizely.get_variation(
                'test_experiment', 'test_user', attributes={'test_attribute': 'test_value'},
            )
            self.assertEqual('variation', variation_key)

    def test_get_variation__invalid_attributes__forced_bucketing(self):
        """ Test that the expected forced variation is called if the user does not pass audience evaluation """

        self.assertTrue(self.optimizely.set_forced_variation('test_experiment', 'test_user', 'variation'))
        self.assertEqual(
            'variation', self.optimizely.get_forced_variation('test_experiment', 'test_user'),
        )
        variation_key = self.optimizely.get_variation(
            'test_experiment', 'test_user', attributes={'test_attribute': 'test_value_invalid'},
        )
        self.assertEqual('variation', variation_key)

    def test_set_forced_variation__invalid_object(self):
        """ Test that set_forced_variation logs error if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertFalse(opt_obj.set_forced_variation('test_experiment', 'test_user', 'test_variation'))

        mock_client_logging.error.assert_called_once_with(
            'Optimizely instance is not valid. ' 'Failing "set_forced_variation".'
        )

    def test_set_forced_variation__invalid_config(self):
        """ Test that set_forced_variation logs error if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_datafile')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertFalse(opt_obj.set_forced_variation('test_experiment', 'test_user', 'test_variation'))

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "set_forced_variation".'
        )

    def test_set_forced_variation__invalid_experiment_key(self):
        """ Test that None is returned and expected log messages are logged during set_forced_variation \
    when exp_key is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.is_non_empty_string', return_value=False
        ) as mock_validator:
            self.assertFalse(self.optimizely.set_forced_variation(99, 'test_user', 'variation'))

        mock_validator.assert_any_call(99)

        mock_client_logging.error.assert_called_once_with('Provided "experiment_key" is in an invalid format.')

    def test_set_forced_variation__invalid_user_id(self):
        """ Test that None is returned and expected log messages are logged during set_forced_variation \
    when user_id is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.assertFalse(self.optimizely.set_forced_variation('test_experiment', 99, 'variation'))
        mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')

    def test_get_forced_variation__invalid_object(self):
        """ Test that get_forced_variation logs error if Optimizely instance is invalid. """

        class InvalidConfigManager(object):
            pass

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict), config_manager=InvalidConfigManager())

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.get_forced_variation('test_experiment', 'test_user'))

        mock_client_logging.error.assert_called_once_with(
            'Optimizely instance is not valid. ' 'Failing "get_forced_variation".'
        )

    def test_get_forced_variation__invalid_config(self):
        """ Test that get_forced_variation logs error if config is invalid. """

        opt_obj = optimizely.Optimizely('invalid_datafile')

        with mock.patch.object(opt_obj, 'logger') as mock_client_logging:
            self.assertIsNone(opt_obj.get_forced_variation('test_experiment', 'test_user'))

        mock_client_logging.error.assert_called_once_with(
            'Invalid config. Optimizely instance is not valid. ' 'Failing "get_forced_variation".'
        )

    def test_get_forced_variation__invalid_experiment_key(self):
        """ Test that None is returned and expected log messages are logged during get_forced_variation \
    when exp_key is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, mock.patch(
            'optimizely.helpers.validator.is_non_empty_string', return_value=False
        ) as mock_validator:
            self.assertIsNone(self.optimizely.get_forced_variation(99, 'test_user'))

        mock_validator.assert_any_call(99)

        mock_client_logging.error.assert_called_once_with('Provided "experiment_key" is in an invalid format.')

    def test_get_forced_variation__invalid_user_id(self):
        """ Test that None is returned and expected log messages are logged during get_forced_variation \
    when user_id is in invalid format. """

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging:
            self.assertIsNone(self.optimizely.get_forced_variation('test_experiment', 99))

        mock_client_logging.error.assert_called_once_with('Provided "user_id" is in an invalid format.')
