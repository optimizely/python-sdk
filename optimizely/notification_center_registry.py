# Copyright 2023, Optimizely
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
from threading import Lock
from typing import Optional
from .logger import Logger as OptimizelyLogger
from .notification_center import NotificationCenter
from .helpers.enums import Errors


class _NotificationCenterRegistry:
    """ Class managing internal notification centers."""
    _notification_centers: dict[str, NotificationCenter] = {}
    _lock = Lock()

    @classmethod
    def get_notification_center(cls, sdk_key: Optional[str], logger: OptimizelyLogger) -> Optional[NotificationCenter]:
        """Returns an internal notification center for the given sdk_key, creating one
        if none exists yet.

        Args:
        sdk_key: A string sdk key to uniquely identify the notification center.
        logger: Optional logger.

        Returns:
        None or NotificationCenter
        """

        if not sdk_key:
            logger.error(f'{Errors.MISSING_SDK_KEY} ODP may not work properly without it.')
            return None

        with cls._lock:
            if sdk_key in cls._notification_centers:
                notification_center = cls._notification_centers[sdk_key]
            else:
                notification_center = NotificationCenter(logger)
                cls._notification_centers[sdk_key] = notification_center

        return notification_center

    @classmethod
    def remove_notification_center(cls, sdk_key: str) -> None:
        """Remove a previously added notification center and clear all its listeners.

        Args:
        sdk_key: The sdk_key of the notification center to remove.
        """

        with cls._lock:
            notification_center = cls._notification_centers.pop(sdk_key, None)
            if notification_center:
                notification_center.clear_all_notification_listeners()
