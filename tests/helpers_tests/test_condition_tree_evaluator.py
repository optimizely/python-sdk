# Copyright 2018, Optimizely
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

from optimizely.helpers.condition_tree_evaluator import evaluate
from tests import base

conditionA = {
    'name': 'browser_type',
    'value': 'safari',
    'type': 'custom_attribute',
}

conditionB = {
    'name': 'device_model',
    'value': 'iphone6',
    'type': 'custom_attribute',
}

conditionC = {
    'name': 'location',
    'match': 'exact',
    'type': 'custom_attribute',
    'value': 'CA',
}


class ConditionTreeEvaluatorTests(base.BaseTest):
    def test_evaluate__returns_true(self):
        """ Test that evaluate returns True when the leaf condition evaluator returns True. """

        self.assertStrictTrue(evaluate(conditionA, lambda a: True))

    def test_evaluate__returns_false(self):
        """ Test that evaluate returns False when the leaf condition evaluator returns False. """

        self.assertStrictFalse(evaluate(conditionA, lambda a: False))

    def test_and_evaluator__returns_true(self):
        """ Test that and_evaluator returns True when all conditions evaluate to True. """

        self.assertStrictTrue(evaluate(['and', conditionA, conditionB], lambda a: True))

    def test_and_evaluator__returns_false(self):
        """ Test that and_evaluator returns False when any one condition evaluates to False. """

        leafEvaluator = mock.MagicMock(side_effect=[True, False])

        self.assertStrictFalse(evaluate(['and', conditionA, conditionB], lambda a: leafEvaluator()))

    def test_and_evaluator__returns_null__when_all_null(self):
        """ Test that and_evaluator returns null when all operands evaluate to null. """

        self.assertIsNone(evaluate(['and', conditionA, conditionB], lambda a: None))

    def test_and_evaluator__returns_null__when_trues_and_null(self):
        """ Test that and_evaluator returns when operands evaluate to trues and null. """

        leafEvaluator = mock.MagicMock(side_effect=[True, None])

        self.assertIsNone(evaluate(['and', conditionA, conditionB], lambda a: leafEvaluator()))

        leafEvaluator = mock.MagicMock(side_effect=[None, True])

        self.assertIsNone(evaluate(['and', conditionA, conditionB], lambda a: leafEvaluator()))

    def test_and_evaluator__returns_false__when_falses_and_null(self):
        """ Test that and_evaluator returns False when when operands evaluate to falses and null. """

        leafEvaluator = mock.MagicMock(side_effect=[False, None])

        self.assertStrictFalse(evaluate(['and', conditionA, conditionB], lambda a: leafEvaluator()))

        leafEvaluator = mock.MagicMock(side_effect=[None, False])

        self.assertStrictFalse(evaluate(['and', conditionA, conditionB], lambda a: leafEvaluator()))

    def test_and_evaluator__returns_false__when_trues_falses_and_null(self):
        """ Test that and_evaluator returns False when operands evaluate to trues, falses and null. """

        leafEvaluator = mock.MagicMock(side_effect=[True, False, None])

        self.assertStrictFalse(evaluate(['and', conditionA, conditionB], lambda a: leafEvaluator()))

    def test_or_evaluator__returns_true__when_any_true(self):
        """ Test that or_evaluator returns True when any one condition evaluates to True. """

        leafEvaluator = mock.MagicMock(side_effect=[False, True])

        self.assertStrictTrue(evaluate(['or', conditionA, conditionB], lambda a: leafEvaluator()))

    def test_or_evaluator__returns_false__when_all_false(self):
        """ Test that or_evaluator returns False when all operands evaluate to False."""

        self.assertStrictFalse(evaluate(['or', conditionA, conditionB], lambda a: False))

    def test_or_evaluator__returns_null__when_all_null(self):
        """ Test that or_evaluator returns null when all operands evaluate to null. """

        self.assertIsNone(evaluate(['or', conditionA, conditionB], lambda a: None))

    def test_or_evaluator__returns_true__when_trues_and_null(self):
        """ Test that or_evaluator returns True when operands evaluate to trues and null. """

        leafEvaluator = mock.MagicMock(side_effect=[None, True])

        self.assertStrictTrue(evaluate(['or', conditionA, conditionB], lambda a: leafEvaluator()))

        leafEvaluator = mock.MagicMock(side_effect=[True, None])

        self.assertStrictTrue(evaluate(['or', conditionA, conditionB], lambda a: leafEvaluator()))

    def test_or_evaluator__returns_null__when_falses_and_null(self):
        """ Test that or_evaluator returns null when operands evaluate to falses and null. """

        leafEvaluator = mock.MagicMock(side_effect=[False, None])

        self.assertIsNone(evaluate(['or', conditionA, conditionB], lambda a: leafEvaluator()))

        leafEvaluator = mock.MagicMock(side_effect=[None, False])

        self.assertIsNone(evaluate(['or', conditionA, conditionB], lambda a: leafEvaluator()))

    def test_or_evaluator__returns_true__when_trues_falses_and_null(self):
        """ Test that or_evaluator returns True when operands evaluate to trues, falses and null. """

        leafEvaluator = mock.MagicMock(side_effect=[False, None, True])

        self.assertStrictTrue(evaluate(['or', conditionA, conditionB, conditionC], lambda a: leafEvaluator()))

    def test_not_evaluator__returns_true(self):
        """ Test that not_evaluator returns True when condition evaluates to False. """

        self.assertStrictTrue(evaluate(['not', conditionA], lambda a: False))

    def test_not_evaluator__returns_false(self):
        """ Test that not_evaluator returns True when condition evaluates to False. """

        self.assertStrictFalse(evaluate(['not', conditionA], lambda a: True))

    def test_not_evaluator_negates_first_condition__ignores_rest(self):
        """ Test that not_evaluator negates first condition and ignores rest. """
        leafEvaluator = mock.MagicMock(side_effect=[False, True, None])

        self.assertStrictTrue(evaluate(['not', conditionA, conditionB, conditionC], lambda a: leafEvaluator()))

        leafEvaluator = mock.MagicMock(side_effect=[True, False, None])

        self.assertStrictFalse(evaluate(['not', conditionA, conditionB, conditionC], lambda a: leafEvaluator()))

        leafEvaluator = mock.MagicMock(side_effect=[None, True, False])

        self.assertIsNone(evaluate(['not', conditionA, conditionB, conditionC], lambda a: leafEvaluator()))

    def test_not_evaluator__returns_null__when_null(self):
        """ Test that not_evaluator returns null when condition evaluates to null. """

        self.assertIsNone(evaluate(['not', conditionA], lambda a: None))

    def test_not_evaluator__returns_null__when_there_are_no_operands(self):
        """ Test that not_evaluator returns null when there are no conditions. """

        self.assertIsNone(evaluate(['not'], lambda a: True))

    def test_evaluate_assumes__OR_operator__when_first_item_in_array_not_recognized_operator(self,):
        """ Test that by default OR operator is assumed when the first item in conditions is not
        a recognized operator. """

        leafEvaluator = mock.MagicMock(side_effect=[False, True])

        self.assertStrictTrue(evaluate([conditionA, conditionB], lambda a: leafEvaluator()))

        self.assertStrictFalse(evaluate([conditionA, conditionB], lambda a: False))
