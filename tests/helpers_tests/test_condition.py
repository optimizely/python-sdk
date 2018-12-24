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

import mock
from six import PY2

from optimizely.helpers import condition as condition_helper

from tests import base

browserConditionSafari = ['browser_type', 'safari', 'custom_attribute', 'exact']
booleanCondition = ['is_firefox', True, 'custom_attribute', 'exact']
integerCondition = ['num_users', 10, 'custom_attribute', 'exact']
doubleCondition = ['pi_value', 3.14, 'custom_attribute', 'exact']

exists_condition_list = [['input_value', None, 'custom_attribute', 'exists']]
exact_string_condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', 'exact']]
exact_int_condition_list = [['lasers_count', 9000, 'custom_attribute', 'exact']]
exact_float_condition_list = [['lasers_count', 9000.0, 'custom_attribute', 'exact']]
exact_bool_condition_list = [['did_register_user', False, 'custom_attribute', 'exact']]
substring_condition_list = [['headline_text', 'buy now', 'custom_attribute', 'substring']]
gt_int_condition_list = [['meters_travelled', 48, 'custom_attribute', 'gt']]
gt_float_condition_list = [['meters_travelled', 48.2, 'custom_attribute', 'gt']]
lt_int_condition_list = [['meters_travelled', 48, 'custom_attribute', 'lt']]
lt_float_condition_list = [['meters_travelled', 48.2, 'custom_attribute', 'lt']]


class CustomAttributeConditionEvaluator(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.condition_list = [browserConditionSafari, booleanCondition, integerCondition, doubleCondition]

  def test_evaluate__returns_true__when_attributes_pass_audience_condition(self):
    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      self.condition_list, {'browser_type': 'safari'}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_evaluate__returns_false__when_attributes_fail_audience_condition(self):
    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      self.condition_list, {'browser_type': 'chrome'}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_evaluate__evaluates__different_typed_attributes(self):
    userAttributes = {
      'browser_type': 'safari',
      'is_firefox': True,
      'num_users': 10,
      'pi_value': 3.14,
    }

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      self.condition_list, userAttributes
    )

    self.assertStrictTrue(evaluator.evaluate(0))
    self.assertStrictTrue(evaluator.evaluate(1))
    self.assertStrictTrue(evaluator.evaluate(2))
    self.assertStrictTrue(evaluator.evaluate(3))

  def test_evaluate__returns_null__when_condition_has_an_invalid_match_property(self):

    condition_list = [['weird_condition', 'hi', 'custom_attribute', 'weird_match']]

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      condition_list, {'weird_condition': 'hi'}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_evaluate__assumes_exact__when_condition_match_property_is_none(self):

    condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', None]]

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      condition_list, {'favorite_constellation': 'Lacerta'}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_evaluate__returns_null__when_condition_has_an_invalid_type_property(self):

    condition_list = [['weird_condition', 'hi', 'weird_type', 'exact']]

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      condition_list, {'weird_condition': 'hi'}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exists__returns_false__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exists_condition_list, {}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_exists__returns_false__when_user_provided_value_is_null(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exists_condition_list, {'input_value': None}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_exists__returns_true__when_user_provided_value_is_string(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exists_condition_list, {'input_value': 'hi'}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_exists__returns_true__when_user_provided_value_is_number(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exists_condition_list, {'input_value': 10}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exists_condition_list, {'input_value': 10.0}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_exists__returns_true__when_user_provided_value_is_boolean(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exists_condition_list, {'input_value': False}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_exact_string__returns_true__when_user_provided_value_is_equal_to_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_string_condition_list, {'favorite_constellation': 'Lacerta'}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_exact_string__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_string_condition_list, {'favorite_constellation': 'The Big Dipper'}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_exact_string__returns_null__when_user_provided_value_is_different_type_from_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_string_condition_list, {'favorite_constellation': False}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exact_string__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_string_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exact_int__returns_true__when_user_provided_value_is_equal_to_condition_value(self):

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        exact_int_condition_list, {'lasers_count': long(9000)}
      )

      self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
        exact_int_condition_list, {'lasers_count': 9000}
      )

    self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_int_condition_list, {'lasers_count': 9000.0}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_exact_float__returns_true__when_user_provided_value_is_equal_to_condition_value(self):

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        exact_float_condition_list, {'lasers_count': long(9000)}
      )

      self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
        exact_float_condition_list, {'lasers_count': 9000}
      )

    self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_float_condition_list, {'lasers_count': 9000.0}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_exact_int__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_int_condition_list, {'lasers_count': 8000}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_exact_float__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_float_condition_list, {'lasers_count': 8000.0}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_exact_int__returns_null__when_user_provided_value_is_different_type_from_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_int_condition_list, {'lasers_count': 'hi'}
    )

    self.assertIsNone(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_int_condition_list, {'lasers_count': True}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exact_float__returns_null__when_user_provided_value_is_different_type_from_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_float_condition_list, {'lasers_count': 'hi'}
    )

    self.assertIsNone(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_float_condition_list, {'lasers_count': True}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exact_int__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_int_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exact_float__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_float_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exact__given_number_values__calls_is_finite_number(self):
    """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
        exact_int_condition_list, {'lasers_count': 9000}
      )

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    return_value=True) as mock_is_finite:
      self.assertTrue(evaluator.evaluate(0))
    mock_is_finite.assert_called_with(9000)

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_int_condition_list, {'lasers_count': 9000.0}
    )

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    return_value=False) as mock_is_finite:
      self.assertIsNone(evaluator.evaluate(0))
    mock_is_finite.assert_called_with(9000.0)

  def test_exact_bool__returns_true__when_user_provided_value_is_equal_to_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_bool_condition_list, {'did_register_user': False}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_exact_bool__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_bool_condition_list, {'did_register_user': True}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_exact_bool__returns_null__when_user_provided_value_is_different_type_from_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_bool_condition_list, {'did_register_user': 0}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_exact_bool__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      exact_bool_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_substring__returns_true__when_condition_value_is_substring_of_user_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      substring_condition_list, {'headline_text': 'Limited time, buy now!'}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

  def test_substring__returns_false__when_condition_value_is_not_a_substring_of_user_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      substring_condition_list, {'headline_text': 'Breaking news!'}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

  def test_substring__returns_null__when_user_provided_value_not_a_string(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      substring_condition_list, {'headline_text': 10}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_substring__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      substring_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_greater_than_int__returns_true__when_user_value_greater_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {'meters_travelled': 48.1}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {'meters_travelled': 49}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        gt_int_condition_list, {'meters_travelled': long(49)}
      )

      self.assertStrictTrue(evaluator.evaluate(0))

  def test_greater_than_float__returns_true__when_user_value_greater_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_float_condition_list, {'meters_travelled': 48.3}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_float_condition_list, {'meters_travelled': 49}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        gt_float_condition_list, {'meters_travelled': long(49)}
      )

      self.assertStrictTrue(evaluator.evaluate(0))

  def test_greater_than_int__returns_false__when_user_value_not_greater_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {'meters_travelled': 47.9}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {'meters_travelled': 47}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        gt_int_condition_list, {'meters_travelled': long(47)}
      )

      self.assertStrictFalse(evaluator.evaluate(0))

  def test_greater_than_float__returns_false__when_user_value_not_greater_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_float_condition_list, {'meters_travelled': 48.2}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_float_condition_list, {'meters_travelled': 48}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        gt_float_condition_list, {'meters_travelled': long(48)}
      )

      self.assertStrictFalse(evaluator.evaluate(0))

  def test_greater_than_int__returns_null__when_user_value_is_not_a_number(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {'meters_travelled': 'a long way'}
    )

    self.assertIsNone(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {'meters_travelled': False}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_greater_than_float__returns_null__when_user_value_is_not_a_number(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_float_condition_list, {'meters_travelled': 'a long way'}
    )

    self.assertIsNone(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_float_condition_list, {'meters_travelled': False}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_greater_than_int__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_greater_than_float__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_float_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_less_than_int__returns_true__when_user_value_less_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_int_condition_list, {'meters_travelled': 47.9}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_int_condition_list, {'meters_travelled': 47}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        lt_int_condition_list, {'meters_travelled': long(47)}
      )

      self.assertStrictTrue(evaluator.evaluate(0))

  def test_less_than_float__returns_true__when_user_value_less_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_float_condition_list, {'meters_travelled': 48.1}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_float_condition_list, {'meters_travelled': 48}
    )

    self.assertStrictTrue(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        lt_float_condition_list, {'meters_travelled': long(48)}
      )

      self.assertStrictTrue(evaluator.evaluate(0))

  def test_less_than_int__returns_false__when_user_value_not_less_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_int_condition_list, {'meters_travelled': 48.1}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_int_condition_list, {'meters_travelled': 49}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        lt_int_condition_list, {'meters_travelled': long(49)}
      )

      self.assertStrictFalse(evaluator.evaluate(0))

  def test_less_than_float__returns_false__when_user_value_not_less_than_condition_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_float_condition_list, {'meters_travelled': 48.2}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_float_condition_list, {'meters_travelled': 49}
    )

    self.assertStrictFalse(evaluator.evaluate(0))

    if PY2:
      evaluator = condition_helper.CustomAttributeConditionEvaluator(
        lt_float_condition_list, {'meters_travelled': long(49)}
      )

      self.assertStrictFalse(evaluator.evaluate(0))

  def test_less_than_int__returns_null__when_user_value_is_not_a_number(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_int_condition_list, {'meters_travelled': False}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_less_than_float__returns_null__when_user_value_is_not_a_number(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_float_condition_list, {'meters_travelled': False}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_less_than_int__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_int_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_less_than_float__returns_null__when_no_user_provided_value(self):

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_float_condition_list, {}
    )

    self.assertIsNone(evaluator.evaluate(0))

  def test_greater_than__calls_is_finite_number(self):
    """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      gt_int_condition_list, {'meters_travelled': 48.1}
    )

    def is_finite_number__rejecting_condition_value(value):
      if value == 48:
        return False
      return True

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    side_effect=is_finite_number__rejecting_condition_value) as mock_is_finite:
      self.assertIsNone(evaluator.evaluate(0))

    # assert that isFiniteNumber only needs to reject condition value to stop evaluation.
    mock_is_finite.assert_called_once_with(48)

    def is_finite_number__rejecting_user_attribute_value(value):
      if value == 48.1:
        return False
      return True

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    side_effect=is_finite_number__rejecting_user_attribute_value) as mock_is_finite:
      self.assertIsNone(evaluator.evaluate(0))

    # assert that isFiniteNumber evaluates user value only if it has accepted condition value.
    mock_is_finite.assert_has_calls([mock.call(48), mock.call(48.1)])

    def is_finite_number__accepting_both_values(value):
      return True

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    side_effect=is_finite_number__accepting_both_values):
      self.assertTrue(evaluator.evaluate(0))

  def test_less_than__calls_is_finite_number(self):
    """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

    evaluator = condition_helper.CustomAttributeConditionEvaluator(
      lt_int_condition_list, {'meters_travelled': 47}
    )

    def is_finite_number__rejecting_condition_value(value):
      if value == 48:
        return False
      return True

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    side_effect=is_finite_number__rejecting_condition_value) as mock_is_finite:
      self.assertIsNone(evaluator.evaluate(0))

    # assert that isFiniteNumber only needs to reject condition value to stop evaluation.
    mock_is_finite.assert_called_once_with(48)

    def is_finite_number__rejecting_user_attribute_value(value):
      if value == 47:
        return False
      return True

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    side_effect=is_finite_number__rejecting_user_attribute_value) as mock_is_finite:
      self.assertIsNone(evaluator.evaluate(0))

    # assert that isFiniteNumber evaluates user value only if it has accepted condition value.
    mock_is_finite.assert_has_calls([mock.call(48), mock.call(47)])

    def is_finite_number__accepting_both_values(value):
      return True

    with mock.patch('optimizely.helpers.validator.is_finite_number',
                    side_effect=is_finite_number__accepting_both_values):
      self.assertTrue(evaluator.evaluate(0))


class ConditionDecoderTests(base.BaseTest):

  def test_loads(self):
    """ Test that loads correctly sets condition structure and list. """

    condition_structure, condition_list = condition_helper.loads(
      self.config_dict['audiences'][0]['conditions']
    )

    self.assertEqual(['and', ['or', ['or', 0]]], condition_structure)
    self.assertEqual([['test_attribute', 'test_value_1', 'custom_attribute', None]], condition_list)

  def test_audience_condition_deserializer_defaults(self):
    """ Test that audience_condition_deserializer defaults to None."""

    browserConditionSafari = {}

    items = condition_helper._audience_condition_deserializer(browserConditionSafari)
    self.assertIsNone(items[0])
    self.assertIsNone(items[1])
    self.assertIsNone(items[2])
    self.assertIsNone(items[3])
