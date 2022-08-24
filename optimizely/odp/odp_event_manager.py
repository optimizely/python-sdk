# Copyright 2019-2022, Optimizely
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
from threading import Thread
from typing import Any, Optional
import queue
from queue import Queue
from sys import version_info

from optimizely import logger as _logging
from .odp_event import OdpEvent
from .odp_config import OdpConfig
from .zaius_rest_api_manager import ZaiusRestApiManager
from optimizely.helpers.enums import OdpEventManagerConfig, Errors


if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final  # type: ignore


class Signal:
    '''Used to create unique objects for sending signals to event queue.'''
    pass


class OdpEventManager:
    """
    Class that sends batches of ODP events.

    The OdpEventManager maintains a single consumer thread that pulls events off of
    the queue and buffers them before the events are sent to ODP.
    """

    _SHUTDOWN_SIGNAL: Final = Signal()
    _FLUSH_SIGNAL: Final = Signal()

    def __init__(
        self,
        odp_config: OdpConfig,
        logger: Optional[_logging.Logger] = None,
        api_manager: Optional[ZaiusRestApiManager] = None

    ):
        """ OdpEventManager init method to configure event batching.

        Args:
            odp_config: ODP integration config.
            logger: Optional component which provides a log method to log messages. By default nothing would be logged.
            api_manager: Optional component which sends events to ODP.
        """
        self.logger = logger or _logging.NoOpLogger()
        self.zaius_manager = api_manager or ZaiusRestApiManager(self.logger)
        self.odp_config = odp_config
        self.event_queue: Queue[OdpEvent | Signal] = Queue(OdpEventManagerConfig.DEFAULT_QUEUE_CAPACITY)
        self.batch_size = OdpEventManagerConfig.DEFAULT_BATCH_SIZE
        self._current_batch: list[OdpEvent] = []
        self.executor = Thread(target=self._run, daemon=True)

    @property
    def is_running(self) -> bool:
        """ Property to check if consumer thread is alive or not. """
        return self.executor.is_alive()

    def start(self) -> None:
        """ Starts the batch processing thread to batch events. """
        if self.is_running:
            self.logger.warning('ODP event processor already started.')
            return

        self.executor.start()

    def _run(self) -> None:
        """ Triggered as part of the thread which batches odp events or flushes event_queue and blocks on get
        for flush interval if queue is empty.
        """
        try:
            while True:
                item = self.event_queue.get()

                if item == self._SHUTDOWN_SIGNAL:
                    self.logger.debug('Received ODP event shutdown signal.')
                    self.event_queue.task_done()
                    break

                if item is self._FLUSH_SIGNAL:
                    self.logger.debug('Received ODP event flush signal.')
                    self._flush_batch()
                    self.event_queue.task_done()
                    continue

                if isinstance(item, OdpEvent):
                    self._add_to_batch(item)
                    self.event_queue.task_done()

        except Exception as exception:
            self.logger.error(f'Uncaught exception processing ODP events. Error: {exception}')

        finally:
            self.logger.info('Exiting ODP event processing loop. Attempting to flush pending events.')
            self._flush_batch()

    def flush(self) -> None:
        """ Adds flush signal to event_queue. """

        self.event_queue.put(self._FLUSH_SIGNAL)

    def _flush_batch(self) -> None:
        """ Flushes current batch by dispatching event. """
        batch_len = len(self._current_batch)
        if batch_len == 0:
            self.logger.debug('Nothing to flush.')
            return

        api_key = self.odp_config.get_api_key()
        api_host = self.odp_config.get_api_host()

        if not api_key or not api_host:
            self.logger.debug('ODP event processing has been disabled.')
            return

        self.logger.debug(f'Flushing batch size {batch_len}.')
        should_retry = False
        event_batch = list(self._current_batch)
        try:
            should_retry = self.zaius_manager.send_odp_events(api_key, api_host, event_batch)
        except Exception as e:
            self.logger.error(Errors.ODP_EVENT_FAILED.format(f'{event_batch} {e}'))

        if should_retry:
            self.logger.debug('Error dispatching ODP events, scheduled to retry.')
            return

        self._current_batch = []

    def _add_to_batch(self, odp_event: OdpEvent) -> None:
        """ Method to append received odp event to current batch."""

        self._current_batch.append(odp_event)
        if len(self._current_batch) >= self.batch_size:
            self.logger.debug('Flushing ODP events on batch size.')
            self._flush_batch()

    def stop(self) -> None:
        """ Stops and disposes batch odp event queue."""
        self.event_queue.put(self._SHUTDOWN_SIGNAL)
        self.logger.warning('Stopping ODP Event Queue.')

        if self.is_running:
            self.executor.join()

        if len(self._current_batch) > 0:
            self.logger.error(Errors.ODP_EVENT_FAILED.format(self._current_batch))

        if self.is_running:
            self.logger.error('Error stopping ODP event queue.')

    def send_event(self, type: str, action: str, identifiers: dict[str, str], data: dict[str, Any]) -> None:
        event = OdpEvent(type, action, identifiers, data)
        self.dispatch(event)

    def dispatch(self, event: OdpEvent) -> None:
        if not self.odp_config.odp_integrated():
            self.logger.debug('ODP event processing has been disabled.')
            return

        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            self.logger.error(Errors.ODP_EVENT_FAILED.format("Queue is full"))
