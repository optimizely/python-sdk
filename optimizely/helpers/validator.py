import json
import jsonschema

from . import constants


def is_datafile_valid(datafile):
  """ Given a datafile determine if it is valid or not.

  Args:
    datafile: JSON string representing the project.

  Returns:
    Boolean depending upon whether datafile is valid or not.
  """

  try:
    jsonschema.Draft4Validator(constants.JSON_SCHEMA).validate(json.loads(datafile))
  except:
    return False

  return True


def _has_method(obj, method):
  """ Given an object determine if it supports the method.

  Args:
    obj: Object which needs to be inspected.
    method: Method whose presence needs to be determined.

  Returns:
    Boolean depending upon whether the method is available or not.
  """

  return getattr(obj, method, None) is not None


def is_event_dispatcher_valid(event_dispatcher):
  """ Given a event_dispatcher determine if it is valid or not i.e. provides a dispatch_event method.

  Args:
    event_dispatcher: Provides a dispatch_event method to send requests.

  Returns:
    Boolean depending upon whether event_dispatcher is valid or not.
  """

  return _has_method(event_dispatcher, 'dispatch_event')


def is_logger_valid(logger):
  """ Given a logger determine if it is valid or not i.e. provides a log method.

  Args:
    logger: Provides a log method to log messages.

  Returns:
    Boolean depending upon whether logger is valid or not.
  """

  return _has_method(logger, 'log')


def is_error_handler_valid(error_handler):
  """ Given a error_handler determine if it is valid or not i.e. provides a handle_error method.

  Args:
    error_handler: Provides a handle_error method to handle exceptions.

  Returns:
    Boolean depending upon whether error_handler is valid or not.
  """

  return _has_method(error_handler, 'handle_error')


def are_attributes_valid(attributes):
  """ Determine if attributes provided are dict or not.

  Args:
    attributes: User attributes which need to be validated.

  Returns:
    Boolean depending upon whether attributes are in valid format or not.
  """

  return type(attributes) is dict
