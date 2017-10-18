from abc import abstractmethod
from .helpers import enums
from logger import NoOpLogger


class EventNotificationListener(object):
  """ Event notification listener, if implemented and added to optimizely,
      callback will be notified of event tracking and experiement activation.
  """
  @abstractmethod
  def on_event_tracked(self, event_key, user_id, attributes, event_value, event):
      pass

  @abstractmethod
  def on_experiment_activated(self, experiment, user_id, attributes, variation):
      pass


class LoggingEventNotificationListener(EventNotificationListener):
  def __init__(self):
    self.logger = NoOpLogger()

  def on_event_tracked(self, event_key, user_id, attributes, event_value, event):
    pass

  def on_experiment_activated(self, experiment, user_id, attributes, variation):
    pass


class EventNotificationBroadcaster(object):
  """ Base class which encapsulates methods to broadcast events for tracking impressions and conversions. """

  def __init__(self, logger):
    self.listeners = []
    self.logger = logger

  def add_listener(self, listener):
      if isinstance(listener, EventNotificationListener):
          if self.listeners.count(listener) == 0:
            self.listeners.append(listener)
            self.logger.log(enums.LogLevels.DEBUG, "added listener")
          else:
            self.logger.log(enums.LogLevels.DEBUG, "listener already exists")
      else:
          self.logger.log(enums.LogLevels.DEBUG, "listener not EventNotificationListener")
  def remove_listener(self, listener):
      for ofListener in self.listeners:
          if ofListener == listener:
              self.listeners.remove(listener)
              self.logger.log(enums.LogLevels.DEBUG, "listener removed")
              return
      self.logger.log(enums.LogLevels.DEBUG, "listener not found to remove")
  def clear_listeners(self):
      del self.listeners[:]
  def broadcast_event_tracked(self, event_key, user_id, attributes, event):
      for listener in self.listeners:
          listener.on_event_tracked(event_key, user_id, attributes, event)
  def broadcast_experiment_activated(self, experiment, user_id, attributes, variation):
      for listener in self.listeners:
          listener.on_experiment_activated(experiment, user_id, attributes, variation)
