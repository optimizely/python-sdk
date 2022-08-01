import json
from unittest import mock

from requests import Response
from requests import exceptions as request_exception

from optimizely.odp.zaius_graphql_api_manager import REQUEST_TIMEOUT
from optimizely.odp.zaius_graphql_api_manager import ZaiusGraphQLApiManager
from . import base


class ZaiusGraphQLApiManagerTest(base.BaseTest):
    user_key = "vuid"
    user_value = "test-user-value"
    api_key = "test-api-key"
    api_host = "test-host"

    def test_fetch_qualified_segments__valid_request(self):
        with mock.patch('requests.post') as mock_request_post:
            api = ZaiusGraphQLApiManager()
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=["a", "b", "c"])

        test_payload = {
            'query': 'query {customer(' + self.user_key + ': "' + self.user_value + '") '
            '{audiences(subset:["a", "b", "c"]) {edges {node {name state}}}}}'
        }
        request_headers = {'content-type': 'application/json', 'x-api-key': self.api_key}
        mock_request_post.assert_called_once_with(url=self.api_host + "/v3/graphql",
                                                  headers=request_headers,
                                                  data=json.dumps(test_payload),
                                                  timeout=REQUEST_TIMEOUT)

    def test_fetch_qualified_segments__success(self):
        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value.json.return_value = json.loads(self.good_response_data)

            api = ZaiusGraphQLApiManager()
            response = api.fetch_segments(api_key=self.api_key,
                                          api_host=self.api_host,
                                          user_key=self.user_key,
                                          user_value=self.user_value,
                                          segments_to_check=['dummy1', 'dummy2', 'dummy3'])

        self.assertEqual(response, ['a', 'b'])

    def test_fetch_qualified_segments__success_with_empty_segments(self):
        with mock.patch('requests.post') as mock_request_post:
            mock_request_post.return_value.json.return_value = json.loads(self.good_empty_response_data)

            api = ZaiusGraphQLApiManager()
            response = api.fetch_segments(api_key=self.api_key,
                                          api_host=self.api_host,
                                          user_key=self.user_key,
                                          user_value=self.user_value,
                                          segments_to_check=['dummy'])

        self.assertEqual(response, [])

    def test_fetch_qualified_segments__invalid_identifier(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value.json.return_value = json.loads(self.invalid_identifier_response_data)

            api = ZaiusGraphQLApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=[])

        mock_request_post.assert_called_once()
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (invalid identifier).')

    def test_fetch_qualified_segments__other_exception(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:
            mock_request_post.return_value.json.return_value = json.loads(self.other_exception_response_data)

            api = ZaiusGraphQLApiManager(logger=mock_logger)
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
            mock_request_post.return_value.json.return_value = json.loads(self.bad_response_data)

            api = ZaiusGraphQLApiManager(logger=mock_logger)
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

            api = ZaiusGraphQLApiManager(logger=mock_logger)
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

            def mock_exception(**kwargs):
                myresponse = Response()
                myresponse.status_code = 403
                raise request_exception.HTTPError(response=myresponse)

            mock_request_post.side_effect = mock_exception

            api = ZaiusGraphQLApiManager(logger=mock_logger)
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
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (403).')

    def test_fetch_qualified_segments__500(self):
        with mock.patch('requests.post') as mock_request_post, \
                mock.patch('optimizely.logger') as mock_logger:

            def mock_exception(**kwargs):
                myresponse = Response()
                myresponse.status_code = 500
                raise request_exception.HTTPError(response=myresponse)

            mock_request_post.side_effect = mock_exception

            api = ZaiusGraphQLApiManager(logger=mock_logger)
            api.fetch_segments(api_key=self.api_key,
                               api_host=self.api_host,
                               user_key=self.user_key,
                               user_value=self.user_value,
                               segments_to_check=["a", "b", "c"])

        # make sure that fetch_segments() is called (once).
        mock_request_post.assert_called_once()
        # assert 500 error log
        mock_logger.error.assert_called_once_with('Audience segments fetch failed (500).')

    def test_make_subset_filter(self):
        api = ZaiusGraphQLApiManager()

        self.assertEqual("(subset:[])", api.make_subset_filter([]))
        self.assertEqual("(subset:[\"a\"])", api.make_subset_filter(["a"]))
        self.assertEqual("(subset:[\"a\", \"b\", \"c\"])", api.make_subset_filter(['a', 'b', 'c']))
        self.assertEqual("(subset:[\"a\", \"b\", \"c\"])", api.make_subset_filter(["a", "b", "c"]))
        self.assertEqual("(subset:[\"a\", \"b\", \"don't\"])", api.make_subset_filter(["a", "b", "don't"]))

    def test_extract_component(self):
        api = ZaiusGraphQLApiManager()
        dictionary = {'a': {'b': {'c': 'v'}}}

        self.assertEqual({'b': {'c': 'v'}}, api.extract_components(dictionary, 'a'))
        self.assertEqual({'c': 'v'}, api.extract_components(dictionary, 'a.b'))
        self.assertEqual('v', api.extract_components(dictionary, 'a.b.c'))
        self.assertIsNone(api.extract_components(dictionary, 'a.b.c.d'))
        self.assertIsNone(api.extract_components(dictionary, 'd'))

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
                "classification": "InvalidIdentifierException"
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
