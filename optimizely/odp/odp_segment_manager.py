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

from typing import List, Optional

from optimizely import logger as optimizely_logger
from optimizely.helpers.enums import Errors
from optimizely.helpers.enums import OptimizelySegmentOption
from optimizely.odp.lru_cache import LRUCache
from optimizely.odp.odp_config import OdpConfig
from optimizely.odp.zaius_graphql_api_manager import ZaiusGraphQLApiManager


class OdpSegmentManager:
    """Schedules connections to ODP for audience segmentation and caches the results."""

    IGNORE_CACHE = OptimizelySegmentOption.IGNORE_CACHE
    RESET_CACHE = OptimizelySegmentOption.RESET_CACHE

    def __init__(self, odp_config: Optional[OdpConfig], segments_cache: Optional[LRUCache[str, List[str]](1000, 1000)],
                 zaius_manager: Optional[ZaiusGraphQLApiManager],
                 logger: Optional[optimizely_logger.Logger] = None) -> None:

        self.odp_config = odp_config
        self.segments_cache = segments_cache
        self.zaius_manager = zaius_manager
        self.logger = logger or optimizely_logger.NoOpLogger()

    def fetch_qualified_segments(self, user_key: str, user_value: str, options: list[OptimizelySegmentOption]):
        if not self.odp_config.odp_integrated():
            self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('apiKey/apiHost not defined'))
            return None

        odp_api_key: Optional[str] = self.odp_config.get_api_key()
        odp_api_host: Optional[str] = self.odp_config.get_api_host()
        odp_segments_to_check: Optional[list[str]] = self.odp_config.get_segments_to_check()

        if not odp_segments_to_check and not len(odp_segments_to_check):
            self.logger.debug('No segments are used in the project. Returning empty list.')
            return []

        cache_key = self.make_cache_key(user_key, user_value)

        ignore_cache = self.IGNORE_CACHE if self.IGNORE_CACHE in options else None
        reset_cache = self.RESET_CACHE if self.RESET_CACHE in options else None

        if reset_cache:
            self._reset()

        if not ignore_cache and not reset_cache:
            segments = self.segments_cache.lookup(cache_key)
            if segments:
                self.logger.debug('ODP cache hit. Returning segments from cache.')
                return segments

        self.logger.debug('ODP cache miss. Making a call to ODP server.')

        segments = self.zaius_manager.fetch_segments(odp_api_key, odp_api_host, user_key, user_value,
                                                     odp_segments_to_check)

        if segments and not ignore_cache:
            self.segments_cache.save(cache_key, segments)

        return segments

    def _reset(self):
        self.segments_cache.reset()

    def make_cache_key(self, user_key: str, user_value: str) -> str:
        return user_key + '-$-' + user_value
