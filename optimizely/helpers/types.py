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

from typing import Optional, Any
from sys import version_info


if version_info < (3, 8):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict  # type: ignore


# Intermediate types for type checking deserialized datafile json before actual class instantiation.
# These aren't used for anything other than type signatures

class BaseEntity(TypedDict):
    pass


class BaseDict(BaseEntity):
    """Base type for parsed datafile json, before instantiation of class objects."""
    id: str
    key: str


class EventDict(BaseDict):
    """Event dict from parsed datafile json."""
    experimentIds: list[str]


class AttributeDict(BaseDict):
    """Attribute dict from parsed datafile json."""
    pass


class TrafficAllocation(BaseEntity):
    """Traffic Allocation dict from parsed datafile json."""
    endOfRange: int
    entityId: str


class VariableDict(BaseDict):
    """Variable dict from parsed datafile json."""
    value: str
    type: str
    defaultValue: str
    subType: str


class VariationDict(BaseDict):
    """Variation dict from parsed datafile json."""
    variables: list[VariableDict]
    featureEnabled: Optional[bool]


class ExperimentDict(BaseDict):
    """Experiment dict from parsed datafile json."""
    status: str
    forcedVariations: dict[str, str]
    variations: list[VariationDict]
    layerId: str
    audienceIds: list[str]
    audienceConditions: list[str | list[str]]
    trafficAllocation: list[TrafficAllocation]


class RolloutDict(BaseEntity):
    """Rollout dict from parsed datafile json."""
    id: str
    experiments: list[ExperimentDict]


class FeatureFlagDict(BaseDict):
    """Feature flag dict from parsed datafile json."""
    rolloutId: str
    variables: list[VariableDict]
    experimentIds: list[str]


class GroupDict(BaseEntity):
    """Group dict from parsed datafile json."""
    id: str
    policy: str
    experiments: list[ExperimentDict]
    trafficAllocation: list[TrafficAllocation]


class AudienceDict(BaseEntity):
    """Audience dict from parsed datafile json."""
    id: str
    name: str
    conditions: list[Any] | str


class IntegrationDict(BaseEntity):
    """Integration dict from parsed datafile json."""
    key: str
    host: str
    publicKey: str
