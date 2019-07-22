# Copyright 2019, Optimizely
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
import json

from operator import itemgetter

from optimizely import version
from optimizely.event.entity import event_batch
from optimizely.event.entity import visitor_attribute
from optimizely.event.entity import snapshot_event
from optimizely.event.entity import visitor
from optimizely.event.entity import decision
from optimizely.event.entity import snapshot
from . import base


class EventEntitiesTest(base.BaseTest):
  def _validate_event_object(self, expected_params, event_obj):
    """ Helper method to validate properties of the event object. """

    expected_params['visitors'][0]['attributes'] = \
      sorted(expected_params['visitors'][0]['attributes'], key=itemgetter('key'))
    event_obj['visitors'][0]['attributes'] = \
      sorted(event_obj['visitors'][0]['attributes'], key=itemgetter('key'))
    self.assertEqual(expected_params, event_obj)

  def dict_clean(self, obj):
    """ Helper method to remove keys from dictionary with None values. """

    result = {}
    for k, v in obj:
      if v is None and k in ['revenue', 'value', 'tags', 'decisions']:
        continue
      else:
        result[k] = v
    return result

  def test_impression_event_equals_serialized_payload(self):
    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }],
        'snapshots': [{
          'decisions': [{
            'variation_id': '111129',
            'experiment_id': '111127',
            'campaign_id': '111182'
          }],
          'events': [{
            'timestamp': 42123,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated'
          }]
        }]
      }],
      'client_name': 'python-sdk',
      'client_version': version.__version__,
      'enrich_decisions': True,
      'anonymize_ip': False,
      'revision': '42'
    }

    batch = event_batch.EventBatch("12001", "111001", "42", "python-sdk", version.__version__,
                                   False, True)
    visitor_attr = visitor_attribute.VisitorAttribute("111094", "test_attribute", "custom", "test_value")
    event = snapshot_event.SnapshotEvent("111182", "a68cf1ad-0393-4e18-af87-efe8f01a7c9c", "campaign_activated",
                                         42123)
    event_decision = decision.Decision("111182", "111127", "111129")

    snapshots = snapshot.Snapshot([event], [event_decision])
    user = visitor.Visitor([snapshots], [visitor_attr], "test_user")

    batch.visitors = [user]

    self.maxDiff = None
    self._validate_event_object(expected_params,
                                json.loads(
                                  json.dumps(batch.__dict__, default=lambda o: o.__dict__),
                                  object_pairs_hook=self.dict_clean
                                ))

  def test_conversion_event_equals_serialized_payload(self):
    expected_params = {
      'account_id': '12001',
      'project_id': '111001',
      'visitors': [{
        'visitor_id': 'test_user',
        'attributes': [{
          'type': 'custom',
          'value': 'test_value',
          'entity_id': '111094',
          'key': 'test_attribute'
        }, {
          'type': 'custom',
          'value': 'test_value2',
          'entity_id': '111095',
          'key': 'test_attribute2'
        }],
        'snapshots': [{
          'events': [{
            'timestamp': 42123,
            'entity_id': '111182',
            'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
            'key': 'campaign_activated',
            'revenue': 4200,
            'tags': {
              'non-revenue': 'abc',
              'revenue': 4200,
              'value': 1.234
            },
            'value': 1.234
          }]
        }]
      }],
      'client_name': 'python-sdk',
      'client_version': version.__version__,
      'enrich_decisions': True,
      'anonymize_ip': False,
      'revision': '42'
    }

    batch = event_batch.EventBatch("12001", "111001", "42", "python-sdk", version.__version__,
                                    False, True)
    visitor_attr_1 = visitor_attribute.VisitorAttribute("111094", "test_attribute", "custom", "test_value")
    visitor_attr_2 = visitor_attribute.VisitorAttribute("111095", "test_attribute2", "custom", "test_value2")
    event = snapshot_event.SnapshotEvent("111182", "a68cf1ad-0393-4e18-af87-efe8f01a7c9c", "campaign_activated",
                                          42123, 4200, 1.234, {'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'})

    snapshots = snapshot.Snapshot([event])
    user = visitor.Visitor([snapshots], [visitor_attr_1, visitor_attr_2], "test_user")

    batch.visitors = [user]

    self._validate_event_object(expected_params,
                                json.loads(
                                  json.dumps(batch.__dict__, default=lambda o: o.__dict__),
                                  object_pairs_hook=self.dict_clean
                                ))
