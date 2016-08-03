import requests


REQUEST_TIMEOUT = 10


class EventDispatcher(object):

  @staticmethod
  def dispatch_event(url, params):
    """ Dispatch the event being represented by the Event object.

    Args:
      url: URL to send impression/conversion event to.
      params: Params to be sent to the impression/conversion event.
    """

    requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
