import json
import logging
import requests

from requests import exceptions as request_exception

from .helpers import enums

REQUEST_TIMEOUT = 10


class EventDispatcher(object):

  @staticmethod
  def dispatch_event(event):
    """ Dispatch the event being represented by the Event object.

    Args:
      event: Object holding information about the request to be dispatched to the Optimizely backend.
    """

    try:
      if event.http_verb == enums.HTTPVerbs.GET:
        requests.get(event.url, params=event.params, timeout=REQUEST_TIMEOUT)
      elif event.http_verb == enums.HTTPVerbs.POST:
        requests.post(event.url, data=json.dumps(event.params), headers=event.headers, timeout=REQUEST_TIMEOUT)
    except request_exception.RequestException as error:
      logging.error('Dispatch event failed. Error: %s' % str(error))
