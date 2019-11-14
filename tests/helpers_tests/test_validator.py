# Copyright 2016-2019, Optimizely
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

import json
import mock

from six import PY2

from optimizely import config_manager
from optimizely import error_handler
from optimizely import event_dispatcher
from optimizely import logger
from optimizely.event import event_processor
from optimizely.helpers import validator

from tests import base


class ValidatorTest(base.BaseTest):
    def test_is_config_manager_valid__returns_true(self):
        """ Test that valid config_manager returns True for valid config manager implementation. """

        self.assertTrue(validator.is_config_manager_valid(config_manager.StaticConfigManager))
        self.assertTrue(validator.is_config_manager_valid(config_manager.PollingConfigManager))

    def test_is_config_manager_valid__returns_false(self):
        """ Test that invalid config_manager returns False for invalid config manager implementation. """

        class CustomConfigManager(object):
            def some_other_method(self):
                pass

        self.assertFalse(validator.is_config_manager_valid(CustomConfigManager()))

    def test_is_event_processor_valid__returns_true(self):
        """ Test that valid event_processor returns True. """

        self.assertTrue(validator.is_event_processor_valid(event_processor.ForwardingEventProcessor))

    def test_is_event_processor_valid__returns_false(self):
        """ Test that invalid event_processor returns False. """

        class CustomEventProcessor(object):
            def some_other_method(self):
                pass

        self.assertFalse(validator.is_event_processor_valid(CustomEventProcessor))

    def test_is_datafile_valid__returns_true(self):
        """ Test that valid datafile returns True. """

        self.assertTrue(validator.is_datafile_valid(json.dumps(self.config_dict)))

    def test_is_datafile_valid__returns_false(self):
        """ Test that invalid datafile returns False. """

        self.assertFalse(validator.is_datafile_valid(json.dumps({'invalid_key': 'invalid_value'})))

    def test_is_event_dispatcher_valid__returns_true(self):
        """ Test that valid event_dispatcher returns True. """

        self.assertTrue(validator.is_event_dispatcher_valid(event_dispatcher.EventDispatcher))

    def test_is_event_dispatcher_valid__returns_false(self):
        """ Test that invalid event_dispatcher returns False. """

        class CustomEventDispatcher(object):
            def some_other_method(self):
                pass

        self.assertFalse(validator.is_event_dispatcher_valid(CustomEventDispatcher))

    def test_is_logger_valid__returns_true(self):
        """ Test that valid logger returns True. """

        self.assertTrue(validator.is_logger_valid(logger.NoOpLogger))

    def test_is_logger_valid__returns_false(self):
        """ Test that invalid logger returns False. """

        class CustomLogger(object):
            def some_other_method(self):
                pass

        self.assertFalse(validator.is_logger_valid(CustomLogger))

    def test_is_error_handler_valid__returns_true(self):
        """ Test that valid error_handler returns True. """

        self.assertTrue(validator.is_error_handler_valid(error_handler.NoOpErrorHandler))

    def test_is_error_handler_valid__returns_false(self):
        """ Test that invalid error_handler returns False. """

        class CustomErrorHandler(object):
            def some_other_method(self):
                pass

        self.assertFalse(validator.is_error_handler_valid(CustomErrorHandler))

    def test_are_attributes_valid__returns_true(self):
        """ Test that valid attributes returns True. """

        self.assertTrue(validator.are_attributes_valid({'key': 'value'}))

    def test_are_attributes_valid__returns_false(self):
        """ Test that invalid attributes returns False. """

        self.assertFalse(validator.are_attributes_valid('key:value'))
        self.assertFalse(validator.are_attributes_valid(['key', 'value']))
        self.assertFalse(validator.are_attributes_valid(42))

    def test_are_event_tags_valid__returns_true(self):
        """ Test that valid event tags returns True. """

        self.assertTrue(validator.are_event_tags_valid({'key': 'value', 'revenue': 0}))

    def test_are_event_tags_valid__returns_false(self):
        """ Test that invalid event tags returns False. """

        self.assertFalse(validator.are_event_tags_valid('key:value'))
        self.assertFalse(validator.are_event_tags_valid(['key', 'value']))
        self.assertFalse(validator.are_event_tags_valid(42))

    def test_is_user_profile_valid__returns_true(self):
        """ Test that valid user profile returns True. """

        self.assertTrue(validator.is_user_profile_valid({'user_id': 'test_user', 'experiment_bucket_map': {}}))
        self.assertTrue(
            validator.is_user_profile_valid(
                {'user_id': 'test_user', 'experiment_bucket_map': {'1234': {'variation_id': '5678'}}}
            )
        )
        self.assertTrue(
            validator.is_user_profile_valid(
                {
                    'user_id': 'test_user',
                    'experiment_bucket_map': {'1234': {'variation_id': '5678'}},
                    'additional_key': 'additional_value',
                }
            )
        )
        self.assertTrue(
            validator.is_user_profile_valid(
                {
                    'user_id': 'test_user',
                    'experiment_bucket_map': {'1234': {'variation_id': '5678', 'additional_key': 'additional_value'}},
                }
            )
        )

    def test_is_user_profile_valid__returns_false(self):
        """ Test that invalid user profile returns True. """

        self.assertFalse(validator.is_user_profile_valid(None))
        self.assertFalse(validator.is_user_profile_valid('user_id'))
        self.assertFalse(validator.is_user_profile_valid({'some_key': 'some_value'}))
        self.assertFalse(validator.is_user_profile_valid({'user_id': 'test_user'}))
        self.assertFalse(
            validator.is_user_profile_valid({'user_id': 'test_user', 'experiment_bucket_map': 'some_value'})
        )
        self.assertFalse(
            validator.is_user_profile_valid({'user_id': 'test_user', 'experiment_bucket_map': {'1234': 'some_value'}})
        )
        self.assertFalse(
            validator.is_user_profile_valid(
                {
                    'user_id': 'test_user',
                    'experiment_bucket_map': {'1234': {'variation_id': '5678'}, '1235': {'some_key': 'some_value'}},
                }
            )
        )

    def test_is_non_empty_string(self):
        """ Test that the method returns True only for a non-empty string. """

        self.assertFalse(validator.is_non_empty_string(None))
        self.assertFalse(validator.is_non_empty_string([]))
        self.assertFalse(validator.is_non_empty_string({}))
        self.assertFalse(validator.is_non_empty_string(0))
        self.assertFalse(validator.is_non_empty_string(99))
        self.assertFalse(validator.is_non_empty_string(1.2))
        self.assertFalse(validator.is_non_empty_string(True))
        self.assertFalse(validator.is_non_empty_string(False))
        self.assertFalse(validator.is_non_empty_string(''))

        self.assertTrue(validator.is_non_empty_string('0'))
        self.assertTrue(validator.is_non_empty_string('test_user'))

    def test_is_attribute_valid(self):
        """ Test that non-string attribute key or unsupported attribute value returns False."""

        # test invalid attribute keys
        self.assertFalse(validator.is_attribute_valid(5, 'test_value'))
        self.assertFalse(validator.is_attribute_valid(True, 'test_value'))
        self.assertFalse(validator.is_attribute_valid(5.5, 'test_value'))

        # test invalid attribute values
        self.assertFalse(validator.is_attribute_valid('test_attribute', None))
        self.assertFalse(validator.is_attribute_valid('test_attribute', {}))
        self.assertFalse(validator.is_attribute_valid('test_attribute', []))
        self.assertFalse(validator.is_attribute_valid('test_attribute', ()))

        # test valid attribute values
        self.assertTrue(validator.is_attribute_valid('test_attribute', False))
        self.assertTrue(validator.is_attribute_valid('test_attribute', True))
        self.assertTrue(validator.is_attribute_valid('test_attribute', 0))
        self.assertTrue(validator.is_attribute_valid('test_attribute', 0.0))
        self.assertTrue(validator.is_attribute_valid('test_attribute', ""))
        self.assertTrue(validator.is_attribute_valid('test_attribute', 'test_value'))

        # test if attribute value is a number, it calls is_finite_number and returns it's result
        with mock.patch('optimizely.helpers.validator.is_finite_number', return_value=True) as mock_is_finite:
            self.assertTrue(validator.is_attribute_valid('test_attribute', 5))

        mock_is_finite.assert_called_once_with(5)

        with mock.patch('optimizely.helpers.validator.is_finite_number', return_value=False) as mock_is_finite:
            self.assertFalse(validator.is_attribute_valid('test_attribute', 5.5))

        mock_is_finite.assert_called_once_with(5.5)

        if PY2:
            with mock.patch('optimizely.helpers.validator.is_finite_number', return_value=None) as mock_is_finite:
                self.assertIsNone(validator.is_attribute_valid('test_attribute', long(5)))

            mock_is_finite.assert_called_once_with(long(5))

    def test_is_finite_number(self):
        """ Test that it returns true if value is a number and not NAN, INF, -INF or greater than 2^53.
        Otherwise False.
    """
        # test non number values
        self.assertFalse(validator.is_finite_number('HelloWorld'))
        self.assertFalse(validator.is_finite_number(True))
        self.assertFalse(validator.is_finite_number(False))
        self.assertFalse(validator.is_finite_number(None))
        self.assertFalse(validator.is_finite_number({}))
        self.assertFalse(validator.is_finite_number([]))
        self.assertFalse(validator.is_finite_number(()))

        # test invalid numbers
        self.assertFalse(validator.is_finite_number(float('inf')))
        self.assertFalse(validator.is_finite_number(float('-inf')))
        self.assertFalse(validator.is_finite_number(float('nan')))
        self.assertFalse(validator.is_finite_number(int(2 ** 53) + 1))
        self.assertFalse(validator.is_finite_number(-int(2 ** 53) - 1))
        self.assertFalse(validator.is_finite_number(float(2 ** 53) + 2.0))
        self.assertFalse(validator.is_finite_number(-float(2 ** 53) - 2.0))
        if PY2:
            self.assertFalse(validator.is_finite_number(long(2 ** 53) + 1))
            self.assertFalse(validator.is_finite_number(-long(2 ** 53) - 1))

        # test valid numbers
        self.assertTrue(validator.is_finite_number(0))
        self.assertTrue(validator.is_finite_number(5))
        self.assertTrue(validator.is_finite_number(5.5))
        # float(2**53) + 1.0 evaluates to float(2**53)
        self.assertTrue(validator.is_finite_number(float(2 ** 53) + 1.0))
        self.assertTrue(validator.is_finite_number(-float(2 ** 53) - 1.0))
        self.assertTrue(validator.is_finite_number(int(2 ** 53)))
        if PY2:
            self.assertTrue(validator.is_finite_number(long(2 ** 53)))


class DatafileValidationTests(base.BaseTest):
    def test_is_datafile_valid__returns_true(self):
        """ Test that valid datafile returns True. """

        self.assertTrue(validator.is_datafile_valid(json.dumps(self.config_dict)))

    def test_is_datafile_valid__returns_false(self):
        """ Test that invalid datafile returns False. """

        # When schema is not valid
        self.assertFalse(validator.is_datafile_valid(json.dumps({'invalid_key': 'invalid_value'})))
