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
from threading import Lock


class OdpConfig:
    """
    Contains configuration used for ODP integration.

    Args:
        api_host: The host URL for the ODP audience segments API (optional).
        api_key: The public API key for the ODP account from which the audience segments will be fetched (optional).
        segments_to_check: A list of all ODP segments used in the current datafile
                            (associated with api_host/api_key).
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        segments_to_check: Optional[list[str]] = None
    ) -> None:
        self._api_key = api_key
        self._api_host = api_host
        self._segments_to_check = segments_to_check or []
        self.lock = Lock()

    def update(self, api_key: Optional[str], api_host: Optional[str], segments_to_check: list[str]) -> bool:
        """
        Override the ODP configuration.

        Args:
            api_host: The host URL for the ODP audience segments API (optional).
            api_key: The public API key for the ODP account from which the audience segments will be fetched (optional).
            segments_to_check: A list of all ODP segments used in the current datafile
                               (associated with api_host/api_key).

        Returns:
            True if the provided values were different than the existing values.
        """
        updated = False
        with self.lock:
            if self._api_key != api_key or self._api_host != api_host or self._segments_to_check != segments_to_check:
                self._api_key = api_key
                self._api_host = api_host
                self._segments_to_check = segments_to_check
                updated = True

        return updated

    def get_api_host(self) -> Optional[str]:
        with self.lock:
            return self._api_host

    def get_api_key(self) -> Optional[str]:
        with self.lock:
            return self._api_key

    def get_segments_to_check(self) -> list[str]:
        with self.lock:
            return self._segments_to_check.copy()

    def odp_integrated(self) -> bool:
        """Returns True if ODP is integrated."""
        with self.lock:
            return self._api_key is not None and self._api_host is not None