# Copyright 2019 Optimizely
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


class EventBatch(object):
  """ Class respresenting Event Batch. """

  def __init__(self, account_id, project_id, revision, client_name, client_version,
               anonymize_ip, enrich_decisions, visitors=None):
    self.account_id = account_id
    self.project_id = project_id
    self.revision = revision
    self.client_name = client_name
    self.client_version = client_version
    self.anonymize_ip = anonymize_ip
    self.enrich_decisions = enrich_decisions
    self.visitors = visitors


class Decision(object):
  """ Class respresenting Decision. """

  def __init__(self, campaign_id, experiment_id, variation_id):
    self.campaign_id = campaign_id
    self.experiment_id = experiment_id
    self.variation_id = variation_id


class Snapshot(object):
  """ Class representing Snapshot. """

  def __init__(self, events, decisions=None):
    self.events = events
    self.decisions = decisions


class SnapshotEvent(object):
  """ Class representing Snapshot Event. """

  def __init__(self, entity_id, uuid, key, timestamp, revenue=None, value=None, tags=None):
    self.entity_id = entity_id
    self.uuid = uuid
    self.key = key
    self.timestamp = timestamp
    self.revenue = revenue
    self.value = value
    self.tags = tags


class Visitor(object):
  """ Class representing Visitor. """

  def __init__(self, snapshots, attributes, visitor_id):
    self.snapshots = snapshots
    self.attributes = attributes
    self.visitor_id = visitor_id


class VisitorAttribute(object):
  """ Class representing Visitor Attribute. """

  def __init__(self, entity_id, key, event_type, value):
    self.entity_id = entity_id
    self.key = key
    self.type = event_type
    self.value = value
