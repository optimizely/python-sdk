# Copyright 2021, Optimizely
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

import mock

from optimizely.config_manager import PollingConfigManager
from optimizely.error_handler import NoOpErrorHandler
from optimizely.event_dispatcher import EventDispatcher
from optimizely.notification_center import NotificationCenter
from optimizely.optimizely_factory import OptimizelyFactory
from optimizely.user_profile import UserProfileService
from . import base


@mock.patch('requests.get')
class OptimizelyFactoryTest(base.BaseTest):
    def setUp(self):
        self.datafile = '{ revision: "42" }'
        self.error_handler = NoOpErrorHandler()
        self.mock_client_logger = mock.MagicMock()
        self.notification_center = NotificationCenter(self.mock_client_logger)
        self.event_dispatcher = EventDispatcher()
        self.user_profile_service = UserProfileService()

    def test_default_instance__should_create_config_manager_when_sdk_key_is_given(self, _):
        optimizely_instance = OptimizelyFactory.default_instance('sdk_key')
        self.assertIsInstance(optimizely_instance.config_manager, PollingConfigManager)

    def test_default_instance__should_create_config_manager_when_params_are_set_valid(self, _):
        OptimizelyFactory.set_polling_interval(40)
        OptimizelyFactory.set_blocking_timeout(5)
        OptimizelyFactory.set_flush_interval(30)
        OptimizelyFactory.set_batch_size(10)
        optimizely_instance = OptimizelyFactory.default_instance('sdk_key', datafile=self.datafile)
        # Verify that values set in OptimizelyFactory are being used inside config manager.
        self.assertEqual(optimizely_instance.config_manager.update_interval, 40)
        self.assertEqual(optimizely_instance.config_manager.blocking_timeout, 5)
        # Verify values set for batch_size and flush_interval
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 30)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 10)

    def test_default_instance__should_create_config_set_default_values_params__invalid(self, _):
        OptimizelyFactory.set_polling_interval(-40)
        OptimizelyFactory.set_blocking_timeout(-85)
        OptimizelyFactory.set_flush_interval(30)
        OptimizelyFactory.set_batch_size(10)

        optimizely_instance = OptimizelyFactory.default_instance('sdk_key', datafile=self.datafile)
        # Verify that values set in OptimizelyFactory are not being used inside config manager.
        self.assertEqual(optimizely_instance.config_manager.update_interval, 300)
        self.assertEqual(optimizely_instance.config_manager.blocking_timeout, 10)
        # Verify values set for batch_size and flush_interval
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 30)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 10)

    def test_default_instance__should_create_http_config_manager_with_the_same_components_as_the_instance(self, _):
        optimizely_instance = OptimizelyFactory.default_instance('sdk_key', None)
        self.assertEqual(optimizely_instance.error_handler, optimizely_instance.config_manager.error_handler)
        self.assertEqual(optimizely_instance.logger, optimizely_instance.config_manager.logger)
        self.assertEqual(optimizely_instance.notification_center,
                         optimizely_instance.config_manager.notification_center)

    def test_custom_instance__should_set_input_values_when_sdk_key_polling_interval_and_blocking_timeout_are_given(
            self, _):
        OptimizelyFactory.set_polling_interval(50)
        OptimizelyFactory.set_blocking_timeout(10)

        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key', None, self.event_dispatcher,
                                                                self.mock_client_logger, self.error_handler, False,
                                                                self.user_profile_service, None,
                                                                self.notification_center)

        self.assertEqual(optimizely_instance.config_manager.update_interval, 50)
        self.assertEqual(optimizely_instance.config_manager.blocking_timeout, 10)

    def test_custom_instance__should_set_default_values_when_sdk_key_polling_interval_and_blocking_timeout_are_invalid(
            self, _):
        OptimizelyFactory.set_polling_interval(-50)
        OptimizelyFactory.set_blocking_timeout(-10)
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key', None, self.event_dispatcher,
                                                                self.mock_client_logger, self.error_handler, False,
                                                                self.user_profile_service, None,
                                                                self.notification_center)
        self.assertEqual(optimizely_instance.config_manager.update_interval, 300)
        self.assertEqual(optimizely_instance.config_manager.blocking_timeout, 10)

    def test_custom_instance__should_take_event_processor_when_flush_interval_and_batch_size_are_set_valid(self, _):
        OptimizelyFactory.set_flush_interval(5)
        OptimizelyFactory.set_batch_size(100)

        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key')
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 5)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 100)

    def test_custom_instance__should_take_event_processor_set_default_values_when_flush_int_and_batch_size_are_invalid(
            self, _):
        OptimizelyFactory.set_flush_interval(-50)
        OptimizelyFactory.set_batch_size(-100)
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key')
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 30)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 10)

    def test_custom_instance__should_assign_passed_components_to_both_the_instance_and_config_manager(self, _):
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key', None, self.event_dispatcher,
                                                                self.mock_client_logger, self.error_handler, False,
                                                                self.user_profile_service, None,
                                                                self.notification_center)
        # Config manager assertion
        self.assertEqual(self.error_handler, optimizely_instance.config_manager.error_handler)
        self.assertEqual(self.mock_client_logger, optimizely_instance.config_manager.logger)
        self.assertEqual(self.notification_center,
                         optimizely_instance.config_manager.notification_center)

        # instance assertions
        self.assertEqual(self.error_handler, optimizely_instance.error_handler)
        self.assertEqual(self.mock_client_logger, optimizely_instance.logger)
        self.assertEqual(self.notification_center,
                         optimizely_instance.notification_center)

    def test_max_event_batch_size__should_log_error_message_and_return_none_when_invalid(self, _):
        self.assertEqual(OptimizelyFactory.set_batch_size([], self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_batch_size('test', self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_batch_size(5.5, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_batch_size(None, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_batch_size(False, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_batch_size(True, self.mock_client_logger), None)
        self.mock_client_logger.error.assert_called_with('Batch size is invalid, setting to default batch size # 10')

        self.assertEqual(OptimizelyFactory.set_batch_size(0, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_batch_size(-8, self.mock_client_logger), None)
        self.mock_client_logger.error.assert_called_with('Batch size is negative, setting to default batch size # 10')

    def test_max_event_batch_size__should_not_log_error_message_when_valid_batch_size(self, _):
        self.assertEqual(OptimizelyFactory.set_batch_size(5, self.mock_client_logger), 5)
        self.mock_client_logger.assert_not_called()

    def test_max_event_flush_interval__should_log_error_message_and_return_none_when_invalid(self, _):
        self.assertEqual(OptimizelyFactory.set_flush_interval([], self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_flush_interval('test', self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_flush_interval(5.5, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_flush_interval(None, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_flush_interval(False, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_flush_interval(True, self.mock_client_logger), None)
        self.mock_client_logger.error.assert_called_with(
            'Flush interval is invalid, setting to default flush interval # 30')

        self.assertEqual(OptimizelyFactory.set_flush_interval(0, self.mock_client_logger), None)
        self.assertEqual(OptimizelyFactory.set_flush_interval(-8, self.mock_client_logger), None)
        self.mock_client_logger.error.assert_called_with(
            'Flush interval is negative, setting to default flush interval # 30')

    def test_max_event_flush_interval__should_not_log_error_message_when_valid_flush_interval(self, _):
        self.assertEqual(OptimizelyFactory.set_flush_interval(50, self.mock_client_logger), 50)
        self.mock_client_logger.assert_not_called()
