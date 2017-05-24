# Copyright 2016-2017, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

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

  def __init__(self, id, key, status, audienceIds, variations, forcedVariations,
               trafficAllocation, layerId, groupId=None, groupPolicy=None, **kwargs):
    self.id = id
    self.key = key
    self.status = status
    self.audienceIds = audienceIds
    self.variations = variations
    self.forcedVariations = forcedVariations
    self.trafficAllocation = trafficAllocation
    self.layerId = layerId
    self.groupId = groupId
    self.groupPolicy = groupPolicy


class Layer(BaseEntity):

  def __init__(self, id, policy, experiments):
    self.id = id
    self.policy = policy
    self.experiments = experiments


class Feature(BaseEntity):

  class VariableType(object):
    BOOLEAN = 'boolean'
    DOUBLE = 'double'
    INTEGER = 'integer'
    STRING = 'string'

  class Variable(BaseEntity):

    def __init__(self, id, key, type, defaultValue):
      self.id = id
      self.key = key
      self.type = type
      self.defaultValue = defaultValue

  def __init__(self, id, key, experimentId, layerId, variables, **kwargs):
    self.id = id
    self.key = key
    self.experimentId = experimentId
    self.layerId = layerId
    self.variables = variables
    self.variable_key_map = {}


class Group(BaseEntity):

  def __init__(self, id, policy, experiments, trafficAllocation, **kwargs):
    self.id = id
    self.policy = policy
    self.experiments = experiments
    self.trafficAllocation = trafficAllocation


class Variation(BaseEntity):

  class VariableUsage(BaseEntity):

    def __init__(self, id, value):
      self.id = id
      self.value = value

  def __init__(self, id, key, variables=None, **kwargs):
    self.id = id
    self.key = key
    self.variables = variables or []
