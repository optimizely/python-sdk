# Copyright 2016-2018, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import jsonschema
import math
import numbers
from six import string_types

from optimizely.user_profile import UserProfile
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
  except:
    return False

  try:
    jsonschema.Draft4Validator(constants.JSON_SCHEMA).validate(datafile_json)
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


def is_user_profile_valid(user_profile):
  """ Determine if provided user profile is valid or not.

  Args:
    user_profile: User's profile which needs to be validated.

  Returns:
    Boolean depending upon whether profile is valid or not.
  """

  if not user_profile:
    return False

  if not type(user_profile) is dict:
    return False

  if UserProfile.USER_ID_KEY not in user_profile:
    return False

  if UserProfile.EXPERIMENT_BUCKET_MAP_KEY not in user_profile:
    return False

  experiment_bucket_map = user_profile.get(UserProfile.EXPERIMENT_BUCKET_MAP_KEY)
  if not type(experiment_bucket_map) is dict:
    return False

  for decision in experiment_bucket_map.values():
    if type(decision) is not dict or UserProfile.VARIATION_ID_KEY not in decision:
      return False

  return True


def is_non_empty_string(input_id_key):
  """ Determine if provided input_id_key is a non-empty string or not.

  Args:
    input_id_key: Variable which needs to be validated.

  Returns:
    Boolean depending upon whether input is valid or not.
  """
  if input_id_key and isinstance(input_id_key, string_types):
    return True

  return False


def is_attribute_valid(attribute_key, attribute_value):
  """ Determine if given attribute is valid.

  Args:
    attribute_key: Variable which needs to be validated
    attribute_value: Variable which needs to be validated

  Returns:
    False if attribute_key is not a string
    False if attribute_value is not one of the supported attribute types
    True otherwise
  """

  if not isinstance(attribute_key, string_types):
    return False

  if isinstance(attribute_value, (string_types, bool)):
    return True

  if isinstance(attribute_value, (numbers.Integral, float)):
    return is_finite_number(attribute_value)

  return False


def is_finite_number(value):
  """ Validates if the given value is a number, enforces
  limit of 1e53 for integers and restricts NAN, INF, -INF for doubles.

  Args:
    value: Value to be validated

  Returns:
    Boolean: True if value is a finite number else False
  """

  if not isinstance(value, (numbers.Integral, float)):
      # numbers.Integral instead of int to accomodate long integer in python 2
    return False

  if isinstance(value, bool):
    # bool is a subclass of int
    return False

  if isinstance(value, numbers.Integral):
    if value > 1e53:
      return False

  if isinstance(value, float):
    if math.isnan(value) or math.isinf(value):
      return False

  return True
