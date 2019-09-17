# Copyright 2019 Optimizely
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
import threading
import time

from datetime import timedelta
from six.moves import queue

from .user_event import UserEvent
from .event_factory import EventFactory
from optimizely import logger as _logging
from optimizely.event_dispatcher import EventDispatcher as default_event_dispatcher
from optimizely.helpers import validator

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class EventProcessor(ABC):
  """ Class encapsulating event_processor functionality. Override with your own processor
  providing process method. """

  @abc.abstractmethod
  def process(user_event):
    pass


class BatchEventProcessor(EventProcessor):
  """
  BatchEventProcessor is a batched implementation of the EventProcessor.
  The BatchEventProcessor maintains a single consumer thread that pulls events off of
  the blocking queue and buffers them for either a configured batch size or for a
  maximum duration before the resulting LogEvent is sent to the EventDispatcher.
  """

  _DEFAULT_QUEUE_CAPACITY = 1000
  _DEFAULT_BATCH_SIZE = 10
  _DEFAULT_FLUSH_INTERVAL = timedelta(seconds=30)
  _DEFAULT_TIMEOUT_INTERVAL = timedelta(seconds=5)
  _SHUTDOWN_SIGNAL = object()
  _FLUSH_SIGNAL = object()
  LOCK = threading.Lock()

  def __init__(self,
                event_dispatcher,
                logger,
                start_on_init=False,
                event_queue=None,
                batch_size=None,
                flush_interval=None,
                timeout_interval=None):
    """ BatchEventProcessor init method to configure event batching.
    Args:
      event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
      logger: Provides a log method to log messages. By default nothing would be logged.
      start_on_init: Optional boolean param which starts the consumer thread if set to True.
                     By default thread does not start unless 'start' method is called.
      event_queue: Optional component which accumulates the events until dispacthed.
      batch_size: Optional param which defines the upper limit of the number of events in event_queue after which
                  the event_queue will be flushed.
      flush_interval: Optional floating point number representing time interval in seconds after which event_queue will
                      be flushed.
      timeout_interval: Optional floating point number representing time interval in seconds before joining the consumer
                        thread.
    """
    self.event_dispatcher = event_dispatcher or default_event_dispatcher
    self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
    self.event_queue = event_queue or queue.Queue(maxsize=self._DEFAULT_QUEUE_CAPACITY)
    self.batch_size = batch_size if self._validate_intantiation_props(batch_size, 'batch_size') \
                        else self._DEFAULT_BATCH_SIZE
    self.flush_interval = timedelta(seconds=flush_interval) \
                            if self._validate_intantiation_props(flush_interval, 'flush_interval') \
                            else self._DEFAULT_FLUSH_INTERVAL
    self.timeout_interval = timedelta(seconds=timeout_interval) \
                              if self._validate_intantiation_props(timeout_interval, 'timeout_interval') \
                              else self._DEFAULT_TIMEOUT_INTERVAL
    self._disposed = False
    self._is_started = False
    self._current_batch = list()

    if start_on_init is True:
      self.start()

  @property
  def is_started(self):
    return self._is_started

  @property
  def disposed(self):
    return self._disposed

  def _validate_intantiation_props(self, prop, prop_name):
    if (prop_name == 'batch_size' and not isinstance(prop, int)) or prop is None or prop < 1 or \
      not validator.is_finite_number(prop):
      self.logger.info('Using default value for {}.'.format(prop_name))
      return False

    return True

  def _get_time(self, _time=None):
    if _time is None:
      return int(round(time.time()))

    return int(round(_time))

  def start(self):
    if self.is_started and not self.disposed:
      self.logger.warning('Service already started')
      return

    self.flushing_interval_deadline = self._get_time() + self._get_time(self.flush_interval.total_seconds())
    self.executor = threading.Thread(target=self._run)
    self.executor.setDaemon(True)
    self.executor.start()

    self._is_started = True

  def _run(self):
    """ Scheduler method that periodically flushes events queue. """
    try:
      while True:
        if self._get_time() > self.flushing_interval_deadline:
          self._flush_queue()

        try:
          item = self.event_queue.get(True, 0.05)

        except queue.Empty:
          self.logger.debug('Empty queue, sleeping for 50ms.')
          time.sleep(0.05)
          continue

        if item == self._SHUTDOWN_SIGNAL:
          self.logger.debug('Received shutdown signal.')
          break

        if item == self._FLUSH_SIGNAL:
          self.logger.debug('Received flush signal.')
          self._flush_queue()
          continue

        if isinstance(item, UserEvent):
          self._add_to_batch(item)

    except Exception as exception:
      self.logger.error('Uncaught exception processing buffer. Error: ' + str(exception))

    finally:
      self.logger.info('Exiting processing loop. Attempting to flush pending events.')
      self._flush_queue()

  def flush(self):
    """ Adds flush signal to event_queue. """

    self.event_queue.put(self._FLUSH_SIGNAL)

  def _flush_queue(self):
    """ Flushes event_queue by dispatching events. """

    if len(self._current_batch) == 0:
      return

    with self.LOCK:
      to_process_batch = list(self._current_batch)
      self._current_batch = list()

    log_event = EventFactory.create_log_event(to_process_batch, self.logger)

    try:
      self.event_dispatcher.dispatch_event(log_event)
    except Exception as e:
      self.logger.error('Error dispatching event: ' + str(log_event) + ' ' + str(e))

  def process(self, user_event):
    if not isinstance(user_event, UserEvent):
      self.logger.error('Provided event is in an invalid format.')
      return

    self.logger.debug('Received user_event: ' + str(user_event))

    try:
      self.event_queue.put_nowait(user_event)
    except queue.Full:
      self.logger.debug('Payload not accepted by the queue. Current size: {}'.format(str(self.event_queue.qsize())))

  def _add_to_batch(self, user_event):
    if self._should_split(user_event):
      self._flush_queue()
      self._current_batch = list()

    # Reset the deadline if starting a new batch.
    if len(self._current_batch) == 0:
      self.flushing_interval_deadline = self._get_time() + \
        self._get_time(self.flush_interval.total_seconds())

    with self.LOCK:
      self._current_batch.append(user_event)
    if len(self._current_batch) >= self.batch_size:
      self._flush_queue()

  def _should_split(self, user_event):
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
    self.executor.join(self.timeout_interval.total_seconds())

    if self.executor.isAlive():
      self.logger.error('Timeout exceeded while attempting to close for ' + str(self.timeout_interval) + ' ms.')

    self.logger.warning('Stopping Scheduler.')
    self._is_started = False
