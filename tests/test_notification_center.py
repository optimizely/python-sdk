# Copyright 2019, Optimizely
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

from unittest import mock
import unittest

from optimizely import notification_center
from optimizely.helpers import enums


def on_activate_listener(*args):
    pass


def on_config_update_listener(*args):
    pass


def on_decision_listener(*args):
    pass


def on_track_listener(*args):
    pass


def on_log_event_listener(*args):
    pass


class NotificationCenterTest(unittest.TestCase):
    def test_add_notification_listener__valid_type(self):
        """ Test successfully adding a notification listener. """

        test_notification_center = notification_center.NotificationCenter()

        # Test by adding different supported notification listeners.
        self.assertEqual(
            1,
            test_notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate_listener),
        )
        self.assertEqual(
            2,
            test_notification_center.add_notification_listener(
                enums.NotificationTypes.OPTIMIZELY_CONFIG_UPDATE, on_config_update_listener,
            ),
        )
        self.assertEqual(
            3,
            test_notification_center.add_notification_listener(enums.NotificationTypes.DECISION, on_decision_listener),
        )
        self.assertEqual(
            4, test_notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track_listener),
        )

        self.assertEqual(
            5,
            test_notification_center.add_notification_listener(
                enums.NotificationTypes.LOG_EVENT, on_log_event_listener
            ),
        )

    def test_add_notification_listener__multiple_listeners(self):
        """ Test that multiple listeners of the same type can be successfully added. """

        def another_on_activate_listener(*args):
            pass

        test_notification_center = notification_center.NotificationCenter()

        # Test by adding multiple listeners of same type.
        self.assertEqual(
            1,
            test_notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate_listener),
        )
        self.assertEqual(
            2,
            test_notification_center.add_notification_listener(
                enums.NotificationTypes.ACTIVATE, another_on_activate_listener
            ),
        )

    def test_add_notification_listener__invalid_type(self):
        """ Test that adding an invalid notification listener fails and returns -1. """

        mock_logger = mock.Mock()
        test_notification_center = notification_center.NotificationCenter(logger=mock_logger)

        def notif_listener(*args):
            pass

        self.assertEqual(
            -1, test_notification_center.add_notification_listener('invalid_notification_type', notif_listener),
        )
        mock_logger.error.assert_called_once_with(
            'Invalid notification_type: invalid_notification_type provided. ' 'Not adding listener.'
        )

    def test_add_notification_listener__same_listener(self):
        """ Test that adding same listener again does nothing and returns -1. """

        mock_logger = mock.Mock()
        test_notification_center = notification_center.NotificationCenter(logger=mock_logger)

        self.assertEqual(
            1, test_notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track_listener),
        )
        self.assertEqual(
            1, len(test_notification_center.notification_listeners[enums.NotificationTypes.TRACK]),
        )

        # Test that adding same listener again makes no difference.
        self.assertEqual(
            -1, test_notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track_listener),
        )
        self.assertEqual(
            1, len(test_notification_center.notification_listeners[enums.NotificationTypes.TRACK]),
        )
        mock_logger.error.assert_called_once_with('Listener has already been added. Not adding it again.')

    def test_remove_notification_listener__valid_listener(self):
        """ Test that removing a valid notification listener returns True. """

        def another_on_activate_listener(*args):
            pass

        test_notification_center = notification_center.NotificationCenter()

        # Add multiple notification listeners.
        self.assertEqual(
            1,
            test_notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate_listener),
        )
        self.assertEqual(
            2,
            test_notification_center.add_notification_listener(enums.NotificationTypes.DECISION, on_decision_listener),
        )
        self.assertEqual(
            3,
            test_notification_center.add_notification_listener(
                enums.NotificationTypes.ACTIVATE, another_on_activate_listener
            ),
        )

        self.assertEqual(
            2, len(test_notification_center.notification_listeners[enums.NotificationTypes.ACTIVATE]),
        )
        self.assertEqual(
            1, len(test_notification_center.notification_listeners[enums.NotificationTypes.DECISION]),
        )
        self.assertEqual(
            0, len(test_notification_center.notification_listeners[enums.NotificationTypes.TRACK]),
        )
        self.assertEqual(
            0, len(test_notification_center.notification_listeners[enums.NotificationTypes.LOG_EVENT]),
        )

        # Remove one of the activate listeners and assert.
        self.assertTrue(test_notification_center.remove_notification_listener(3))
        self.assertEqual(
            1, len(test_notification_center.notification_listeners[enums.NotificationTypes.ACTIVATE]),
        )

    def test_remove_notification_listener__invalid_listener(self):
        """ Test that removing a invalid notification listener returns False. """

        def another_on_activate_listener(*args):
            pass

        test_notification_center = notification_center.NotificationCenter()

        # Add multiple notification listeners.
        self.assertEqual(
            1,
            test_notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate_listener),
        )
        self.assertEqual(
            2,
            test_notification_center.add_notification_listener(enums.NotificationTypes.DECISION, on_decision_listener),
        )
        self.assertEqual(
            3,
            test_notification_center.add_notification_listener(
                enums.NotificationTypes.ACTIVATE, another_on_activate_listener
            ),
        )
        self.assertEqual(
            4,
            test_notification_center.add_notification_listener(
                enums.NotificationTypes.LOG_EVENT, on_log_event_listener
            ),
        )

        # Try removing a listener which does not exist.
        self.assertFalse(test_notification_center.remove_notification_listener(42))

    def test_clear_notification_listeners(self):
        """ Test that notification listeners of a certain type are cleared
            up on using the clear_notification_listeners API. """

        test_notification_center = notification_center.NotificationCenter()

        # Add listeners
        test_notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate_listener)
        test_notification_center.add_notification_listener(
            enums.NotificationTypes.OPTIMIZELY_CONFIG_UPDATE, on_config_update_listener
        )
        test_notification_center.add_notification_listener(enums.NotificationTypes.DECISION, on_decision_listener)
        test_notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track_listener)
        test_notification_center.add_notification_listener(enums.NotificationTypes.LOG_EVENT, on_log_event_listener)

        # Assert all listeners are there:
        for notification_type in notification_center.NOTIFICATION_TYPES:
            self.assertEqual(
                1, len(test_notification_center.notification_listeners[notification_type]),
            )

        # Clear all of type DECISION.
        test_notification_center.clear_notification_listeners(enums.NotificationTypes.DECISION)
        self.assertEqual(
            0, len(test_notification_center.notification_listeners[enums.NotificationTypes.DECISION]),
        )

    def test_clear_notification_listeners__invalid_type(self):
        """ Test that clear_notification_listener logs error if provided notification type is invalid. """

        mock_logger = mock.Mock()
        test_notification_center = notification_center.NotificationCenter(logger=mock_logger)

        test_notification_center.clear_notification_listeners('invalid_notification_type')
        mock_logger.error.assert_called_once_with(
            'Invalid notification_type: invalid_notification_type provided. ' 'Not removing any listener.'
        )

    def test_clear_all_notification_listeners(self):
        """ Test that all notification listeners are cleared on using the clear all API. """

        test_notification_center = notification_center.NotificationCenter()

        # Add listeners
        test_notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, on_activate_listener)
        test_notification_center.add_notification_listener(
            enums.NotificationTypes.OPTIMIZELY_CONFIG_UPDATE, on_config_update_listener
        )
        test_notification_center.add_notification_listener(enums.NotificationTypes.DECISION, on_decision_listener)
        test_notification_center.add_notification_listener(enums.NotificationTypes.TRACK, on_track_listener)
        test_notification_center.add_notification_listener(enums.NotificationTypes.LOG_EVENT, on_log_event_listener)

        # Assert all listeners are there:
        for notification_type in notification_center.NOTIFICATION_TYPES:
            self.assertEqual(
                1, len(test_notification_center.notification_listeners[notification_type]),
            )

        # Clear all and assert again.
        test_notification_center.clear_all_notification_listeners()

        for notification_type in notification_center.NOTIFICATION_TYPES:
            self.assertEqual(
                0, len(test_notification_center.notification_listeners[notification_type]),
            )

    def set_listener_called_to_true(self):
        """ Helper method which sets the value of listener_called to True. Used to test sending of notifications."""
        self.listener_called = True

    def test_send_notifications(self):
        """ Test that send_notifications dispatches notification to the callback(s). """

        test_notification_center = notification_center.NotificationCenter()
        self.listener_called = False
        test_notification_center.add_notification_listener(
            enums.NotificationTypes.DECISION, self.set_listener_called_to_true
        )
        test_notification_center.send_notifications(enums.NotificationTypes.DECISION)
        self.assertTrue(self.listener_called)

    def test_send_notifications__invalid_notification_type(self):
        """ Test that send_notifications logs exception when notification_type is invalid. """

        mock_logger = mock.Mock()
        test_notification_center = notification_center.NotificationCenter(logger=mock_logger)
        test_notification_center.send_notifications('invalid_notification_type')
        mock_logger.error.assert_called_once_with(
            'Invalid notification_type: invalid_notification_type provided. ' 'Not triggering any notification.'
        )

    def test_send_notifications__fails(self):
        """ Test that send_notifications logs exception when call back fails. """

        # Defining a listener here which expects 2 arguments.
        def some_listener(arg_1, arg_2):
            pass

        mock_logger = mock.Mock()
        test_notification_center = notification_center.NotificationCenter(logger=mock_logger)
        test_notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE, some_listener)

        # Not providing any of the 2 expected arguments during send.
        test_notification_center.send_notifications(enums.NotificationTypes.ACTIVATE)
        mock_logger.exception.assert_called_once_with(
            f'Unknown problem when sending "{enums.NotificationTypes.ACTIVATE}" type notification.'
        )
