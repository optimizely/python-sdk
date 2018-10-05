# Copyright 2016,2018, Optimizely
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


class ConditionalOperatorTypes(object):
  AND = 'and'
  OR = 'or'
  NOT = 'not'


DEFAULT_OPERATOR_TYPES = [
  ConditionalOperatorTypes.AND,
  ConditionalOperatorTypes.OR,
  ConditionalOperatorTypes.NOT
]


class ConditionEvaluator(object):
  """ Class encapsulating methods to be used in audience condition evaluation. """

  def __init__(self, attributes):
    self.attributes = attributes

  def evaluator(self, condition):
    """ Method to compare single audience condition against provided user data i.e. attributes.

    Args:
      condition: Dict representing audience condition name, value, type etc.

    Returns:
      Boolean indicating the result of comparing the condition value against the user attributes.
    """

    return self.attributes.get(condition['name']) == condition['value']

  def and_evaluator(self, conditions):
    """ Evaluates a list of conditions as if the evaluator had been applied
    to each entry and the results AND-ed together

    Args:
      conditions: List of conditions ex: [operand_1, operand_2]

    Returns:
      Boolean: True if all operands evaluate to True
    """

    for condition in conditions:
      result = self.evaluate(condition)
      if result is False:
        return False

    return True

  def or_evaluator(self, conditions):
    """ Evaluates a list of conditions as if the evaluator had been applied
    to each entry and the results OR-ed together

    Args:
      conditions: List of conditions ex: [operand_1, operand_2]

    Returns:
      Boolean: True if any operand evaluates to True
    """

    for condition in conditions:
      result = self.evaluate(condition)
      if result is True:
        return True

    return False

  def not_evaluator(self, single_condition):
    """ Evaluates a list of conditions as if the evaluator had been applied
    to a single entry and NOT was applied to the result.

    Args:
      single_condition: List of of a single condition ex: [operand_1]

    Returns:
      Boolean: True if the operand evaluates to False
    """
    if len(single_condition) != 1:
      return False

    return not self.evaluate(single_condition[0])

  OPERATORS = {
    ConditionalOperatorTypes.AND: and_evaluator,
    ConditionalOperatorTypes.OR: or_evaluator,
    ConditionalOperatorTypes.NOT: not_evaluator
  }

  def evaluate(self, conditions):
    """ Top level method to evaluate audience conditions.

    Args:
      conditions: Nested list of and/or conditions.
                  Ex: ['and', operand_1, ['or', operand_2, operand_3]]

    Returns:
      Boolean result of evaluating the conditions evaluate
    """

    if isinstance(conditions, list):
      if conditions[0] in DEFAULT_OPERATOR_TYPES:
        return self.OPERATORS[conditions[0]](self, conditions[1:])
      else:
        return False

    return self.evaluator(conditions)


class ConditionDecoder(object):
  """ Class encapsulating methods to be used in audience condition decoding. """

  @staticmethod
  def deserialize_audience_conditions(conditions_string):
    """ Deserializes the conditions property into a list of structures and conditions.

    Args:
      conditions_string: String defining valid and/or conditions.

    Returns:
      list of conditions.
    """

    return json.loads(conditions_string)
