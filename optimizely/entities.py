# Copyright 2016, Optimizely
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

  def __init__(self, id, key, segmentId=None):
    self.id = id
    self.key = key
    self.segmentId = segmentId


class Audience(BaseEntity):

  def __init__(self, id, name, conditions, conditionStructure=None, conditionList=None):
    self.id = id
    self.name = name
    self.conditions = conditions
    self.conditionStructure = conditionStructure
    self.conditionList = conditionList


class Event(BaseEntity):

  def __init__(self, id, key, experimentIds):
    self.id = id
    self.key = key
    self.experimentIds = experimentIds


class Experiment(BaseEntity):

  def __init__(self, id, key, status, audienceIds, variations, forcedVariations,
               trafficAllocation, layerId=None, groupId=None, groupPolicy=None, percentageIncluded=None):
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
    self.percentageIncluded = percentageIncluded


class Group(BaseEntity):

  def __init__(self, id, policy, experiments, trafficAllocation):
    self.id = id
    self.policy = policy
    self.experiments = experiments
    self.trafficAllocation = trafficAllocation


class Variation(BaseEntity):

  def __init__(self, id, key):
    self.id = id
    self.key = key
