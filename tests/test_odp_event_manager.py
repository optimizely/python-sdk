# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
from unittest import mock
from copy import deepcopy
import uuid

from optimizely.odp.odp_event import OdpEvent
from optimizely.odp.odp_event_manager import OdpEventManager
from optimizely.odp.odp_config import OdpConfig
from .base import BaseTest, CopyingMock
from optimizely.version import __version__


class MockOdpEventManager(OdpEventManager):
    def _add_to_batch(self, *args):
        raise Exception("Unexpected error")


class OdpEventManagerTest(BaseTest):
    user_key = "vuid"
    user_value = "test-user-value"
    api_key = "test-api-key"
    api_host = "https://test-host.com"
    test_uuid = str(uuid.uuid4())
    odp_config = OdpConfig(api_key, api_host)

    events = [
        {
            "type": "t1",
            "action": "a1",
            "identifiers": {"id-key-1": "id-value-1"},
            "data": {"key-1": "value1", "key-2": 2, "key-3": 3.0, "key-4": None}
        },
        {
            "type": "t2",
            "action": "a2",
            "identifiers": {"id-key-2": "id-value-2"},
            "data": {"key-2": "value2"}
        }
    ]

    processed_events = [
        {
            "type": "t1",
            "action": "a1",
            "identifiers": {"id-key-1": "id-value-1"},
            "data": {
                "idempotence_id": test_uuid,
                "data_source_type": "sdk",
                "data_source": "python-sdk",
                "data_source_version": __version__,
                "key-1": "value1",
                "key-2": 2,
                "key-3": 3.0,
                "key-4": None
            }
        },
        {
            "type": "t2",
            "action": "a2",
            "identifiers": {"id-key-2": "id-value-2"},
            "data": {
                "idempotence_id": test_uuid,
                "data_source_type": "sdk",
                "data_source": "python-sdk",
                "data_source_version": __version__,
                "key-2": "value2"
            }
        }
    ]

    def test_odp_event_init(self):
        with mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event = OdpEvent(**self.events[0])
        self.assertEqual(event, self.processed_events[0])

    def test_invalid_odp_event(self):
        event = deepcopy(self.events[0])
        event['data']['invalid-item'] = {}
        with self.assertRaises(TypeError):
            OdpEvent(**event)

    def test_odp_event_manager_success(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        with mock.patch('requests.post', return_value=self.fake_server_response(status_code=200)):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.stop()

        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_any_call('Flushing batch size 2.')
        mock_logger.debug.assert_any_call('Received ODP event shutdown signal.')
        self.assertStrictFalse(event_manager.is_running)

    def test_odp_event_manager_batch(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        event_manager.batch_size = 2
        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.event_queue.join()

        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events)
        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_any_call('Flushing ODP events on batch size.')
        event_manager.stop()

    def test_odp_event_manager_multiple_batches(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        event_manager.batch_size = 2
        batch_count = 4

        with mock.patch.object(
            event_manager.zaius_manager,
            'send_odp_events',
            new_callable=CopyingMock,
            return_value=False
        ) as mock_send, mock.patch(
            'uuid.uuid4',
            return_value=self.test_uuid
        ):
            for _ in range(batch_count):
                event_manager.send_event(**self.events[0])
                event_manager.send_event(**self.events[1])
            event_manager.event_queue.join()

        self.assertEqual(mock_send.call_count, batch_count)
        mock_send.assert_has_calls(
            [mock.call(self.api_key, self.api_host, self.processed_events)] * batch_count
        )

        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_has_calls([
            mock.call('Flushing ODP events on batch size.'),
            mock.call('Flushing batch size 2.')
        ] * batch_count, any_order=True)
        event_manager.stop()

    def test_odp_event_manager_flush(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()
            event_manager.event_queue.join()

        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events)
        mock_logger.error.assert_not_called()
        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.debug.assert_any_call('Received ODP event flush signal.')
        event_manager.stop()

    def test_odp_event_manager_multiple_flushes(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()
        flush_count = 4

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            for _ in range(flush_count):
                event_manager.send_event(**self.events[0])
                event_manager.send_event(**self.events[1])
                event_manager.flush()
            event_manager.event_queue.join()

        self.assertEqual(mock_send.call_count, flush_count)
        for call in mock_send.call_args_list:
            self.assertEqual(call, mock.call(self.api_key, self.api_host, self.processed_events))
        mock_logger.error.assert_not_called()

        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.debug.assert_has_calls([
            mock.call('Received ODP event flush signal.'),
            mock.call('Flushing batch size 2.')
        ] * flush_count, any_order=True)
        event_manager.stop()

    def test_odp_event_manager_network_failure(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', return_value=True
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()
            event_manager.event_queue.join()

        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events)
        self.assertEqual(len(event_manager._current_batch), 2)
        mock_logger.debug.assert_any_call('Error dispatching ODP events, scheduled to retry.')
        self.assertStrictTrue(event_manager.is_running)
        event_manager.stop()

    def test_odp_event_manager_retry(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=True
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()
            event_manager.event_queue.join()

        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events)
        self.assertEqual(len(event_manager._current_batch), 2)
        mock_logger.debug.assert_any_call('Error dispatching ODP events, scheduled to retry.')

        mock_logger.reset_mock()

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send:
            event_manager.stop()

        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events)
        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_not_called()

    def test_odp_event_manager_send_failure(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        with mock.patch.object(
            event_manager.zaius_manager,
            'send_odp_events',
            new_callable=CopyingMock,
            side_effect=Exception('Unexpected error')
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()
            event_manager.event_queue.join()

        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events)
        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_any_call(f"ODP event send failed ({self.processed_events} Unexpected error).")
        self.assertStrictTrue(event_manager.is_running)
        event_manager.stop()

    def test_odp_event_manager_disabled(self):
        mock_logger = mock.Mock()
        odp_config = OdpConfig()
        odp_config.update(None, None, None)
        event_manager = OdpEventManager(odp_config, mock_logger)
        event_manager.start()

        event_manager.send_event(**self.events[0])
        event_manager.send_event(**self.events[1])
        event_manager.event_queue.join()

        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_any_call('ODP event queue has been disabled.')
        self.assertStrictTrue(event_manager.is_running)
        event_manager.stop()

    def test_odp_event_manager_queue_full(self):
        mock_logger = mock.Mock()

        with mock.patch('optimizely.helpers.enums.OdpEventManagerConfig.DEFAULT_QUEUE_CAPACITY', 1):
            event_manager = OdpEventManager(self.odp_config, mock_logger)

        with mock.patch('optimizely.odp.odp_event_manager.OdpEventManager.is_running', True):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])

        mock_logger.warning.assert_called_once_with('ODP event send failed (Queue is full).')
        mock_logger.error.assert_not_called()

    def test_odp_event_manager_thread_exception(self):
        mock_logger = mock.Mock()
        event_manager = MockOdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        event_manager.send_event(**self.events[0])
        time.sleep(.1)
        event_manager.send_event(**self.events[0])

        event_manager.thread.join()
        mock_logger.error.assert_has_calls([
            mock.call('Uncaught exception processing ODP events. Error: Unexpected error'),
            mock.call('ODP event send failed (Queue is down).')
        ])

    def test_odp_event_manager_invalid_data_type(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        event = deepcopy(self.events[0])
        event['data']['invalid-item'] = {}

        event_manager.send_event(**event)
        event_manager.stop()

        mock_logger.error.assert_called_once_with(
            'ODP event send failed (ODP event data values can only be str, int, float and None).'
        )

    def test_odp_event_manager_override_default_data(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        event = deepcopy(self.events[0])
        event['data']['data_source'] = 'my-app'

        processed_event = deepcopy(self.processed_events[0])
        processed_event['data']['data_source'] = 'my-app'

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**event)
            event_manager.flush()
            event_manager.event_queue.join()

        mock_send.assert_called_once_with(self.api_key, self.api_host, [processed_event])

    def test_odp_event_manager_flush_timeout(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.flush_interval = .5
        event_manager._set_flush_deadline()
        event_manager.start()

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            time.sleep(1)
            event_manager.stop()

        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_any_call('Flushing on interval.')
        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events)
        event_manager.stop()

    def test_odp_event_manager_events_before_odp_ready(self):
        mock_logger = mock.Mock()
        odp_config = OdpConfig()
        event_manager = OdpEventManager(odp_config, mock_logger)
        event_manager.start()

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])

            odp_config.update(self.api_key, self.api_host, [])
            event_manager.event_queue.join()

            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()

            event_manager.event_queue.join()

        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_has_calls([
            mock.call('Adding ODP event to queue.'),
            mock.call('Adding ODP event to queue.'),
            mock.call('ODP ready. Starting event processing.'),
            mock.call('Adding ODP event to queue.'),
            mock.call('Adding ODP event to queue.'),
            mock.call('Received ODP event flush signal.'),
            mock.call('Flushing batch size 4.')
        ])
        mock_send.assert_called_once_with(self.api_key, self.api_host, self.processed_events * 2)
        event_manager.stop()

    def test_odp_event_manager_events_before_odp_disabled(self):
        mock_logger = mock.Mock()
        odp_config = OdpConfig()
        event_manager = OdpEventManager(odp_config, mock_logger)
        event_manager.start()

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])

            odp_config.update(None, None, [])
            event_manager.event_queue.join()

            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()

            event_manager.event_queue.join()

        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_has_calls([
            mock.call('Adding ODP event to queue.'),
            mock.call('Adding ODP event to queue.'),
            mock.call('ODP ready. Starting event processing.'),
            mock.call('ODP event queue has been disabled.'),
            mock.call('ODP event queue has been disabled.'),
            mock.call('Received ODP event flush signal.'),
            mock.call('ODP event queue has been disabled.')
        ])
        self.assertEqual(len(event_manager._current_batch), 0)
        mock_send.assert_not_called()
        event_manager.stop()
