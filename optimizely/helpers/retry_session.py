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

from typing import Optional, Sequence

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_retry_session(
    retries: Optional[int], backoff_factor: float, status_forcelist: Sequence[int] = (500, 502, 503, 504)
) -> requests.Session:
    """ Create a requests session that retries failed requests.

    The same retry adapter is registered for both https:// and http:// URLs.

    Args:
      retries: Total number of retries. None means no total limit (same as urllib3's Retry).
      backoff_factor: Backoff factor between retries.
      status_forcelist: HTTP status codes that should trigger a retry. Defaults to 500, 502, 503 and 504.

    Returns:
      A configured requests.Session.
    """
    session = requests.Session()

    retry = Retry(total=retries,
                  backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)

    # http:// kept so retries still apply to user-configured http:// datafile URLs / event endpoints.
    # nosemgrep
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session
