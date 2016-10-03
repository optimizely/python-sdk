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
