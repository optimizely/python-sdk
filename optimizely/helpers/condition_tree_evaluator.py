# Copyright 2018-2019, Optimizely
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

from .condition import ConditionOperatorTypes


def and_evaluator(conditions, leaf_evaluator):
    """ Evaluates a list of conditions as if the evaluator had been applied
  to each entry and the results AND-ed together.

  Args:
    conditions: List of conditions ex: [operand_1, operand_2].
    leaf_evaluator: Function which will be called to evaluate leaf condition values.

  Returns:
    Boolean:
      - True if all operands evaluate to True.
      - False if a single operand evaluates to False.
    None: if conditions couldn't be evaluated.
  """
    saw_null_result = False

    for condition in conditions:
        result = evaluate(condition, leaf_evaluator)
        if result is False:
            return False
        if result is None:
            saw_null_result = True

    return None if saw_null_result else True


def or_evaluator(conditions, leaf_evaluator):
    """ Evaluates a list of conditions as if the evaluator had been applied
  to each entry and the results OR-ed together.

  Args:
    conditions: List of conditions ex: [operand_1, operand_2].
    leaf_evaluator: Function which will be called to evaluate leaf condition values.

  Returns:
    Boolean:
      - True if any operand evaluates to True.
      - False if all operands evaluate to False.
    None: if conditions couldn't be evaluated.
  """
    saw_null_result = False

    for condition in conditions:
        result = evaluate(condition, leaf_evaluator)
        if result is True:
            return True
        if result is None:
            saw_null_result = True

    return None if saw_null_result else False


def not_evaluator(conditions, leaf_evaluator):
    """ Evaluates a list of conditions as if the evaluator had been applied
  to a single entry and NOT was applied to the result.

  Args:
    conditions: List of conditions ex: [operand_1, operand_2].
    leaf_evaluator: Function which will be called to evaluate leaf condition values.

  Returns:
    Boolean:
      - True if the operand evaluates to False.
      - False if the operand evaluates to True.
    None: if conditions is empty or condition couldn't be evaluated.
  """
    if not len(conditions) > 0:
        return None

    result = evaluate(conditions[0], leaf_evaluator)
    return None if result is None else not result


EVALUATORS_BY_OPERATOR_TYPE = {
    ConditionOperatorTypes.AND: and_evaluator,
    ConditionOperatorTypes.OR: or_evaluator,
    ConditionOperatorTypes.NOT: not_evaluator,
}


def evaluate(conditions, leaf_evaluator):
    """ Top level method to evaluate conditions.

  Args:
    conditions: Nested array of and/or conditions, or a single leaf condition value of any type.
                Example: ['and', '0', ['or', '1', '2']]
    leaf_evaluator: Function which will be called to evaluate leaf condition values.

  Returns:
    Boolean: Result of evaluating the conditions using the operator rules and the leaf evaluator.
    None: if conditions couldn't be evaluated.

  """

    if isinstance(conditions, list):
        if conditions[0] in list(EVALUATORS_BY_OPERATOR_TYPE.keys()):
            return EVALUATORS_BY_OPERATOR_TYPE[conditions[0]](conditions[1:], leaf_evaluator)
        else:
            # assume OR when operator is not explicit.
            return EVALUATORS_BY_OPERATOR_TYPE[ConditionOperatorTypes.OR](conditions, leaf_evaluator)

    leaf_condition = conditions
    return leaf_evaluator(leaf_condition)
