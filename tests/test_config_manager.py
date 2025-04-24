# Copyright 2019-2022, Optimizely
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
from unittest import mock
import requests
import time

from optimizely import config_manager
from optimizely import exceptions as optimizely_exceptions
from optimizely import optimizely_config
from optimizely import project_config
from optimizely.helpers import enums

from . import base


class StaticConfigManagerTest(base.BaseTest):
    def test_init__invalid_logger_fails(self):
        """ Test that initialization fails if logger is invalid. """

        class InvalidLogger:
            pass

        with self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException, 'Provided "logger" is in an invalid format.',
        ):
            config_manager.StaticConfigManager(logger=InvalidLogger())

    def test_init__invalid_error_handler_fails(self):
        """ Test that initialization fails if error_handler is invalid. """

        class InvalidErrorHandler:
            pass

        with self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException, 'Provided "error_handler" is in an invalid format.',
        ):
            config_manager.StaticConfigManager(error_handler=InvalidErrorHandler())

    def test_init__invalid_notification_center_fails(self):
        """ Test that initialization fails if notification_center is invalid. """

        class InvalidNotificationCenter:
            pass

        with self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException, 'Provided "notification_center" is in an invalid format.',
        ):
            config_manager.StaticConfigManager(notification_center=InvalidNotificationCenter())

    def test_set_config__success(self):
        """ Test set_config when datafile is valid. """
        test_datafile = json.dumps(self.config_dict_with_features)
        mock_logger = mock.Mock()
        mock_notification_center = mock.Mock()

        with mock.patch('optimizely.config_manager.BaseConfigManager._validate_instantiation_options'):
            project_config_manager = config_manager.StaticConfigManager(
                datafile=test_datafile, logger=mock_logger, notification_center=mock_notification_center,
            )

        project_config_manager._set_config(test_datafile)
        mock_logger.debug.assert_called_with(
            'Received new datafile and updated config. ' 'Old revision number: None. New revision number: 1.'
        )
        mock_notification_center.send_notifications.assert_called_once_with('OPTIMIZELY_CONFIG_UPDATE')

        self.assertIsInstance(
            project_config_manager.optimizely_config,
            optimizely_config.OptimizelyConfig
        )

    def test_set_config__twice__with_same_content(self):
        """ Test calling set_config twice with same content to ensure config is not updated. """
        test_datafile = json.dumps(self.config_dict_with_features)
        mock_logger = mock.Mock()
        mock_notification_center = mock.Mock()

        with mock.patch('optimizely.config_manager.BaseConfigManager._validate_instantiation_options'), \
                mock.patch('optimizely.optimizely_config.OptimizelyConfigService.get_config') as mock_opt_service:
            project_config_manager = config_manager.StaticConfigManager(
                datafile=test_datafile, logger=mock_logger, notification_center=mock_notification_center,
            )

        project_config_manager._set_config(test_datafile)
        mock_logger.debug.assert_called_with(
            'Received new datafile and updated config. ' 'Old revision number: None. New revision number: 1.'
        )
        self.assertEqual(1, mock_logger.debug.call_count)
        mock_notification_center.send_notifications.assert_called_once_with('OPTIMIZELY_CONFIG_UPDATE')
        self.assertEqual(1, mock_opt_service.call_count)

        mock_logger.reset_mock()
        mock_notification_center.reset_mock()
        mock_opt_service.reset_mock()

        # Call set config again and confirm that no new log message denoting config update is there
        project_config_manager._set_config(test_datafile)
        self.assertEqual(0, mock_logger.debug.call_count)
        self.assertEqual(0, mock_notification_center.call_count)
        # Assert that mock_opt_service is not called again.
        self.assertEqual(0, mock_opt_service.call_count)

    def test_set_config__twice__with_diff_content(self):
        """ Test calling set_config twice with different content to ensure config is updated. """
        test_datafile = json.dumps(self.config_dict_with_features)
        mock_logger = mock.Mock()
        mock_notification_center = mock.Mock()

        with mock.patch('optimizely.config_manager.BaseConfigManager._validate_instantiation_options'):
            project_config_manager = config_manager.StaticConfigManager(
                datafile=test_datafile, logger=mock_logger, notification_center=mock_notification_center,
            )

        mock_logger.debug.assert_called_with(
            'Received new datafile and updated config. ' 'Old revision number: None. New revision number: 1.'
        )
        self.assertEqual(1, mock_logger.debug.call_count)
        mock_notification_center.send_notifications.assert_called_once_with('OPTIMIZELY_CONFIG_UPDATE')
        self.assertEqual('1', project_config_manager.optimizely_config.revision)

        mock_logger.reset_mock()
        mock_notification_center.reset_mock()

        # Call set config again
        other_datafile = json.dumps(self.config_dict_with_multiple_experiments)
        project_config_manager._set_config(other_datafile)
        mock_logger.debug.assert_called_with(
            'Received new datafile and updated config. ' 'Old revision number: 1. New revision number: 42.'
        )
        self.assertEqual(1, mock_logger.debug.call_count)
        mock_notification_center.send_notifications.assert_called_once_with('OPTIMIZELY_CONFIG_UPDATE')
        self.assertEqual('42', project_config_manager.optimizely_config.revision)

    def test_set_config__schema_validation(self):
        """ Test set_config calls or does not call schema validation based on skip_json_validation value. """

        test_datafile = json.dumps(self.config_dict_with_features)
        mock_logger = mock.Mock()

        # Test that schema is validated.
        # Note: set_config is called in __init__ itself.
        with mock.patch('optimizely.helpers.validator.is_datafile_valid', return_value=True) as mock_validate_datafile:
            config_manager.StaticConfigManager(datafile=test_datafile, logger=mock_logger)
        mock_validate_datafile.assert_called_once_with(test_datafile)

        # Test that schema is not validated if skip_json_validation option is set to True.
        with mock.patch('optimizely.helpers.validator.is_datafile_valid', return_value=True) as mock_validate_datafile:
            config_manager.StaticConfigManager(datafile=test_datafile, logger=mock_logger, skip_json_validation=True)
        mock_validate_datafile.assert_not_called()

    def test_set_config__unsupported_datafile_version(self):
        """ Test set_config when datafile has unsupported version. """

        test_datafile = json.dumps(self.config_dict_with_features)
        mock_logger = mock.Mock()
        mock_notification_center = mock.Mock()

        with mock.patch('optimizely.config_manager.BaseConfigManager._validate_instantiation_options'):
            project_config_manager = config_manager.StaticConfigManager(
                datafile=test_datafile, logger=mock_logger, notification_center=mock_notification_center,
            )

        invalid_version_datafile = self.config_dict_with_features.copy()
        invalid_version_datafile['version'] = 'invalid_version'
        test_datafile = json.dumps(invalid_version_datafile)

        # Call set_config with datafile having invalid version
        project_config_manager._set_config(test_datafile)
        mock_logger.error.assert_called_once_with(
            'This version of the Python SDK does not support ' 'the given datafile version: "invalid_version".'
        )
        self.assertEqual(0, mock_notification_center.call_count)

    def test_set_config__invalid_datafile(self):
        """ Test set_config when datafile is invalid. """

        test_datafile = json.dumps(self.config_dict_with_features)
        mock_logger = mock.Mock()
        mock_notification_center = mock.Mock()

        with mock.patch('optimizely.config_manager.BaseConfigManager._validate_instantiation_options'):
            project_config_manager = config_manager.StaticConfigManager(
                datafile=test_datafile, logger=mock_logger, notification_center=mock_notification_center,
            )

        # Call set_config with invalid content
        project_config_manager._set_config('invalid_datafile')
        mock_logger.error.assert_called_once_with('Provided "datafile" is in an invalid format.')
        self.assertEqual(0, mock_notification_center.call_count)

    def test_get_config(self):
        """ Test get_config. """
        test_datafile = json.dumps(self.config_dict_with_features)
        project_config_manager = config_manager.StaticConfigManager(datafile=test_datafile)

        # Assert that config is set.
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

    def test_get_config_blocks(self):
        """ Test that get_config blocks until blocking timeout is hit. """
        start_time = time.time()
        project_config_manager = config_manager.PollingConfigManager(sdk_key='sdk_key', blocking_timeout=1)
        # Assert get_config should block until blocking timeout.
        project_config_manager.get_config()
        end_time = time.time()
        self.assertEqual(1, round(end_time - start_time))


@mock.patch('requests.Session.get')
class PollingConfigManagerTest(base.BaseTest):
    def test_init__no_sdk_key_no_datafile__fails(self, _):
        """ Test that initialization fails if there is no sdk_key or datafile provided. """
        self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException,
            enums.Errors.MISSING_SDK_KEY,
            config_manager.PollingConfigManager,
            sdk_key=None,
            datafile=None,
        )

    def test_get_datafile_url__no_sdk_key_no_url_raises(self, _):
        """ Test that get_datafile_url raises exception if no sdk_key or url is provided. """
        self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException,
            'Must provide at least one of sdk_key or url.',
            config_manager.PollingConfigManager.get_datafile_url,
            None,
            None,
            'url_template',
        )

    def test_get_datafile_url__invalid_url_template_raises(self, _):
        """ Test that get_datafile_url raises if url_template is invalid. """
        # No url_template provided
        self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException,
            'Invalid url_template None provided',
            config_manager.PollingConfigManager.get_datafile_url,
            'optly_datafile_key',
            None,
            None,
        )

        # Incorrect url_template provided
        test_url_template = 'invalid_url_template_without_sdk_key_field_{key}'
        self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException,
            f'Invalid url_template {test_url_template} provided',
            config_manager.PollingConfigManager.get_datafile_url,
            'optly_datafile_key',
            None,
            test_url_template,
        )

    def test_get_datafile_url__sdk_key_and_template_provided(self, _):
        """ Test get_datafile_url when sdk_key and template are provided. """
        test_sdk_key = 'optly_key'
        test_url_template = 'www.optimizelydatafiles.com/{sdk_key}.json'
        expected_url = test_url_template.format(sdk_key=test_sdk_key)
        self.assertEqual(
            expected_url, config_manager.PollingConfigManager.get_datafile_url(test_sdk_key, None, test_url_template),
        )

    def test_get_datafile_url__url_and_template_provided(self, _):
        """ Test get_datafile_url when url and url_template are provided. """
        test_url_template = 'www.optimizelydatafiles.com/{sdk_key}.json'
        test_url = 'www.myoptimizelydatafiles.com/my_key.json'
        self.assertEqual(
            test_url, config_manager.PollingConfigManager.get_datafile_url(None, test_url, test_url_template),
        )

    def test_get_datafile_url__sdk_key_and_url_and_template_provided(self, _):
        """ Test get_datafile_url when sdk_key, url and url_template are provided. """
        test_sdk_key = 'optly_key'
        test_url_template = 'www.optimizelydatafiles.com/{sdk_key}.json'
        test_url = 'www.myoptimizelydatafiles.com/my_key.json'

        # Assert that if url is provided, it is always returned
        self.assertEqual(
            test_url, config_manager.PollingConfigManager.get_datafile_url(test_sdk_key, test_url, test_url_template),
        )

    def test_set_update_interval(self, _):
        """ Test set_update_interval with different inputs. """

        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')

        # Assert that if invalid update_interval is set, then exception is raised.
        with self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException, 'Invalid update_interval "invalid interval" provided.',
        ):
            project_config_manager.set_update_interval('invalid interval')

        # Assert that update_interval cannot be set to less than allowed minimum and instead is set to default value.
        project_config_manager.set_update_interval(-4.2)
        self.assertEqual(
            enums.ConfigManager.DEFAULT_UPDATE_INTERVAL, project_config_manager.update_interval,
        )

        # Assert that if no update_interval is provided, it is set to default value.
        project_config_manager.set_update_interval(None)
        self.assertEqual(
            enums.ConfigManager.DEFAULT_UPDATE_INTERVAL, project_config_manager.update_interval,
        )

        # Assert that if valid update_interval is provided, it is set to that value.
        project_config_manager.set_update_interval(42)
        self.assertEqual(42, project_config_manager.update_interval)

        project_config_manager.stop()

    def test_set_blocking_timeout(self, _):
        """ Test set_blocking_timeout with different inputs. """

        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')

        # Assert that if invalid blocking_timeout is set, then exception is raised.
        with self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException, 'Invalid blocking timeout "invalid timeout" provided.',
        ):
            project_config_manager.set_blocking_timeout('invalid timeout')

        # Assert that blocking_timeout cannot be set to less than allowed minimum and instead is set to default value.
        project_config_manager.set_blocking_timeout(-4)
        self.assertEqual(
            enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT, project_config_manager.blocking_timeout,
        )

        # Assert that blocking_timeout can be set to 0.
        project_config_manager.set_blocking_timeout(0)
        self.assertIs(0, project_config_manager.blocking_timeout)

        # Assert that if no blocking_timeout is provided, it is set to default value.
        project_config_manager.set_blocking_timeout(None)
        self.assertEqual(
            enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT, project_config_manager.blocking_timeout,
        )

        # Assert that if valid blocking_timeout is provided, it is set to that value.
        project_config_manager.set_blocking_timeout(5)
        self.assertEqual(5, project_config_manager.blocking_timeout)

        project_config_manager.stop()

    def test_set_last_modified(self, _):
        """ Test that set_last_modified sets last_modified field based on header. """

        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')

        last_modified_time = 'Test Last Modified Time'
        test_response_headers = {
            'Last-Modified': last_modified_time,
            'Some-Other-Important-Header': 'some_value',
        }
        project_config_manager.set_last_modified(test_response_headers)
        self.assertEqual(last_modified_time, project_config_manager.last_modified)
        project_config_manager.stop()

    def test_fetch_datafile(self, _):
        """ Test that fetch_datafile sets config and last_modified based on response. """
        sdk_key = 'some_key'

        expected_datafile_url = enums.ConfigManager.DATAFILE_URL_TEMPLATE.format(sdk_key=sdk_key)
        test_headers = {'Last-Modified': 'New Time'}
        test_datafile = json.dumps(self.config_dict_with_features)
        test_response = requests.Response()
        test_response.status_code = 200
        test_response.headers = test_headers
        test_response._content = test_datafile
        with mock.patch('requests.Session.get', return_value=test_response) as mock_request:
            project_config_manager = config_manager.PollingConfigManager(sdk_key=sdk_key)
            project_config_manager.stop()

        mock_request.assert_called_once_with(
            expected_datafile_url,
            headers={},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT
        )
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

        # Call fetch_datafile again and assert that request to URL is with If-Modified-Since header.
        with mock.patch('requests.Session.get', return_value=test_response) as mock_requests:
            project_config_manager._initialize_thread()
            project_config_manager.start()
            project_config_manager.stop()

        mock_requests.assert_called_once_with(
            expected_datafile_url,
            headers={'If-Modified-Since': test_headers['Last-Modified']},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT,
        )
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

    def test_fetch_datafile__status_exception_raised(self, _):
        """ Test that config_manager keeps running if status code exception is raised when fetching datafile. """
        class MockExceptionResponse:
            def raise_for_status(self):
                raise requests.exceptions.RequestException('Error Error !!')

        sdk_key = 'some_key'
        mock_logger = mock.Mock()
        expected_datafile_url = enums.ConfigManager.DATAFILE_URL_TEMPLATE.format(sdk_key=sdk_key)
        test_headers = {'Last-Modified': 'New Time'}
        test_datafile = json.dumps(self.config_dict_with_features)
        test_response = requests.Response()
        test_response.status_code = 200
        test_response.headers = test_headers
        test_response._content = test_datafile

        with mock.patch('requests.Session.get', return_value=test_response) as mock_request:
            project_config_manager = config_manager.PollingConfigManager(sdk_key=sdk_key, logger=mock_logger)
            project_config_manager.stop()

        mock_request.assert_called_once_with(
            expected_datafile_url,
            headers={},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT
        )
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

        # Call fetch_datafile again, but raise exception this time
        with mock.patch('requests.Session.get', return_value=MockExceptionResponse()) as mock_requests:
            project_config_manager._initialize_thread()
            project_config_manager.start()
            project_config_manager.stop()

        mock_requests.assert_called_once_with(
            expected_datafile_url,
            headers={'If-Modified-Since': test_headers['Last-Modified']},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT,
        )
        mock_logger.error.assert_called_once_with(
            f'Fetching datafile from {expected_datafile_url} failed. Error: Error Error !!'
        )
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

    def test_fetch_datafile__request_exception_raised(self, _):
        """ Test that config_manager keeps running if a request exception is raised when fetching datafile. """
        sdk_key = 'some_key'
        mock_logger = mock.Mock()

        expected_datafile_url = enums.ConfigManager.DATAFILE_URL_TEMPLATE.format(sdk_key=sdk_key)
        test_headers = {'Last-Modified': 'New Time'}
        test_datafile = json.dumps(self.config_dict_with_features)
        test_response = requests.Response()
        test_response.status_code = 200
        test_response.headers = test_headers
        test_response._content = test_datafile
        with mock.patch('requests.Session.get', return_value=test_response) as mock_request:
            project_config_manager = config_manager.PollingConfigManager(sdk_key=sdk_key, logger=mock_logger)
            project_config_manager.stop()

        mock_request.assert_called_once_with(
            expected_datafile_url,
            headers={},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT
        )
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

        # Call fetch_datafile again, but raise exception this time
        with mock.patch(
            'requests.Session.get',
            side_effect=requests.exceptions.RequestException('Error Error !!'),
        ) as mock_requests:
            project_config_manager._initialize_thread()
            project_config_manager.start()
            project_config_manager.stop()

        mock_requests.assert_called_once_with(
            expected_datafile_url,
            headers={'If-Modified-Since': test_headers['Last-Modified']},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT,
        )
        mock_logger.error.assert_called_once_with(
            f'Fetching datafile from {expected_datafile_url} failed. Error: Error Error !!'
        )
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

    def test_fetch_datafile__exception_polling_thread_failed(self, _):
        """ Test that exception is raised when polling thread stops. """
        sdk_key = 'some_key'
        mock_logger = mock.Mock()

        test_headers = {'Last-Modified': 'New Time'}
        test_datafile = json.dumps(self.config_dict_with_features)
        test_response = requests.Response()
        test_response.status_code = 200
        test_response.headers = test_headers
        test_response._content = test_datafile

        with mock.patch('requests.Session.get', return_value=test_response):
            project_config_manager = config_manager.PollingConfigManager(sdk_key=sdk_key,
                                                                         logger=mock_logger,
                                                                         update_interval=300)

            project_config_manager.stop()

            # verify the error log message
            log_messages = [args[0] for args, _ in mock_logger.error.call_args_list]
            for message in log_messages:
                print(message)
                if "Thread for background datafile polling failed. " \
                   "Error: timestamp too large to convert to C PyTime_t" not in message:
                    assert False

    def test_is_running(self, _):
        """ Test that polling thread is running after instance of PollingConfigManager is created. """
        with mock.patch('optimizely.config_manager.PollingConfigManager.fetch_datafile'):
            project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')
            self.assertTrue(project_config_manager.is_running)

        project_config_manager.stop()


@mock.patch('requests.Session.get')
class AuthDatafilePollingConfigManagerTest(base.BaseTest):
    def test_init__datafile_access_token_none__fails(self, _):
        """ Test that initialization fails if datafile_access_token is None. """
        self.assertRaisesRegex(
            optimizely_exceptions.InvalidInputException,
            'datafile_access_token cannot be empty or None.',
            config_manager.AuthDatafilePollingConfigManager,
            datafile_access_token=None
        )

    def test_set_datafile_access_token(self, _):
        """ Test that datafile_access_token is properly set as instance variable. """
        datafile_access_token = 'some_token'
        sdk_key = 'some_key'

        project_config_manager = config_manager.AuthDatafilePollingConfigManager(
            datafile_access_token=datafile_access_token, sdk_key=sdk_key)

        self.assertEqual(datafile_access_token, project_config_manager.datafile_access_token)
        project_config_manager.stop()

    def test_fetch_datafile(self, _):
        """ Test that fetch_datafile sets authorization header in request header and sets config based on response. """
        datafile_access_token = 'some_token'
        sdk_key = 'some_key'
        with mock.patch('optimizely.config_manager.AuthDatafilePollingConfigManager.fetch_datafile'), mock.patch(
            'optimizely.config_manager.AuthDatafilePollingConfigManager._run'
        ):
            project_config_manager = config_manager.AuthDatafilePollingConfigManager(
                datafile_access_token=datafile_access_token, sdk_key=sdk_key)
        expected_datafile_url = enums.ConfigManager.AUTHENTICATED_DATAFILE_URL_TEMPLATE.format(sdk_key=sdk_key)
        test_headers = {'Last-Modified': 'New Time'}
        test_datafile = json.dumps(self.config_dict_with_features)
        test_response = requests.Response()
        test_response.status_code = 200
        test_response.headers = test_headers
        test_response._content = test_datafile

        # Call fetch_datafile and assert that request was sent with correct authorization header
        with mock.patch('requests.Session.get',
                        return_value=test_response) as mock_request:
            project_config_manager.fetch_datafile()

        mock_request.assert_called_once_with(
            expected_datafile_url,
            headers={'Authorization': f'Bearer {datafile_access_token}'},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT,
        )

        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

    def test_fetch_datafile__request_exception_raised(self, _):
        """ Test that config_manager keeps running if a request exception is raised when fetching datafile. """
        datafile_access_token = 'some_token'
        sdk_key = 'some_key'
        mock_logger = mock.Mock()

        expected_datafile_url = enums.ConfigManager.AUTHENTICATED_DATAFILE_URL_TEMPLATE.format(sdk_key=sdk_key)
        test_headers = {'Last-Modified': 'New Time'}
        test_datafile = json.dumps(self.config_dict_with_features)
        test_response = requests.Response()
        test_response.status_code = 200
        test_response.headers = test_headers
        test_response._content = test_datafile

        # Call fetch_datafile and assert that request was sent with correct authorization header
        with mock.patch('requests.Session.get', return_value=test_response) as mock_request:
            project_config_manager = config_manager.AuthDatafilePollingConfigManager(
                datafile_access_token=datafile_access_token,
                sdk_key=sdk_key,
                logger=mock_logger
            )
            project_config_manager.stop()

        mock_request.assert_called_once_with(
            expected_datafile_url,
            headers={'Authorization': f'Bearer {datafile_access_token}'},
            timeout=enums.ConfigManager.REQUEST_TIMEOUT,
        )

        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

        # Call fetch_datafile again, but raise exception this time
        with mock.patch(
            'requests.Session.get',
            side_effect=requests.exceptions.RequestException('Error Error !!'),
        ) as mock_requests:
            project_config_manager._initialize_thread()
            project_config_manager.start()
            project_config_manager.stop()

        mock_requests.assert_called_once_with(
            expected_datafile_url,
            headers={
                'If-Modified-Since': test_headers['Last-Modified'],
                'Authorization': f'Bearer {datafile_access_token}',
            },
            timeout=enums.ConfigManager.REQUEST_TIMEOUT,
        )
        mock_logger.error.assert_called_once_with(
            f'Fetching datafile from {expected_datafile_url} failed. Error: Error Error !!'
        )
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)
