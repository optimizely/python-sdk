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

from __future__ import annotations

from typing import Sequence

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_retry_session(retries: int, backoff_factor: float, status_forcelist: Sequence[int]) -> requests.Session:
    """ Create a requests session that retries failed requests.

    The same retry adapter is registered for both https:// and http:// URLs. The SDK defaults are all https://.
    The http:// prefix is registered only so that retries also apply when a user configures a custom http://
    datafile URL or event endpoint (for example an internal proxy or a local test server). Registering an adapter
    does not send anything over http://, it only configures how requests to that prefix are retried.

    Args:
      retries: Total number of retries.
      backoff_factor: Backoff factor between retries.
      status_forcelist: HTTP status codes that should trigger a retry.

    Returns:
      A configured requests.Session.
    """
    session = requests.Session()

    retry = Retry(total=retries,
                  backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)

    # Intentional, see the docstring: this only registers the retry adapter, it does not send anything over http://.
    # (Bare nosemgrep: the full rule id for request-session-with-http does not fit in the 120 character line limit.)
    # nosemgrep
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session
