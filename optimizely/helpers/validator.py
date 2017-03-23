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

import json
import jsonschema

from optimizely import project_config
from . import constants


def is_datafile_valid(datafile):
  """ Given a datafile determine if it is valid or not.

  Args:
    datafile: JSON string representing the project.

  Returns:
    Boolean depending upon whether datafile is valid or not.
  """

  try:
    datafile_json = json.loads(datafile)
    datafile_version = datafile_json.get('version')
  except:
    return False

  json_schema = None

  if datafile_version == project_config.V1_CONFIG_VERSION:
    json_schema = constants.JSON_SCHEMA_V1
  if datafile_version == project_config.V2_CONFIG_VERSION:
    json_schema = constants.JSON_SCHEMA_V2

  if not json_schema:
    return False

  try:
    jsonschema.Draft4Validator(json_schema).validate(datafile_json)
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


def are_event_tags_valid(event_tags):
  """ Determine if event tags provided are dict or not.

  Args:
    event_tags: Event tags which need to be validated.

  Returns:
    Boolean depending upon whether event_tags are in valid format or not.
  """

  return type(event_tags) is dict
