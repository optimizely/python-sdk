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

import time
from enum import Enum
from queue import Empty, Queue, Full
from threading import Thread
from typing import Optional

from optimizely import logger as _logging
from optimizely.helpers.enums import OdpEventManagerConfig, Errors, OdpManagerConfig
from .odp_config import OdpConfig, OdpConfigState
from .odp_event import OdpEvent, OdpDataDict
from .odp_event_api_manager import OdpEventApiManager


class Signal(Enum):
    """Enum for sending signals to the event queue."""
    SHUTDOWN = 1
    FLUSH = 2
    UPDATE_CONFIG = 3


class OdpEventManager:
    """
    Class that sends batches of ODP events.

    The OdpEventManager maintains a single consumer thread that pulls events off of
    the queue and buffers them before events are sent to ODP.
    Sends events when the batch size is met or when the flush timeout has elapsed.
    Flushes the event queue after specified time (seconds).
    """

    def __init__(
        self,
        logger: Optional[_logging.Logger] = None,
        api_manager: Optional[OdpEventApiManager] = None,
        request_timeout: Optional[int] = None,
        flush_interval: Optional[int] = None
    ):
        """OdpEventManager init method to configure event batching.

        Args:
            logger: Optional component which provides a log method to log messages. By default nothing would be logged.
            api_manager: Optional component which sends events to ODP.
            request_timeout: Optional event timeout in seconds - wait time for odp platform to respond before failing.
            flush_interval: Optional time to wait for events to accumulate before sending the batch in seconds.
        """
        self.logger = logger or _logging.NoOpLogger()
        self.api_manager = api_manager or OdpEventApiManager(self.logger, request_timeout)

        self.odp_config: Optional[OdpConfig] = None
        self.api_key: Optional[str] = None
        self.api_host: Optional[str] = None

        self.event_queue: Queue[OdpEvent | Signal] = Queue(OdpEventManagerConfig.DEFAULT_QUEUE_CAPACITY)
        self.batch_size = 1 if flush_interval == 0 else OdpEventManagerConfig.DEFAULT_BATCH_SIZE

        self.flush_interval = OdpEventManagerConfig.DEFAULT_FLUSH_INTERVAL if flush_interval is None \
            else flush_interval

        self._flush_deadline: float = 0
        self.retry_count = OdpEventManagerConfig.DEFAULT_RETRY_COUNT
        self._current_batch: list[OdpEvent] = []
        """_current_batch should only be modified by the processing thread, as it is not thread safe"""
        self.thread = Thread(target=self._run, daemon=True)
        self.thread_exception = False
        """thread_exception will be True if the processing thread did not exit cleanly"""

    @property
    def is_running(self) -> bool:
        """Property to check if consumer thread is alive or not."""
        return self.thread.is_alive()

    def start(self, odp_config: OdpConfig) -> None:
        """Starts the batch processing thread to batch events."""
        if self.is_running:
            self.logger.warning('ODP event queue already started.')
            return

        self.odp_config = odp_config
        self.api_host = self.odp_config.get_api_host()
        self.api_key = self.odp_config.get_api_key()

        self.thread.start()

    def _run(self) -> None:
        """Processes the event queue from a child thread. Events are batched until
        the batch size is met or until the flush timeout has elapsed.
        """
        try:
            while True:
                timeout = self._get_queue_timeout()

                try:
                    item = self.event_queue.get(True, timeout)
                except Empty:
                    item = None

                if item == Signal.SHUTDOWN:
                    self.logger.debug('ODP event queue: received shutdown signal.')
                    break

                elif item == Signal.FLUSH:
                    self.logger.debug('ODP event queue: received flush signal.')
                    self._flush_batch()
                    self.event_queue.task_done()

                elif item == Signal.UPDATE_CONFIG:
                    self.logger.debug('ODP event queue: received update config signal.')
                    self._update_config()
                    self.event_queue.task_done()

                elif isinstance(item, OdpEvent):
                    self._add_to_batch(item)
                    self.event_queue.task_done()

                elif len(self._current_batch) > 0:
                    self.logger.debug('ODP event queue: flushing on interval.')
                    self._flush_batch()

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
        batch_len = len(self._current_batch)
        if batch_len == 0:
            self.logger.debug('ODP event queue: nothing to flush.')
            return

        if not self.api_key or not self.api_host:
            self.logger.debug(Errors.ODP_NOT_INTEGRATED)
            self._current_batch.clear()
            return

        self.logger.debug(f'ODP event queue: flushing batch size {batch_len}.')
        should_retry = False

        for i in range(1 + self.retry_count):
            try:
                should_retry = self.api_manager.send_odp_events(self.api_key,
                                                                self.api_host,
                                                                self._current_batch)
            except Exception as error:
                should_retry = False
                self.logger.error(Errors.ODP_EVENT_FAILED.format(f'Error: {error} {self._current_batch}'))

            if not should_retry:
                break
            if i < self.retry_count:
                self.logger.debug('Error dispatching ODP events, scheduled to retry.')

        if should_retry:
            self.logger.error(Errors.ODP_EVENT_FAILED.format(f'Failed after {i} retries: {self._current_batch}'))

        self._current_batch.clear()

    def _add_to_batch(self, odp_event: OdpEvent) -> None:
        """Appends received ODP event to current batch, flushing if batch is greater than batch size.
        Should only be called by the processing thread."""
        if not self._current_batch:
            self._set_flush_deadline()

        self._current_batch.append(odp_event)
        if len(self._current_batch) >= self.batch_size:
            self.logger.debug('ODP event queue: flushing on batch size.')
            self._flush_batch()

    def _set_flush_deadline(self) -> None:
        """Sets time that next flush will occur."""
        self._flush_deadline = time.time() + self.flush_interval

    def _get_time_till_flush(self) -> float:
        """Returns seconds until next flush; no less than 0."""
        return max(0, self._flush_deadline - time.time())

    def _get_queue_timeout(self) -> Optional[float]:
        """Returns seconds until next flush or None if current batch is empty."""
        if len(self._current_batch) == 0:
            return None
        return self._get_time_till_flush()

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

    def send_event(self, type: str, action: str, identifiers: dict[str, str], data: OdpDataDict) -> None:
        """Create OdpEvent and add it to the event queue."""
        if not self.odp_config:
            self.logger.debug('ODP event queue: cannot send before config has been set.')
            return

        odp_state = self.odp_config.odp_state()
        if odp_state == OdpConfigState.UNDETERMINED:
            self.logger.debug('ODP event queue: cannot send before the datafile has loaded.')
            return

        if odp_state == OdpConfigState.NOT_INTEGRATED:
            self.logger.debug(Errors.ODP_NOT_INTEGRATED)
            return

        self.dispatch(OdpEvent(type, action, identifiers, data))

    def dispatch(self, event: OdpEvent) -> None:
        """Add OdpEvent to the event queue."""
        if self.thread_exception:
            self.logger.error(Errors.ODP_EVENT_FAILED.format('Queue is down'))
            return

        if not self.is_running:
            self.logger.warning('ODP event queue is shutdown, not accepting events.')
            return

        try:
            self.logger.debug('ODP event queue: adding event.')
            self.event_queue.put_nowait(event)
        except Full:
            self.logger.warning(Errors.ODP_EVENT_FAILED.format("Queue is full"))

    def identify_user(self, user_id: str) -> None:
        self.send_event(OdpManagerConfig.EVENT_TYPE, 'identified',
                        {OdpManagerConfig.KEY_FOR_USER_ID: user_id}, {})

    def update_config(self) -> None:
        """Adds update config signal to event_queue."""
        try:
            self.event_queue.put_nowait(Signal.UPDATE_CONFIG)
        except Full:
            self.logger.error("Error updating ODP config for the event queue")

    def _update_config(self) -> None:
        """Updates the configuration used to send events."""
        if len(self._current_batch) > 0:
            self._flush_batch()

        if self.odp_config:
            self.api_host = self.odp_config.get_api_host()
            self.api_key = self.odp_config.get_api_key()
