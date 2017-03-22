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

import mock
import unittest

from optimizely import event_builder
from optimizely import exceptions
from optimizely import version
from optimizely.helpers import enums
from . import base


class EventTest(unittest.TestCase):

  def test_init(self):
    url = 'event.optimizely.com'
    params = {
      'a': '111001',
      'n': 'test_event',
      'g': '111028',
      'u': 'oeutest_user'
    }
    http_verb = 'POST'
    headers = {'Content-Type': 'application/json'}
    event_obj = event_builder.Event(url, params, http_verb=http_verb, headers=headers)
    self.assertEqual(url, event_obj.url)
    self.assertEqual(params, event_obj.params)
    self.assertEqual(http_verb, event_obj.http_verb)
    self.assertEqual(headers, event_obj.headers)


class EventBuilderV1Test(base.BaseTestV1):

  def setUp(self):
    base.BaseTestV1.setUp(self)
    self.event_builder = self.optimizely.event_builder
    self.maxDiff = None

  def _validate_event_object(self, event_obj, expected_url, expected_params, expected_verb, expected_headers):
    """ Helper method to validate properties of the event object. """

    self.assertEqual(expected_url, event_obj.url)
    self.assertEqual(expected_params, event_obj.params)
    self.assertEqual(expected_verb, event_obj.http_verb)
    self.assertEqual(expected_headers, event_obj.headers)

  def test_get_event_builder__with_v1_datafile(self):
    """ Test that appropriate event builder is returned when datafile is of v1 version. """

    event_builder_obj = event_builder.get_event_builder(self.optimizely.config, self.optimizely.bucketer)
    self.assertIsInstance(event_builder_obj, event_builder.EventBuilderV1)

  def test_create_impression_event(self):
    """ Test that create_impression_event creates Event object with right params. """

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'visitor-event',
      'x111127': '111129',
      'g': '111127',
      'u': 'test_user',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    with mock.patch('time.time', return_value=42):
      event_obj = self.event_builder.create_impression_event(
        self.project_config.get_experiment_from_key('test_experiment'), '111129', 'test_user', None
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV1.OFFLINE_API_PATH.format(project_id='111001'),
                                expected_params, 'GET', None)

  def test_create_impression_event__with_attributes(self):
    """ Test that create_impression_event creates Event object
    with right params when attributes are provided. """

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'visitor-event',
      'x111127': '111129',
      'g': '111127',
      'u': 'test_user',
      's11133': 'test_value',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    with mock.patch('time.time', return_value=42):
      event_obj = self.event_builder.create_impression_event(
        self.project_config.get_experiment_from_key('test_experiment'),
        '111129', 'test_user', {'test_attribute': 'test_value'}
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV1.OFFLINE_API_PATH.format(project_id='111001'),
                                expected_params, 'GET', None)

  def test_create_conversion_event__with_attributes(self):
    """ Test that create_conversion_event creates Event object
    with right params when attributes are provided. """

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'test_event',
      'x111127': '111129',
      'g': '111095',
      'u': 'test_user',
      's11133': 'test_value',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    with mock.patch('time.time', return_value=42):
      event_obj = self.event_builder.create_conversion_event(
        'test_event', 'test_user', {'test_attribute': 'test_value'}, None,
        [self.project_config.get_experiment_from_key('test_experiment')]
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV1.OFFLINE_API_PATH.format(project_id='111001'),
                                expected_params, 'GET', None)

  def test_create_conversion_event__with_attributes_no_match(self):
    """ Test that create_conversion_event creates Event object with right params if attributes do not match. """

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'test_event',
      'g': '111095',
      'u': 'test_user',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    with mock.patch('time.time', return_value=42):
      event_obj = self.event_builder.create_conversion_event('test_event', 'test_user', None, None, [])
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV1.OFFLINE_API_PATH.format(project_id='111001'),
                                expected_params, 'GET', None)

  def test_create_conversion_event__with_event_value(self):
    """ Test that create_conversion_event creates Event object
    with right params when event value is provided. """

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'test_event',
      'x111127': '111129',
      'g': '111095,111096',
      'u': 'test_user',
      's11133': 'test_value',
      'v': 4200,
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    with mock.patch('time.time', return_value=42):
      event_obj = self.event_builder.create_conversion_event(
        'test_event', 'test_user', {'test_attribute': 'test_value'}, {'revenue': 4200},
        [self.project_config.get_experiment_from_key('test_experiment')]
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV1.OFFLINE_API_PATH.format(project_id='111001'),
                                expected_params, 'GET', None)

  def test_create_conversion_event__with_invalid_event_value(self):
    """ Test that create_conversion_event creates Event object
    with right params when event value is provided. """

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'test_event',
      'x111127': '111129',
      'g': '111095',
      'u': 'test_user',
      's11133': 'test_value',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    with mock.patch('time.time', return_value=42):
      event_obj = self.event_builder.create_conversion_event(
        'test_event', 'test_user', {'test_attribute': 'test_value'}, {'revenue': '4200'},
        [self.project_config.get_experiment_from_key('test_experiment')]
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV1.OFFLINE_API_PATH.format(project_id='111001'),
                                expected_params, 'GET', None)

  def test_create_conversion_event__with_deprecated_event_value(self):
    """ Test that create_conversion_event creates Event object
    with right params when event value is provided. """

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'test_event',
      'x111127': '111129',
      'g': '111095',
      'u': 'test_user',
      's11133': 'test_value',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    with mock.patch('time.time', return_value=42):
      event_obj = self.event_builder.create_conversion_event(
        'test_event', 'test_user', {'test_attribute': 'test_value'}, 4200,
        [self.project_config.get_experiment_from_key('test_experiment')]
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV1.OFFLINE_API_PATH.format(project_id='111001'),
                                expected_params, 'GET', None)


class EventBuilderV2Test(base.BaseTestV2):

  def setUp(self):
    base.BaseTestV2.setUp(self)
    self.event_builder = self.optimizely.event_builder
    self.maxDiff = None

  def _validate_event_object(self, event_obj, expected_url, expected_params, expected_verb, expected_headers):
    """ Helper method to validate properties of the event object. """

    self.assertEqual(expected_url, event_obj.url)
    self.assertEqual(expected_params, event_obj.params)
    self.assertEqual(expected_verb, event_obj.http_verb)
    self.assertEqual(expected_headers, event_obj.headers)

  def test_get_event_builder__with_v2_datafile(self):
    """ Test that appropriate event builder is returned when datafile is of v2 version. """

    event_builder_obj = event_builder.get_event_builder(self.optimizely.config, self.optimizely.bucketer)
    self.assertIsInstance(event_builder_obj, event_builder.EventBuilderV2)

  def test_get_event_builder__invalid_datafile_version(self):
    """ Test that get_event_builder raises exception for unsupported datafile version. """

    with mock.patch('optimizely.project_config.ProjectConfig.get_version', return_value='unsupported_version'):
      self.assertRaisesRegexp(exceptions.InvalidInputException, enums.Errors.UNSUPPORTED_DATAFILE_VERSION,
                              event_builder.get_event_builder, self.optimizely.config, self.optimizely.bucketer)

  def test_create_impression_event(self):
    """ Test that create_impression_event creates Event object with right params. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'layerId': '111182',
      'visitorId': 'test_user',
      'decision': {
        'experimentId': '111127',
        'variationId': '111129',
        'isLayerHoldback': False
      },
      'revision': '42',
      'timestamp': 42123,
      'isGlobalHoldback': False,
      'userFeatures': [],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123):
      event_obj = self.event_builder.create_impression_event(
        self.project_config.get_experiment_from_key('test_experiment'), '111129', 'test_user', None
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV2.IMPRESSION_ENDPOINT,
                                expected_params,
                                event_builder.EventBuilderV2.HTTP_VERB,
                                event_builder.EventBuilderV2.HTTP_HEADERS)

  def test_create_impression_event__with_attributes(self):
    """ Test that create_impression_event creates Event object
    with right params when attributes are provided. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'layerId': '111182',
      'visitorId': 'test_user',
      'revision': '42',
      'decision': {
        'experimentId': '111127',
        'variationId': '111129',
        'isLayerHoldback': False
      },
      'timestamp': 42123,
      'isGlobalHoldback': False,
      'userFeatures': [{
        'id': '111094',
        'name': 'test_attribute',
        'type': 'custom',
        'value': 'test_value',
        'shouldIndex': True
      }],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123):
      event_obj = self.event_builder.create_impression_event(
        self.project_config.get_experiment_from_key('test_experiment'),
        '111129', 'test_user', {'test_attribute': 'test_value'}
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV2.IMPRESSION_ENDPOINT,
                                expected_params,
                                event_builder.EventBuilderV2.HTTP_VERB,
                                event_builder.EventBuilderV2.HTTP_HEADERS)

  def test_create_conversion_event__with_attributes(self):
    """ Test that create_conversion_event creates Event object
    with right params when attributes are provided. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'visitorId': 'test_user',
      'eventName': 'test_event',
      'eventEntityId': '111095',
      'eventMetrics': [],
      'eventFeatures': [],
      'revision': '42',
      'layerStates': [{
          'layerId': '111182',
          'revision': '42',
          'decision': {
            'experimentId': '111127',
            'variationId': '111129',
            'isLayerHoldback': False
          },
          'actionTriggered': True,
        }
      ],
      'timestamp': 42123,
      'isGlobalHoldback': False,
      'userFeatures': [{
        'id': '111094',
        'name': 'test_attribute',
        'type': 'custom',
        'value': 'test_value',
        'shouldIndex': True
      }],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123), \
      mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=5042):
      event_obj = self.event_builder.create_conversion_event(
        'test_event', 'test_user', {'test_attribute': 'test_value'}, None,
        [self.project_config.get_experiment_from_key('test_experiment')]
      )
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV2.CONVERSION_ENDPOINT,
                                expected_params,
                                event_builder.EventBuilderV2.HTTP_VERB,
                                event_builder.EventBuilderV2.HTTP_HEADERS)

  def test_create_conversion_event__with_attributes_no_match(self):
    """ Test that create_conversion_event creates Event object with right params if attributes do not match. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'visitorId': 'test_user',
      'revision': '42',
      'eventName': 'test_event',
      'eventEntityId': '111095',
      'eventMetrics': [],
      'eventFeatures': [],
      'layerStates': [],
      'timestamp': 42123,
      'isGlobalHoldback': False,
      'userFeatures': [],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123):
      event_obj = self.event_builder.create_conversion_event('test_event', 'test_user', None, None, [])
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV2.CONVERSION_ENDPOINT,
                                expected_params,
                                event_builder.EventBuilderV2.HTTP_VERB,
                                event_builder.EventBuilderV2.HTTP_HEADERS)

  def test_create_conversion_event__with_event_value(self):
    """ Test that create_conversion_event creates Event object
    with right params when event value is provided. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'visitorId': 'test_user',
      'eventName': 'test_event',
      'eventEntityId': '111095',
      'eventMetrics': [{
        'name': 'revenue',
        'value': 4200
      }],
      'eventFeatures': [{
          'name': 'non-revenue',
          'type': 'custom',
          'value': 'abc',
          'shouldIndex': False,
        }, {
          'name': 'revenue',
          'type': 'custom',
          'value': 4200,
          'shouldIndex': False,
      }],
      'layerStates': [{
          'layerId': '111182',
          'revision': '42',
          'decision': {
            'experimentId': '111127',
            'variationId': '111129',
            'isLayerHoldback': False
          },
          'actionTriggered': True,
        }
      ],
      'timestamp': 42123,
      'revision': '42',
      'isGlobalHoldback': False,
      'userFeatures': [{
        'id': '111094',
        'name': 'test_attribute',
        'type': 'custom',
        'value': 'test_value',
        'shouldIndex': True
      }],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123), \
         mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=5042):
      event_obj = self.event_builder.create_conversion_event(
        'test_event', 'test_user', {'test_attribute': 'test_value'}, {'revenue': 4200, 'non-revenue': 'abc'},
        [self.project_config.get_experiment_from_key('test_experiment')]
      )

    # Sort event features based on ID
    event_obj.params['eventFeatures'] = sorted(event_obj.params['eventFeatures'], key=lambda x: x.get('name'))
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV2.CONVERSION_ENDPOINT,
                                expected_params,
                                event_builder.EventBuilderV2.HTTP_VERB,
                                event_builder.EventBuilderV2.HTTP_HEADERS)

  def test_create_conversion_event__with_invalid_event_value(self):
    """ Test that create_conversion_event creates Event object
    with right params when event value is provided. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'visitorId': 'test_user',
      'eventName': 'test_event',
      'eventEntityId': '111095',
      'revision': '42',
      'eventMetrics': [],
      'eventFeatures': [{
          'name': 'non-revenue',
          'type': 'custom',
          'value': 'abc',
          'shouldIndex': False,
        }, {
          'name': 'revenue',
          'type': 'custom',
          'value': '4200',
          'shouldIndex': False,
      }],
      'layerStates': [{
          'layerId': '111182',
          'revision': '42',
          'decision': {
            'experimentId': '111127',
            'variationId': '111129',
            'isLayerHoldback': False
          },
          'actionTriggered': True,
        }
      ],
      'timestamp': 42123,
      'isGlobalHoldback': False,
      'userFeatures': [{
        'id': '111094',
        'name': 'test_attribute',
        'type': 'custom',
        'value': 'test_value',
        'shouldIndex': True
      }],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123), \
      mock.patch('optimizely.bucketer.Bucketer._generate_bucket_value', return_value=5042):
      event_obj = self.event_builder.create_conversion_event(
        'test_event', 'test_user', {'test_attribute': 'test_value'}, {'revenue': '4200', 'non-revenue': 'abc'},
        [self.project_config.get_experiment_from_key('test_experiment')]
      )
    # Sort event features based on ID
    event_obj.params['eventFeatures'] = sorted(event_obj.params['eventFeatures'], key=lambda x: x.get('name'))
    self._validate_event_object(event_obj,
                                event_builder.EventBuilderV2.CONVERSION_ENDPOINT,
                                expected_params,
                                event_builder.EventBuilderV2.HTTP_VERB,
                                event_builder.EventBuilderV2.HTTP_HEADERS)
