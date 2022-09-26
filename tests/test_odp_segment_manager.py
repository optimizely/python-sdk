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
from unittest.mock import call

from requests import exceptions as request_exception

from optimizely.odp.lru_cache import LRUCache
from optimizely.odp.odp_config import OdpConfig
from optimizely.odp.optimizely_odp_option import OptimizelyOdpOption
from optimizely.odp.odp_segment_manager import OdpSegmentManager
from optimizely.odp.zaius_graphql_api_manager import ZaiusGraphQLApiManager
from tests import base


class OdpSegmentManagerTest(base.BaseTest):
    api_host = 'host'
    api_key = 'valid'
    user_key = 'fs_user_id'
    user_value = 'test-user-value'

    def test_empty_list_with_no_segments_to_check(self):
        odp_config = OdpConfig(self.api_key, self.api_host, [])
        mock_logger = mock.MagicMock()
        segments_cache = LRUCache(1000, 1000)
        api = ZaiusGraphQLApiManager(mock_logger)
        segment_manager = OdpSegmentManager(segments_cache, api, mock_logger)
        segment_manager.odp_config = odp_config

        with mock.patch.object(api, 'fetch_segments') as mock_fetch_segments:
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, [])
        mock_logger.debug.assert_called_once_with('No segments are used in the project. Returning empty list.')
        mock_logger.error.assert_not_called()
        mock_fetch_segments.assert_not_called()

    def test_fetch_segments_success_cache_miss(self):
        """
        we are fetching user key/value 'fs_user_id'/'test-user-value'
        which is different from what we have passed to cache (fs_user_id-$-123/['d'])
        ---> hence we trigger a cache miss
        """
        odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
        mock_logger = mock.MagicMock()
        segments_cache = LRUCache(1000, 1000)

        segment_manager = OdpSegmentManager(segments_cache, logger=mock_logger)
        segment_manager.odp_config = odp_config
        cache_key = segment_manager.make_cache_key(self.user_key, '123')
        segment_manager.segments_cache.save(cache_key, ["d"])

        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.good_response_data)

            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, ["a", "b"])
        actual_cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
        self.assertEqual(segment_manager.segments_cache.lookup(actual_cache_key), ["a", "b"])

        self.assertEqual(mock_logger.debug.call_count, 2)
        mock_logger.debug.assert_has_calls([call('ODP cache miss.'), call('Making a call to ODP server.')])
        mock_logger.error.assert_not_called()

    def test_fetch_segments_success_cache_hit(self):
        odp_config = OdpConfig()
        odp_config.update(self.api_key, self.api_host, ['c'])
        mock_logger = mock.MagicMock()
        segments_cache = LRUCache(1000, 1000)

        segment_manager = OdpSegmentManager(segments_cache, logger=mock_logger)
        segment_manager.odp_config = odp_config
        cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
        segment_manager.segments_cache.save(cache_key, ['c'])

        with mock.patch.object(segment_manager.zaius_manager, 'fetch_segments') as mock_fetch_segments:
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, ['c'])
        mock_logger.debug.assert_called_once_with('ODP cache hit. Returning segments from cache.')
        mock_logger.error.assert_not_called()
        mock_fetch_segments.assert_not_called()

    def test_fetch_segments_missing_api_host_api_key(self):
        with mock.patch('optimizely.logger') as mock_logger:
            segment_manager = OdpSegmentManager(LRUCache(1000, 1000), logger=mock_logger)
            segment_manager.odp_config = OdpConfig()
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, None)
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (api_key/api_host not defined).')

    def test_fetch_segments_network_error(self):
        """
        Trigger connection error with mock side_effect. Note that Python's requests don't
        have a status code for connection error, that's why we need to trigger the exception
        instead of returning a fake server response with status code 500.
        The error log should come form the GraphQL API manager, not from ODP Segment Manager.
        The active mock logger should be placed as parameter in ZaiusGraphQLApiManager object.
        """
        odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
        mock_logger = mock.MagicMock()
        segments_cache = LRUCache(1000, 1000)
        segment_manager = OdpSegmentManager(segments_cache, logger=mock_logger)
        segment_manager.odp_config = odp_config

        with mock.patch('requests.post',
                        side_effect=request_exception.ConnectionError('Connection error')):
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, None)
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (network error).')

    def test_options_ignore_cache(self):
        odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
        mock_logger = mock.MagicMock()
        segments_cache = LRUCache(1000, 1000)

        segment_manager = OdpSegmentManager(segments_cache, logger=mock_logger)
        segment_manager.odp_config = odp_config
        cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
        segment_manager.segments_cache.save(cache_key, ['d'])

        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.good_response_data)

            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value,
                                                                [OptimizelyOdpOption.IGNORE_CACHE])

        self.assertEqual(segments, ["a", "b"])
        self.assertEqual(segment_manager.segments_cache.lookup(cache_key), ['d'])
        mock_logger.debug.assert_called_once_with('Making a call to ODP server.')
        mock_logger.error.assert_not_called()

    def test_options_reset_cache(self):
        odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
        mock_logger = mock.MagicMock()
        segments_cache = LRUCache(1000, 1000)

        segment_manager = OdpSegmentManager(segments_cache, logger=mock_logger)
        segment_manager.odp_config = odp_config
        cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
        segment_manager.segments_cache.save(cache_key, ['d'])
        segment_manager.segments_cache.save('123', ['c', 'd'])

        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.good_response_data)

            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value,
                                                                [OptimizelyOdpOption.RESET_CACHE])

        self.assertEqual(segments, ["a", "b"])
        self.assertEqual(segment_manager.segments_cache.lookup(cache_key), ['a', 'b'])
        self.assertTrue(len(segment_manager.segments_cache.map) == 1)
        mock_logger.debug.assert_called_once_with('Making a call to ODP server.')
        mock_logger.error.assert_not_called()

    def test_make_correct_cache_key(self):
        segment_manager = OdpSegmentManager(None)
        cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
        self.assertEqual(cache_key, 'fs_user_id-$-test-user-value')

    # test json response
    good_response_data = """
        {
            "data": {
                "customer": {
                    "audiences": {
                        "edges": [
                            {
                                "node": {
                                    "name": "a",
                                    "state": "qualified",
                                    "description": "qualifed sample 1"
                                }
                            },
                            {
                                "node": {
                                    "name": "b",
                                    "state": "qualified",
                                    "description": "qualifed sample 2"
                                }
                            },
                            {
                                "node": {
                                    "name": "c",
                                    "state": "not_qualified",
                                    "description": "not-qualified sample"
                                }
                            }
                        ]
                    }
                }
            }
        }
        """
