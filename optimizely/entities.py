# Copyright 2016-2020, Optimizely
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


class BaseEntity(object):
    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Attribute(BaseEntity):
    def __init__(self, id, key, **kwargs):
        self.id = id
        self.key = key


class Audience(BaseEntity):
    def __init__(self, id, name, conditions, conditionStructure=None, conditionList=None, **kwargs):
        self.id = id
        self.name = name
        self.conditions = conditions
        self.conditionStructure = conditionStructure
        self.conditionList = conditionList


class Event(BaseEntity):
    def __init__(self, id, key, experimentIds, **kwargs):
        self.id = id
        self.key = key
        self.experimentIds = experimentIds


class Experiment(BaseEntity):
    def __init__(
        self,
        id,
        key,
        status,
        audienceIds,
        variations,
        forcedVariations,
        trafficAllocation,
        layerId,
        audienceConditions=None,
        groupId=None,
        groupPolicy=None,
        **kwargs
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

    def get_audience_conditions_or_ids(self):
        """ Returns audienceConditions if present, otherwise audienceIds. """
        return self.audienceConditions if self.audienceConditions is not None else self.audienceIds


class FeatureFlag(BaseEntity):
    def __init__(self, id, key, experimentIds, rolloutId, variables, groupId=None, **kwargs):
        self.id = id
        self.key = key
        self.experimentIds = experimentIds
        self.rolloutId = rolloutId
        self.variables = variables
        self.groupId = groupId


class Group(BaseEntity):
    def __init__(self, id, policy, experiments, trafficAllocation, **kwargs):
        self.id = id
        self.policy = policy
        self.experiments = experiments
        self.trafficAllocation = trafficAllocation


class Layer(BaseEntity):
    def __init__(self, id, experiments, **kwargs):
        self.id = id
        self.experiments = experiments


class Variable(BaseEntity):
    class Type(object):
        BOOLEAN = 'boolean'
        DOUBLE = 'double'
        INTEGER = 'integer'
        JSON = 'json'
        STRING = 'string'

    def __init__(self, id, key, type, defaultValue, **kwargs):
        self.id = id
        self.key = key
        self.type = type
        self.defaultValue = defaultValue


class Variation(BaseEntity):
    class VariableUsage(BaseEntity):
        def __init__(self, id, value, **kwards):
            self.id = id
            self.value = value

    def __init__(self, id, key, featureEnabled=False, variables=None, **kwargs):
        self.id = id
        self.key = key
        self.featureEnabled = featureEnabled
        self.variables = variables or []
