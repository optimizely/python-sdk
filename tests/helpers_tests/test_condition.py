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

from optimizely.helpers import condition as condition_helper

from tests import base


class ConditionEvaluatorTests(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.condition_list = condition_helper.ConditionDecoder.deserialize_audience_conditions(
      self.config_dict['audiences'][0]['conditions']
    )

    attributes = {
      'test_attribute': 'test_value_1',
      'browser_type': 'firefox',
      'location': 'San Francisco'
    }
    self.condition_evaluator = condition_helper.ConditionEvaluator(attributes)

  def test_evaluator__returns_true(self):
    """ Test that evaluator correctly returns True when there is an exact match.
    Also test that evaluator works for falsy values. """

    # string attribute value
    condition_list = {'type': 'custom_attribute', 'name': 'test_attribute', 'value': ''}
    condition_evaluator = condition_helper.ConditionEvaluator({'test_attribute': ''})
    self.assertTrue(condition_evaluator.evaluator(condition_list))

    # boolean attribute value
    condition_list = {'type': 'custom_attribute', 'name': 'boolean_key', 'value': False}
    condition_evaluator = condition_helper.ConditionEvaluator({'boolean_key': False})
    self.assertTrue(condition_evaluator.evaluator(condition_list))

    # integer attribute value
    condition_list = {'type': 'custom_attribute', 'name': 'integer_key', 'value': 0}
    condition_evaluator = condition_helper.ConditionEvaluator({'integer_key': 0})
    self.assertTrue(condition_evaluator.evaluator(condition_list))

    # double attribute value
    condition_list = {'type': 'custom_attribute', 'name': 'double_key', 'value': 0.0}
    condition_evaluator = condition_helper.ConditionEvaluator({'double_key': 0.0})
    self.assertTrue(condition_evaluator.evaluator(condition_list))

  def test_evaluator__returns_false(self):
    """ Test that evaluator correctly returns False when there is no match. """
    condition_list = {'type': 'custom_attribute', 'name': 'browser_type', 'value': 'firefox'}
    attributes = {
      'browser_type': 'chrome',
      'location': 'San Francisco'
    }
    condition_evaluator = condition_helper.ConditionEvaluator(attributes)

    self.assertFalse(condition_evaluator.evaluator(condition_list))

  def test_and_evaluator__returns_true(self):
    """ Test that and_evaluator returns True when all conditions evaluate to True. """

    conditions = range(5)

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate', return_value=True):
      self.assertTrue(self.condition_evaluator.and_evaluator(conditions))

  def test_and_evaluator__returns_false(self):
    """ Test that and_evaluator returns False when any one condition evaluates to False. """

    conditions = range(5)

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate',
                    side_effect=[True, True, False, True, True]):
      self.assertFalse(self.condition_evaluator.and_evaluator(conditions))

  def test_or_evaluator__returns_true(self):
    """ Test that or_evaluator returns True when any one condition evaluates to True. """

    conditions = range(5)

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate',
                    side_effect=[False, False, True, False, False]):
      self.assertTrue(self.condition_evaluator.or_evaluator(conditions))

  def test_or_evaluator__returns_false(self):
    """ Test that or_evaluator returns False when all conditions evaluator to False. """

    conditions = range(5)

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate', return_value=False):
      self.assertFalse(self.condition_evaluator.or_evaluator(conditions))

  def test_not_evaluator__returns_true(self):
    """ Test that not_evaluator returns True when condition evaluates to False. """

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate', return_value=False):
      self.assertTrue(self.condition_evaluator.not_evaluator([42]))

  def test_not_evaluator__returns_false(self):
    """ Test that not_evaluator returns False when condition evaluates to True. """

    with mock.patch('optimizely.helpers.condition.ConditionEvaluator.evaluate', return_value=True):
      self.assertFalse(self.condition_evaluator.not_evaluator([42]))

  def test_not_evaluator__returns_false_more_than_one_condition(self):
    """ Test that not_evaluator returns False when list has more than 1 condition. """

    self.assertFalse(self.condition_evaluator.not_evaluator([42, 43]))

  def test_evaluate__returns_true(self):
    """ Test that evaluate returns True when conditions evaluate to True. """

    self.assertTrue(self.condition_evaluator.evaluate(self.condition_list))

  def test_evaluate__returns_false(self):
    """ Test that evaluate returns False when conditions evaluate to False. """

    condition_structure = {"name": "test_attribute", "type": "custom_attribute", "value": "test_value_x"}
    self.assertFalse(self.condition_evaluator.evaluate(condition_structure))


class ConditionDecoderTests(base.BaseTest):

  def test_deserialize_audience_conditions(self):
    """ Test that deserialize_audience_conditions correctly sets condition list. """

    condition_list = condition_helper.ConditionDecoder.deserialize_audience_conditions(
      self.config_dict['audiences'][0]['conditions']
    )

    self.assertEqual(
      ['and', ['or', ['or', {"name": "test_attribute", "type": "custom_attribute", "value": "test_value_1"}]]],
      condition_list
    )
