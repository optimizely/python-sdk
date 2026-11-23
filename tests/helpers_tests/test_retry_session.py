# Copyright 2026, Optimizely
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

import unittest

import requests
from requests.adapters import HTTPAdapter

from optimizely.helpers.retry_session import create_retry_session


class CreateRetrySessionTest(unittest.TestCase):
    def test_returns_session_with_retry_adapter_for_https_and_http(self):
        session = create_retry_session(retries=3, backoff_factor=0.2, status_forcelist=[500, 503])

        self.assertIsInstance(session, requests.Session)
        for prefix in ('https://', 'http://'):
            adapter = session.get_adapter(prefix + 'example.com')
            self.assertIsInstance(adapter, HTTPAdapter)
            self.assertEqual(3, adapter.max_retries.total)
            self.assertEqual(0.2, adapter.max_retries.backoff_factor)
            self.assertEqual([500, 503], list(adapter.max_retries.status_forcelist))

    def test_status_forcelist_defaults_to_server_error_codes(self):
        session = create_retry_session(retries=3, backoff_factor=0.2)

        adapter = session.get_adapter('https://example.com')
        self.assertEqual([500, 502, 503, 504], list(adapter.max_retries.status_forcelist))
