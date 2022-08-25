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

import queue
from unittest import mock
import uuid

from optimizely.odp.odp_event import OdpEvent
from optimizely.odp.odp_event_manager import OdpEventManager
from optimizely.odp.odp_config import OdpConfig
from .base import BaseTest, CopyingMock
from optimizely.version import __version__


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
            "data": {"key-1": "value1"}
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
                "key-1": "value1"
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
        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.event_queue.join()

        self.assertEqual(mock_send.call_count, 2)
        for call in mock_send.call_args_list:
            self.assertEqual(call[0], (self.api_key, self.api_host, self.processed_events))

        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_any_call('Flushing ODP events on batch size.')
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

        with mock.patch.object(
            event_manager.zaius_manager, 'send_odp_events', new_callable=CopyingMock, return_value=False
        ) as mock_send, mock.patch('uuid.uuid4', return_value=self.test_uuid):
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()
            event_manager.send_event(**self.events[0])
            event_manager.send_event(**self.events[1])
            event_manager.flush()
            event_manager.event_queue.join()

        self.assertEqual(mock_send.call_count, 2)
        for call in mock_send.call_args_list:
            self.assertEqual(call[0], (self.api_key, self.api_host, self.processed_events))
        mock_logger.error.assert_not_called()
        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.debug.assert_any_call('Received ODP event flush signal.')
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
        event_manager = OdpEventManager(OdpConfig(), mock_logger)
        event_manager.start()

        event_manager.send_event(**self.events[0])
        event_manager.send_event(**self.events[1])
        event_manager.event_queue.join()

        self.assertEqual(len(event_manager._current_batch), 0)
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_any_call('ODP event processing has been disabled.')
        self.assertStrictTrue(event_manager.is_running)
        event_manager.stop()

    def test_odp_event_manager_queue_full(self):
        mock_logger = mock.Mock()
        event_manager = OdpEventManager(self.odp_config, mock_logger)
        event_manager.start()

        with mock.patch.object(event_manager.event_queue, 'put_nowait', side_effect=queue.Full):
            event_manager.send_event(**self.events[0])

        mock_logger.error.assert_any_call('ODP event send failed (Queue is full).')
        self.assertStrictTrue(event_manager.is_running)
        event_manager.stop()
