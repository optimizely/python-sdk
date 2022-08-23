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

from typing import Any


class OdpEvent:
    """ Representation of an odp event which can be sent to the Optimizely odp platform. """

    def __init__(self, type: str, action: str,
                 identifiers: dict[str, str], data: dict[str, Any]) -> None:
        self.type = type
        self.action = action
        self.identifiers = identifiers
        self.data = data