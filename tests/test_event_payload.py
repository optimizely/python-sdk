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

from optimizely import version
from optimizely.event.payload import Decision, EventBatch, Snapshot, SnapshotEvent, Visitor, VisitorAttribute
from . import base


class EventPayloadTest(base.BaseTest):

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

    batch = EventBatch('12001', '111001', '42', 'python-sdk', version.__version__,
                                   False, True)
    visitor_attr = VisitorAttribute('111094', 'test_attribute', 'custom', 'test_value')
    event = SnapshotEvent('111182', 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c', 'campaign_activated',
                                         42123)
    event_decision = Decision('111182', '111127', '111129')

    snapshots = Snapshot([event], [event_decision])
    user = Visitor([snapshots], [visitor_attr], 'test_user')

    batch.visitors = [user]

    self.assertEqual(batch, expected_params)

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

    batch = EventBatch('12001', '111001', '42', 'python-sdk', version.__version__,
                                   False, True)
    visitor_attr_1 = VisitorAttribute('111094', 'test_attribute', 'custom', 'test_value')
    visitor_attr_2 = VisitorAttribute('111095', 'test_attribute2', 'custom', 'test_value2')
    event = SnapshotEvent('111182', 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c', 'campaign_activated',
                                          42123, 4200, 1.234, {'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'})

    snapshots = Snapshot([event])
    user = Visitor([snapshots], [visitor_attr_1, visitor_attr_2], 'test_user')

    batch.visitors = [user]

    self.assertEqual(batch, expected_params)
