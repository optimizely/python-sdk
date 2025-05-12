import unittest
import json
from unittest.mock import MagicMock, patch, call
from optimizely.cmab.cmab_client import DefaultCmabClient, CmabRetryConfig
from requests.exceptions import RequestException
from optimizely.helpers.enums import Errors
from optimizely.exceptions import CmabFetchError, CmabInvalidResponseError


class TestDefaultCmabClient(unittest.TestCase):
    def setUp(self):
        self.mock_http_client = MagicMock()
        self.mock_logger = MagicMock()
        self.retry_config = CmabRetryConfig(max_retries=3, initial_backoff=0.01, max_backoff=1, backoff_multiplier=2)
        self.client = DefaultCmabClient(
            http_client=self.mock_http_client,
            logger=self.mock_logger,
            retry_config=None
        )
        self.rule_id = 'test_rule'
        self.user_id = 'user123'
        self.attributes = {'attr1': 'value1', 'attr2': 'value2'}
        self.cmab_uuid = 'uuid-1234'
        self.expected_url = f"https://prediction.cmab.optimizely.com/predict/{self.rule_id}"
        self.expected_body = {
            "instances": [{
                "visitorId": self.user_id,
                "experimentId": self.rule_id,
                "attributes": [
                    {"id": "attr1", "value": "value1", "type": "custom_attribute"},
                    {"id": "attr2", "value": "value2", "type": "custom_attribute"}
                ],
                "cmabUUID": self.cmab_uuid,
            }]
        }
        self.expected_headers = {'Content-Type': 'application/json'}

    def test_fetch_decision_returns_success_no_retry(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'predictions': [{'variation_id': 'abc123'}]
        }
        self.mock_http_client.post.return_value = mock_response
        result = self.client.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)
        self.assertEqual(result, 'abc123')
        self.mock_http_client.post.assert_called_once_with(
            self.expected_url,
            data=json.dumps(self.expected_body),
            headers=self.expected_headers,
            timeout=10.0
        )

    def test_fetch_decision_returns_http_exception_no_retry(self):
        self.mock_http_client.post.side_effect = RequestException('Connection error')

        with self.assertRaises(CmabFetchError) as context:
            self.client.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)

        self.mock_http_client.post.assert_called_once()
        self.mock_logger.error.assert_called_with(Errors.CMAB_FETCH_FAILED.format('Connection error'))
        self.assertIn('Connection error', str(context.exception))

    def test_fetch_decision_returns_non_2xx_status_no_retry(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(CmabFetchError) as context:
            self.client.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)

        self.mock_http_client.post.assert_called_once_with(
            self.expected_url,
            data=json.dumps(self.expected_body),
            headers=self.expected_headers,
            timeout=10.0
        )
        self.mock_logger.error.assert_called_with(Errors.CMAB_FETCH_FAILED.format(str(mock_response.status_code)))
        self.assertIn(str(mock_response.status_code), str(context.exception))

    def test_fetch_decision_returns_invalid_json_no_retry(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(CmabInvalidResponseError) as context:
            self.client.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)

        self.mock_http_client.post.assert_called_once_with(
            self.expected_url,
            data=json.dumps(self.expected_body),
            headers=self.expected_headers,
            timeout=10.0
        )
        self.mock_logger.error.assert_called_with(Errors.INVALID_CMAB_FETCH_RESPONSE)
        self.assertIn(Errors.INVALID_CMAB_FETCH_RESPONSE, str(context.exception))

    def test_fetch_decision_returns_invalid_response_structure_no_retry(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'no_predictions': []}
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(CmabInvalidResponseError) as context:
            self.client.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)

        self.mock_http_client.post.assert_called_once_with(
            self.expected_url,
            data=json.dumps(self.expected_body),
            headers=self.expected_headers,
            timeout=10.0
        )
        self.mock_logger.error.assert_called_with(Errors.INVALID_CMAB_FETCH_RESPONSE)
        self.assertIn(Errors.INVALID_CMAB_FETCH_RESPONSE, str(context.exception))

    @patch('time.sleep', return_value=None)
    def test_fetch_decision_returns_success_with_retry_on_first_try(self, mock_sleep):
        # Create client with retry
        client_with_retry = DefaultCmabClient(
            http_client=self.mock_http_client,
            logger=self.mock_logger,
            retry_config=self.retry_config
        )

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'predictions': [{'variation_id': 'abc123'}]
        }
        self.mock_http_client.post.return_value = mock_response

        result = client_with_retry.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)

        # Verify result and request parameters
        self.assertEqual(result, 'abc123')
        self.mock_http_client.post.assert_called_once_with(
            self.expected_url,
            data=json.dumps(self.expected_body),
            headers=self.expected_headers,
            timeout=10.0
        )
        self.assertEqual(self.mock_http_client.post.call_count, 1)
        mock_sleep.assert_not_called()

    @patch('time.sleep', return_value=None)
    def test_fetch_decision_returns_success_with_retry_on_third_try(self, mock_sleep):
        client_with_retry = DefaultCmabClient(
            http_client=self.mock_http_client,
            logger=self.mock_logger,
            retry_config=self.retry_config
        )

        # Create failure and success responses
        failure_response = MagicMock()
        failure_response.status_code = 500

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            'predictions': [{'variation_id': 'xyz456'}]
        }

        # First two calls fail, third succeeds
        self.mock_http_client.post.side_effect = [
            failure_response,
            failure_response,
            success_response
        ]

        result = client_with_retry.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)

        self.assertEqual(result, 'xyz456')
        self.assertEqual(self.mock_http_client.post.call_count, 3)

        # Verify all HTTP calls used correct parameters
        self.mock_http_client.post.assert_called_with(
            self.expected_url,
            data=json.dumps(self.expected_body),
            headers=self.expected_headers,
            timeout=10.0
        )

        # Verify retry logging
        self.mock_logger.info.assert_has_calls([
            call("Retrying CMAB request (attempt: 1) after 0.01 seconds..."),
            call("Retrying CMAB request (attempt: 2) after 0.02 seconds...")
        ])

        # Verify sleep was called with correct backoff times
        mock_sleep.assert_has_calls([
            call(0.01),
            call(0.02)
        ])

    @patch('time.sleep', return_value=None)
    def test_fetch_decision_exhausts_all_retry_attempts(self, mock_sleep):
        client_with_retry = DefaultCmabClient(
            http_client=self.mock_http_client,
            logger=self.mock_logger,
            retry_config=self.retry_config
        )

        # Create failure response
        failure_response = MagicMock()
        failure_response.status_code = 500

        # All attempts fail
        self.mock_http_client.post.return_value = failure_response

        with self.assertRaises(CmabFetchError):
            client_with_retry.fetch_decision(self.rule_id, self.user_id, self.attributes, self.cmab_uuid)

        # Verify all attempts were made (1 initial + 3 retries)
        self.assertEqual(self.mock_http_client.post.call_count, 4)

        # Verify retry logging
        self.mock_logger.info.assert_has_calls([
            call("Retrying CMAB request (attempt: 1) after 0.01 seconds..."),
            call("Retrying CMAB request (attempt: 2) after 0.02 seconds..."),
            call("Retrying CMAB request (attempt: 3) after 0.08 seconds...")
        ])

        # Verify sleep was called for each retry
        mock_sleep.assert_has_calls([
            call(0.01),
            call(0.02),
            call(0.08)
        ])

        # Verify final error
        self.mock_logger.error.assert_called_with(
            Errors.CMAB_FETCH_FAILED.format('Exhausted all retries for CMAB request.')
        )
