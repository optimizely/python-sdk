import mock
import unittest

from optimizely import event_builder
from optimizely import version
from . import base


class EventTest(unittest.TestCase):

  def setUp(self):
    self.url = 'event.optimizely.com'
    self.params = {
      'a': '111001',
      'n': 'test_event',
      'g': '111028',
      'u': 'oeutest_user'
    }
    self.http_verb = 'POST'
    self.headers = {'Content-Type': 'application/json'}
    self.event_obj = event_builder.Event(self.url, self.params, self.http_verb, self.headers)

  def test_get_url(self):
    """ Test that get_url returns URL as expected. """

    self.assertEqual(self.url, self.event_obj.get_url())

  def test_get_params(self):
    """ Test that get_params returns params as expected. """

    self.assertEqual(self.params, self.event_obj.get_params())

  def test_get_http_verb(self):
    """ Test that get_params returns HTTP verb as expected. """

    self.assertEqual(self.http_verb, self.event_obj.get_http_verb())

  def test_get_headers(self):
    """ Test that get_headers returns headers as expected. """

    self.assertEqual(self.headers, self.event_obj.get_headers())


class EventBuilderV1Test(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.event_builder = self.optimizely.event_builder

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
      event_obj = self.event_builder.create_impression_event('test_experiment', '111129', 'test_user', None)
    self.assertEqual(expected_params, event_obj.get_params())

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
      event_obj = self.event_builder.create_impression_event('test_experiment', '111129', 'test_user',
                                                             {'test_attribute': 'test_value'})
    self.assertEqual(expected_params, event_obj.get_params())

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
      event_obj = self.event_builder.create_conversion_event('test_event', 'test_user',
                                                             {'test_attribute': 'test_value'}, None,
                                                             [('111127', 'test_experiment')])
    self.assertEqual(expected_params, event_obj.get_params())

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
    self.assertEqual(expected_params, event_obj.get_params())

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
      event_obj = self.event_builder.create_conversion_event('test_event', 'test_user',
                                                             {'test_attribute': 'test_value'}, 4200,
                                                             [('111127', 'test_experiment')])
    self.assertEqual(expected_params, event_obj.get_params())


class EventBuilderV2Test(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.event_builder = event_builder.EventBuilderV2(self.optimizely.config, self.optimizely.bucketer)

  def test_create_impression_event(self):
    """ Test that create_impression_event creates Event object with right params. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'layerId': '',
      'visitorId': 'test_user',
      'decision': {
        'experimentId': '111127',
        'variationId': '111129',
        'isLayerHoldback': False
      },
      'timestamp': 42123,
      'isGlobalHoldback': False,
      'userFeatures': [],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123):
      event_obj = self.event_builder.create_impression_event('test_experiment', '111129', 'test_user', None)
    self.assertEqual(expected_params, event_obj.get_params())

  def test_create_impression_event__with_attributes(self):
    """ Test that create_impression_event creates Event object
    with right params when attributes are provided. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'layerId': '',
      'visitorId': 'test_user',
      'decision': {
        'experimentId': '111127',
        'variationId': '111129',
        'isLayerHoldback': False
      },
      'timestamp': 42123,
      'isGlobalHoldback': False,
      'userFeatures': [],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123):
      event_obj = self.event_builder.create_impression_event('test_experiment', '111129', 'test_user',
                                                             {'test_attribute': 'test_value'})
    self.assertEqual(expected_params, event_obj.get_params())

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
      'layerStates': [{
          'layerId': '',
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
      'userFeatures': [],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123):
      event_obj = self.event_builder.create_conversion_event('test_event', 'test_user',
                                                             {'test_attribute': 'test_value'}, None,
                                                             [('111127', 'test_experiment')])
    self.assertEqual(expected_params, event_obj.get_params())

  def test_create_conversion_event__with_attributes_no_match(self):
    """ Test that create_conversion_event creates Event object with right params if attributes do not match. """

    expected_params = {
      'accountId': '12001',
      'projectId': '111001',
      'visitorId': 'test_user',
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
    self.assertEqual(expected_params, event_obj.get_params())

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
      'eventFeatures': [],
      'layerStates': [{
          'layerId': '',
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
      'userFeatures': [],
      'clientEngine': 'python-sdk',
      'clientVersion': version.__version__
    }
    with mock.patch('time.time', return_value=42.123):
      event_obj = self.event_builder.create_conversion_event('test_event', 'test_user',
                                                             {'test_attribute': 'test_value'}, 4200,
                                                             [('111127', 'test_experiment')])
    self.assertEqual(expected_params, event_obj.get_params())
