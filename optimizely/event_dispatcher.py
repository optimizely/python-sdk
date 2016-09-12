import json
import requests


REQUEST_TIMEOUT = 10


class EventDispatcher(object):

  @staticmethod
  def dispatch_event(url, params, http_verb='GET', headers=None):
    """ Dispatch the event being represented by the Event object.

    Args:
      url: URL to send impression/conversion event to.
      params: Params to be sent to the impression/conversion event.
      http_verb: Optional parameter defining the HTTP method to be used for the request.
      headers: Optional parameter defining the headers to be used to make the request.
    """

    if http_verb == 'GET':
      requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    elif http_verb == 'POST':
      requests.post(url, data=json.dumps(params), headers=headers, timeout=REQUEST_TIMEOUT)
