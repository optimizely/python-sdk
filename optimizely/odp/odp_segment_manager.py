# Copyright 2022, Optimizely
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

from __future__ import annotations

from typing import Optional

from optimizely import logger as optimizely_logger
from optimizely.helpers.enums import Errors
from optimizely.odp.odp_config import OdpConfig
from optimizely.odp.optimizely_odp_option import OptimizelyOdpOption
from optimizely.odp.lru_cache import OptimizelySegmentsCache
from optimizely.odp.odp_segment_api_manager import OdpSegmentApiManager


class OdpSegmentManager:
    """Schedules connections to ODP for audience segmentation and caches the results."""

    def __init__(
        self,
        segments_cache: OptimizelySegmentsCache,
        api_manager: Optional[OdpSegmentApiManager] = None,
        logger: Optional[optimizely_logger.Logger] = None,
        timeout: Optional[int] = None
    ) -> None:

        self.odp_config: Optional[OdpConfig] = None
        self.segments_cache = segments_cache
        self.logger = logger or optimizely_logger.NoOpLogger()
        self.api_manager = api_manager or OdpSegmentApiManager(self.logger, timeout)

    def fetch_qualified_segments(self, user_key: str, user_value: str, options: list[str]) -> Optional[list[str]]:
        """
        Args:
            user_key: The key for identifying the id type.
            user_value: The id itself.
            options: An array of OptimizelySegmentOptions used to ignore and/or reset the cache.

        Returns:
            Qualified segments for the user from the cache or the ODP server if not in the cache.
        """
        if self.odp_config:
            odp_api_key = self.odp_config.get_api_key()
            odp_api_host = self.odp_config.get_api_host()
            odp_segments_to_check = self.odp_config.get_segments_to_check()

        if not self.odp_config or not (odp_api_key and odp_api_host):
            self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('api_key/api_host not defined'))
            return None

        if not odp_segments_to_check:
            self.logger.debug('No segments are used in the project. Returning empty list.')
            return []

        cache_key = self.make_cache_key(user_key, user_value)

        ignore_cache = OptimizelyOdpOption.IGNORE_CACHE in options
        reset_cache = OptimizelyOdpOption.RESET_CACHE in options

        if reset_cache:
            self.reset()

        if not ignore_cache and not reset_cache:
            segments = self.segments_cache.lookup(cache_key)
            if segments:
                self.logger.debug('ODP cache hit. Returning segments from cache.')
                return segments
            self.logger.debug('ODP cache miss.')

        self.logger.debug('Making a call to ODP server.')

        segments = self.api_manager.fetch_segments(odp_api_key, odp_api_host, user_key, user_value,
                                                   odp_segments_to_check)

        if segments and not ignore_cache:
            self.segments_cache.save(cache_key, segments)

        return segments

    def reset(self) -> None:
        self.segments_cache.reset()

    def make_cache_key(self, user_key: str, user_value: str) -> str:
        return f'{user_key}-$-{user_value}'
