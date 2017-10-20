# Copyright 2017, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import abstractmethod, ABCMeta
from .helpers import enums
from .logger import SimpleLogger


class EventNotificationListener(object):
  """ Event notification listener: If implemented and added to optimizely via add_listener,
    callback will be notified of event tracking and experiment activation.
"""
  __metaclass__ = ABCMeta

  @abstractmethod
  def on_event_tracked(self, event_key, user_id, attributes, event_tags, event):
    """
    Abstract method triggered when optimizely track is called.
    :param event_key: The event key passed into track.
    :param user_id: The user Id being tracked.
    :param attributes: The attributes passed into the track call.
    :param event: The event.
    :return:
    """
    pass

  @abstractmethod
  def on_experiment_activated(self, experiment, user_id, attributes, variation):
    """
    Abstract method triggered when optimizely activate is called.
    :param experiment: The experiment being activated.
    :param user_id: The user_id passed into activate.
    :param attributes: The attributes passed into activate.
    :param variation: The variation passed back from an activate.
    :return:
    """
    pass


class LoggingEventNotificationListener(EventNotificationListener):
  """
  A default simple logger implementation of EventNotificationListener
  """
  def __init__(self):
    self.logger = SimpleLogger()

  def on_event_tracked(self, event_key, user_id, attributes, event_tags, event):
    self.logger.log(enums.LogLevels.DEBUG,"inside event track")

  def on_experiment_activated(self, experiment, user_id, attributes, variation):
    self.logger.log(enums.LogLevels.DEBUG,"inside experiment activated")


class EventNotificationBroadcaster(object):
  """ Base class which encapsulates methods to broadcast events for tracking impressions and conversions. """

  def __init__(self, logger):
    """
    init
    :param logger: SimpleLogger or NoOpLogger
    """
    self.listeners = []
    self.logger = logger

  def add_listener(self, listener):
    """
    Add a EventNotificationListener
    :param listener: A subclass of EventNotificationListener
    :return:
    """
    if isinstance(listener, EventNotificationListener):
      if self.listeners.count(listener) == 0:
        self.listeners.append(listener)
        self.logger.log(enums.LogLevels.DEBUG, "added listener")
      else:
        self.logger.log(enums.LogLevels.DEBUG, "listener already exists")
    else:
      self.logger.log(enums.LogLevels.DEBUG, "listener not EventNotificationListener")

  def remove_listener(self, listener):
    """
    Remove a listener added earlier.
    :param listener: The listener to remove
    :return:
    """
    for ofListener in self.listeners:
      if ofListener == listener:
        self.listeners.remove(listener)
        self.logger.log(enums.LogLevels.DEBUG, "listener removed")
        return
    self.logger.log(enums.LogLevels.DEBUG, "listener not found to remove")

  def clear_listeners(self):
    """
    Clear all the listeners out.
    :return:
    """
    del self.listeners[:]

  def broadcast_event_tracked(self, event_key, user_id, attributes, event_tags, event):
    """
    Broadcast a track event was called.
    :param event_key: The event key
    :param user_id:  The user id passed into optimizely.track
    :param attributes: Attributes passed into optimizely.track
    :param event: The event logged by the event dispatcher
    :return:
    """
    for listener in self.listeners:
      listener.on_event_tracked(event_key, user_id, attributes, event_tags, event)

  def broadcast_experiment_activated(self, experiment, user_id, attributes, variation):
    """
    Broadcast an experiment activate was called.
    :param experiment: The experiment that was activated.
    :param user_id: The user_id passed into activate
    :param attributes: The attributes passed into activate
    :param variation: The variation that was passed back from the activate
    :return:
    """
    for listener in self.listeners:
      listener.on_experiment_activated(experiment, user_id, attributes, variation)
