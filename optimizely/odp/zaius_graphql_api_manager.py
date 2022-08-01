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
from sys import version_info
from typing import Optional, List

import requests

from optimizely import logger as optimizely_logger
from optimizely.helpers.enums import Errors

if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final  # type: ignore

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


REQUEST_TIMEOUT: Final = 10


class ZaiusGraphQLApiManager:
    """Interface for manging the fetching of audience segments."""
    def __init__(self, logger: Optional[optimizely_logger.Logger] = None):
        self.logger = logger or optimizely_logger.NoOpLogger()

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

        segments_filter = self.make_subset_filter(segments_to_check)
        payload_dict = {
            'query': 'query {customer(' + str(user_key) + ': "' + str(user_value) + '") '
                     '{audiences' + segments_filter + ' {edges {node {name state}}}}}'
        }

        try:
            response = requests.post(url=url,
                                     headers=request_headers,
                                     data=json.dumps(payload_dict),
                                     timeout=REQUEST_TIMEOUT)

            response.raise_for_status()
            response_dict = response.json()

        except requests.exceptions.RequestException as err:
            # There is no status code with network issues such as ConnectionError or Timeouts
            # (i.e. no internet, server can't be reached).
            if isinstance(err, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                self.logger.debug(f'GraphQL download failed: {err}')
                self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('network error'))
                return None
            elif err.response.status_code >= 400:
                self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format(err.response.status_code))
                return None

        else:
            if response_dict and 'errors' in response_dict:
                odp_errors_list = self.extract_components(response_dict, 'errors')
                error_class = self.extract_components(odp_errors_list[0], 'extensions.classification')

                if error_class == 'InvalidIdentifierException':
                    self.logger.error(Errors.INVALID_SEGMENT_IDENTIFIER)
                    return None
                else:
                    self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format(error_class))
                    return None
            else:
                audiences = self.extract_components(response_dict, 'data.customer.audiences.edges')

                if audiences is None:
                    self.logger.error(Errors.FETCH_SEGMENTS_FAILED.format('decode error'))
                    return None

                segments = [edge['node']['name'] for edge in audiences if edge['node']['state'] == 'qualified']
                return segments

    @staticmethod
    def make_subset_filter(segments: list[str]) -> str:
        """
        segments = []: (fetch none)
         --> subsetFilter = "(subset:[])"
        segments = ["a"]: (fetch one segment)
         --> subsetFilter = '(subset:["a"])'

         Purposely using .join() method to deal with special cases of
         any words with apostrophes (i.e. don't). .join() menhod enquotes
         correctly without conflicting with the apostrophe.
        """
        if segments == []:
            return '(subset:[])'
        return '(subset:["' + '", "'.join(segments) + '"]' + ')'

    @staticmethod
    def extract_components(dictionary: dict, key_path: str) -> List[Optional[str]]:
        """ Takes path to the key in dotted ke_path across nested dicts,
        slices the path and returns the value of that key.
        Works on consecutive nested dictionaries. Doesn't work if other
        data structures are mixed in (i.e. lists). List can be the final
        value.
        """
        current = dictionary

        for component in key_path.split('.'):
            if component not in current:
                return None
            current = current[component]
        extracted_list = current
        return extracted_list
