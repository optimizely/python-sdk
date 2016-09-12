import json
import requests


REQUEST_TIMEOUT = 10


class EventDispatcher(object):

  @staticmethod
  def dispatch_event(event):
    """ Dispatch the event being represented by the Event object.

    Args:
      event: Object holding information about the request to be dispatched to the event endpoint.
    """

    if event.http_verb == 'GET':
      requests.get(event.url, params=event.params, timeout=REQUEST_TIMEOUT)
    elif event.http_verb == 'POST':
      requests.post(event.url, data=json.dumps(event.params), headers=event.headers, timeout=REQUEST_TIMEOUT)
