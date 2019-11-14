# Copyright 2017-2019, Optimizely
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

from .helpers import enums
from . import logger as optimizely_logger


NOTIFICATION_TYPES = tuple(
    getattr(enums.NotificationTypes, attr) for attr in dir(enums.NotificationTypes) if not attr.startswith('__')
)


class NotificationCenter(object):
    """ Class encapsulating methods to manage notifications and their listeners.
  The enums.NotificationTypes includes predefined notifications."""

    def __init__(self, logger=None):
        self.listener_id = 1
        self.notification_listeners = {}
        for notification_type in NOTIFICATION_TYPES:
            self.notification_listeners[notification_type] = []
        self.logger = optimizely_logger.adapt_logger(logger or optimizely_logger.NoOpLogger())

    def add_notification_listener(self, notification_type, notification_callback):
        """ Add a notification callback to the notification center for a given notification type.

    Args:
      notification_type: A string representing the notification type from helpers.enums.NotificationTypes
      notification_callback: Closure of function to call when event is triggered.

    Returns:
      Integer notification ID used to remove the notification or
      -1 if the notification listener has already been added or
      if the notification type is invalid.
    """

        if notification_type not in NOTIFICATION_TYPES:
            self.logger.error('Invalid notification_type: {} provided. Not adding listener.'.format(notification_type))
            return -1

        for _, listener in self.notification_listeners[notification_type]:
            if listener == notification_callback:
                self.logger.error('Listener has already been added. Not adding it again.')
                return -1

        self.notification_listeners[notification_type].append((self.listener_id, notification_callback))
        current_listener_id = self.listener_id
        self.listener_id += 1

        return current_listener_id

    def remove_notification_listener(self, notification_id):
        """ Remove a previously added notification callback.

    Args:
      notification_id: The numeric id passed back from add_notification_listener

    Returns:
      The function returns boolean true if found and removed, false otherwise.
    """

        for listener in self.notification_listeners.values():
            listener_to_remove = list(filter(lambda tup: tup[0] == notification_id, listener))
            if len(listener_to_remove) > 0:
                listener.remove(listener_to_remove[0])
                return True

        return False

    def clear_notification_listeners(self, notification_type):
        """ Remove notification listeners for a certain notification type.

    Args:
      notification_type: String denoting notification type.
    """

        if notification_type not in NOTIFICATION_TYPES:
            self.logger.error(
                'Invalid notification_type: {} provided. Not removing any listener.'.format(notification_type)
            )
        self.notification_listeners[notification_type] = []

    def clear_notifications(self, notification_type):
        """ (DEPRECATED since 3.2.0, use clear_notification_listeners)
    Remove notification listeners for a certain notification type.

    Args:
      notification_type: key to the list of notifications .helpers.enums.NotificationTypes
    """
        self.clear_notification_listeners(notification_type)

    def clear_all_notification_listeners(self):
        """ Remove all notification listeners. """
        for notification_type in self.notification_listeners.keys():
            self.clear_notification_listeners(notification_type)

    def clear_all_notifications(self):
        """ (DEPRECATED since 3.2.0, use clear_all_notification_listeners)
    Remove all notification listeners. """
        self.clear_all_notification_listeners()

    def send_notifications(self, notification_type, *args):
        """ Fires off the notification for the specific event.  Uses var args to pass in a
        arbitrary list of parameter according to which notification type was fired.

    Args:
      notification_type: Type of notification to fire (String from .helpers.enums.NotificationTypes)
      args: Variable list of arguments to the callback.
    """

        if notification_type not in NOTIFICATION_TYPES:
            self.logger.error(
                'Invalid notification_type: {} provided. ' 'Not triggering any notification.'.format(notification_type)
            )
            return

        if notification_type in self.notification_listeners:
            for notification_id, callback in self.notification_listeners[notification_type]:
                try:
                    callback(*args)
                except:
                    self.logger.exception(
                        'Unknown problem when sending "{}" type notification.'.format(notification_type)
                    )
