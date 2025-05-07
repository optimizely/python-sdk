import unittest
import json
from unittest.mock import MagicMock, patch
from optimizely.cmab.cmab_client import DefaultCmabClient, CmabRetryConfig
from requests.exceptions import RequestException
from optimizely.helpers.enums import Errors
from optimizely.exceptions import CmabFetchError, CmabInvalidResponseError


class TestDefaultCmabClient_do_fetch(unittest.TestCase):
    def setUp(self):
        self.mock_http_client = MagicMock()
        self.mock_logger = MagicMock()
        self.client = DefaultCmabClient(http_client=self.mock_http_client, logger=self.mock_logger)

    def test_do_fetch_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'predictions': [{'variation_id': 'abc123'}]
        }
        self.mock_http_client.post.return_value = mock_response

        result = self.client._do_fetch('http://fake-url', {'some': 'data'}, 1.0)
        self.assertEqual(result, 'abc123')

    def test_do_fetch_http_exception(self):
        self.mock_http_client.post.side_effect = RequestException('Connection error')

        with self.assertRaises(CmabFetchError) as context:
            self.client._do_fetch('http://fake-url', {'some': 'data'}, 1.0)

        self.mock_logger.error.assert_called_with(Errors.CMAB_FETCH_FAILED.format('Connection error'))
        self.assertIn('Connection error', str(context.exception))

    def test_do_fetch_non_2xx_status(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(CmabFetchError) as context:
            self.client._do_fetch('http://fake-url', {'some': 'data'}, 1.0)

        self.mock_logger.error.assert_called_with(Errors.CMAB_FETCH_FAILED.format(str(mock_response.status_code)))
        self.assertIn(str(mock_response.status_code), str(context.exception))

    def test_do_fetch_invalid_json(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(CmabInvalidResponseError) as context:
            self.client._do_fetch('http://fake-url', {'some': 'data'}, 1.0)

        self.mock_logger.error.assert_called_with(Errors.INVALID_CMAB_FETCH_RESPONSE)
        self.assertIn(Errors.INVALID_CMAB_FETCH_RESPONSE, str(context.exception))

    def test_do_fetch_invalid_response_structure(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'no_predictions': []}
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(CmabInvalidResponseError) as context:
            self.client._do_fetch('http://fake-url', {'some': 'data'}, 1.0)

        self.mock_logger.error.assert_called_with(Errors.INVALID_CMAB_FETCH_RESPONSE)
        self.assertIn(Errors.INVALID_CMAB_FETCH_RESPONSE, str(context.exception))


class TestDefaultCmabClientWithRetry(unittest.TestCase):
    def setUp(self):
        self.mock_http_client = MagicMock()
        self.mock_logger = MagicMock()
        self.retry_config = CmabRetryConfig(max_retries=2, initial_backoff=0.01, max_backoff=1, backoff_multiplier=2)
        self.client = DefaultCmabClient(
            http_client=self.mock_http_client,
            logger=self.mock_logger,
            retry_config=self.retry_config
        )

    @patch("time.sleep", return_value=None)
    def test_do_fetch_with_retry_success_on_first_try(self, _):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "predictions": [{"variation_id": "abc123"}]
        }
        self.mock_http_client.post.return_value = mock_response

        result = self.client._do_fetch_with_retry("http://fake-url", {}, self.retry_config, 1.0)
        self.assertEqual(result, "abc123")
        self.assertEqual(self.mock_http_client.post.call_count, 1)

    @patch("time.sleep", return_value=None)
    def test_do_fetch_with_retry_success_on_retry(self, _):
        # First call fails, second call succeeds
        failure_response = MagicMock()
        failure_response.status_code = 500

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "predictions": [{"variation_id": "xyz456"}]
        }

        self.mock_http_client.post.side_effect = [
            failure_response,
            success_response
        ]

        result = self.client._do_fetch_with_retry("http://fake-url", {}, self.retry_config, 1.0)
        self.assertEqual(result, "xyz456")
        self.assertEqual(self.mock_http_client.post.call_count, 2)
        self.mock_logger.info.assert_called_with("Retrying CMAB request (attempt: 1) after 0.01 seconds...")

    @patch("time.sleep", return_value=None)
    def test_do_fetch_with_retry_exhausts_all_attempts(self, _):
        failure_response = MagicMock()
        failure_response.status_code = 500

        self.mock_http_client.post.return_value = failure_response

        with self.assertRaises(CmabFetchError):
            self.client._do_fetch_with_retry("http://fake-url", {}, self.retry_config, 1.0)

        self.assertEqual(self.mock_http_client.post.call_count, 3)  # 1 original + 2 retries
        self.mock_logger.error.assert_called_with(
            Errors.CMAB_FETCH_FAILED.format("Exhausted all retries for CMAB request."))


class TestDefaultCmabClientFetchDecision(unittest.TestCase):
    def setUp(self):
        self.mock_http_client = MagicMock()
        self.mock_logger = MagicMock()
        self.retry_config = CmabRetryConfig(max_retries=2, initial_backoff=0.01, max_backoff=1, backoff_multiplier=2)
        self.client = DefaultCmabClient(
            http_client=self.mock_http_client,
            logger=self.mock_logger,
            retry_config=None
        )
        self.rule_id = 'test_rule'
        self.user_id = 'user123'
        self.attributes = {'attr1': 'value1'}
        self.cmab_uuid = 'uuid-1234'

    @patch.object(DefaultCmabClient, '_do_fetch', return_value='var-abc')
    def test_fetch_decision_success_no_retry(self, mock_do_fetch):
        result = self.client.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)
        self.assertEqual(result, 'var-abc')
        mock_do_fetch.assert_called_once()

    @patch.object(DefaultCmabClient, '_do_fetch_with_retry', return_value='var-xyz')
    def test_fetch_decision_success_with_retry(self, mock_do_fetch_with_retry):
        client_with_retry = DefaultCmabClient(
            http_client=self.mock_http_client,
            logger=self.mock_logger,
            retry_config=self.retry_config
        )
        result = client_with_retry.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)
        self.assertEqual(result, 'var-xyz')
        mock_do_fetch_with_retry.assert_called_once()

    @patch.object(DefaultCmabClient, '_do_fetch', side_effect=RequestException("Network error"))
    def test_fetch_decision_request_exception(self, mock_do_fetch):
        with self.assertRaises(CmabFetchError):
            self.client.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)
        self.mock_logger.error.assert_called_with(Errors.CMAB_FETCH_FAILED.format("Network error"))
