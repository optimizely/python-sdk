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


from typing import Optional

from optimizely.helpers import enums
from optimizely.odp.lru_cache import OptimizelySegmentsCache
from optimizely.odp.odp_event_manager import OdpEventManager
from optimizely.odp.odp_segment_manager import OdpSegmentManager


class OptimizelySdkSettings:
    """Contains configuration used for Optimizely Project initialization."""

    def __init__(
            self,
            odp_disabled: bool = False,
            segments_cache_size: int = enums.OdpSegmentsCacheConfig.DEFAULT_CAPACITY,
            segments_cache_timeout_in_secs: int = enums.OdpSegmentsCacheConfig.DEFAULT_TIMEOUT_SECS,
            odp_segments_cache: Optional[OptimizelySegmentsCache] = None,
            odp_segment_manager: Optional[OdpSegmentManager] = None,
            odp_event_manager: Optional[OdpEventManager] = None,
            odp_segment_request_timeout: Optional[int] = None,
            odp_event_request_timeout: Optional[int] = None,
            odp_event_flush_interval: Optional[int] = None
    ) -> None:
        """
        Args:
          odp_disabled: Set this flag to true (default = False) to disable ODP features.
          segments_cache_size: The maximum size of audience segments cache (optional. default = 10,000).
            Set to zero to disable caching.
          segments_cache_timeout_in_secs: The timeout in seconds of audience segments cache (optional. default = 600).
            Set to zero to disable timeout.
          odp_segments_cache: A custom odp segments cache. Required methods include:
            `save(key, value)`, `lookup(key) -> value`, and `reset()`
          odp_segment_manager: A custom odp segment manager. Required method is:
            `fetch_qualified_segments(user_key, user_value, options)`.
          odp_event_manager: A custom odp event manager. Required method is:
            `send_event(type:, action:, identifiers:, data:)`
          odp_segment_request_timeout: Time to wait in seconds for fetch_qualified_segments request to
            send successfully (optional).
          odp_event_request_timeout: Time to wait in seconds for send_odp_events request to send successfully.
          odp_event_flush_interval: Time to wait for events to accumulate before sending a batch in seconds (optional).
        """

        self.odp_disabled = odp_disabled
        self.segments_cache_size = segments_cache_size
        self.segments_cache_timeout_in_secs = segments_cache_timeout_in_secs
        self.segments_cache = odp_segments_cache
        self.odp_segment_manager = odp_segment_manager
        self.odp_event_manager = odp_event_manager
        self.fetch_segments_timeout = odp_segment_request_timeout
        self.odp_event_timeout = odp_event_request_timeout
        self.odp_flush_interval = odp_event_flush_interval
