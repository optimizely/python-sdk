import json
import time
import requests
import math
from typing import Dict, Any, Optional, List
from optimizely import logger  as _logging
from optimizely.helpers.enums import Errors

# CMAB_PREDICTION_ENDPOINT is the endpoint for CMAB predictions
CMAB_PREDICTION_ENDPOINT = "https://prediction.cmab.optimizely.com/predict/%s" 

# Default constants for CMAB requests
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 0.1  # in seconds (100 ms)
DEFAULT_MAX_BACKOFF = 10 # in seconds
DEFAULT_BACKOFF_MULTIPLIER = 2.0
MAX_WAIT_TIME = 10.0

class CmabRetryConfig:
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
    def __init__(self, http_client: Optional[requests.Session] = None,
                 retry_config: Optional[CmabRetryConfig] = None,
                 logger: Optional[_logging.Logger] = None):
        self.http_client = http_client or requests.Session()
        self.retry_config = retry_config
        self.logger = _logging.adapt_logger(logger or _logging.NoOpLogger())
        
    def fetch_decision(
        self,
        rule_id: str,
        user_id: str,
        attributes: Dict[str, Any],
        cmab_uuid: str
    ) -> Optional[str]:

        url = CMAB_PREDICTION_ENDPOINT % rule_id
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
        
        try:
            if self.retry_config:
                variation_id = self._do_fetch_with_retry(url, request_body, self.retry_config)
            else:
                variation_id = self._do_fetch(url, request_body)
            return variation_id

        except requests.RequestException as e:
            self.logger.error(f"Error fetching CMAB decision: {e}")
            pass

    def _do_fetch(self, url: str, request_body: str) -> Optional[str]:
        headers = {'Content-Type': 'application/json'}
        try:
            response = self.http_client.post(url, data=json.dumps(request_body), headers=headers, timeout=MAX_WAIT_TIME)
        except requests.exceptions.RequestException as e:
            self.logger.exception(str(e))
            return None

        if not 200 <= response.status_code < 300:
            self.logger.exception(f'CMAB Request failed with status code: {response.status_code}')
            return None

        try:
            body = response.json()
        except json.JSONDecodeError as e:
            self.logger.exception(str(e))
            return None

        if not self.validate_response(body):
            self.logger.exception('Invalid response')
            return None

        return str(body['predictions'][0]['variation_id'])
    
    def validate_response(self, body: dict) -> bool:
        return (
            isinstance(body, dict)
            and 'predictions' in body
            and isinstance(body['predictions'], list)
            and len(body['predictions']) > 0
            and isinstance(body['predictions'][0], dict)
            and "variation_id" in body["predictions"][0]
        )

    def _do_fetch_with_retry(self, url: str, request_body: dict, retry_config: CmabRetryConfig) -> Optional[str]:
        backoff = retry_config.initial_backoff
        for attempt in range(retry_config.max_retries + 1):
            variation_id = self._do_fetch(url, request_body)
            if variation_id:
                return variation_id
            if attempt < retry_config.max_retries:
                self.logger.info(f"Retrying CMAB request (attempt: {attempt + 1}) after {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * math.pow(retry_config.backoff_multiplier, attempt + 1), retry_config.max_backoff)
        self.logger.error("Exhausted all retries for CMAB request.")
        return None
