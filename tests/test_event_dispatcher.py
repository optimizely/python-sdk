import mock
import unittest

from optimizely import event_dispatcher


class EventDispatcherTest(unittest.TestCase):

  def test_dispatch_event(self):
    """ Test that dispatch event fires off requests call with provided URL and params. """

    url = 'https://www.optimizely.com'
    params = {
      'a': '111001',
      'n': 'test_event',
      'g': '111028',
      'u': 'oeutest_user'
    }

    with mock.patch('requests.get') as mock_request_get:
      event_dispatcher.EventDispatcher.dispatch_event(url, params)

    mock_request_get.assert_called_once_with(url, params=params, timeout=event_dispatcher.REQUEST_TIMEOUT)
