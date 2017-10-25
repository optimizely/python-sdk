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
import sys

from .helpers import enums

class NotificationCenter(object):
  """ Class encapsulating Broadcast Notifications. The enums.NotifcationTypes includes predefined notifications."""
  def __init__(self, logger):
    self.notification_id = 1
    self.notifications = {}
    for attr, value in enums.NotificationTypes.__dict__.iteritems():
      self.notifications[value] = []
    self.logger = logger

  def add_notification(self, notification_type, notification_callback):
    """ Add a notification callback to the notification center.

    Args:
      notification_type: .helpers.enums.NotificationTypes
      notification_callback: closure of function to call when event is triggered.
    Returns:
      notification id used to remove the notification
    """
    if notification_type not in self.notifications:
      self.notifications[notification_type] = [(self.notification_id, notification_callback)]
    else:
      for callback in self.notifications[notification_type]:
        if callback[1] == notification_callback:
          return -1
      self.notifications[notification_type].append((self.notification_id, notification_callback))

    ret_val = self.notification_id

    self.notification_id += 1

    return ret_val

  def remove_notification(self, notification_id):
    """ Remove a previously added notification callback.

    Args:
      notification_id:
    Returns:
      The function returns true if found and removed, false otherwise.
    """
    for key in self.notifications.keys():
      for callback in self.notifications[key]:
        if callback[0] == notification_id:
          self.notifications[key].remove(callback)
          return True

    return False

  def clean_all_notifications(self):
    """ Remove all notifications """
    for key in self.notifications.keys():
      self.notifications[key] = []

  def clear_notifications(self, notification_type):
    """ Remove notifications for a certain notification type

    Args:
      notification_type: key to the list of notifications .helpers.enums.NotificationTypes
    """
    self.notifications[notification_type] = []

  def fire_notifications(self, notification_type, *args):
    """ Fires off the notification for the specific event.  Uses var args to pass in a
    arbitrary list of parameter according to which notification type was fired.

    Args:
      notification_type: Type of notification to fire.
      args: list of arguments to the callback.
    """
    if notification_type in self.notifications:
      for callback in self.notifications[notification_type]:
        try:
          callback[1](*args)
        except:
          error = sys.exc_info()[1]
          self.logger.log(enums.LogLevels.ERROR, 'Problem calling notify callback. Error: %s' % str(error))


