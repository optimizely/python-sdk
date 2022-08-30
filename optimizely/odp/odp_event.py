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

from typing import Any, Union
import uuid
import json
from optimizely import version

OdpDataType = Union[str, int, float, bool, None]


class OdpEvent:
    """ Representation of an odp event which can be sent to the Optimizely odp platform. """

    def __init__(self, type: str, action: str, identifiers: dict[str, str], data: dict[str, OdpDataType]) -> None:
        self.type = type
        self.action = action
        self.identifiers = identifiers
        self.data = self._add_common_event_data(data)

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OdpEvent):
            return self.__dict__ == other.__dict__
        elif isinstance(other, dict):
            return self.__dict__ == other
        else:
            return False

    def _add_common_event_data(self, custom_data: dict[str, OdpDataType]) -> dict[str, OdpDataType]:
        data: dict[str, OdpDataType] = {
            'idempotence_id': str(uuid.uuid4()),
            'data_source_type': 'sdk',
            'data_source': 'python-sdk',
            'data_source_version': version.__version__
        }
        data.update(custom_data)
        return data


class OdpEventEncoder(json.JSONEncoder):
    def default(self, obj: object) -> Any:
        if isinstance(obj, OdpEvent):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)
