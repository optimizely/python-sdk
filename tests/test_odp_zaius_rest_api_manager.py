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
            api.send_odp_events(api_key=self.api_key,
                                api_host=self.api_host,
                                events=self.events)

        request_headers = {'content-type': 'application/json', 'x-api-key': self.api_key}
        mock_request_post.assert_called_once_with(url=self.api_host + "/v3/events",
                                                  headers=request_headers,
                                                  data=json.dumps(self.events),
                                                  timeout=OdpRestApiConfig.REQUEST_TIMEOUT)

    def test_send_odp_ovents_success(self):
        with mock.patch('requests.post') as mock_request_post:
            # no need to mock url and content because we're not returning the response
            mock_request_post.return_value = self.fake_server_response(status_code=200)

            api = ZaiusRestApiManager()
            should_retry = api.send_odp_events(api_key=self.api_key,
                                               api_host=self.api_host,
                                               events=self.events)  # content of events doesn't matter for the test

            self.assertFalse(should_retry)

    def test_send_odp_events_invalid_json_no_retry(self):
        events = {1, 2, 3}  # using a set to trigger JSON-not-serializable error

        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            api = ZaiusRestApiManager(logger=mock_logger)
            should_retry = api.send_odp_events(api_key=self.api_key,
                                               api_host=self.api_host,
                                               events=events)

        self.assertFalse(should_retry)
        mock_request_post.assert_not_called()
        mock_logger.error.assert_called_once_with(
            'ODP event send failed (Object of type set is not JSON serializable).')

    def test_send_odp_events_invalid_url_no_retry(self):
        invalid_url = 'https://*api.zaius.com'

        with mock.patch('requests.post',
                        side_effect=request_exception.InvalidURL('Invalid URL')) as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            api = ZaiusRestApiManager(logger=mock_logger)
            should_retry = api.send_odp_events(api_key=self.api_key,
                                               api_host=invalid_url,
                                               events=self.events)

        self.assertFalse(should_retry)
        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('ODP event send failed (Invalid URL).')

    def test_send_odp_events_network_error_retry(self):
        with mock.patch('requests.post',
                        side_effect=request_exception.ConnectionError('Connection error')) as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            api = ZaiusRestApiManager(logger=mock_logger)
            should_retry = api.send_odp_events(api_key=self.api_key,
                                               api_host=self.api_host,
                                               events=self.events)

        self.assertTrue(should_retry)
        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('ODP event send failed (network error).')

    def test_send_odp_events_400_no_retry(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=400,
                                                                       url=self.api_host,
                                                                       content=self.failure_response_data)

            api = ZaiusRestApiManager(logger=mock_logger)
            should_retry = api.send_odp_events(api_key=self.api_key,
                                               api_host=self.api_host,
                                               events=self.events)

        self.assertFalse(should_retry)
        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('ODP event send failed ({"title":"Bad Request","status":400,'
                                                  '"timestamp":"2022-07-01T20:44:00.945Z","detail":{"invalids":'
                                                  '[{"event":0,"message":"missing \'type\' field"}]}}).')

    def test_send_odp_events_500_retry(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=500, url=self.api_host)

            api = ZaiusRestApiManager(logger=mock_logger)
            should_retry = api.send_odp_events(api_key=self.api_key,
                                               api_host=self.api_host,
                                               events=self.events)

        self.assertTrue(should_retry)
        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('ODP event send failed (500 Server Error: None for url: test-host).')

    # test json responses
    success_response_data = '{"title":"Accepted","status":202,"timestamp":"2022-07-01T16:04:06.786Z"}'

    failure_response_data = '{"title":"Bad Request","status":400,"timestamp":"2022-07-01T20:44:00.945Z",' \
                            '"detail":{"invalids":[{"event":0,"message":"missing \'type\' field"}]}}'
