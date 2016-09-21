class Attribute(object):

  def __init__(self, id, key, segmentId=None):
    self.id = id
    self.key = key
    self.segmentId = segmentId


class Event(object):

  def __init__(self, id, key, experimentIds):
    self.id = id
    self.key = key
    self.experimentIds = experimentIds


class Experiment(object):

  def __init__(self, id, key, status, audienceIds, variations, forcedVariations,
               trafficAllocation, layerId=None, groupId=None, groupPolicy=None):
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
