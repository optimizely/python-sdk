# Copyright 2019-2020 Optimizely
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

import abc
import numbers
import threading
import time

from datetime import timedelta
from six.moves import queue

from optimizely import logger as _logging
from optimizely import notification_center as _notification_center
from optimizely.event_dispatcher import EventDispatcher as default_event_dispatcher
from optimizely.helpers import enums
from optimizely.helpers import validator
from .event_factory import EventFactory
from .user_event import UserEvent

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class BaseEventProcessor(ABC):
    """ Class encapsulating event processing. Override with your own implementation. """

    @abc.abstractmethod
    def process(self, user_event):
        """ Method to provide intermediary processing stage within event production.
    Args:
      user_event: UserEvent instance that needs to be processed and dispatched.
    """
        pass


class BatchEventProcessor(BaseEventProcessor):
    """
  BatchEventProcessor is an implementation of the BaseEventProcessor that batches events.

  The BatchEventProcessor maintains a single consumer thread that pulls events off of
  the blocking queue and buffers them for either a configured batch size or for a
  maximum duration before the resulting LogEvent is sent to the EventDispatcher.
  """

    _DEFAULT_QUEUE_CAPACITY = 1000
    _DEFAULT_BATCH_SIZE = 10
    _DEFAULT_FLUSH_INTERVAL = 30
    _DEFAULT_TIMEOUT_INTERVAL = 5
    _SHUTDOWN_SIGNAL = object()
    _FLUSH_SIGNAL = object()
    LOCK = threading.Lock()

    def __init__(
        self,
        event_dispatcher,
        logger=None,
        start_on_init=False,
        event_queue=None,
        batch_size=None,
        flush_interval=None,
        timeout_interval=None,
        notification_center=None,
    ):
        """ BatchEventProcessor init method to configure event batching.

    Args:
      event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
      logger: Optional component which provides a log method to log messages. By default nothing would be logged.
      start_on_init: Optional boolean param which starts the consumer thread if set to True.
                     Default value is False.
      event_queue: Optional component which accumulates the events until dispacthed.
      batch_size: Optional param which defines the upper limit on the number of events in event_queue after which
                  the event_queue will be flushed.
      flush_interval: Optional floating point number representing time interval in seconds after which event_queue will
                      be flushed.
      timeout_interval: Optional floating point number representing time interval in seconds before joining the consumer
                        thread.
      notification_center: Optional instance of notification_center.NotificationCenter.
    """
        self.event_dispatcher = event_dispatcher or default_event_dispatcher
        self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
        self.event_queue = event_queue or queue.Queue(maxsize=self._DEFAULT_QUEUE_CAPACITY)
        self.batch_size = (
            batch_size
            if self._validate_instantiation_props(batch_size, 'batch_size', self._DEFAULT_BATCH_SIZE)
            else self._DEFAULT_BATCH_SIZE
        )
        self.flush_interval = (
            timedelta(seconds=flush_interval)
            if self._validate_instantiation_props(flush_interval, 'flush_interval', self._DEFAULT_FLUSH_INTERVAL)
            else timedelta(seconds=self._DEFAULT_FLUSH_INTERVAL)
        )
        self.timeout_interval = (
            timedelta(seconds=timeout_interval)
            if self._validate_instantiation_props(timeout_interval, 'timeout_interval', self._DEFAULT_TIMEOUT_INTERVAL)
            else timedelta(seconds=self._DEFAULT_TIMEOUT_INTERVAL)
        )

        self.notification_center = notification_center or _notification_center.NotificationCenter(self.logger)
        self._current_batch = list()

        if not validator.is_notification_center_valid(self.notification_center):
            self.logger.error(enums.Errors.INVALID_INPUT.format('notification_center'))
            self.logger.debug('Creating notification center for use.')
            self.notification_center = _notification_center.NotificationCenter(self.logger)

        self.executor = None
        if start_on_init is True:
            self.start()

    @property
    def is_running(self):
        """ Property to check if consumer thread is alive or not. """
        return self.executor.isAlive() if self.executor else False

    def _validate_instantiation_props(self, prop, prop_name, default_value):
        """ Method to determine if instantiation properties like batch_size, flush_interval
    and timeout_interval are valid.

    Args:
      prop: Property value that needs to be validated.
      prop_name: Property name.
      default_value: Default value for property.

    Returns:
      False if property value is None or less than or equal to 0 or not a finite number.
      False if property name is batch_size and value is a floating point number.
      True otherwise.
    """
        is_valid = True

        if prop is None or not validator.is_finite_number(prop) or prop <= 0:
            is_valid = False

        if prop_name == 'batch_size' and not isinstance(prop, numbers.Integral):
            is_valid = False

        if is_valid is False:
            self.logger.info('Using default value {} for {}.'.format(default_value, prop_name))

        return is_valid

    def _get_time(self, _time=None):
        """ Method to return time as float in seconds. If _time is None, uses current time.

    Args:
      _time: time in seconds.

    Returns:
      Float time in seconds.
    """
        if _time is None:
            return time.time()

        return _time

    def start(self):
        """ Starts the batch processing thread to batch events. """
        if hasattr(self, 'executor') and self.is_running:
            self.logger.warning('BatchEventProcessor already started.')
            return

        self.flushing_interval_deadline = self._get_time() + self._get_time(self.flush_interval.total_seconds())
        self.executor = threading.Thread(target=self._run)
        self.executor.setDaemon(True)
        self.executor.start()

    def _run(self):
        """ Triggered as part of the thread which batches events or flushes event_queue and hangs on get
    for flush interval if queue is empty.
    """
        try:
            while True:
                if self._get_time() >= self.flushing_interval_deadline:
                    self._flush_batch()
                    self.flushing_interval_deadline = self._get_time() + \
                        self._get_time(self.flush_interval.total_seconds())
                    self.logger.debug('Flush interval deadline. Flushed batch.')

                try:
                    interval = self.flushing_interval_deadline - self._get_time()
                    item = self.event_queue.get(True, interval)

                    if item is None:
                        continue

                except queue.Empty:
                    continue

                if item == self._SHUTDOWN_SIGNAL:
                    self.logger.debug('Received shutdown signal.')
                    break

                if item == self._FLUSH_SIGNAL:
                    self.logger.debug('Received flush signal.')
                    self._flush_batch()
                    continue

                if isinstance(item, UserEvent):
                    self._add_to_batch(item)

        except Exception as exception:
            self.logger.error('Uncaught exception processing buffer. Error: ' + str(exception))

        finally:
            self.logger.info('Exiting processing loop. Attempting to flush pending events.')
            self._flush_batch()

    def flush(self):
        """ Adds flush signal to event_queue. """

        self.event_queue.put(self._FLUSH_SIGNAL)

    def _flush_batch(self):
        """ Flushes current batch by dispatching event. """
        batch_len = len(self._current_batch)
        if batch_len == 0:
            self.logger.debug('Nothing to flush.')
            return

        self.logger.debug('Flushing batch size ' + str(batch_len))

        with self.LOCK:
            to_process_batch = list(self._current_batch)
            self._current_batch = list()

        log_event = EventFactory.create_log_event(to_process_batch, self.logger)

        self.notification_center.send_notifications(enums.NotificationTypes.LOG_EVENT, log_event)

        try:
            self.event_dispatcher.dispatch_event(log_event)
        except Exception as e:
            self.logger.error('Error dispatching event: ' + str(log_event) + ' ' + str(e))

    def process(self, user_event):
        """ Method to process the user_event by putting it in event_queue.

    Args:
      user_event: UserEvent Instance.
    """
        if not isinstance(user_event, UserEvent):
            self.logger.error('Provided event is in an invalid format.')
            return

        self.logger.debug(
            'Received event of type {} for user {}.'.format(type(user_event).__name__, user_event.user_id)
        )

        try:
            self.event_queue.put_nowait(user_event)
        except queue.Full:
            self.logger.debug(
                'Payload not accepted by the queue. Current size: {}'.format(str(self.event_queue.qsize()))
            )

    def _add_to_batch(self, user_event):
        """ Method to append received user event to current batch.

    Args:
      user_event: UserEvent Instance.
    """
        if self._should_split(user_event):
            self.logger.debug('Flushing batch on split.')
            self._flush_batch()

        # Reset the deadline if starting a new batch.
        if len(self._current_batch) == 0:
            self.flushing_interval_deadline = self._get_time() + self._get_time(self.flush_interval.total_seconds())

        with self.LOCK:
            self._current_batch.append(user_event)
        if len(self._current_batch) >= self.batch_size:
            self.logger.debug('Flushing on batch size.')
            self._flush_batch()

    def _should_split(self, user_event):
        """ Method to check if current event batch should split into two.

    Args:
      user_event: UserEvent Instance.

    Returns:
      - True, if revision number and project_id of last event in current batch do not match received event's
      revision number and project id respectively.
      - False, otherwise.
    """
        if len(self._current_batch) == 0:
            return False

        current_context = self._current_batch[-1].event_context
        new_context = user_event.event_context

        if current_context.revision != new_context.revision:
            return True

        if current_context.project_id != new_context.project_id:
            return True

        return False

    def stop(self):
        """ Stops and disposes batch event processor. """
        self.event_queue.put(self._SHUTDOWN_SIGNAL)
        self.logger.warning('Stopping Scheduler.')

        if self.executor:
            self.executor.join(self.timeout_interval.total_seconds())

        if self.is_running:
            self.logger.error('Timeout exceeded while attempting to close for ' + str(self.timeout_interval) + ' ms.')


class ForwardingEventProcessor(BaseEventProcessor):
    """
  ForwardingEventProcessor serves as the default EventProcessor.

  The ForwardingEventProcessor sends the LogEvent to EventDispatcher as soon as it is received.
  """

    def __init__(self, event_dispatcher, logger=None, notification_center=None):
        """ ForwardingEventProcessor init method to configure event dispatching.

    Args:
      event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
      logger: Optional component which provides a log method to log messages. By default nothing would be logged.
      notification_center: Optional instance of notification_center.NotificationCenter.
    """
        self.event_dispatcher = event_dispatcher or default_event_dispatcher
        self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
        self.notification_center = notification_center or _notification_center.NotificationCenter(self.logger)

        if not validator.is_notification_center_valid(self.notification_center):
            self.logger.error(enums.Errors.INVALID_INPUT.format('notification_center'))
            self.notification_center = _notification_center.NotificationCenter()

    def process(self, user_event):
        """ Method to process the user_event by dispatching it.

    Args:
      user_event: UserEvent Instance.
    """
        if not isinstance(user_event, UserEvent):
            self.logger.error('Provided event is in an invalid format.')
            return

        self.logger.debug(
            'Received event of type {} for user {}.'.format(type(user_event).__name__, user_event.user_id)
        )

        log_event = EventFactory.create_log_event(user_event, self.logger)

        self.notification_center.send_notifications(enums.NotificationTypes.LOG_EVENT, log_event)

        try:
            self.event_dispatcher.dispatch_event(log_event)
        except Exception as e:
            self.logger.exception('Error dispatching event: ' + str(log_event) + ' ' + str(e))
