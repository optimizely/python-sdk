# Copyright 2016, 2018, Optimizely
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
import math
import numbers

from six import string_types, PY2


class ConditionOperatorTypes(object):
  AND = 'and'
  OR = 'or'
  NOT = 'not'


class ConditionMatchTypes(object):
  EXACT = 'exact'
  EXISTS = 'exists'
  GREATER_THAN = 'gt'
  LESS_THAN = 'lt'
  SUBSTRING = 'substring'


class ConditionTreeEvaluator(object):
  """ Class encapsulating methods to be used in audience condition tree evaluation. """

  def and_evaluator(self, conditions, leaf_evaluator):
    """ Evaluates a list of conditions as if the evaluator had been applied
    to each entry and the results AND-ed together

    Args:
      conditions: List of conditions ex: [operand_1, operand_2]
      leaf_evaluator: Function which will be called to evaluate leaf condition values

    Returns:
      Boolean:
        - True if all operands evaluate to True
        - False if a single operand evaluates to False
      None: if conditions couldn't be evaluated
    """
    saw_null_result = False

    for condition in conditions:
      result = self.evaluate(condition, leaf_evaluator)
      if result is False:
        return False
      if result is None:
        saw_null_result = True

    return None if saw_null_result else True

  def or_evaluator(self, conditions, leaf_evaluator):
    """ Evaluates a list of conditions as if the evaluator had been applied
    to each entry and the results OR-ed together

    Args:
      conditions: List of conditions ex: [operand_1, operand_2]
      leaf_evaluator: Function which will be called to evaluate leaf condition values

    Returns:
      Boolean:
        - True if any operand evaluates to True
        - False if all operands evaluate to False
      None: if conditions couldn't be evaluated

    """
    saw_null_result = False

    for condition in conditions:
      result = self.evaluate(condition, leaf_evaluator)
      if result is True:
        return True
      if result is None:
        saw_null_result = True

    return None if saw_null_result else False

  def not_evaluator(self, conditions, leaf_evaluator):
    """ Evaluates a list of conditions as if the evaluator had been applied
    to a single entry and NOT was applied to the result.

    Args:
      conditions: List of conditions ex: [operand_1, operand_2]
      leaf_evaluator: Function which will be called to evaluate leaf condition values

    Returns:
      Boolean:
        - True if the operand evaluates to False
        - False if the operand evaluates to True
      None: if conditions is empty or condition couldn't be evaluated

    """
    if not len(conditions) > 0:
      return None

    result = self.evaluate(conditions[0], leaf_evaluator)
    return None if result is None else not result

  DEFAULT_OPERATOR_TYPES = [
    ConditionOperatorTypes.AND,
    ConditionOperatorTypes.OR,
    ConditionOperatorTypes.NOT
  ]

  EVALUATORS_BY_OPERATOR_TYPE = {
    ConditionOperatorTypes.AND: and_evaluator,
    ConditionOperatorTypes.OR: or_evaluator,
    ConditionOperatorTypes.NOT: not_evaluator
  }

  def evaluate(self, conditions, leaf_evaluator):
    """ Top level method to evaluate conditions

    Args:
      conditions: Nested array of and/or conditions, or a single leaf condition value of any type
                  Example: ['and', '0', ['or', '1', '2']]
      leaf_evaluator: Function which will be called to evaluate leaf condition values

    Returns:
      Boolean: Result of evaluating the conditions using the operator rules and the leaf evaluator.
      None: if conditions couldn't be evaluated

    """

    if isinstance(conditions, list):
      if conditions[0] in self.DEFAULT_OPERATOR_TYPES:
        return self.EVALUATORS_BY_OPERATOR_TYPE[conditions[0]](self, conditions[1:], leaf_evaluator)
      else:
        # assume OR when operator is not explicit
        return self.EVALUATORS_BY_OPERATOR_TYPE[ConditionOperatorTypes.OR](self, conditions, leaf_evaluator)

    leaf_condition = conditions
    return leaf_evaluator(leaf_condition)


class CustomAttributeConditionEvaluator(object):
  """ Class encapsulating methods to be used in audience leaf condition evaluation. """

  CUSTOM_ATTRIBUTE_CONDITION_TYPE = 'custom_attribute'

  MATCH_TYPES = [
    ConditionMatchTypes.EXACT,
    ConditionMatchTypes.EXISTS,
    ConditionMatchTypes.GREATER_THAN,
    ConditionMatchTypes.LESS_THAN,
    ConditionMatchTypes.SUBSTRING
  ]

  def __init__(self, condition_data, attributes):
    self.condition_data = condition_data
    self.attributes = attributes or {}

  def is_finite(self, value):
    """ Method to validate if the given value is a number and not one of NAN, INF, -INF

    Args:
      value: Value to be validated

    Returns:
      Boolean: True if value is a number and not NAN, INF or -INF else False
    """
    if not isinstance(value, (numbers.Integral, float)):
      # numbers.Integral instead of int to accomodate long integer in python 2
      return False

    if math.isnan(value) or math.isinf(value):
      return False

    return True

  def is_value_valid_for_exact_conditions(self, value):
    """ Method to validate if the value is valid for exact match type evaluation

    Args:
      value: Value to validate

    Returns:
      Boolean: True if value is a string type, or a boolean, or is finite. Otherwise False
    """
    if isinstance(value, string_types) or isinstance(value, bool) or self.is_finite(value):
      return True

    return False

  def exact_evaluator(self, index):
    """ Evaluate the given exact match condition for the user attributes

    Args:
      index: Index of the condition to be evaluated

    Returns:
      Boolean:
        - True if the user attribute value is equal (===) to the condition value
        - False if the user attribute value is not equal (!==) to the condition value
      None:
        - if the condition value or user attribute value has an invalid type
        - if there is a mismatch between the user attribute type and the condition value type
    """
    condition_value = self.condition_data[index][1]
    if PY2 and isinstance(condition_value, unicode):
      # str and unicode are used interchangeably in python 2.
      # encode it to str to avoid type mismatch
      condition_value = condition_value.encode()

    condition_value_type = type(condition_value)

    user_value = self.attributes.get(self.condition_data[index][0])
    if PY2 and isinstance(user_value, unicode):
      user_value = user_value.encode()

    user_value_type = type(user_value)

    if not self.is_value_valid_for_exact_conditions(condition_value) or \
       not self.is_value_valid_for_exact_conditions(user_value) or \
            condition_value_type != user_value_type:
      return None

    return condition_value == user_value

  def exists_evaluator(self, index):
    """ Evaluate the given exists match condition for the user attributes

      Args:
        index: Index of the condition to be evaluated

      Returns:
        Boolean: True if the user attributes have a non-null value for the given condition,
                 otherwise False
    """
    attr_name = self.condition_data[index][0]
    return self.attributes.get(attr_name) is not None

  def greater_than_evaluator(self, index):
    """ Evaluate the given greater than match condition for the user attributes

      Args:
        index: Index of the condition to be evaluated

      Returns:
        Boolean:
          - True if the user attribute value is greater than the condition value
          - False if the user attribute value is less than or equal to the condition value
        None: if the condition value isn't finite or the user attribute value isn't finite
    """
    condition_value = self.condition_data[index][1]
    user_value = self.attributes.get(self.condition_data[index][0])

    if not self.is_finite(condition_value) or not self.is_finite(user_value):
      return None

    return user_value > condition_value

  def less_than_evaluator(self, index):
    """ Evaluate the given less than match condition for the user attributes

    Args:
      index: Index of the condition to be evaluated

    Returns:
      Boolean:
        - True if the user attribute value is less than the condition value
        - False if the user attribute value is greater than or equal to the condition value
      None: if the condition value isn't finite or the user attribute value isn't finite
    """
    condition_value = self.condition_data[index][1]
    user_value = self.attributes.get(self.condition_data[index][0])

    if not self.is_finite(condition_value) or not self.is_finite(user_value):
      return None

    return user_value < condition_value

  def substring_evaluator(self, index):
    """ Evaluate the given substring match condition for the given user attributes

    Args:
      index: Index of the condition to be evaluated

    Returns:
      Boolean:
        - True if the condition value is a substring of the user attribute value
        - False if the condition value is not a substring of the user attribute value
      None: if the condition value isn't a string or the user attribute value isn't a string
    """
    condition_value = self.condition_data[index][1]
    user_value = self.attributes.get(self.condition_data[index][0])

    if not isinstance(condition_value, string_types) or not isinstance(user_value, string_types):
      return None

    return condition_value in user_value

  EVALUATORS_BY_MATCH_TYPE = {
    ConditionMatchTypes.EXACT: exact_evaluator,
    ConditionMatchTypes.EXISTS: exists_evaluator,
    ConditionMatchTypes.GREATER_THAN: greater_than_evaluator,
    ConditionMatchTypes.LESS_THAN: less_than_evaluator,
    ConditionMatchTypes.SUBSTRING: substring_evaluator
  }

  def evaluate(self, index):
    """ Given a custom attribute audience condition and user attributes, evaluate the
        condition against the attributes.

    Args:
      index: Index of the condition to be evaluated

    Returns:
      Boolean:
        - True if the user attributes match the given condition
        - False if the user attributes don't match the given condition
      None: if the user attributes and condition can't be evaluated
    """

    if self.condition_data[index][2] != self.CUSTOM_ATTRIBUTE_CONDITION_TYPE:
      return None

    condition_match = self.condition_data[index][3]

    if condition_match not in self.MATCH_TYPES:
      return None

    return self.EVALUATORS_BY_MATCH_TYPE[condition_match](self, index)


class ConditionDecoder(object):
  """ Class which provides an object_hook method for decoding dict
  objects into a list when given a condition_decoder. """

  def __init__(self, condition_decoder):
    self.condition_list = []
    self.index = -1
    self.decoder = condition_decoder

  def object_hook(self, object_dict):
    """ Hook which when passed into a json.JSONDecoder will replace each dict
    in a json string with its index and convert the dict to an object as defined
    by the passed in condition_decoder. The newly created condition object is
    appended to the conditions_list.

    Args:
      object_dict: Dict representing an object.

    Returns:
      An index which will be used as the placeholder in the condition_structure
    """
    instance = self.decoder(object_dict)
    self.condition_list.append(instance)
    self.index += 1
    return self.index


def _audience_condition_deserializer(obj_dict):
  """ Deserializer defining how dict objects need to be decoded for audience conditions.

  Args:
    obj_dict: Dict representing one audience condition.

  Returns:
    List consisting of condition key and corresponding value.
  """
  return [
    obj_dict.get('name'),
    obj_dict.get('value'),
    obj_dict.get('type'),
    obj_dict.get('match', ConditionMatchTypes.EXACT)
  ]


def loads(conditions_string):
  """ Deserializes the conditions property into its corresponding
  components: the condition_structure and the condition_list.

  Args:
    conditions_string: String defining valid and/or conditions.

  Returns:
    A tuple of (condition_structure, condition_list).
    condition_structure: nested list of operators and placeholders for operands.
    condition_list: list of conditions whose index correspond to the values of the placeholders.
  """
  decoder = ConditionDecoder(_audience_condition_deserializer)

  # Create a custom JSONDecoder using the ConditionDecoder's object_hook method
  # to create the condition_structure as well as populate the condition_list
  json_decoder = json.JSONDecoder(object_hook=decoder.object_hook)

  # Perform the decoding
  condition_structure = json_decoder.decode(conditions_string)
  condition_list = decoder.condition_list

  return (condition_structure, condition_list)
