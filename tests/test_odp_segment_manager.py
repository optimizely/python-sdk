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

from requests import exceptions as request_exception

from optimizely.odp.odp_options import OptimizelySegmentOption
from optimizely.odp.lru_cache import LRUCache
from optimizely.odp.odp_config import OdpConfig
from optimizely.odp.odp_segment_manager import OdpSegmentManager
from optimizely.odp.zaius_graphql_api_manager import ZaiusGraphQLApiManager
from tests import base


class OdpSegmentManagerTest(base.BaseTest):
    api_host = 'host'
    api_key = 'valid'
    user_key = 'fs_user_id'
    user_value = 'test-user-value'

    def test_empty_array_with_no_segments_to_check(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.good_response_data)

            odp_config = OdpConfig(self.api_key, self.api_host, [])
            segments_cache = LRUCache(1000, 1000)
            api = ZaiusGraphQLApiManager()

            segment_manager = OdpSegmentManager(odp_config, segments_cache, api, mock_logger)
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

            self.assertEqual(segments, [])
            mock_logger.debug.assert_called_once_with('No segments are used in the project. Returning empty list.')
            mock_logger.error.assert_not_called()

    def test_fetch_segments_success_cache_miss(self):
        """
        we are fetching user key/value 'fs_user_id'/'test-user-value'
        which is different from what we have passed to cache (fs_user_id-$-123/['d'])
        ---> hence we trigger a cache miss
        """
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.good_response_data)

            odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
            segments_cache = LRUCache(1000, 1000)
            api = ZaiusGraphQLApiManager()

            segment_manager = OdpSegmentManager(odp_config, segments_cache, api, mock_logger)

            cache_key = segment_manager.make_cache_key(self.user_key, '123')
            segment_manager.segments_cache.save(cache_key, ["d"])

            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, ["a", "b"])
        actual_cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
        self.assertEqual(segment_manager.segments_cache.lookup(actual_cache_key), ["a", "b"])
        mock_logger.debug.assert_called_once_with('ODP cache miss. Making a call to ODP server.')
        mock_logger.error.assert_not_called()

    def test_fetch_segments_success_cache_hit(self):
        with mock.patch('optimizely.logger') as mock_logger:
            odp_config = OdpConfig()
            odp_config.update(self.api_key, self.api_host, ['c'])
            segments_cache = LRUCache(1000, 1000)
            segment_manager = OdpSegmentManager(odp_config, segments_cache, None, mock_logger)

            cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
            segment_manager.segments_cache.save(cache_key, ['c'])

            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, ['c'])
        mock_logger.debug.assert_called_once_with('ODP cache hit. Returning segments from cache.')
        mock_logger.error.assert_not_called()

    def test_fetch_segments_missing_api_host_api_key(self):
        with mock.patch('optimizely.logger') as mock_logger:
            segment_manager = OdpSegmentManager(OdpConfig(), LRUCache(1000, 1000), None, mock_logger)
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, None)
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (apiKey/apiHost not defined).')

    def test_fetch_segments_network_error(self):
        """
        Trigger connection error with mock side_effect. Note that Python's requests don't
        have a status code for connection error, that's why we need to trigger the exception
        instead of returning a fake server response with status code 500.
        The error log should come form the GraphQL API manager, not from ODP Segment Manager.
        The active mock logger should be placed as parameter in ZaiusGraphQLApiManager object.
        """
        with mock.patch('requests.post',
                        side_effect=request_exception.ConnectionError('Connection error')), \
                mock.patch('optimizely.logger') as mock_logger:
            odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
            segments_cache = LRUCache(1000, 1000)
            api = ZaiusGraphQLApiManager(mock_logger)

            segment_manager = OdpSegmentManager(odp_config, segments_cache, api, None)
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

            self.assertEqual(segments, None)
            mock_logger.error.assert_called_once_with('Audience segments fetch failed (network error).')

    def test_options_ignore_cache(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.good_response_data)

            odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
            segments_cache = LRUCache(1000, 1000)
            api = ZaiusGraphQLApiManager()

            segment_manager = OdpSegmentManager(odp_config, segments_cache, api, mock_logger)

            cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
            segment_manager.segments_cache.save(cache_key, ['d'])

            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value,
                                                                [OptimizelySegmentOption.IGNORE_CACHE])

        self.assertEqual(segments, ["a", "b"])
        self.assertEqual(segment_manager.segments_cache.lookup(cache_key), ['d'])
        mock_logger.debug.assert_called_once_with('ODP cache miss. Making a call to ODP server.')
        mock_logger.error.assert_not_called()

    def test_options_reset_cache(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.good_response_data)

            odp_config = OdpConfig(self.api_key, self.api_host, ["a", "b", "c"])
            segments_cache = LRUCache(1000, 1000)
            api = ZaiusGraphQLApiManager()

            segment_manager = OdpSegmentManager(odp_config, segments_cache, api, mock_logger)

            cache_key = segment_manager.make_cache_key(self.user_key, self.user_value)
            segment_manager.segments_cache.save(cache_key, ['d'])
            segment_manager.segments_cache.save('123', ['c', 'd'])

            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value,
                                                                [OptimizelySegmentOption.RESET_CACHE])

        self.assertEqual(segments, ["a", "b"])
        self.assertEqual(segment_manager.segments_cache.lookup(cache_key), ['a', 'b'])
        self.assertTrue(len(segment_manager.segments_cache.map) == 1)
        mock_logger.debug.assert_called_once_with('ODP cache miss. Making a call to ODP server.')
        mock_logger.error.assert_not_called()

    def test_make_correct_cache_key(self):
        segment_manager = OdpSegmentManager(None, None, None, None)
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
