# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from unittest import mock

from requests import exceptions as request_exception

from tests.helpers_for_tests import fake_server_response
from optimizely.helpers.enums import OdpRestApiConfig
from optimizely.odp.zaius_rest_api_manager import ZaiusRestApiManager
from . import base


class ZaiusRestApiManagerTest(base.BaseTest):
    user_key = "vuid"
    user_value = "test-user-value"
    api_key = "test-api-key"
    api_host = "test-host"

    events = [
        {"type": "t1", "action": "a1", "identifiers": {"id-key-1": "id-value-1"}, "data": {"key-1": "value1"}},
        {"type": "t2", "action": "a2", "identifiers": {"id-key-2": "id-value-2"}, "data": {"key-2": "value2"}},
    ]

    def test_send_odp_events__valid_request(self):
        with mock.patch('requests.post') as mock_request_post:
            api = ZaiusRestApiManager()
            api.sendOdpEvents(api_key=self.api_key,
                              api_host=self.api_host,
                              events=self.events)

        request_headers = {'content-type': 'application/json', 'x-api-key': self.api_key}
        mock_request_post.assert_called_once_with(url=self.api_host + "/v3/events",
                                                  headers=request_headers,
                                                  data=json.dumps(self.events),
                                                  timeout=OdpRestApiConfig.REQUEST_TIMEOUT)

    def testSendOdpEvents_success(self):
        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value = \
                fake_server_response(status_code=200)

            api = ZaiusRestApiManager()
            response = api.sendOdpEvents(api_key=self.api_key,
                                         api_host=self.api_host,
                                         events=self.events)  # content of events doesn't matter for the test

            self.assertFalse(response)

    def testSendOdpEvents_network_error_retry(self):
        with mock.patch('requests.post',
                        side_effect=request_exception.ConnectionError('Connection error')) as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            api = ZaiusRestApiManager(logger=mock_logger)
            response = api.sendOdpEvents(api_key=self.api_key,
                                         api_host=self.api_host,
                                         events=self.events)

        self.assertTrue(response)
        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('ODP event send failed (network error).')

    def testSendOdpEvents_400_no_retry(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = fake_server_response(status_code=403, url=self.api_host)

            api = ZaiusRestApiManager(logger=mock_logger)
            response = api.sendOdpEvents(api_key=self.api_key,
                                         api_host=self.api_host,
                                         events=self.events)

        self.assertFalse(response)
        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('ODP event send failed (403 Client Error: None for url: test-host).')

    def testSendOdpEvents_500_retry(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = fake_server_response(status_code=500, url=self.api_host)

            api = ZaiusRestApiManager(logger=mock_logger)
            response = api.sendOdpEvents(api_key=self.api_key,
                                         api_host=self.api_host,
                                         events=self.events)

        self.assertTrue(response)
        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('ODP event send failed (500 Server Error: None for url: test-host).')
