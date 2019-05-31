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

import json
import mock
import requests
import unittest

from optimizely import config_manager
from optimizely import exceptions as optimizely_exceptions
from optimizely import project_config
from optimizely.helpers import enums


class StaticConfigManagerTest(unittest.TestCase):
    def test_get_config(self):
        test_datafile = json.dumps({
            'some_datafile_key': 'some_datafile_value',
            'version': project_config.SUPPORTED_VERSIONS[0]
        })
        project_config_manager = config_manager.StaticConfigManager(datafile=test_datafile)

        # Assert that config is set.
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)


class PollingConfigManagerTest(unittest.TestCase):
    def test_init__no_sdk_key_no_url__fails(self):
        """ Test that initialization fails if there is no sdk_key or url provided. """
        self.assertRaisesRegexp(optimizely_exceptions.InvalidInputException,
                                'Must provide at least one of sdk_key or url.',
                                config_manager.PollingConfigManager, sdk_key=None, url=None)

    def test_get_datafile_url__no_sdk_key_no_url_raises(self):
        """ Test that get_datafile_url raises exception if no sdk_key or url is provided. """
        self.assertRaisesRegexp(optimizely_exceptions.InvalidInputException,
                                'Must provide at least one of sdk_key or url.',
                                config_manager.PollingConfigManager.get_datafile_url, None, None, 'url_template')

    def test_get_datafile_url__invalid_url_template_raises(self):
        """ Test that get_datafile_url raises if url_template is invalid. """
        # No url_template provided
        self.assertRaisesRegexp(optimizely_exceptions.InvalidInputException,
                                'Invalid url_template None provided',
                                config_manager.PollingConfigManager.get_datafile_url, 'optly_datafile_key', None, None)

        # Incorrect url_template provided
        test_url_template = 'invalid_url_template_without_sdk_key_field_{key}'
        self.assertRaisesRegexp(optimizely_exceptions.InvalidInputException,
                                'Invalid url_template {} provided'.format(test_url_template),
                                config_manager.PollingConfigManager.get_datafile_url,
                                'optly_datafile_key', None, test_url_template)

    def test_get_datafile_url__sdk_key_and_template_provided(self):
        """ Test get_datafile_url when sdk_key and template are provided. """
        test_sdk_key = 'optly_key'
        test_url_template = 'www.optimizelydatafiles.com/{sdk_key}.json'
        expected_url = test_url_template.format(sdk_key=test_sdk_key)
        self.assertEqual(expected_url,
                         config_manager.PollingConfigManager.get_datafile_url(test_sdk_key, None, test_url_template))

    def test_get_datafile_url__url_and_template_provided(self):
        """ Test get_datafile_url when url and url_template are provided. """
        test_url_template = 'www.optimizelydatafiles.com/{sdk_key}.json'
        test_url = 'www.myoptimizelydatafiles.com/my_key.json'
        self.assertEqual(test_url, config_manager.PollingConfigManager.get_datafile_url(None,
                                                                                        test_url,
                                                                                        test_url_template))

    def test_get_datafile_url__sdk_key_and_url_and_template_provided(self):
        """ Test get_datafile_url when sdk_key, url and url_template are provided. """
        test_sdk_key = 'optly_key'
        test_url_template = 'www.optimizelydatafiles.com/{sdk_key}.json'
        test_url = 'www.myoptimizelydatafiles.com/my_key.json'

        # Assert that if url is provided, it is always returned
        self.assertEqual(test_url, config_manager.PollingConfigManager.get_datafile_url(test_sdk_key,
                                                                                        test_url,
                                                                                        test_url_template))

    def test_set_update_interval(self):
        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')

        # Assert that update_interval cannot be set to less than allowed minimum and instead is set to default value.
        project_config_manager.set_update_interval(0.42)
        self.assertEqual(enums.ConfigManager.DEFAULT_UPDATE_INTERVAL, project_config_manager.update_interval)

        # Assert that if no update_interval is provided, it is set to default value.
        project_config_manager.set_update_interval(None)
        self.assertEqual(enums.ConfigManager.DEFAULT_UPDATE_INTERVAL, project_config_manager.update_interval)

        # Assert that if valid update_interval is provided, it is set to that value.
        project_config_manager.set_update_interval(42)
        self.assertEqual(42, project_config_manager.update_interval)

    def test_set_last_modified(self):
        """ Test that set_last_modified sets last_modified field based on header. """
        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')
        self.assertIsNone(project_config_manager.last_modified)

        last_modified_time = 'Test Last Modified Time'
        test_response_headers = {
            'Last-Modified': last_modified_time,
            'Some-Other-Important-Header': 'some_value'
        }
        project_config_manager.set_last_modified(test_response_headers)
        self.assertEqual(last_modified_time, project_config_manager.last_modified)

    def test_set_and_get_config(self):
        """ Test that set_last_modified sets config field based on datafile. """
        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')

        # Assert that config is not set.
        self.assertIsNone(project_config_manager.get_config())

        # Set and check config.
        project_config_manager.set_config(json.dumps({
            'some_datafile_key': 'some_datafile_value',
            'version': project_config.SUPPORTED_VERSIONS[0]
        }))
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

    def test_fetch_datafile(self):
        """ Test that fetch_datafile sets config and last_modified based on response. """
        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')
        expected_datafile_url = 'https://cdn.optimizely.com/datafiles/some_key.json'
        test_headers = {
            'Last-Modified': 'New Time'
        }
        test_datafile = json.dumps({
            'some_datafile_key': 'some_datafile_value',
            'version': project_config.SUPPORTED_VERSIONS[0]
        })
        test_response = requests.Response()
        test_response.status_code = 200
        test_response.headers = test_headers
        test_response._content = test_datafile
        with mock.patch('requests.get', return_value=test_response) as mock_requests:
            project_config_manager.fetch_datafile()

        mock_requests.assert_called_once_with(expected_datafile_url, headers={})
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

        # Call fetch_datafile again and assert that request to URL is with If-Modified-Since header.
        with mock.patch('requests.get', return_value=test_response) as mock_requests:
            project_config_manager.fetch_datafile()

        mock_requests.assert_called_once_with(expected_datafile_url,
                                              headers={'If-Modified-Since': test_headers['Last-Modified']})
        self.assertEqual(test_headers['Last-Modified'], project_config_manager.last_modified)
        self.assertIsInstance(project_config_manager.get_config(), project_config.ProjectConfig)

    def test_is_running(self):
        """ Test is_running before and after starting thread. """
        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')
        self.assertFalse(project_config_manager.is_running)
        with mock.patch('optimizely.config_manager.PollingConfigManager.fetch_datafile') as mock_fetch_datafile, \
            mock.patch('time.sleep') as mock_sleep:
            project_config_manager.start()
            self.assertTrue(project_config_manager.is_running)

        mock_fetch_datafile.assert_called_with()
        mock_sleep.assert_called_with(enums.ConfigManager.DEFAULT_UPDATE_INTERVAL)

    def test_start(self):
        """ Test that calling start starts the polling thread. """
        project_config_manager = config_manager.PollingConfigManager(sdk_key='some_key')
        self.assertFalse(project_config_manager._polling_thread.is_alive())
        with mock.patch('optimizely.config_manager.PollingConfigManager.fetch_datafile') as mock_fetch_datafile, \
            mock.patch('time.sleep') as mock_sleep:
            project_config_manager.start()
            self.assertTrue(project_config_manager._polling_thread.is_alive())

        mock_fetch_datafile.assert_called_with()
        mock_sleep.assert_called_with(enums.ConfigManager.DEFAULT_UPDATE_INTERVAL)
