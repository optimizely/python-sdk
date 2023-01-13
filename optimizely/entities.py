# Copyright 2016-2022, Optimizely
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
from typing import TYPE_CHECKING, Any, Optional, Sequence
from sys import version_info

if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final  # type: ignore


if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from .helpers.types import ExperimentDict, TrafficAllocation, VariableDict, VariationDict


class BaseEntity:
    def __eq__(self, other: object) -> bool:
        return self.__dict__ == other.__dict__


class Attribute(BaseEntity):
    def __init__(self, id: str, key: str, **kwargs: Any):
        self.id = id
        self.key = key


class Audience(BaseEntity):
    def __init__(
        self,
        id: str,
        name: str,
        conditions: str,
        conditionStructure: Optional[list[str | list[str]]] = None,
        conditionList: Optional[list[str | list[str]]] = None,
        **kwargs: Any
    ):
        self.id = id
        self.name = name
        self.conditions = conditions
        self.conditionStructure = conditionStructure
        self.conditionList = conditionList

    def get_segments(self) -> list[str]:
        """ Extract all audience segments used in the this audience's conditions.

        Returns:
            List of segment names.
        """
        if not self.conditionList:
            return []
        return list({c[1] for c in self.conditionList if c[3] == 'qualified'})


class Event(BaseEntity):
    def __init__(self, id: str, key: str, experimentIds: list[str], **kwargs: Any):
        self.id = id
        self.key = key
        self.experimentIds = experimentIds


class Experiment(BaseEntity):
    def __init__(
        self,
        id: str,
        key: str,
        status: str,
        audienceIds: list[str],
        variations: list[VariationDict],
        forcedVariations: dict[str, str],
        trafficAllocation: list[TrafficAllocation],
        layerId: str,
        audienceConditions: Optional[Sequence[str | list[str]]] = None,
        groupId: Optional[str] = None,
        groupPolicy: Optional[str] = None,
        **kwargs: Any
    ):
        self.id = id
        self.key = key
        self.status = status
        self.audienceIds = audienceIds
        self.audienceConditions = audienceConditions
        self.variations = variations
        self.forcedVariations = forcedVariations
        self.trafficAllocation = trafficAllocation
        self.layerId = layerId
        self.groupId = groupId
        self.groupPolicy = groupPolicy

    def get_audience_conditions_or_ids(self) -> Sequence[str | list[str]]:
        """ Returns audienceConditions if present, otherwise audienceIds. """
        return self.audienceConditions if self.audienceConditions is not None else self.audienceIds

    def __str__(self) -> str:
        return self.key

    @staticmethod
    def get_default() -> Experiment:
        """ returns an empty experiment object. """
        experiment = Experiment(
            id='',
            key='',
            layerId='',
            status='',
            variations=[],
            trafficAllocation=[],
            audienceIds=[],
            audienceConditions=[],
            forcedVariations={}
        )

        return experiment


class FeatureFlag(BaseEntity):
    def __init__(
        self, id: str, key: str, experimentIds: list[str], rolloutId: str,
        variables: list[VariableDict], groupId: Optional[str] = None, **kwargs: Any
    ):
        self.id = id
        self.key = key
        self.experimentIds = experimentIds
        self.rolloutId = rolloutId
        self.variables: dict[str, Variable] = variables  # type: ignore[assignment]
        self.groupId = groupId


class Group(BaseEntity):
    def __init__(
        self, id: str, policy: str, experiments: list[Experiment],
        trafficAllocation: list[TrafficAllocation], **kwargs: Any
    ):
        self.id = id
        self.policy = policy
        self.experiments = experiments
        self.trafficAllocation = trafficAllocation


class Layer(BaseEntity):
    """Layer acts as rollout."""
    def __init__(self, id: str, experiments: list[ExperimentDict], **kwargs: Any):
        self.id = id
        self.experiments = experiments


class Variable(BaseEntity):
    class Type:
        BOOLEAN: Final = 'boolean'
        DOUBLE: Final = 'double'
        INTEGER: Final = 'integer'
        JSON: Final = 'json'
        STRING: Final = 'string'

    def __init__(self, id: str, key: str, type: str, defaultValue: Any, **kwargs: Any):
        self.id = id
        self.key = key
        self.type = type
        self.defaultValue = defaultValue


class Variation(BaseEntity):
    class VariableUsage(BaseEntity):
        def __init__(self, id: str, value: str, **kwargs: Any):
            self.id = id
            self.value = value

    def __init__(
        self, id: str, key: str, featureEnabled: bool = False, variables: Optional[list[Variable]] = None, **kwargs: Any
    ):
        self.id = id
        self.key = key
        self.featureEnabled = featureEnabled
        self.variables = variables or []

    def __str__(self) -> str:
        return self.key


class Integration(BaseEntity):
    def __init__(self, key: str, host: Optional[str] = None, publicKey: Optional[str] = None, **kwargs: Any):
        self.key = key
        self.host = host
        self.publicKey = publicKey
