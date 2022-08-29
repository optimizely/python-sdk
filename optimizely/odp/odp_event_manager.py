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
from enum import Enum
from threading import Thread
from typing import Any, Optional
import time
from queue import Empty, Queue, Full

from optimizely import logger as _logging
from .odp_event import OdpEvent
from .odp_config import OdpConfig
from .zaius_rest_api_manager import ZaiusRestApiManager
from optimizely.helpers.enums import OdpEventManagerConfig, Errors


class Signal(Enum):
    """Enum for sending signals to the event queue."""
    SHUTDOWN = 1
    FLUSH = 2


class OdpEventManager:
    """
    Class that sends batches of ODP events.

    The OdpEventManager maintains a single consumer thread that pulls events off of
    the queue and buffers them before events are sent to ODP.
    Waits for odp_config.odp_ready to be set before processing.
    Sends events when the batch size is met or when the flush timeout has elapsed.
    """

    def __init__(
        self,
        odp_config: OdpConfig,
        logger: Optional[_logging.Logger] = None,
        api_manager: Optional[ZaiusRestApiManager] = None
    ):
        """OdpEventManager init method to configure event batching.

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
        self.flush_interval = OdpEventManagerConfig.DEFAULT_FLUSH_INTERVAL
        self._set_flush_deadline()
        self._current_batch: list[OdpEvent] = []
        """_current_batch should only be modified by the processing thread, as it is not thread safe"""
        self.thread = Thread(target=self._run, daemon=True)
        self.thread_exception = False
        """thread_exception will be True if the processing thread did not exit cleanly"""

    @property
    def is_running(self) -> bool:
        """Property to check if consumer thread is alive or not."""
        return self.thread.is_alive()

    def start(self) -> None:
        """Starts the batch processing thread to batch events."""
        if self.is_running:
            self.logger.warning('ODP event queue already started.')
            return

        self.thread.start()

    def _run(self) -> None:
        """Processes the event queue from a child thread. Events are batched until
        the batch size is met or until the flush timeout has elapsed.
        """
        try:
            self.odp_config.odp_ready.wait()
            self.logger.debug('ODP ready. Starting event processing.')

            while True:
                timeout = self._get_time_till_flush()

                try:
                    item = self.event_queue.get(True, timeout)
                except Empty:
                    item = None

                if item == Signal.SHUTDOWN:
                    self.logger.debug('Received ODP event shutdown signal.')
                    break

                elif item == Signal.FLUSH:
                    self.logger.debug('Received ODP event flush signal.')
                    self._flush_batch()
                    self.event_queue.task_done()
                    continue

                elif isinstance(item, OdpEvent):
                    self._add_to_batch(item)
                    self.event_queue.task_done()

                elif len(self._current_batch) > 0:
                    self.logger.debug('Flushing on interval.')
                    self._flush_batch()

                else:
                    self._set_flush_deadline()

        except Exception as exception:
            self.thread_exception = True
            self.logger.error(f'Uncaught exception processing ODP events. Error: {exception}')

        finally:
            self.logger.info('Exiting ODP event processing loop. Attempting to flush pending events.')
            self._flush_batch()
            if item == Signal.SHUTDOWN:
                self.event_queue.task_done()

    def flush(self) -> None:
        """Adds flush signal to event_queue."""
        try:
            self.event_queue.put_nowait(Signal.FLUSH)
        except Full:
            self.logger.error("Error flushing ODP event queue")

    def _flush_batch(self) -> None:
        """Flushes current batch by dispatching event.
        Should only be called by the processing thread."""
        self._set_flush_deadline()

        batch_len = len(self._current_batch)
        if batch_len == 0:
            self.logger.debug('Nothing to flush.')
            return

        api_key = self.odp_config.get_api_key()
        api_host = self.odp_config.get_api_host()

        if not api_key or not api_host:
            self.logger.debug('ODP event queue has been disabled.')
            self._current_batch.clear()
            return

        self.logger.debug(f'Flushing batch size {batch_len}.')
        should_retry = False
        try:
            should_retry = self.zaius_manager.send_odp_events(api_key, api_host, self._current_batch)
        except Exception as e:
            self.logger.error(Errors.ODP_EVENT_FAILED.format(f'{self._current_batch} {e}'))

        if should_retry:
            self.logger.debug('Error dispatching ODP events, scheduled to retry.')
            return

        self._current_batch.clear()

    def _add_to_batch(self, odp_event: OdpEvent) -> None:
        """Appends received ODP event to current batch, flushing if batch is greater than batch size.
        Should only be called by the processing thread."""

        self._current_batch.append(odp_event)
        if len(self._current_batch) >= self.batch_size:
            self.logger.debug('Flushing ODP events on batch size.')
            self._flush_batch()

    def _set_flush_deadline(self) -> None:
        """Sets time that next flush will occur."""
        self._flush_deadline = time.time() + self.flush_interval

    def _get_time_till_flush(self) -> float:
        """Returns seconds until next flush."""
        return max(0, self._flush_deadline - time.time())

    def stop(self) -> None:
        """Flushes and then stops ODP event queue."""
        try:
            self.event_queue.put_nowait(Signal.SHUTDOWN)
        except Full:
            self.logger.error('Error stopping ODP event queue.')
            return

        self.logger.warning('Stopping ODP event queue.')

        if self.is_running:
            self.thread.join()

        if len(self._current_batch) > 0:
            self.logger.error(Errors.ODP_EVENT_FAILED.format(self._current_batch))

        if self.is_running:
            self.logger.error('Error stopping ODP event queue.')

    def send_event(self, type: str, action: str, identifiers: dict[str, str], data: dict[str, Any]) -> None:
        """Create OdpEvent and add it to the event queue."""
        if not self.odp_config.odp_integrated():
            self.logger.debug('ODP event queue has been disabled.')
            return

        try:
            event = OdpEvent(type, action, identifiers, data)
        except TypeError as error:
            self.logger.error(Errors.ODP_EVENT_FAILED.format(error))
            return

        self.dispatch(event)

    def dispatch(self, event: OdpEvent) -> None:
        """Add OdpEvent to the event queue."""
        if self.thread_exception:
            self.logger.error(Errors.ODP_EVENT_FAILED.format('Queue is down'))
            return

        if not self.is_running:
            self.logger.warning('ODP event queue is shutdown, not accepting events.')
            return

        try:
            self.logger.debug('Adding ODP event to queue.')
            self.event_queue.put_nowait(event)
        except Full:
            self.logger.warning(Errors.ODP_EVENT_FAILED.format("Queue is full"))
