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

from __future__ import annotations

from unittest import mock

from optimizely import exceptions as optimizely_exception
from optimizely.helpers.enums import Errors
from optimizely.odp.lru_cache import LRUCache
from optimizely.odp.odp_config import OdpConfig
from optimizely.odp.odp_event_manager import OdpEventManager
from optimizely.odp.odp_manager import OdpManager
from optimizely.odp.odp_segment_manager import OdpSegmentManager
from optimizely.odp.zaius_graphql_api_manager import ZaiusGraphQLApiManager
from optimizely.odp.zaius_rest_api_manager import ZaiusRestApiManager
from tests import base


# import pytest


class OdpManagerTest(base.BaseTest):
    cache_size = 10
    cache_timeout = 20

    def test_configurations_disable_odp(self):
        mock_logger = mock.MagicMock()

        manager = OdpManager(disable=True,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             logger=mock_logger)
        manager.fetch_qualified_segments('user1', [])
        mock_logger.debug.assert_called_once_with(Errors.ODP_NOT_ENABLED)

        manager.update_odp_config(api_key='valid', api_host='host', segments_to_check=[])
        self.assertIsNone(manager.odp_config.get_api_key())
        self.assertIsNone(manager.odp_config.get_api_host())

        # these call should be dropped gracefully with None
        manager.identify_user('user1')

        self.assertRaisesRegex(optimizely_exception.OdpNotEnabled, Errors.ODP_NOT_ENABLED,
                               manager.send_event, type='t1', action='a1', identifiers={}, data={})

        self.assertIsNone(manager.event_manager)
        self.assertIsNone(manager.segment_manager)

    def test_fetch_qualified_segments(self):
        mock_logger = mock.MagicMock()
        segment_manager = OdpSegmentManager(OdpConfig(), LRUCache(1000, 1000),
                                            ZaiusGraphQLApiManager(), mock_logger)

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             segment_manager=segment_manager,
                             logger=mock_logger)

        with mock.patch.object(segment_manager, 'fetch_qualified_segments') as mock_fetch_qualif_segments:
            manager.fetch_qualified_segments('user1', [])

        mock_logger.debug.assert_not_called()
        mock_fetch_qualif_segments.assert_called_once_with('fs_user_id', 'user1', [])

    def test_identify_user_datafile_not_ready(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger)
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        with mock.patch.object(event_manager, 'identify_user') as mock_identify_user:
            manager.identify_user('user1')

        mock_identify_user.assert_called_once_with('user1')

    def test_identify_user_odp_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        manager.update_odp_config(api_key='key1', api_host='host1', segments_to_check=[])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.identify_user('user1')

        mock_dispatch_event.assert_called_once()
        self.assertEqual(mock_dispatch_event.call_args[0][0].type, 'fullstack')
        self.assertEqual(mock_dispatch_event.call_args[0][0].action, 'identified')
        self.assertEqual(mock_dispatch_event.call_args[0][0].identifiers, {'fs_user_id': 'user1'})
        self.assertGreater(len(mock_dispatch_event.call_args[0][0].data['idempotence_id']), 0)
        self.assertEqual(mock_dispatch_event.call_args[0][0].data['data_source_type'], 'sdk')
        self.assertEqual(mock_dispatch_event.call_args[0][0].data['data_source'], 'python-sdk')
        self.assertEqual(mock_dispatch_event.call_args[0][0].data['data_source_version'], '4.1.0')

    def test_identify_user_odp_not_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        manager.update_odp_config(api_key=None, api_host=None, segments_to_check=[])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.identify_user('user1')

        mock_dispatch_event.assert_not_called()
        mock_logger.debug.assert_called_with(Errors.ODP_NOT_INTEGRATED)

    def test_identify_user_odp_disabled(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        manager.enabled = False

        with mock.patch.object(event_manager, 'identify_user') as mock_identify_user:
            manager.identify_user('user1')

        mock_identify_user.assert_called_once_with('user1')
        mock_logger.debug.assert_called_with('ODP identify event is not dispatched (ODP disabled).')

    def test_send_event_datafile_not_ready(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_not_called()
        mock_logger.debug.assert_called_with('ODP event queue: cannot send before the datafile has loaded.')

    def test_send_event_odp_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        manager.update_odp_config(api_key='key1', api_host='host1', segments_to_check=[])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_called_once()
        # asserting each arg individually because one of them is dynamic (idempotence_id/uuid)
        # otherwise could use assert_called_once_with_args()
        self.assertEqual(mock_dispatch_event.call_args[0][0].type, 't1')
        self.assertEqual(mock_dispatch_event.call_args[0][0].action, 'a1')
        self.assertEqual(mock_dispatch_event.call_args[0][0].identifiers, {'id-key1': 'id-val-1'})
        self.assertGreater(len(mock_dispatch_event.call_args[0][0].data['idempotence_id']), 0)
        self.assertEqual(mock_dispatch_event.call_args[0][0].data['data_source_type'], 'sdk')
        self.assertEqual(mock_dispatch_event.call_args[0][0].data['data_source'], 'python-sdk')
        self.assertEqual(mock_dispatch_event.call_args[0][0].data['data_source_version'], '4.1.0')

    def test_send_event_odp_not_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        manager.update_odp_config(api_key=None, api_host=None, segments_to_check=[])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_not_called()
        mock_logger.debug.assert_called_with(Errors.ODP_NOT_INTEGRATED)

    def test_send_event_odp_disabled(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        manager.enabled = False

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            self.assertRaisesRegex(optimizely_exception.OdpNotEnabled, Errors.ODP_NOT_ENABLED,
                                   manager.send_event, 't1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_not_called()
        mock_logger.debug.assert_not_called()

    def test_update_odp_config__reset_called(self):
        # build segment manager
        mock_logger = mock.MagicMock()
        segment_manager = OdpSegmentManager(OdpConfig(), LRUCache(1000, 1000),
                                            ZaiusGraphQLApiManager(), mock_logger)
        # build event manager
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             segment_manager=segment_manager,
                             logger=mock_logger)

        with mock.patch.object(segment_manager, 'reset') as mock_reset:
            manager.update_odp_config('key1', 'host1', [])
            mock_reset.assert_called_once()
            mock_reset.reset_mock()

            manager.update_odp_config('key1', 'host1', [])
            mock_reset.assert_not_called()

            manager.update_odp_config('key2', 'host1', [])
            mock_reset.assert_called_once()
            mock_reset.reset_mock()

            manager.update_odp_config('key2', 'host2', [])
            mock_reset.assert_called_once()
            mock_reset.reset_mock()

            manager.update_odp_config('key2', 'host2', ['a'])
            mock_reset.assert_called_once()
            mock_reset.reset_mock()

            manager.update_odp_config('key2', 'host2', ['a', 'b'])
            mock_reset.assert_called_once()
            mock_reset.reset_mock()

            manager.update_odp_config('key2', 'host2', ['c'])
            mock_reset.assert_called_once()
            mock_reset.reset_mock()

            manager.update_odp_config('key2', 'host2', ['c'])
            mock_reset.assert_not_called()

            manager.update_odp_config(None, None, [])
            mock_reset.assert_called_once()

    def test_update_odp_config__flush_called(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        with mock.patch.object(event_manager, 'flush') as mock_flush:
            first_api_key = manager.odp_config.get_api_key()
            manager.update_odp_config(api_key='key1', api_host='host1', segments_to_check=[])
            second_api_key = manager.odp_config.get_api_key()

        self.assertEqual(mock_flush.call_count, 2)
        self.assertEqual(first_api_key, None)
        self.assertEqual(second_api_key, 'key1')

        with mock.patch.object(event_manager, 'flush') as mock_flush:
            first_api_key = manager.odp_config.get_api_key()
            manager.update_odp_config(api_key='key2', api_host='host1', segments_to_check=[])
            second_api_key = manager.odp_config.get_api_key()

        self.assertEqual(mock_flush.call_count, 2)
        self.assertEqual(first_api_key, 'key1')
        self.assertEqual(second_api_key, 'key2')

        with mock.patch.object(event_manager, 'flush') as mock_flush:
            first_api_key = manager.odp_config.get_api_key()
            manager.update_odp_config(api_key='key2', api_host='host1', segments_to_check=[])
            second_api_key = manager.odp_config.get_api_key()

        self.assertEqual(mock_flush.call_count, 1)
        self.assertEqual(first_api_key, 'key2')
        self.assertEqual(second_api_key, 'key2')

        with mock.patch.object(event_manager, 'flush') as mock_flush:
            first_api_key = manager.odp_config.get_api_key()
            manager.update_odp_config(api_key=None, api_host=None, segments_to_check=[])
            second_api_key = manager.odp_config.get_api_key()

        self.assertEqual(mock_flush.call_count, 2)
        self.assertEqual(first_api_key, 'key2')
        self.assertEqual(second_api_key, None)

    def test_update_odp_config__odp_config_propagated_properly(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger, ZaiusRestApiManager())
        event_manager.start()

        manager = OdpManager(disable=False,
                             cache_size=10,
                             cache_timeout_in_sec=20,
                             event_manager=event_manager,
                             logger=mock_logger)

        manager.update_odp_config(api_key='key1', api_host='host1', segments_to_check=[])

        self.assertEqual(manager.segment_manager.odp_config.get_api_key(), 'key1')
        self.assertEqual(manager.segment_manager.odp_config.get_api_host(), 'host1')
        self.assertEqual(manager.event_manager.odp_config.get_api_key(), 'key1')
        self.assertEqual(manager.event_manager.odp_config.get_api_host(), 'host1')

        # odp disabled with invalid apiKey (apiKey/apiHost propagated into submanagers)
        manager.update_odp_config(None, None, [])

        self.assertEqual(manager.segment_manager.odp_config.get_api_key(), None)
        self.assertEqual(manager.segment_manager.odp_config.get_api_host(), None)
        self.assertEqual(manager.event_manager.odp_config.get_api_key(), None)
        self.assertEqual(manager.event_manager.odp_config.get_api_host(), None)
