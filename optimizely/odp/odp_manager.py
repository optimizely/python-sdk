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

from typing import Optional, Any

from optimizely import exceptions as optimizely_exception
from optimizely import logger as optimizely_logger
from optimizely.helpers.enums import Errors, OdpManagerConfig, OdpSegmentsCacheConfig
from optimizely.helpers.validator import are_odp_data_types_valid
from optimizely.odp.lru_cache import OptimizelySegmentsCache, LRUCache
from optimizely.odp.odp_config import OdpConfig, OdpConfigState
from optimizely.odp.odp_event_manager import OdpEventManager
from optimizely.odp.odp_segment_manager import OdpSegmentManager
from optimizely.odp.zaius_graphql_api_manager import ZaiusGraphQLApiManager


class OdpManager:
    """Orchestrates segment manager, event manager and odp config."""

    def __init__(
        self,
        disable: bool,
        segments_cache: Optional[OptimizelySegmentsCache] = None,
        segment_manager: Optional[OdpSegmentManager] = None,
        event_manager: Optional[OdpEventManager] = None,
        logger: Optional[optimizely_logger.Logger] = None
    ) -> None:

        self.enabled = not disable
        self.odp_config = OdpConfig()
        self.logger = logger or optimizely_logger.NoOpLogger()

        self.segment_manager = segment_manager
        self.event_manager = event_manager

        if not self.enabled:
            self.logger.info('ODP is disabled.')
            return

        if not self.segment_manager:
            if not segments_cache:
                segments_cache = LRUCache(
                    OdpSegmentsCacheConfig.DEFAULT_CAPACITY,
                    OdpSegmentsCacheConfig.DEFAULT_TIMEOUT_SECS
                )
            self.segment_manager = OdpSegmentManager(
                self.odp_config,
                segments_cache,
                ZaiusGraphQLApiManager(logger), logger
            )
        else:
            self.segment_manager.odp_config = self.odp_config

        if event_manager:
            self.event_manager = event_manager
        else:
            self.event_manager = OdpEventManager(self.logger)

        self.event_manager.start(self.odp_config)

    def fetch_qualified_segments(self, user_id: str, options: list[str]) -> Optional[list[str]]:
        if not self.enabled or not self.segment_manager:
            self.logger.error(Errors.ODP_NOT_ENABLED)
            return None

        user_key = OdpManagerConfig.KEY_FOR_USER_ID
        user_value = user_id

        return self.segment_manager.fetch_qualified_segments(user_key, user_value, options)

    def identify_user(self, user_id: str) -> None:
        if not self.enabled or not self.event_manager:
            self.logger.debug('ODP identify event is not dispatched (ODP disabled).')
            return
        if self.odp_config.odp_state() == OdpConfigState.NOT_INTEGRATED:
            self.logger.debug('ODP identify event is not dispatched (ODP not integrated).')
            return

        self.event_manager.identify_user(user_id)

    def send_event(self, type: str, action: str, identifiers: dict[str, str], data: dict[str, Any]) -> None:
        """
        Send an event to the ODP server.

        Args:
            type: The event type.
            action: The event action name.
            identifiers: A dictionary for identifiers.
            data: A dictionary for associated data. The default event data will be added to this data
            before sending to the ODP server.

        Raises custom exception if error is detected.
        """
        if not self.enabled or not self.event_manager:
            raise optimizely_exception.OdpNotEnabled(Errors.ODP_NOT_ENABLED)

        if self.odp_config.odp_state() == OdpConfigState.NOT_INTEGRATED:
            raise optimizely_exception.OdpNotIntegrated(Errors.ODP_NOT_INTEGRATED)

        if not are_odp_data_types_valid(data):
            raise optimizely_exception.OdpInvalidData(Errors.ODP_INVALID_DATA)

        self.event_manager.send_event(type, action, identifiers, data)

    def update_odp_config(self, api_key: Optional[str], api_host: Optional[str],
                          segments_to_check: list[str]) -> None:
        if not self.enabled:
            return

        config_changed = self.odp_config.update(api_key, api_host, segments_to_check)
        if not config_changed:
            self.logger.debug('Odp config was not changed.')
            return

        # reset segments cache when odp integration or segments to check are changed
        if self.segment_manager:
            self.segment_manager.reset()

        if self.event_manager:
            self.event_manager.update_config()
