# Copyright 2025 Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import time
import requests
import math
from typing import Dict, Any, Optional
from optimizely import logger as _logging
from optimizely.helpers.enums import Errors
from optimizely.exceptions import CmabFetchError, CmabInvalidResponseError

# Default constants for CMAB requests
DEFAULT_MAX_RETRIES = 1
DEFAULT_INITIAL_BACKOFF = 0.1  # in seconds (100 ms)
DEFAULT_MAX_BACKOFF = 10  # in seconds
DEFAULT_BACKOFF_MULTIPLIER = 2.0
MAX_WAIT_TIME = 10.0
DEFAULT_PREDICTION_ENDPOINT = "https://prediction.cmab.optimizely.com/predict/{}"


class CmabRetryConfig:
    """Configuration for retrying CMAB requests.

    Contains parameters for maximum retries, backoff intervals, and multipliers.
    """
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
        max_backoff: float = DEFAULT_MAX_BACKOFF,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
    ):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier


class DefaultCmabClient:
    """Client for interacting with the CMAB service.

    Provides methods to fetch decisions with optional retry logic.
    """
    def __init__(self, http_client: Optional[requests.Session] = None,
                 retry_config: Optional[CmabRetryConfig] = None,
                 logger: Optional[_logging.Logger] = None,
                 prediction_endpoint: Optional[str] = None):
        """Initialize the CMAB client.

        Args:
            http_client (Optional[requests.Session]): HTTP client for making requests.
            retry_config (Optional[CmabRetryConfig]): Configuration for retry logic.
            logger (Optional[_logging.Logger]): Logger for logging messages.
            prediction_endpoint (Optional[str]): Custom prediction endpoint URL template.
                                                  Use {} as placeholder for rule_id.
        """
        self.http_client = http_client or requests.Session()
        self.retry_config = retry_config
        self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
        self.prediction_endpoint = prediction_endpoint or DEFAULT_PREDICTION_ENDPOINT

    def fetch_decision(
        self,
        rule_id: str,
        user_id: str,
        attributes: Dict[str, Any],
        cmab_uuid: str,
        timeout: float = MAX_WAIT_TIME
    ) -> str:
        """Fetch a decision from the CMAB prediction service.

        Args:
            rule_id (str): The rule ID for the experiment.
            user_id (str): The user ID for the request.
            attributes (Dict[str, Any]): User attributes for the request.
            cmab_uuid (str): Unique identifier for the CMAB request.
            timeout (float): Maximum wait time for request to respond in seconds. Defaults to 10 seconds.

        Returns:
            str: The variation ID.
        """
        url = self.prediction_endpoint.format(rule_id)
        cmab_attributes = [
            {"id": key, "value": value, "type": "custom_attribute"}
            for key, value in attributes.items()
        ]

        request_body = {
            "instances": [{
                "visitorId": user_id,
                "experimentId": rule_id,
                "attributes": cmab_attributes,
                "cmabUUID": cmab_uuid,
            }]
        }
        if self.retry_config:
            variation_id = self._do_fetch_with_retry(url, request_body, self.retry_config, timeout)
        else:
            variation_id = self._do_fetch(url, request_body, timeout)
        return variation_id

    def _do_fetch(self, url: str, request_body: Dict[str, Any], timeout: float) -> str:
        """Perform a single fetch request to the CMAB prediction service.

        Args:
            url (str): The endpoint URL.
            request_body (Dict[str, Any]): The request payload.
            timeout (float): Maximum wait time for request to respond in seconds.
        Returns:
            str: The variation ID
        """
        headers = {'Content-Type': 'application/json'}
        try:
            response = self.http_client.post(url, data=json.dumps(request_body), headers=headers, timeout=timeout)
        except requests.exceptions.RequestException as e:
            error_message = Errors.CMAB_FETCH_FAILED.format(str(e))
            self.logger.error(error_message)
            raise CmabFetchError(error_message)

        if not 200 <= response.status_code < 300:
            error_message = Errors.CMAB_FETCH_FAILED.format(str(response.status_code))
            self.logger.error(error_message)
            raise CmabFetchError(error_message)

        try:
            body = response.json()
        except json.JSONDecodeError:
            error_message = Errors.INVALID_CMAB_FETCH_RESPONSE
            self.logger.error(error_message)
            raise CmabInvalidResponseError(error_message)

        if not self.validate_response(body):
            error_message = Errors.INVALID_CMAB_FETCH_RESPONSE
            self.logger.error(error_message)
            raise CmabInvalidResponseError(error_message)

        return str(body['predictions'][0]['variation_id'])

    def validate_response(self, body: Dict[str, Any]) -> bool:
        """Validate the response structure from the CMAB service.

        Args:
            body (Dict[str, Any]): The response body to validate.

        Returns:
            bool: True if the response is valid, False otherwise.
        """
        return (
            isinstance(body, dict) and
            'predictions' in body and
            isinstance(body['predictions'], list) and
            len(body['predictions']) > 0 and
            isinstance(body['predictions'][0], dict) and
            "variation_id" in body["predictions"][0]
        )

    def _do_fetch_with_retry(
        self,
        url: str,
        request_body: Dict[str, Any],
        retry_config: CmabRetryConfig,
        timeout: float
    ) -> str:
        """Perform a fetch request with retry logic.

        Args:
            url (str): The endpoint URL.
            request_body (Dict[str, Any]): The request payload.
            retry_config (CmabRetryConfig): Configuration for retry logic.
            timeout (float): Maximum wait time for request to respond in seconds.
        Returns:
            str: The variation ID
        """
        backoff = retry_config.initial_backoff
        for attempt in range(retry_config.max_retries + 1):
            try:
                variation_id = self._do_fetch(url, request_body, timeout)
                return variation_id
            except:
                if attempt < retry_config.max_retries:
                    self.logger.info(f"Retrying CMAB request (attempt: {attempt + 1}) after {backoff} seconds...")
                    time.sleep(backoff)
                    backoff = min(backoff * math.pow(retry_config.backoff_multiplier, attempt + 1),
                                  retry_config.max_backoff)

        error_message = Errors.CMAB_FETCH_FAILED.format('Exhausted all retries for CMAB request.')
        self.logger.error(error_message)
        raise CmabFetchError(error_message)
