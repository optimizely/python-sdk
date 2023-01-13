# Copyright 2022, Optimizely
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

from __future__ import annotations

import json
from typing import Optional

import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

from optimizely import logger as optimizely_logger
from optimizely.helpers.enums import Errors, OdpEventApiConfig
from optimizely.odp.odp_event import OdpEvent, OdpEventEncoder

"""
 ODP REST Events API
 - https://api.zaius.com/v3/events
 - test ODP public API key = "W4WzcEs-ABgXorzY7h1LCQ"

 [Event Request]
 curl -i -H 'Content-Type: application/json' -H 'x-api-key: W4WzcEs-ABgXorzY7h1LCQ' -X POST -d
 '{"type":"fullstack","action":"identified","identifiers":{"vuid": "123","fs_user_id": "abc"},
 "data":{"idempotence_id":"xyz","source":"swift-sdk"}}' https://api.zaius.com/v3/events
 [Event Response]
 {"title":"Accepted","status":202,"timestamp":"2022-06-30T20:59:52.046Z"}
"""


class OdpEventApiManager:
    """Provides an internal service for ODP event REST api access."""

    def __init__(self, logger: Optional[optimizely_logger.Logger] = None, timeout: Optional[int] = None):
        self.logger = logger or optimizely_logger.NoOpLogger()
        self.timeout = timeout or OdpEventApiConfig.REQUEST_TIMEOUT

    def send_odp_events(self,
                        api_key: str,
                        api_host: str,
                        events: list[OdpEvent]) -> bool:
        """
        Dispatch the event being represented by the OdpEvent object.

        Args:
          api_key: public api key
          api_host: domain url of the host
          events: list of odp events to be sent to optimizely's odp platform.

        Returns:
            retry is True - if network or server error (5xx), otherwise False
        """
        should_retry = False
        url = f'{api_host}/v3/events'
        request_headers = {'content-type': 'application/json', 'x-api-key': api_key}

        try:
            payload_dict = json.dumps(events, cls=OdpEventEncoder)
        except TypeError as err:
            self.logger.error(Errors.ODP_EVENT_FAILED.format(err))
            return should_retry

        try:
            response = requests.post(url=url,
                                     headers=request_headers,
                                     data=payload_dict,
                                     timeout=self.timeout)

            response.raise_for_status()

        except (ConnectionError, Timeout):
            self.logger.error(Errors.ODP_EVENT_FAILED.format('network error'))
            # retry on network errors
            should_retry = True
        except RequestException as err:
            if err.response is not None:
                if 400 <= err.response.status_code < 500:
                    # log 4xx
                    self.logger.error(Errors.ODP_EVENT_FAILED.format(err.response.text))
                else:
                    # log 5xx
                    self.logger.error(Errors.ODP_EVENT_FAILED.format(err))
                    # retry on 500 exceptions
                    should_retry = True
            else:
                # log exceptions without response body (i.e. invalid url)
                self.logger.error(Errors.ODP_EVENT_FAILED.format(err))

        return should_retry
