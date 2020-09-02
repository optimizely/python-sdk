# Copyright 2019-2020, Optimizely
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

import datetime
import mock
import time
from six.moves import queue

from optimizely.event.payload import Decision, Visitor
from optimizely.event.event_processor import (
    BatchEventProcessor,
    ForwardingEventProcessor,
)
from optimizely.event.event_factory import EventFactory
from optimizely.event.log_event import LogEvent
from optimizely.event.user_event_factory import UserEventFactory
from optimizely.event_dispatcher import EventDispatcher as default_event_dispatcher
from optimizely.helpers import enums
from optimizely.logger import NoOpLogger
from . import base


class CanonicalEvent(object):
    def __init__(self, experiment_id, variation_id, event_name, visitor_id, attributes, tags):
        self._experiment_id = experiment_id
        self._variation_id = variation_id
        self._event_name = event_name
        self._visitor_id = visitor_id
        self._attributes = attributes or {}
        self._tags = tags or {}

    def __eq__(self, other):
        if other is None:
            return False

        return self.__dict__ == other.__dict__


class CustomEventDispatcher(object):

    IMPRESSION_EVENT_NAME = 'campaign_activated'

    def __init__(self, countdown_event=None):
        self.countdown_event = countdown_event
        self.expected_events = list()
        self.actual_events = list()

    def compare_events(self):
        if len(self.expected_events) != len(self.actual_events):
            return False

        for index, event in enumerate(self.expected_events):
            expected_event = event
            actual_event = self.actual_events[index]

            if not expected_event == actual_event:
                return False

        return True

    def dispatch_event(self, actual_log_event):
        visitors = []
        log_event_params = actual_log_event.params

        if 'visitors' in log_event_params:

            for visitor in log_event_params['visitors']:
                visitor_instance = Visitor(**visitor)
                visitors.append(visitor_instance)

        if len(visitors) == 0:
            return

        for visitor in visitors:
            for snapshot in visitor.snapshots:
                decisions = snapshot.get('decisions') or [Decision(None, None, None)]
                for decision in decisions:
                    for event in snapshot.get('events'):
                        attributes = visitor.attributes

                        self.actual_events.append(
                            CanonicalEvent(
                                decision.experiment_id,
                                decision.variation_id,
                                event.get('key'),
                                visitor.visitor_id,
                                attributes,
                                event.get('event_tags'),
                            )
                        )

    def expect_impression(self, experiment_id, variation_id, user_id, attributes=None):
        self._expect(experiment_id, variation_id, self.IMPRESSION_EVENT_NAME, user_id, None)

    def expect_conversion(self, event_name, user_id, attributes=None, event_tags=None):
        self._expect(None, None, event_name, user_id, attributes, event_tags)

    def _expect(self, experiment_id, variation_id, event_name, visitor_id, attributes, tags):
        expected_event = CanonicalEvent(experiment_id, variation_id, event_name, visitor_id, attributes, tags)
        self.expected_events.append(expected_event)


class BatchEventProcessorTest(base.BaseTest):

    DEFAULT_QUEUE_CAPACITY = 1000
    MAX_BATCH_SIZE = 10
    MAX_DURATION_SEC = 0.2
    MAX_TIMEOUT_INTERVAL_SEC = 0.1
    TEST_TIMEOUT = 0.3

    def setUp(self, *args, **kwargs):
        base.BaseTest.setUp(self, 'config_dict_with_multiple_experiments')
        self.test_user_id = 'test_user'
        self.event_name = 'test_event'
        self.event_queue = queue.Queue(maxsize=self.DEFAULT_QUEUE_CAPACITY)
        self.optimizely.logger = NoOpLogger()
        self.notification_center = self.optimizely.notification_center

    def tearDown(self):
        self.event_processor.stop()

    def _build_conversion_event(self, event_name, project_config=None):
        config = project_config or self.project_config
        return UserEventFactory.create_conversion_event(config, event_name, self.test_user_id, {}, {})

    def _set_event_processor(self, event_dispatcher, logger):
        self.event_processor = BatchEventProcessor(
            event_dispatcher,
            logger,
            True,
            self.event_queue,
            self.MAX_BATCH_SIZE,
            self.MAX_DURATION_SEC,
            self.MAX_TIMEOUT_INTERVAL_SEC,
            self.optimizely.notification_center,
        )

    def test_drain_on_stop(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        user_event = self._build_conversion_event(self.event_name)
        self.event_processor.process(user_event)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.assertEqual(0, self.event_processor.event_queue.qsize())

    def test_flush_on_max_timeout(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        user_event = self._build_conversion_event(self.event_name)
        self.event_processor.process(user_event)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.assertEqual(0, self.event_processor.event_queue.qsize())

    def test_flush_once_max_timeout(self):
        event_dispatcher = CustomEventDispatcher()

        self.optimizely.logger = NoOpLogger()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        user_event = self._build_conversion_event(self.event_name)
        self.event_processor.process(user_event)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.assertEqual(0, self.event_processor.event_queue.qsize())
        self.assertTrue(mock_config_logging.debug.called)
        mock_config_logging.debug.assert_any_call('Received event of type ConversionEvent for user test_user.')
        mock_config_logging.debug.assert_any_call('Flushing batch size 1')
        mock_config_logging.debug.assert_any_call('Flush interval deadline. Flushed batch.')
        self.assertTrue(mock_config_logging.debug.call_count == 3)
        self.optimizely.logger = NoOpLogger()

    def test_flush_max_batch_size(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        for i in range(0, self.MAX_BATCH_SIZE):
            user_event = self._build_conversion_event(self.event_name)
            self.event_processor.process(user_event)
            event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.assertEqual(0, self.event_processor.event_queue.qsize())

    def test_flush(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        user_event = self._build_conversion_event(self.event_name)
        self.event_processor.process(user_event)
        self.event_processor.flush()
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        self.event_processor.process(user_event)
        self.event_processor.flush()
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.assertEqual(0, self.event_processor.event_queue.qsize())

    def test_flush_on_mismatch_revision(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        self.project_config.revision = 1
        self.project_config.project_id = 'X'

        user_event_1 = self._build_conversion_event(self.event_name, self.project_config)
        self.event_processor.process(user_event_1)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        self.project_config.revision = 2
        self.project_config.project_id = 'X'

        user_event_2 = self._build_conversion_event(self.event_name, self.project_config)
        self.event_processor.process(user_event_2)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.assertEqual(0, self.event_processor.event_queue.qsize())

    def test_flush_on_mismatch_project_id(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        self.project_config.revision = 1
        self.project_config.project_id = 'X'

        user_event_1 = self._build_conversion_event(self.event_name, self.project_config)
        self.event_processor.process(user_event_1)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        self.project_config.revision = 1
        self.project_config.project_id = 'Y'

        user_event_2 = self._build_conversion_event(self.event_name, self.project_config)
        self.event_processor.process(user_event_2)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.assertEqual(0, self.event_processor.event_queue.qsize())

    def test_stop_and_start(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(event_dispatcher, mock_config_logging)

        user_event = self._build_conversion_event(self.event_name, self.project_config)
        self.event_processor.process(user_event)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        time.sleep(self.TEST_TIMEOUT)

        self.assertStrictTrue(event_dispatcher.compare_events())
        self.event_processor.stop()

        self.event_processor.process(user_event)
        event_dispatcher.expect_conversion(self.event_name, self.test_user_id)

        self.event_processor.start()
        self.assertStrictTrue(self.event_processor.is_running)

        self.event_processor.stop()
        self.assertStrictFalse(self.event_processor.is_running)

        self.assertEqual(0, self.event_processor.event_queue.qsize())

    def test_init__invalid_batch_size(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                self.optimizely.logger,
                True,
                self.event_queue,
                5.5,
                self.MAX_DURATION_SEC,
                self.MAX_TIMEOUT_INTERVAL_SEC,
            )

        # default batch size is 10.
        self.assertEqual(10, self.event_processor.batch_size)
        mock_config_logging.info.assert_called_with('Using default value 10 for batch_size.')

    def test_init__NaN_batch_size(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                self.optimizely.logger,
                True,
                self.event_queue,
                'batch_size',
                self.MAX_DURATION_SEC,
                self.MAX_TIMEOUT_INTERVAL_SEC,
            )

        # default batch size is 10.
        self.assertEqual(10, self.event_processor.batch_size)
        mock_config_logging.info.assert_called_with('Using default value 10 for batch_size.')

    def test_init__invalid_flush_interval(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                mock_config_logging,
                True,
                self.event_queue,
                self.MAX_BATCH_SIZE,
                0,
                self.MAX_TIMEOUT_INTERVAL_SEC,
            )

        # default flush interval is 30s.
        self.assertEqual(datetime.timedelta(seconds=30), self.event_processor.flush_interval)
        mock_config_logging.info.assert_called_with('Using default value 30 for flush_interval.')

    def test_init__float_flush_interval(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                mock_config_logging,
                True,
                self.event_queue,
                self.MAX_BATCH_SIZE,
                0.5,
                self.MAX_TIMEOUT_INTERVAL_SEC,
            )

        # default flush interval is 30s.
        self.assertEqual(datetime.timedelta(seconds=0.5), self.event_processor.flush_interval)

    def test_init__float_flush_deadline(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                mock_config_logging,
                True,
                self.event_queue,
                self.MAX_BATCH_SIZE,
                0.5,
                self.MAX_TIMEOUT_INTERVAL_SEC,
            )

        # default flush interval is 30s.
        self.assertTrue(isinstance(self.event_processor.flushing_interval_deadline, float))

    def test_init__bool_flush_interval(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                self.optimizely.logger,
                True,
                self.event_queue,
                self.MAX_BATCH_SIZE,
                True,
                self.MAX_TIMEOUT_INTERVAL_SEC,
            )

        # default flush interval is 30s.
        self.assertEqual(datetime.timedelta(seconds=30), self.event_processor.flush_interval)
        mock_config_logging.info.assert_called_with('Using default value 30 for flush_interval.')

    def test_init__string_flush_interval(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                self.optimizely.logger,
                True,
                self.event_queue,
                self.MAX_BATCH_SIZE,
                'True',
                self.MAX_TIMEOUT_INTERVAL_SEC,
            )

        # default flush interval is 30s.
        self.assertEqual(datetime.timedelta(seconds=30), self.event_processor.flush_interval)
        mock_config_logging.info.assert_called_with('Using default value 30 for flush_interval.')

    def test_init__invalid_timeout_interval(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                self.optimizely.logger,
                True,
                self.event_queue,
                self.MAX_BATCH_SIZE,
                self.MAX_DURATION_SEC,
                -100,
            )

        # default timeout interval is 5s.
        self.assertEqual(datetime.timedelta(seconds=5), self.event_processor.timeout_interval)
        mock_config_logging.info.assert_called_with('Using default value 5 for timeout_interval.')

    def test_init__NaN_timeout_interval(self):
        event_dispatcher = CustomEventDispatcher()

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = BatchEventProcessor(
                event_dispatcher,
                self.optimizely.logger,
                True,
                self.event_queue,
                self.MAX_BATCH_SIZE,
                self.MAX_DURATION_SEC,
                False,
            )

        # default timeout interval is 5s.
        self.assertEqual(datetime.timedelta(seconds=5), self.event_processor.timeout_interval)
        mock_config_logging.info.assert_called_with('Using default value 5 for timeout_interval.')

    def test_notification_center__on_log_event(self):

        mock_event_dispatcher = mock.Mock()
        callback_hit = [False]

        def on_log_event(log_event):
            self.assertStrictTrue(isinstance(log_event, LogEvent))
            callback_hit[0] = True

        self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.LOG_EVENT, on_log_event)

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self._set_event_processor(mock_event_dispatcher, mock_config_logging)

        user_event = self._build_conversion_event(self.event_name, self.project_config)
        self.event_processor.process(user_event)

        self.event_processor.stop()

        self.assertEqual(True, callback_hit[0])
        self.assertEqual(
            1, len(self.optimizely.notification_center.notification_listeners[enums.NotificationTypes.LOG_EVENT]),
        )


class CustomForwardingEventDispatcher(object):
    def __init__(self, is_updated=False):
        self.is_updated = is_updated

    def dispatch_event(self, log_event):
        if log_event.http_verb == 'POST' and log_event.url == EventFactory.EVENT_ENDPOINT:
            self.is_updated = True
        return self.is_updated


class ForwardingEventProcessorTest(base.BaseTest):
    def setUp(self, *args, **kwargs):
        base.BaseTest.setUp(self, 'config_dict_with_multiple_experiments')
        self.test_user_id = 'test_user'
        self.event_name = 'test_event'
        self.optimizely.logger = NoOpLogger()
        self.notification_center = self.optimizely.notification_center
        self.event_dispatcher = CustomForwardingEventDispatcher(is_updated=False)

        with mock.patch.object(self.optimizely, 'logger') as mock_config_logging:
            self.event_processor = ForwardingEventProcessor(
                self.event_dispatcher, mock_config_logging, self.notification_center
            )

    def _build_conversion_event(self, event_name):
        return UserEventFactory.create_conversion_event(self.project_config, event_name, self.test_user_id, {}, {})

    def test_event_processor__dispatch_raises_exception(self):
        """ Test that process logs dispatch failure gracefully. """

        user_event = self._build_conversion_event(self.event_name)
        log_event = EventFactory.create_log_event(user_event, self.optimizely.logger)

        with mock.patch.object(self.optimizely, 'logger') as mock_client_logging, mock.patch.object(
            self.event_dispatcher, 'dispatch_event', side_effect=Exception('Failed to send.'),
        ):

            event_processor = ForwardingEventProcessor(
                self.event_dispatcher, mock_client_logging, self.notification_center
            )
            event_processor.process(user_event)

        mock_client_logging.exception.assert_called_once_with(
            'Error dispatching event: ' + str(log_event) + ' Failed to send.'
        )

    def test_event_processor__with_test_event_dispatcher(self):
        user_event = self._build_conversion_event(self.event_name)
        self.event_processor.process(user_event)
        self.assertStrictTrue(self.event_dispatcher.is_updated)

    def test_notification_center(self):

        callback_hit = [False]

        def on_log_event(log_event):
            self.assertStrictTrue(isinstance(log_event, LogEvent))
            callback_hit[0] = True

        self.optimizely.notification_center.add_notification_listener(enums.NotificationTypes.LOG_EVENT, on_log_event)

        user_event = self._build_conversion_event(self.event_name)
        self.event_processor.process(user_event)

        self.assertEqual(True, callback_hit[0])
        self.assertEqual(
            1, len(self.optimizely.notification_center.notification_listeners[enums.NotificationTypes.LOG_EVENT]),
        )

    def test_event_processor_defaults_to_default_event_dispatcher(self):
        event_processor = ForwardingEventProcessor(None)
        self.assertEqual(
            event_processor.event_dispatcher,
            default_event_dispatcher
        )
