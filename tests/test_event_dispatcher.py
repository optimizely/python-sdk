import mock
import json
import unittest

from optimizely import event_builder
from optimizely import event_dispatcher


class EventDispatcherTest(unittest.TestCase):

  def test_dispatch_event__get_request(self):
    """ Test that dispatch event fires off requests call with provided URL and params. """

    url = 'https://www.optimizely.com'
    params = {
      'a': '111001',
      'n': 'test_event',
      'g': '111028',
      'u': 'oeutest_user'
    }
    event = event_builder.Event(url, params)

    with mock.patch('requests.get') as mock_request_get:
      event_dispatcher.EventDispatcher.dispatch_event(event)

    mock_request_get.assert_called_once_with(url, params=params, timeout=event_dispatcher.REQUEST_TIMEOUT)

  def test_dispatch_event__post_request(self):
    """ Test that dispatch event fires off requests call with provided URL, params, HTTP verb and headers. """

    url = 'https://www.optimizely.com'
    params = {
      'accountId': '111001',
      'eventName': 'test_event',
      'eventEntityId': '111028',
      'visitorId': 'oeutest_user'
    }
    event = event_builder.Event(url, params, http_verb='POST', headers={'Content-Type': 'application/json'})

    with mock.patch('requests.post') as mock_request_post:
      event_dispatcher.EventDispatcher.dispatch_event(event)

    mock_request_post.assert_called_once_with(url, data=json.dumps(params),
                                              headers={'Content-Type': 'application/json'},
                                              timeout=event_dispatcher.REQUEST_TIMEOUT)
