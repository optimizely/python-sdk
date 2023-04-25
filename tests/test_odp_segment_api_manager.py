# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from unittest import mock

from requests import exceptions as request_exception

from optimizely.helpers.enums import OdpSegmentApiConfig
from optimizely.odp.odp_segment_api_manager import OdpSegmentApiManager
from . import base


class OdpSegmentApiManagerTest(base.BaseTest):
    user_key = "vuid"
    user_value = "test-user-value"
    api_key = "test-api-key"
    api_host = "test-host"

    def test_fetch_qualified_segments__valid_request(self):
        with mock.patch('requests.post') as mock_request_post:
            api = OdpSegmentApiManager()
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=["a", "b", "c"])

        test_payload = {
            'query': 'query($userId: String, $audiences: [String]) {'
            'customer(vuid: $userId) '
            '{audiences(subset: $audiences) {edges {node {name state}}}}}',
            'variables': {'userId': self.user_value, 'audiences': ["a", "b", "c"]}
        }
        request_headers = {'content-type': 'application/json', 'x-api-key': self.api_key}
        mock_request_post.assert_called_once_with(url=self.api_host + "/v3/graphql",
                                                  headers=request_headers,
                                                  data=json.dumps(test_payload),
                                                  timeout=OdpSegmentApiConfig.REQUEST_TIMEOUT)

    def test_fetch_qualified_segments__custom_timeout(self):
        with mock.patch('requests.post') as mock_request_post:
            api = OdpSegmentApiManager(timeout=12)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=["a", "b", "c"])

        test_payload = {
            'query': 'query($userId: String, $audiences: [String]) {'
            'customer(vuid: $userId) '
            '{audiences(subset: $audiences) {edges {node {name state}}}}}',
            'variables': {'userId': self.user_value, 'audiences': ["a", "b", "c"]}
        }
        request_headers = {'content-type': 'application/json', 'x-api-key': self.api_key}
        mock_request_post.assert_called_once_with(url=self.api_host + "/v3/graphql",
                                                  headers=request_headers,
                                                  data=json.dumps(test_payload),
                                                  timeout=12)

    def test_fetch_qualified_segments__success(self):
        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200, content=self.good_response_data)

            api = OdpSegmentApiManager()
            response = api.fetch_segments(api_key=self.api_key,
                                          api_host=self.api_host,
                                          user_key=self.user_key,
                                          user_value=self.user_value,
                                          segments_to_check=['dummy1', 'dummy2', 'dummy3'])

        self.assertEqual(response, ['a', 'b'])

    def test_fetch_qualified_segments__node_missing(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200, content=self.node_missing_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=['dummy1', 'dummy2', 'dummy3'])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (decode error).')

    def test_fetch_qualified_segments__mixed_missing_keys(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200,
                                          content=self.mixed_missing_keys_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=['dummy1', 'dummy2', 'dummy3'])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (decode error).')

    def test_fetch_qualified_segments__success_with_empty_segments(self):
        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200, content=self.good_empty_response_data)

            api = OdpSegmentApiManager()
            response = api.fetch_segments(api_key=self.api_key,
                                          api_host=self.api_host,
                                          user_key=self.user_key,
                                          user_value=self.user_value,
                                          segments_to_check=['dummy'])

        self.assertEqual(response, [])

    def test_fetch_qualified_segments__invalid_identifier(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200,
                                          content=self.invalid_identifier_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.warning.assert_called_once_with('Audience segments fetch failed (invalid identifier).')

    def test_fetch_qualified_segments__other_exception(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200, content=self.other_exception_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (TestExceptionClass).')

    def test_fetch_qualified_segments__bad_response(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200, content=self.bad_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (decode error).')

    def test_fetch_qualified_segments__name_invalid(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = \
                self.fake_server_response(status_code=200, content=self.name_invalid_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (JSON decode error).')

    def test_fetch_qualified_segments__invalid_key(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.invalid_edges_key_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (decode error).')

    def test_fetch_qualified_segments__invalid_key_in_error_body(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=200,
                                                                       content=self.invalid_key_for_error_response_data)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (decode error).')

    def test_fetch_qualified_segments__network_error(self):
        with mock.patch('requests.post',
                        side_effect=request_exception.ConnectionError('Connection error')) as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (network error).')
        mock_logger.debug.assert_called_once_with('GraphQL download failed: Connection error')

    def test_fetch_qualified_segments__400(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=403, url=self.api_host)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=["a", "b", "c"])

        # make sure that fetch_segments() is called (once).
        # could use assert_called_once_with() but it's not needed,
        # we already it assert_called_once_with() in test_fetch_qualified_segments__valid_request()
        mock_request_post.assert_called_once()
        # assert 403 error log
        mock_logger.error.assert_called_once_with('Audience segments fetch failed '
                                                  f'(403 Client Error: None for url: {self.api_host}).')

    def test_fetch_qualified_segments__500(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value = self.fake_server_response(status_code=500, url=self.api_host)

            api = OdpSegmentApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=["a", "b", "c"])

        # make sure that fetch_segments() is called (once).
        mock_request_post.assert_called_once()
        # assert 500 error log
        mock_logger.error.assert_called_once_with('Audience segments fetch failed '
                                                  f'(500 Server Error: None for url: {self.api_host}).')

    # test json responses

    good_response_data = """
        {
            "data": {
                "customer": {
                    "audiences": {
                        "edges": [
                            {
                                "node": {
                                    "name": "a",
                                    "state": "qualified",
                                    "description": "qualifed sample 1"
                                }
                            },
                            {
                                "node": {
                                    "name": "b",
                                    "state": "qualified",
                                    "description": "qualifed sample 2"
                                }
                            },
                            {
                                "node": {
                                    "name": "c",
                                    "state": "not_qualified",
                                    "description": "not-qualified sample"
                                }
                            }
                        ]
                    }
                }
            }
        }
        """

    good_empty_response_data = """
        {
            "data": {
                "customer": {
                    "audiences": {
                        "edges": []
                    }
                }
            }
        }
        """

    invalid_identifier_response_data = """
        {
          "errors": [
            {
              "message": "Exception while fetching data (/customer) :\
               java.lang.RuntimeException: could not resolve _fs_user_id = asdsdaddddd",
              "locations": [
                {
                  "line": 2,
                  "column": 3
                }
              ],
              "path": [
                "customer"
              ],
              "extensions": {
                "classification": "DataFetchingException",
                "code": "INVALID_IDENTIFIER_EXCEPTION"
              }
            }
          ],
          "data": {
            "customer": null
          }
        }
        """

    other_exception_response_data = """
        {
          "errors": [
            {
              "message": "Exception while fetching data (/customer) :\
               java.lang.RuntimeException: could not resolve _fs_user_id = asdsdaddddd",
              "extensions": {
                "classification": "TestExceptionClass"
              }
            }
          ],
          "data": {
            "customer": null
          }
        }
        """

    bad_response_data = """
        {
            "data": {}
        }
        """

    invalid_edges_key_response_data = """
        {
            "data": {
                "customer": {
                    "audiences": {
                        "invalid_test_key": [
                            {
                                "node": {
                                    "name": "a",
                                    "state": "qualified",
                                    "description": "qualifed sample 1"
                                }
                            }
                        ]
                    }
                }
            }
        }
        """

    invalid_key_for_error_response_data = """
        {
          "errors": [
            {
              "message": "Exception while fetching data (/customer) :\
               java.lang.RuntimeException: could not resolve _fs_user_id = asdsdaddddd",
              "locations": [
                {
                  "line": 2,
                  "column": 3
                }
              ],
              "path": [
                "customer"
              ],
              "invalid_test_key": {
                "classification": "InvalidIdentifierException"
              }
            }
          ],
          "data": {
            "customer": null
          }
    }
    """
    name_invalid_response_data = """
        {
            "data": {
                "customer": {
                    "audiences": {
                        "edges": [
                            {
                                "node": {
                                    "name": "a":::invalid-part-here:::,
                                    "state": "qualified",
                                    "description": "qualifed sample 1"
                                }
                            }
                        ]
                    }
                }
            }
        }
        """

    node_missing_response_data = """
        {
            "data": {
                "customer": {
                    "audiences": {
                        "edges": [
                            {}
                        ]
                    }
                }
            }
        }
        """

    mixed_missing_keys_response_data = """
        {
            "data": {
                "customer": {
                    "audiences": {
                        "edges": [
                            {
                                "node": {
                                    "state": "qualified"
                                }
                            },
                            {
                                "node": {
                                    "name": "a"
                                }
                            },
                            {
                                "other-name": {
                                    "name": "a",
                                    "state": "qualified"
                                }
                            }
                        ]
                    }
                }
            }
        }
        """
