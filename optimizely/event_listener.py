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
    """ Abstract method triggered when optimizely track is called.
   Args:
    event_key: The event key passed into track.
    user_id: The user Id being tracked.
    attributes: The attributes passed into the track call.
    event: The event.

    """
    pass

  @abstractmethod
  def on_experiment_activated(self, experiment, user_id, attributes, variation, event):
    """ Abstract method triggered when optimizely activate is called.
    Args:
     experiment: The experiment being activated.
     user_id: The user_id passed into activate.
     attributes: The attributes passed into activate.
     variation: The variation passed back from an activate.
     event: The Optimizely event object.

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

  def on_experiment_activated(self, experiment, user_id, attributes, variation, event):
    self.logger.log(enums.LogLevels.DEBUG,"inside experiment activated")


class EventNotificationBroadcaster(object):
  """ Base class which encapsulates methods to broadcast events for tracking impressions and conversions. """

  def __init__(self, logger):
    """ init
    Args:
      logger: SimpleLogger or NoOpLogger
    """
    self.listeners = []
    self.logger = logger

  def add_listener(self, listener):
    """ Add a EventNotificationListener
    Args:
      listener: A subclass of EventNotificationListener

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
    """ Remove a listener added earlier.
    Args:
      listener: The listener to remove

    """
    for ofListener in self.listeners:
      if ofListener == listener:
        self.listeners.remove(listener)
        self.logger.log(enums.LogLevels.DEBUG, "listener removed")
        return
    self.logger.log(enums.LogLevels.DEBUG, "listener not found to remove")

  def clear_listeners(self):
    """ Clear all the listeners out.

    """
    del self.listeners[:]

  def broadcast_event_tracked(self, event_key, user_id, attributes, event_tags, event):
    """ Broadcast a track event was called.
    Args:
      event_key: The event key
      user_id:  The user id passed into optimizely.track
      attributes: Attributes passed into optimizely.track
      event: The event logged by the event dispatcher

    """
    for listener in self.listeners:
      listener.on_event_tracked(event_key, user_id, attributes, event_tags, event)

  def broadcast_experiment_activated(self, experiment, user_id, attributes, variation, event):
    """ Broadcast an experiment activate was called.
    Args:
      experiment: The experiment that was activated.
      user_id: The user_id passed into activate
      attributes: The attributes passed into activate
      variation: The variation that was passed back from the activate
      event: Optimizely event object being sent.

    """
    for listener in self.listeners:
      listener.on_experiment_activated(experiment, user_id, attributes, variation, event)
