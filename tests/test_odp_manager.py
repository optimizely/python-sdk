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


class OdpManagerTest(base.BaseTest):
    # api_host = 'host'
    # api_key = 'valid'

    def test_empty_list_with_no_segments_to_check(self):
        odp_config = OdpConfig(self.api_key, self.api_host, [])
        mock_logger = mock.MagicMock()
        segments_cache = LRUCache(1000, 1000)
        api = ZaiusGraphQLApiManager()
        segment_manager = OdpSegmentManager(odp_config, segments_cache, api, mock_logger)

        with mock.patch.object(api, 'fetch_segments') as mock_fetch_segments:
            segments = segment_manager.fetch_qualified_segments(self.user_key, self.user_value, [])

        self.assertEqual(segments, [])
        mock_logger.debug.assert_called_once_with('No segments are used in the project. Returning empty list.')
        mock_logger.error.assert_not_called()
        mock_fetch_segments.assert_not_called()

    def test_configurations_cache(self):
        pass

    def test_configurations_disable_odp(self):
        pass

    def test_fetch_qualified_segments(self):
        pass

    def test_identify_user_datafile_not_ready(self):
        pass

    def test_identify_user_odp_integrated(self):
        pass

    def test_identify_user_odp_not_integrated(self):
        pass

    def test_identify_user_odp_disabled(self):
        pass

    def test_send_event_datafile_not_ready(self):
        pass

    def test_send_event_odp_integrated(self):
        pass

    def test_send_event_odp_not_Integrated(self):
        pass

    def test_send_event_odp_disabled(self):
        pass

    def test_update_odp_config__reset_called(self):
        pass

    def test_update_odp_config__flush_called(self):
        pass

    def test_update_odp_config__odp_config_propagated_properly(self):
        pass

