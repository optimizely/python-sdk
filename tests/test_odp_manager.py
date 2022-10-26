# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from unittest import mock

from optimizely import version
from optimizely.helpers.enums import Errors
from optimizely.odp.lru_cache import OptimizelySegmentsCache, LRUCache
from optimizely.odp.odp_config import OdpConfig
from optimizely.odp.odp_event_manager import OdpEventManager
from optimizely.odp.odp_manager import OdpManager
from optimizely.odp.odp_segment_manager import OdpSegmentManager
from optimizely.odp.odp_segment_api_manager import OdpSegmentApiManager
from optimizely.odp.odp_event_api_manager import OdpEventApiManager
from tests import base


class CustomCache:
    def reset(self) -> None:
        pass


class OdpManagerTest(base.BaseTest):

    def test_configurations_disable_odp(self):
        mock_logger = mock.MagicMock()
        manager = OdpManager(True, OptimizelySegmentsCache, logger=mock_logger)

        mock_logger.info.assert_called_once_with('ODP is disabled.')
        manager.update_odp_config('valid', 'host', [])
        self.assertIsNone(manager.odp_config.get_api_key())
        self.assertIsNone(manager.odp_config.get_api_host())

        manager.fetch_qualified_segments('user1', [])
        mock_logger.error.assert_called_once_with(Errors.ODP_NOT_ENABLED)
        mock_logger.reset_mock()

        # these call should be dropped gracefully with None
        manager.identify_user('user1')

        manager.send_event('t1', 'a1', {}, {})
        mock_logger.error.assert_called_once_with('ODP is not enabled.')

        self.assertIsNone(manager.event_manager)
        self.assertIsNone(manager.segment_manager)

    def test_fetch_qualified_segments(self):
        mock_logger = mock.MagicMock()
        segment_manager = OdpSegmentManager(OptimizelySegmentsCache,
                                            OdpSegmentApiManager(mock_logger), mock_logger)

        manager = OdpManager(False, OptimizelySegmentsCache, segment_manager, logger=mock_logger)

        with mock.patch.object(segment_manager, 'fetch_qualified_segments') as mock_fetch_qualif_segments:
            manager.fetch_qualified_segments('user1', [])

        mock_logger.debug.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_fetch_qualif_segments.assert_called_once_with('fs_user_id', 'user1', [])

        with mock.patch.object(segment_manager, 'fetch_qualified_segments') as mock_fetch_qualif_segments:
            manager.fetch_qualified_segments('user1', ['IGNORE_CACHE'])

        mock_logger.debug.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_fetch_qualif_segments.assert_called_once_with('fs_user_id', 'user1', ['IGNORE_CACHE'])

    def test_fetch_qualified_segments__disabled(self):
        mock_logger = mock.MagicMock()
        segment_manager = OdpSegmentManager(OptimizelySegmentsCache,
                                            OdpSegmentApiManager(mock_logger), mock_logger)

        manager = OdpManager(True, OptimizelySegmentsCache, segment_manager, logger=mock_logger)

        with mock.patch.object(segment_manager, 'fetch_qualified_segments') as mock_fetch_qualif_segments:
            manager.fetch_qualified_segments('user1', [])
            mock_logger.error.assert_called_once_with(Errors.ODP_NOT_ENABLED)
            mock_fetch_qualif_segments.assert_not_called()

    def test_fetch_qualified_segments__segment_mgr_is_none(self):
        """
        When segment manager is None, then fetching segment
        should take place using the default segment manager.
        """
        mock_logger = mock.MagicMock()
        manager = OdpManager(False, LRUCache(10, 20), logger=mock_logger)
        manager.update_odp_config('api_key', 'api_host', [])

        with mock.patch.object(manager.segment_manager, 'fetch_qualified_segments') as mock_fetch_qualif_segments:
            manager.fetch_qualified_segments('user1', [])

        mock_logger.error.assert_not_called()
        mock_fetch_qualif_segments.assert_called_once_with('fs_user_id', 'user1', [])

    def test_fetch_qualified_segments__seg_cache_and_seg_mgr_are_none(self):
        """
        When segment cache and segment manager are None, then fetching segment
        should take place using the default managers.
        """
        mock_logger = mock.MagicMock()
        manager = OdpManager(False, mock_logger)
        manager.update_odp_config('api_key', 'api_host', [])

        with mock.patch.object(manager.segment_manager, 'fetch_qualified_segments') as mock_fetch_qualif_segments:
            manager.fetch_qualified_segments('user1', [])

        mock_logger.debug.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_fetch_qualif_segments.assert_called_once_with('fs_user_id', 'user1', [])

    def test_identify_user_datafile_not_ready(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(OdpConfig(), mock_logger)

        manager = OdpManager(False, OptimizelySegmentsCache, event_manager=event_manager, logger=mock_logger)

        with mock.patch.object(event_manager, 'identify_user') as mock_identify_user:
            manager.identify_user('user1')

        mock_identify_user.assert_called_once_with('user1')
        mock_logger.error.assert_not_called()

    def test_identify_user_odp_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, LRUCache(10, 20), event_manager=event_manager, logger=mock_logger)
        manager.update_odp_config('key1', 'host1', [])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.identify_user('user1')

        mock_dispatch_event.assert_called_once_with({
            'type': 'fullstack',
            'action': 'identified',
            'identifiers': {'fs_user_id': 'user1'},
            'data': {
                'idempotence_id': mock.ANY,
                'data_source_type': 'sdk',
                'data_source': 'python-sdk',
                'data_source_version': version.__version__
            }})
        mock_logger.error.assert_not_called()

    def test_identify_user_odp_not_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, CustomCache(), event_manager=event_manager, logger=mock_logger)
        manager.update_odp_config(None, None, [])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.identify_user('user1')

        mock_dispatch_event.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_any_call('ODP identify event is not dispatched (ODP not integrated).')

    def test_identify_user_odp_disabled(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, OptimizelySegmentsCache, event_manager=event_manager, logger=mock_logger)
        manager.enabled = False

        with mock.patch.object(event_manager, 'identify_user') as mock_identify_user:
            manager.identify_user('user1')

        mock_identify_user.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_called_with('ODP identify event is not dispatched (ODP disabled).')

    def test_send_event_datafile_not_ready(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, OptimizelySegmentsCache, event_manager=event_manager, logger=mock_logger)

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_called_with('ODP event queue: cannot send before config has been set.')

    def test_send_event_odp_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, LRUCache(10, 20), event_manager=event_manager, logger=mock_logger)
        manager.update_odp_config('key1', 'host1', [])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_called_once_with({
            'type': 't1',
            'action': 'a1',
            'identifiers': {'id-key1': 'id-val-1'},
            'data': {
                'idempotence_id': mock.ANY,
                'data_source_type': 'sdk',
                'data_source': 'python-sdk',
                'data_source_version': version.__version__,
                'key1': 'val1'
            }})

    def test_send_event_odp_not_integrated(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, CustomCache(), event_manager=event_manager, logger=mock_logger)
        manager.update_odp_config('api_key', 'api_host', [])
        manager.update_odp_config(None, None, [])

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_not_called()
        mock_logger.error.assert_called_once_with('ODP is not integrated.')

    def test_send_event_odp_disabled(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(True, OptimizelySegmentsCache, event_manager=event_manager, logger=mock_logger)

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_not_called()
        mock_logger.error.assert_called_once_with('ODP is not enabled.')

    def test_send_event_odp_disabled__event_manager_not_available(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, OptimizelySegmentsCache, event_manager=event_manager, logger=mock_logger)
        manager.event_manager = False

        with mock.patch.object(event_manager, 'dispatch') as mock_dispatch_event:
            manager.send_event('t1', 'a1', {'id-key1': 'id-val-1'}, {'key1': 'val1'})

        mock_dispatch_event.assert_not_called()
        mock_logger.error.assert_called_once_with('ODP is not enabled.')

    def test_config_not_changed(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, CustomCache(), event_manager=event_manager, logger=mock_logger)
        # finish initialization
        manager.update_odp_config(None, None, [])
        # update without change
        manager.update_odp_config(None, None, [])
        mock_logger.debug.assert_any_call('Odp config was not changed.')
        mock_logger.error.assert_not_called()

    def test_update_odp_config__reset_called(self):
        # build segment manager
        mock_logger = mock.MagicMock()
        segment_manager = OdpSegmentManager(OptimizelySegmentsCache,
                                            OdpSegmentApiManager(mock_logger), mock_logger)
        # build event manager
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())

        manager = OdpManager(False, OptimizelySegmentsCache, segment_manager, event_manager, mock_logger)

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
        mock_logger.error.assert_not_called()

    def test_update_odp_config__update_config_called(self):
        """
        Test if event_manager.update_config is called when change
        to odp_config is made or not in OdpManager.
        """
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())
        manager = OdpManager(False, LRUCache(10, 20), event_manager=event_manager, logger=mock_logger)
        event_manager.start(manager.odp_config)

        with mock.patch.object(event_manager, 'update_config') as mock_update:
            first_api_key = manager.odp_config.get_api_key()
            manager.update_odp_config('key1', 'host1', [])
            second_api_key = manager.odp_config.get_api_key()

        mock_update.assert_called_once()
        mock_logger.debug.assert_not_called()
        self.assertEqual(first_api_key, None)
        self.assertEqual(second_api_key, 'key1')

        with mock.patch.object(event_manager, 'update_config') as mock_update:
            first_api_key = manager.odp_config.get_api_key()
            manager.update_odp_config('key2', 'host1', [])
            second_api_key = manager.odp_config.get_api_key()

        mock_update.assert_called_once()
        mock_logger.debug.assert_not_called()
        self.assertEqual(first_api_key, 'key1')
        self.assertEqual(second_api_key, 'key2')

        with mock.patch.object(event_manager, 'update_config') as mock_update:
            first_api_key = manager.odp_config.get_api_key()
            manager.update_odp_config('key2', 'host1', [])
            second_api_key = manager.odp_config.get_api_key()

        # event_manager.update_config not called when no change to odp_config
        mock_update.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.debug.assert_called_with('Odp config was not changed.')
        self.assertEqual(first_api_key, 'key2')
        self.assertEqual(second_api_key, 'key2')

    def test_update_odp_config__odp_config_propagated_properly(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger, OdpEventApiManager())
        manager = OdpManager(False, LRUCache(10, 20), event_manager=event_manager, logger=mock_logger)
        manager.update_odp_config('key1', 'host1', ['a', 'b'])

        self.assertEqual(manager.segment_manager.odp_config.get_api_key(), 'key1')
        self.assertEqual(manager.segment_manager.odp_config.get_api_host(), 'host1')
        self.assertEqual(manager.segment_manager.odp_config.get_segments_to_check(), ['a', 'b'])
        self.assertEqual(manager.event_manager.odp_config.get_api_key(), 'key1')
        self.assertEqual(manager.event_manager.odp_config.get_api_host(), 'host1')
        self.assertEqual(manager.event_manager.odp_config.get_segments_to_check(), ['a', 'b'])

        # odp disabled with invalid apiKey (apiKey/apiHost propagated into submanagers)
        manager.update_odp_config(None, None, [])

        self.assertEqual(manager.segment_manager.odp_config.get_api_key(), None)
        self.assertEqual(manager.segment_manager.odp_config.get_api_host(), None)
        self.assertEqual(manager.segment_manager.odp_config.get_segments_to_check(), [])
        self.assertEqual(manager.event_manager.odp_config.get_api_key(), None)
        self.assertEqual(manager.event_manager.odp_config.get_api_host(), None)
        self.assertEqual(manager.event_manager.odp_config.get_segments_to_check(), [])

        manager.update_odp_config(None, None, ['a', 'b'])
        self.assertEqual(manager.segment_manager.odp_config.get_segments_to_check(), ['a', 'b'])
        self.assertEqual(manager.event_manager.odp_config.get_segments_to_check(), ['a', 'b'])
        mock_logger.error.assert_not_called()

    def test_update_odp_config__odp_config_starts_event_manager(self):
        mock_logger = mock.MagicMock()
        event_manager = OdpEventManager(mock_logger)
        manager = OdpManager(False, event_manager=event_manager, logger=mock_logger)
        self.assertFalse(event_manager.is_running)

        manager.update_odp_config('key1', 'host1', ['a', 'b'])
        self.assertTrue(event_manager.is_running)

        mock_logger.error.assert_not_called()
        manager.close()

    def test_segments_cache_default_settings(self):
        manager = OdpManager(False)
        segments_cache = manager.segment_manager.segments_cache
        self.assertEqual(segments_cache.capacity, 10_000)
        self.assertEqual(segments_cache.timeout, 600)
