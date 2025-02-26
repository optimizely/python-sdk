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

import json
import time
from unittest import mock

from optimizely.config_manager import PollingConfigManager
from optimizely.odp.odp_config import OdpConfigState
from optimizely.error_handler import NoOpErrorHandler
from optimizely.event_dispatcher import EventDispatcher
from optimizely.notification_center import NotificationCenter
from optimizely.optimizely_factory import OptimizelyFactory
from optimizely.user_profile import UserProfileService

from . import base


@mock.patch('requests.Session.get')
class OptimizelyFactoryTest(base.BaseTest):
    def delay(*args, **kwargs):
        time.sleep(.5)
        return mock.DEFAULT

    def setUp(self):
        super().setUp()
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

    def test_set_batch_size_and_set_flush_interval___should_set_values_valid_or_invalid(self, _):

        # pass valid value so no default value is set
        OptimizelyFactory.set_flush_interval(5)
        OptimizelyFactory.set_batch_size(100)
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key')
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 5)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 100)

        # pass invalid value so set default value
        OptimizelyFactory.set_flush_interval('test')
        OptimizelyFactory.set_batch_size('test')
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key')
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 30)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 10)

        OptimizelyFactory.set_flush_interval(20.5)
        OptimizelyFactory.set_batch_size(85.5)
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key')
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 20)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 10)

        OptimizelyFactory.set_flush_interval(None)
        OptimizelyFactory.set_batch_size(None)
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key')
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 30)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 10)

        OptimizelyFactory.set_flush_interval(True)
        OptimizelyFactory.set_batch_size(True)
        optimizely_instance = OptimizelyFactory.custom_instance('sdk_key')
        self.assertEqual(optimizely_instance.event_processor.flush_interval.seconds, 30)
        self.assertEqual(optimizely_instance.event_processor.batch_size, 10)

    def test_update_odp_config_correctly(self, _):
        with mock.patch('requests.Session.get') as mock_request_post:
            mock_request_post.return_value = self.fake_server_response(
                status_code=200,
                content=json.dumps(self.config_dict_with_audience_segments)
            )
            client = OptimizelyFactory.custom_instance('instance-test')

            # wait for config to be ready
            client.config_manager.get_config()

        odp_config = client.odp_manager.odp_config
        odp_settings = self.config_dict_with_audience_segments['integrations'][0]
        self.assertEqual(odp_config.get_api_key(), odp_settings['publicKey'])
        self.assertEqual(odp_config.get_api_host(), odp_settings['host'])

        client.close()

    def test_update_odp_config_correctly_with_custom_config_manager_and_delay(self, _):
        logger = mock.MagicMock()

        test_datafile = json.dumps(self.config_dict_with_audience_segments)
        test_response = self.fake_server_response(status_code=200, content=test_datafile)

        with mock.patch('requests.Session.get', return_value=test_response, side_effect=self.delay):
            # initialize config_manager with delay, so it will receive the datafile after client initialization
            config_manager = PollingConfigManager(sdk_key='test', logger=logger)
            client = OptimizelyFactory.default_instance_with_config_manager(config_manager=config_manager)
            odp_manager = client.odp_manager

            # confirm odp config has not yet been updated
            self.assertEqual(odp_manager.odp_config.odp_state(), OdpConfigState.UNDETERMINED)

            # wait for datafile
            client.config_manager.get_config()

        # wait for odp config to be updated
        odp_manager.event_manager.event_queue.join()

        self.assertEqual(odp_manager.odp_config.odp_state(), OdpConfigState.INTEGRATED)

        logger.error.assert_not_called()

        client.close()

    def test_update_odp_config_correctly_with_delay(self, _):
        logger = mock.MagicMock()

        test_datafile = json.dumps(self.config_dict_with_audience_segments)
        test_response = self.fake_server_response(status_code=200, content=test_datafile)

        with mock.patch('requests.Session.get', return_value=test_response, side_effect=self.delay):
            # initialize config_manager with delay, so it will receive the datafile after client initialization
            client = OptimizelyFactory.default_instance(sdk_key='test')
            odp_manager = client.odp_manager

            # confirm odp config has not yet been updated
            self.assertEqual(odp_manager.odp_config.odp_state(), OdpConfigState.UNDETERMINED)

            # wait for datafile
            client.config_manager.get_config()

        # wait for odp config to be updated
        odp_manager.event_manager.event_queue.join()

        self.assertEqual(odp_manager.odp_config.odp_state(), OdpConfigState.INTEGRATED)

        logger.error.assert_not_called()

        client.close()

    def test_odp_updated_with_custom_instance(self, _):
        logger = mock.MagicMock()

        test_datafile = json.dumps(self.config_dict_with_audience_segments)
        test_response = self.fake_server_response(status_code=200, content=test_datafile)

        with mock.patch('requests.Session.get', return_value=test_response, side_effect=self.delay):
            # initialize config_manager with delay, so it will receive the datafile after client initialization
            client = OptimizelyFactory.custom_instance(sdk_key='test')
            odp_manager = client.odp_manager

            # confirm odp config has not yet been updated
            self.assertEqual(odp_manager.odp_config.odp_state(), OdpConfigState.UNDETERMINED)

            # wait for datafile
            client.config_manager.get_config()

        # wait for odp config to be updated
        odp_manager.event_manager.event_queue.join()

        self.assertEqual(odp_manager.odp_config.odp_state(), OdpConfigState.INTEGRATED)

        logger.error.assert_not_called()

        client.close()
