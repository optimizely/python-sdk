# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from requests import Response
from typing import Optional


def fake_server_response(status_code: Optional[int] = None, content: Optional[str] = None,
                         url: Optional[str] = None) -> Optional[Response]:
    """Mock the server response."""
    response = Response()
    response.status_code = status_code
    if content:
        response._content = content.encode('utf-8')
    response.url = url
    return response
