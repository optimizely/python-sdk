import mock
import unittest

from optimizely import event_builder
from optimizely import version
from . import base


class EventTest(unittest.TestCase):

  def test_get_url(self):
    """ Test that get_url returns URL as expected. """

    params = {
      'a': '111001',
      'n': 'test_event',
      'g': '111028',
      'u': 'oeutest_user'
    }

    event_obj = event_builder.Event(params)
    self.assertEqual('https://111001.log.optimizely.com/event', event_obj.get_url())

  def test_get_params(self):
    """ Test that get_params returns params as expected. """

    params = {
      'a': '111001',
      'n': 'test_event',
      'g': '111028',
      'u': 'oeutest_user'
    }

    event_obj = event_builder.Event(params)
    self.assertEqual(params, event_obj.get_params())


class EventBuilderTest(base.BaseTest):

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
    self.assertEqual(expected_params, event_obj.params)

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
    self.assertEqual(expected_params, event_obj.params)

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
    self.assertEqual(expected_params, event_obj.params)

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
    self.assertEqual(expected_params, event_obj.params)

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
    self.assertEqual(expected_params, event_obj.params)
