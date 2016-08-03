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

  def __init__(self, condition_data, attributes):
    self.condition_data = condition_data
    self.attributes = attributes

  def evaluator(self, condition):
    """ Method to compare single audience condition against provided user data i.e. attributes.

    Args:
      condition: Integer representing the index of condition_data that needs to be used for comparison.

    Returns:
      Boolean indicating the result of comparing the condition value against the user attributes.
    """

    return self.attributes.get(self.condition_data[condition][0]) == self.condition_data[condition][1]

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
  return [obj_dict.get('name'), obj_dict.get('value')]


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
