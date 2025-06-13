# Copyright 2021-2022, Optimizely
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
from typing import TYPE_CHECKING, Optional

from optimizely.helpers.sdk_settings import OptimizelySdkSettings

from . import logger as optimizely_logger
from .config_manager import BaseConfigManager, PollingConfigManager
from .error_handler import BaseErrorHandler, NoOpErrorHandler
from .event.event_processor import BatchEventProcessor
from .event_dispatcher import EventDispatcher, CustomEventDispatcher
from .notification_center import NotificationCenter
from .optimizely import Optimizely

if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from .user_profile import UserProfileService


class OptimizelyFactory:
    """ Optimizely factory to provides basic utility to instantiate the Optimizely
        SDK with a minimal number of configuration options."""

    max_event_batch_size: Optional[int] = None
    max_event_flush_interval: Optional[int] = None
    polling_interval: Optional[float] = None
    blocking_timeout: Optional[int] = None

    @staticmethod
    def set_batch_size(batch_size: int) -> int:
        """ Convenience method for setting the maximum number of events contained within a batch.
        Args:
          batch_size: Sets size of event_queue.
         """

        OptimizelyFactory.max_event_batch_size = batch_size
        return OptimizelyFactory.max_event_batch_size

    @staticmethod
    def set_flush_interval(flush_interval: int) -> int:
        """ Convenience method for setting the maximum time interval in milliseconds between event dispatches.
        Args:
          flush_interval: Time interval between event dispatches.
         """

        OptimizelyFactory.max_event_flush_interval = flush_interval
        return OptimizelyFactory.max_event_flush_interval

    @staticmethod
    def set_polling_interval(polling_interval: int) -> int:
        """ Method to set frequency at which datafile has to be polled.
            Args:
              polling_interval: Time in seconds after which to update datafile.
        """
        OptimizelyFactory.polling_interval = polling_interval
        return OptimizelyFactory.polling_interval

    @staticmethod
    def set_blocking_timeout(blocking_timeout: int) -> int:
        """ Method to set time in seconds to block the config call until config has been initialized.
            Args:
              blocking_timeout: Time in seconds to block the config call.
       """
        OptimizelyFactory.blocking_timeout = blocking_timeout
        return OptimizelyFactory.blocking_timeout

    @staticmethod
    def default_instance(sdk_key: str, datafile: Optional[str] = None) -> Optimizely:
        """ Returns a new optimizely instance..
          Args:
            sdk_key:  Required string uniquely identifying the fallback datafile corresponding to project.
            datafile: Optional JSON string datafile.
        """
        error_handler = NoOpErrorHandler()
        logger = optimizely_logger.NoOpLogger()
        notification_center = NotificationCenter(logger)

        config_manager = PollingConfigManager(
            sdk_key=sdk_key,
            update_interval=OptimizelyFactory.polling_interval,
            blocking_timeout=OptimizelyFactory.blocking_timeout,
            datafile=datafile,
            logger=logger,
            error_handler=error_handler,
            notification_center=notification_center
        )

        event_processor = BatchEventProcessor(
            event_dispatcher=EventDispatcher(),
            logger=logger,
            batch_size=OptimizelyFactory.max_event_batch_size,
            flush_interval=OptimizelyFactory.max_event_flush_interval,
            notification_center=notification_center,
        )

        optimizely = Optimizely(
            datafile, None, logger, error_handler, None, None, sdk_key, config_manager, notification_center,
            event_processor
        )
        return optimizely

    @staticmethod
    def default_instance_with_config_manager(config_manager: BaseConfigManager) -> Optimizely:
        return Optimizely(
            config_manager=config_manager
        )

    @staticmethod
    def custom_instance(
        sdk_key: str,
        datafile: Optional[str] = None,
        event_dispatcher: Optional[CustomEventDispatcher] = None,
        logger: Optional[optimizely_logger.Logger] = None,
        error_handler: Optional[BaseErrorHandler] = None,
        skip_json_validation: Optional[bool] = None,
        user_profile_service: Optional[UserProfileService] = None,
        config_manager: Optional[BaseConfigManager] = None,
        notification_center: Optional[NotificationCenter] = None,
        settings: Optional[OptimizelySdkSettings] = None
    ) -> Optimizely:
        """ Returns a new optimizely instance.
             if max_event_batch_size and max_event_flush_interval are None then default batch_size and flush_interval
             will be used to setup BatchEventProcessor.

             Args:
               sdk_key: Required string uniquely identifying the fallback datafile corresponding to project.
               datafile: Optional JSON string datafile.
               event_dispatcher: Optional EventDispatcher interface provides a dispatch_event method which if given a
                                 URL and params sends a request to it.
               logger: Optional Logger interface provides a log method to log messages.
                       By default nothing would be logged.
               error_handler: Optional ErrorHandler interface which provides a handle_error method to handle exceptions.
                              By default all exceptions will be suppressed.
               skip_json_validation: Optional boolean param to skip JSON schema validation of the provided datafile.
               user_profile_service: Optional UserProfileService interface provides methods to store and retrieve
                                     user profiles.
               config_manager: Optional ConfigManager interface responds to 'config' method.
               notification_center: Optional Instance of NotificationCenter.
               settings: Optional Instance of OptimizelySdkSettings.
        """

        error_handler = error_handler or NoOpErrorHandler()
        logger = logger or optimizely_logger.NoOpLogger()
        notification_center = notification_center if isinstance(notification_center,
                                                                NotificationCenter) else NotificationCenter(logger)

        event_processor = BatchEventProcessor(
            event_dispatcher=event_dispatcher or EventDispatcher(),
            logger=logger,
            batch_size=OptimizelyFactory.max_event_batch_size,
            flush_interval=OptimizelyFactory.max_event_flush_interval,
            notification_center=notification_center,
        )

        config_manager = config_manager or PollingConfigManager(
            sdk_key=sdk_key,
            update_interval=OptimizelyFactory.polling_interval,
            blocking_timeout=OptimizelyFactory.blocking_timeout,
            datafile=datafile,
            logger=logger,
            error_handler=error_handler,
            skip_json_validation=skip_json_validation,
            notification_center=notification_center,
        )

        return Optimizely(
            datafile, event_dispatcher, logger, error_handler, skip_json_validation, user_profile_service,
            sdk_key, config_manager, notification_center, event_processor, settings=settings
        )
