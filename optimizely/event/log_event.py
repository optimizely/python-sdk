# Copyright 2019, 2022, Optimizely
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
from typing import Optional, Any
from sys import version_info
from optimizely import event_builder


if version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal  # type: ignore


class LogEvent(event_builder.Event):
    """ Representation of an event which can be sent to Optimizely events API. """

    def __init__(
        self,
        url: str,
        params: dict[str, Any],
        http_verb: Optional[Literal['POST', 'GET']] = None,
        headers: Optional[dict[str, str]] = None
    ):
        self.url = url
        self.params = params
        self.http_verb = http_verb or 'POST'
        self.headers = headers

    def __str__(self) -> str:
        return f'{self.__class__}: {self.__dict__}'
