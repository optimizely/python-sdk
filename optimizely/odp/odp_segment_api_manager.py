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
from requests.exceptions import RequestException, ConnectionError, Timeout, JSONDecodeError

from optimizely import logger as optimizely_logger
from optimizely.helpers.enums import Errors, OdpSegmentApiConfig

"""
 ODP GraphQL API
 - https://api.zaius.com/v3/graphql
 - test ODP public API key = "W4WzcEs-ABgXorzY7h1LCQ"


 [GraphQL Request]

 # fetch info with fs_user_id for ["has_email", "has_email_opted_in", "push_on_sale"] segments
 curl -i -H 'Content-Type: application/json' -H 'x-api-key: W4WzcEs-ABgXorzY7h1LCQ' -X POST -d
 '{"query":"query {customer(fs_user_id: \"tester-101\") {audiences(subset:[\"has_email\",
 \"has_email_opted_in\", \"push_on_sale\"]) {edges {node {name state}}}}}"}' https://api.zaius.com/v3/graphql
 # fetch info with vuid for ["has_email", "has_email_opted_in", "push_on_sale"] segments
 curl -i -H 'Content-Type: application/json' -H 'x-api-key: W4WzcEs-ABgXorzY7h1LCQ' -X POST -d
 '{"query":"query {customer(vuid: \"d66a9d81923d4d2f99d8f64338976322\") {audiences(subset:[\"has_email\",
 \"has_email_opted_in\", \"push_on_sale\"]) {edges {node {name state}}}}}"}' https://api.zaius.com/v3/graphql

    query MyQuery {
    customer(vuid: "d66a9d81923d4d2f99d8f64338976322") {
     audiences(subset:["has_email", "has_email_opted_in", "push_on_sale"]) {
       edges {
         node {
           name
           state
         }
       }
     }
    }
    }


    [GraphQL Response]
    {
    "data": {
     "customer": {
       "audiences": {
         "edges": [
           {
             "node": {
               "name": "has_email",
               "state": "qualified",
             }
           },
           {
             "node": {
               "name": "has_email_opted_in",
               "state": "qualified",
             }
           },
            ...
         ]
       }
     }
    }
    }

    [GraphQL Error Response]
    {
    "errors": [
     {
       "message": "Exception while fetching data (/customer) : java.lang.RuntimeException:
       could not resolve _fs_user_id = asdsdaddddd",
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


class OdpSegmentApiManager:
    """Interface for manging the fetching of audience segments."""

    def __init__(self, logger: Optional[optimizely_logger.Logger] = None, timeout: Optional[int] = None):
        self.logger = logger or optimizely_logger.NoOpLogger()
        self.timeout = timeout or OdpSegmentApiConfig.REQUEST_TIMEOUT

    def fetch_segments(self, api_key: str, api_host: str, user_key: str,
                       user_value: str, segments_to_check: list[str]) -> Optional[list[str]]:
        """
        Fetch segments from ODP GraphQL API.

        Args:
            api_key: public api key
            api_host: domain url of the host
            user_key: vuid or fs_user_id (client device id or fullstack id)
            user_value: vaue of user_key
            segments_to_check: lit of segments to check

        Returns:
            Audience segments from GraphQL.
        """
        url = f'{api_host}/v3/graphql'
        request_headers = {'content-type': 'application/json',
                           'x-api-key': str(api_key)}

        query = {
            'query':
                'query($userId: String, $audiences: [String]) {'
                f'customer({user_key}: $userId) '
                '{audiences(subset: $audiences) {edges {node {name state}}}}}',
            'variables': {
                'userId': str(user_value),
                'audiences': segments_to_check}
        }

        try:
            payload_dict = json.dumps(query)
        except TypeError as err:
            self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format(err))
            return None

        try:
            response = requests.post(url=url,
                                     headers=request_headers,
                                     data=payload_dict,
                                     timeout=self.timeout)

            response.raise_for_status()
            response_dict = response.json()

        # There is no status code with network issues such as ConnectionError or Timeouts
        # (i.e. no internet, server can't be reached).
        except (ConnectionError, Timeout) as err:
            self.logger.debug(f'GraphQL download failed: {err}')
            self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('network error'))
            return None
        except JSONDecodeError:
            self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('JSON decode error'))
            return None
        except RequestException as err:
            self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format(err))
            return None

        if response_dict and 'errors' in response_dict:
            try:
                extensions = response_dict['errors'][0]['extensions']
                error_class = extensions['classification']
                error_code = extensions.get('code')
            except (KeyError, IndexError, TypeError):
                self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('decode error'))
                return None

            if error_code == 'INVALID_IDENTIFIER_EXCEPTION':
                self.logger.warning(Errors.FETCH_SEGMENTS_FAILED.format('invalid identifier'))
                return None
            else:
                self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format(error_class))
                return None
        else:
            try:
                audiences = response_dict['data']['customer']['audiences']['edges']
                segments = [edge['node']['name'] for edge in audiences if edge['node']['state'] == 'qualified']
                return segments
            except (KeyError, TypeError):
                self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('decode error'))
                return None
