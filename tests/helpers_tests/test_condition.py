# Copyright 2016-2020, Optimizely
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
ge_int_condition_list = [['meters_travelled', 48, 'custom_attribute', 'ge']]
ge_float_condition_list = [['meters_travelled', 48.2, 'custom_attribute', 'ge']]
lt_int_condition_list = [['meters_travelled', 48, 'custom_attribute', 'lt']]
lt_float_condition_list = [['meters_travelled', 48.2, 'custom_attribute', 'lt']]
le_int_condition_list = [['meters_travelled', 48, 'custom_attribute', 'le']]
le_float_condition_list = [['meters_travelled', 48.2, 'custom_attribute', 'le']]


class CustomAttributeConditionEvaluatorTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self)
        self.condition_list = [
            browserConditionSafari,
            booleanCondition,
            integerCondition,
            doubleCondition,
        ]
        self.mock_client_logger = mock.MagicMock()

    def test_evaluate__returns_true__when_attributes_pass_audience_condition(self):
        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            self.condition_list, {'browser_type': 'safari'}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_evaluate__returns_false__when_attributes_fail_audience_condition(self):
        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            self.condition_list, {'browser_type': 'chrome'}, self.mock_client_logger
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
            self.condition_list, userAttributes, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))
        self.assertStrictTrue(evaluator.evaluate(1))
        self.assertStrictTrue(evaluator.evaluate(2))
        self.assertStrictTrue(evaluator.evaluate(3))

    def test_evaluate__returns_null__when_condition_has_an_invalid_match_property(self):

        condition_list = [['weird_condition', 'hi', 'custom_attribute', 'weird_match']]

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            condition_list, {'weird_condition': 'hi'}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_evaluate__assumes_exact__when_condition_match_property_is_none(self):

        condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', None]]

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            condition_list, {'favorite_constellation': 'Lacerta'}, self.mock_client_logger,
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_evaluate__returns_null__when_condition_has_an_invalid_type_property(self):

        condition_list = [['weird_condition', 'hi', 'weird_type', 'exact']]

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            condition_list, {'weird_condition': 'hi'}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_semver_eq__returns_true(self):
        semver_equal_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_eq']]
        user_versions = ['2.0.0', '2.0']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_equal_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertTrue(result, custom_err_msg)

    def test_semver_eq__returns_false(self):
        semver_equal_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_eq']]
        user_versions = ['2.9', '1.9']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_equal_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertFalse(result, custom_err_msg)

    def test_semver_le__returns_true(self):
        semver_less_than_or_equal_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_le']]
        user_versions = ['2.0.0', '1.9']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_less_than_or_equal_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertTrue(result, custom_err_msg)

    def test_semver_le__returns_false(self):
        semver_less_than_or_equal_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_le']]
        user_versions = ['2.5.1']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_less_than_or_equal_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertFalse(result, custom_err_msg)

    def test_semver_ge__returns_true(self):
        semver_greater_than_or_equal_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_ge']]
        user_versions = ['2.0.0', '2.9']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_or_equal_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertTrue(result, custom_err_msg)

    def test_semver_ge__returns_false(self):
        semver_greater_than_or_equal_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_ge']]
        user_versions = ['1.9']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_or_equal_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertFalse(result, custom_err_msg)

    def test_semver_lt__returns_true(self):
        semver_less_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_lt']]
        user_versions = ['1.9']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_less_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertTrue(result, custom_err_msg)

    def test_semver_lt__returns_false(self):
        semver_less_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_lt']]
        user_versions = ['2.0.0', '2.5.1']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_less_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertFalse(result, custom_err_msg)

    def test_semver_gt__returns_true(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        user_versions = ['2.9']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertTrue(result, custom_err_msg)

    def test_semver_gt__returns_false(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        user_versions = ['2.0.0', '1.9']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertFalse(result, custom_err_msg)

    def test_evaluate__returns_None__when_user_version_is_not_string(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        user_versions = [True, 37]
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertIsNone(result, custom_err_msg)

    def test_evaluate__returns_None__when_user_version_with_invalid_semantic(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        user_versions = ['3.7.2.2', '+']
        for user_version in user_versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertIsNone(result, custom_err_msg)

    def test_compare_user_version_with_target_version_equal_to_0(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        versions = [
            ('2.0.1', '2.0.1'),
            ('2.9.9-beta', '2.9.9-beta'),
            ('2.1', '2.1.0'),
            ('2', '2.12'),
            ('2.9', '2.9.1'),
            ('2.9.1', '2.9.1+beta')
        ]
        for target_version, user_version in versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.compare_user_version_with_target_version(target_version, user_version)
            custom_err_msg = "Got {} in result. Failed for user version:" \
                             " {} and target version: {}".format(result,
                                                                 user_version,
                                                                 target_version
                                                                 )
            self.assertEqual(result, 0, custom_err_msg)

    def test_compare_user_version_with_target_version_greater_than_0(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        versions = [
            ('2.0.0', '2.0.1'),
            ('2.0', '3.0.1'),
            ('2.1.2-beta', '2.1.2-release'),
            ('2.1.3-beta1', '2.1.3-beta2'),
            ('2.9.9-beta', '2.9.9'),
            ('2.9.9+beta', '2.9.9'),
            ('3.7.0-prerelease+build', '3.7.0-prerelease+rc'),
            ('2.2.3-beta-beta1', '2.2.3-beta-beta2'),
            ('2.2.3-beta+beta1', '2.2.3-beta+beta2'),
            ('2.2.3+beta2-beta1', '2.2.3+beta3-beta2')
        ]
        for target_version, user_version in versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.compare_user_version_with_target_version(target_version, user_version)
            custom_err_msg = "Got {} in result. Failed for user version:" \
                             " {} and target version: {}".format(result,
                                                                 user_version,
                                                                 target_version)
            self.assertEqual(result, 1, custom_err_msg)

    def test_compare_user_version_with_target_version_less_than_0(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        versions = [
            ('2.0.1', '2.0.0'),
            ('3.0', '2.0.1'),
            ('2.3', '2.0.1'),
            ('2.3.5', '2.3.1'),
            ('2.9.8', '2.9'),
            ('2.1.2-release', '2.1.2-beta'),
            ('2.9.9+beta', '2.9.9-beta'),
            ('3.7.0+build3.7.0-prerelease+build', '3.7.0-prerelease'),
            ('2.1.3-beta-beta2', '2.1.3-beta'),
            ('2.1.3-beta1+beta3', '2.1.3-beta1+beta2')
        ]
        for target_version, user_version in versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.compare_user_version_with_target_version(target_version, user_version)
            custom_err_msg = "Got {} in result. Failed for user version: {} " \
                             "and target version: {}".format(result,
                                                             user_version,
                                                             target_version)
            self.assertEqual(result, -1, custom_err_msg)

    def test_compare_invalid_user_version_with(self):
        semver_greater_than_2_0_condition_list = [['Android', "2.0", 'custom_attribute', 'semver_gt']]
        versions = ['-', '.', '..', '+', '+test', ' ', '2 .3. 0', '2.', '.2.2', '3.7.2.2', '3.x', ',',
                    '+build-prerelease', '2..2']
        target_version = '2.1.0'

        for user_version in versions:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_greater_than_2_0_condition_list, {'Android': user_version}, self.mock_client_logger)
            result = evaluator.compare_user_version_with_target_version(user_version, target_version)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertIsNone(result, custom_err_msg)

    def test_exists__returns_false__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, {}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

    def test_exists__returns_false__when_user_provided_value_is_null(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, {'input_value': None}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

    def test_exists__returns_true__when_user_provided_value_is_string(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, {'input_value': 'hi'}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_exists__returns_true__when_user_provided_value_is_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, {'input_value': 10}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, {'input_value': 10.0}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_exists__returns_true__when_user_provided_value_is_boolean(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, {'input_value': False}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_exact_string__returns_true__when_user_provided_value_is_equal_to_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_string_condition_list, {'favorite_constellation': 'Lacerta'}, self.mock_client_logger,
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_exact_string__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_string_condition_list, {'favorite_constellation': 'The Big Dipper'}, self.mock_client_logger,
        )

        self.assertStrictFalse(evaluator.evaluate(0))

    def test_exact_string__returns_null__when_user_provided_value_is_different_type_from_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_string_condition_list, {'favorite_constellation': False}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_exact_string__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_string_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_exact_int__returns_true__when_user_provided_value_is_equal_to_condition_value(self, ):

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                exact_int_condition_list, {'lasers_count': long(9000)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_int_condition_list, {'lasers_count': 9000}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_int_condition_list, {'lasers_count': 9000.0}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_exact_float__returns_true__when_user_provided_value_is_equal_to_condition_value(self, ):

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                exact_float_condition_list, {'lasers_count': long(9000)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_float_condition_list, {'lasers_count': 9000}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_float_condition_list, {'lasers_count': 9000.0}, self.mock_client_logger,
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_exact_int__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_int_condition_list, {'lasers_count': 8000}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

    def test_exact_float__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_float_condition_list, {'lasers_count': 8000.0}, self.mock_client_logger,
        )

        self.assertStrictFalse(evaluator.evaluate(0))

    def test_exact_int__returns_null__when_user_provided_value_is_different_type_from_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_int_condition_list, {'lasers_count': 'hi'}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_int_condition_list, {'lasers_count': True}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_exact_float__returns_null__when_user_provided_value_is_different_type_from_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_float_condition_list, {'lasers_count': 'hi'}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_float_condition_list, {'lasers_count': True}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_exact_int__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_int_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_exact_float__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_float_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_exact__given_number_values__calls_is_finite_number(self):
        """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_int_condition_list, {'lasers_count': 9000}, self.mock_client_logger
        )

        # assert that isFiniteNumber only needs to reject condition value to stop evaluation.
        with mock.patch('optimizely.helpers.validator.is_finite_number', side_effect=[False, True]) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        mock_is_finite.assert_called_once_with(9000)

        # assert that isFiniteNumber evaluates user value only if it has accepted condition value.
        with mock.patch('optimizely.helpers.validator.is_finite_number', side_effect=[True, False]) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        mock_is_finite.assert_has_calls([mock.call(9000), mock.call(9000)])

        # assert CustomAttributeConditionEvaluator.evaluate returns True only when isFiniteNumber returns
        # True both for condition and user values.
        with mock.patch('optimizely.helpers.validator.is_finite_number', side_effect=[True, True]) as mock_is_finite:
            self.assertTrue(evaluator.evaluate(0))

        mock_is_finite.assert_has_calls([mock.call(9000), mock.call(9000)])

    def test_exact_bool__returns_true__when_user_provided_value_is_equal_to_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_bool_condition_list, {'did_register_user': False}, self.mock_client_logger,
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_exact_bool__returns_false__when_user_provided_value_is_not_equal_to_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_bool_condition_list, {'did_register_user': True}, self.mock_client_logger,
        )

        self.assertStrictFalse(evaluator.evaluate(0))

    def test_exact_bool__returns_null__when_user_provided_value_is_different_type_from_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_bool_condition_list, {'did_register_user': 0}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_exact_bool__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_bool_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_substring__returns_true__when_condition_value_is_substring_of_user_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, {'headline_text': 'Limited time, buy now!'}, self.mock_client_logger,
        )

        self.assertStrictTrue(evaluator.evaluate(0))

    def test_substring__returns_false__when_condition_value_is_not_a_substring_of_user_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, {'headline_text': 'Breaking news!'}, self.mock_client_logger,
        )

        self.assertStrictFalse(evaluator.evaluate(0))

    def test_substring__returns_null__when_user_provided_value_not_a_string(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, {'headline_text': 10}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_substring__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_int__returns_true__when_user_value_greater_than_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                gt_int_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_greater_than_float__returns_true__when_user_value_greater_than_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_float_condition_list, {'meters_travelled': 48.3}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_float_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                gt_float_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_greater_than_int__returns_false__when_user_value_not_greater_than_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {'meters_travelled': 47.9}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {'meters_travelled': 47}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                gt_int_condition_list, {'meters_travelled': long(47)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_greater_than_float__returns_false__when_user_value_not_greater_than_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_float_condition_list, {'meters_travelled': 48.2}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_float_condition_list, {'meters_travelled': 48}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                gt_float_condition_list, {'meters_travelled': long(48)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_greater_than_int__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {'meters_travelled': 'a long way'}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {'meters_travelled': False}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_float__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_float_condition_list, {'meters_travelled': 'a long way'}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_float_condition_list, {'meters_travelled': False}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_int__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_float__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_float_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_or_equal_int__returns_true__when_user_value_greater_than_or_equal_condition_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': 48}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                gt_int_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_greater_than_or_equal_float__returns_true__when_user_value_greater_than_or_equal_condition_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {'meters_travelled': 48.3}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {'meters_travelled': 48.2}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                ge_float_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_greater_than_or_equal_int__returns_false__when_user_value_not_greater_than_or_equal_condition_value(
            self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': 47.9}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': 47}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                ge_int_condition_list, {'meters_travelled': long(47)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_greater_than_or_equal_float__returns_false__when_user_value_not_greater_than_or_equal_condition_value(
            self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {'meters_travelled': 48}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                ge_float_condition_list, {'meters_travelled': long(48)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_greater_than_or_equal_int__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': 'a long way'}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': False}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_or_equal_float__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {'meters_travelled': 'a long way'}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {'meters_travelled': False}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_or_equal_int__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than_or_equal_float__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_float_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_int__returns_true__when_user_value_less_than_condition_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_int_condition_list, {'meters_travelled': 47.9}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_int_condition_list, {'meters_travelled': 47}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                lt_int_condition_list, {'meters_travelled': long(47)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_less_than_float__returns_true__when_user_value_less_than_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_float_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_float_condition_list, {'meters_travelled': 48}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                lt_float_condition_list, {'meters_travelled': long(48)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_less_than_int__returns_false__when_user_value_not_less_than_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_int_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_int_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                lt_int_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_less_than_float__returns_false__when_user_value_not_less_than_condition_value(self, ):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_float_condition_list, {'meters_travelled': 48.2}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_float_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                lt_float_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_less_than_int__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_int_condition_list, {'meters_travelled': False}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_float__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_float_condition_list, {'meters_travelled': False}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_int__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_int_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_float__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_float_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_or_equal_int__returns_true__when_user_value_less_than_or_equal_condition_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {'meters_travelled': 47.9}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {'meters_travelled': 47}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {'meters_travelled': 48}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                le_int_condition_list, {'meters_travelled': long(47)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                le_int_condition_list, {'meters_travelled': long(48)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_less_than_or_equal_float__returns_true__when_user_value_less_than_or_equal_condition_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_float_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_float_condition_list, {'meters_travelled': 48.2}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_float_condition_list, {'meters_travelled': 48}, self.mock_client_logger
        )

        self.assertStrictTrue(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                le_float_condition_list, {'meters_travelled': long(48)}, self.mock_client_logger,
            )

            self.assertStrictTrue(evaluator.evaluate(0))

    def test_less_than_or_equal_int__returns_false__when_user_value_not_less_than_or_equal_condition_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                le_int_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_less_than_or_equal_float__returns_false__when_user_value_not_less_than_or_equal_condition_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_float_condition_list, {'meters_travelled': 48.3}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_float_condition_list, {'meters_travelled': 49}, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        if PY2:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                le_float_condition_list, {'meters_travelled': long(49)}, self.mock_client_logger,
            )

            self.assertStrictFalse(evaluator.evaluate(0))

    def test_less_than_or_equal_int__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {'meters_travelled': False}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_or_equal_float__returns_null__when_user_value_is_not_a_number(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_float_condition_list, {'meters_travelled': False}, self.mock_client_logger,
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_or_equal_int__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_less_than_or_equal_float__returns_null__when_no_user_provided_value(self):

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_float_condition_list, {}, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

    def test_greater_than__calls_is_finite_number(self):
        """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_int_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        def is_finite_number__rejecting_condition_value(value):
            if value == 48:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_condition_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber only needs to reject condition value to stop evaluation.
        mock_is_finite.assert_called_once_with(48)

        def is_finite_number__rejecting_user_attribute_value(value):
            if value == 48.1:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_user_attribute_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber evaluates user value only if it has accepted condition value.
        mock_is_finite.assert_has_calls([mock.call(48), mock.call(48.1)])

        def is_finite_number__accepting_both_values(value):
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number', side_effect=is_finite_number__accepting_both_values,
        ):
            self.assertTrue(evaluator.evaluate(0))

    def test_less_than__calls_is_finite_number(self):
        """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_int_condition_list, {'meters_travelled': 47}, self.mock_client_logger
        )

        def is_finite_number__rejecting_condition_value(value):
            if value == 48:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_condition_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber only needs to reject condition value to stop evaluation.
        mock_is_finite.assert_called_once_with(48)

        def is_finite_number__rejecting_user_attribute_value(value):
            if value == 47:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_user_attribute_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber evaluates user value only if it has accepted condition value.
        mock_is_finite.assert_has_calls([mock.call(48), mock.call(47)])

        def is_finite_number__accepting_both_values(value):
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number', side_effect=is_finite_number__accepting_both_values,
        ):
            self.assertTrue(evaluator.evaluate(0))

    def test_greater_than_or_equal__calls_is_finite_number(self):
        """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            ge_int_condition_list, {'meters_travelled': 48.1}, self.mock_client_logger
        )

        def is_finite_number__rejecting_condition_value(value):
            if value == 48:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_condition_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber only needs to reject condition value to stop evaluation.
        mock_is_finite.assert_called_once_with(48)

        def is_finite_number__rejecting_user_attribute_value(value):
            if value == 48.1:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_user_attribute_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber evaluates user value only if it has accepted condition value.
        mock_is_finite.assert_has_calls([mock.call(48), mock.call(48.1)])

        def is_finite_number__accepting_both_values(value):
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number', side_effect=is_finite_number__accepting_both_values,
        ):
            self.assertTrue(evaluator.evaluate(0))

    def test_less_than_or_equal__calls_is_finite_number(self):
        """ Test that CustomAttributeConditionEvaluator.evaluate returns True
        if is_finite_number returns True. Returns None if is_finite_number returns False. """

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            le_int_condition_list, {'meters_travelled': 47}, self.mock_client_logger
        )

        def is_finite_number__rejecting_condition_value(value):
            if value == 48:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_condition_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber only needs to reject condition value to stop evaluation.
        mock_is_finite.assert_called_once_with(48)

        def is_finite_number__rejecting_user_attribute_value(value):
            if value == 47:
                return False
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number',
                side_effect=is_finite_number__rejecting_user_attribute_value,
        ) as mock_is_finite:
            self.assertIsNone(evaluator.evaluate(0))

        # assert that isFiniteNumber evaluates user value only if it has accepted condition value.
        mock_is_finite.assert_has_calls([mock.call(48), mock.call(47)])

        def is_finite_number__accepting_both_values(value):
            return True

        with mock.patch(
                'optimizely.helpers.validator.is_finite_number', side_effect=is_finite_number__accepting_both_values,
        ):
            self.assertTrue(evaluator.evaluate(0))

    def test_invalid_semver__returns_None__when_semver_is_invalid(self):
        semver_less_than_or_equal_2_0_1_condition_list = [['Android', "2.0.1", 'custom_attribute', 'semver_le']]
        invalid_test_cases = ["-", ".", "..", "+", "+test", " ", "2 .0. 0",
                              "2.", ".0.0", "1.2.2.2", "2.x", ",",
                              "+build-prerelease", "2..0"]

        for user_version in invalid_test_cases:
            evaluator = condition_helper.CustomAttributeConditionEvaluator(
                semver_less_than_or_equal_2_0_1_condition_list, {'Android': user_version}, self.mock_client_logger)

            result = evaluator.evaluate(0)
            custom_err_msg = "Got {} in result. Failed for user version: {}".format(result, user_version)
            self.assertIsNone(result, custom_err_msg)


class ConditionDecoderTests(base.BaseTest):
    def test_loads(self):
        """ Test that loads correctly sets condition structure and list. """

        condition_structure, condition_list = condition_helper.loads(self.config_dict['audiences'][0]['conditions'])

        self.assertEqual(['and', ['or', ['or', 0]]], condition_structure)
        self.assertEqual(
            [['test_attribute', 'test_value_1', 'custom_attribute', None]], condition_list,
        )

    def test_audience_condition_deserializer_defaults(self):
        """ Test that audience_condition_deserializer defaults to None."""

        browserConditionSafari = {}

        items = condition_helper._audience_condition_deserializer(browserConditionSafari)
        self.assertIsNone(items[0])
        self.assertIsNone(items[1])
        self.assertIsNone(items[2])
        self.assertIsNone(items[3])


class CustomAttributeConditionEvaluatorLogging(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self)
        self.mock_client_logger = mock.MagicMock()

    def test_evaluate__match_type__invalid(self):
        log_level = 'warning'
        condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', 'regex']]
        user_attributes = {}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": 'Lacerta',
            "type": 'custom_attribute',
            "match": 'regex',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" uses an unknown match '
                'type. You may need to upgrade to a newer release of the Optimizely SDK.'
            ).format(json.dumps(expected_condition_log))
        )

    def test_evaluate__condition_type__invalid(self):
        log_level = 'warning'
        condition_list = [['favorite_constellation', 'Lacerta', 'sdk_version', 'exact']]
        user_attributes = {}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": 'Lacerta',
            "type": 'sdk_version',
            "match": 'exact',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" uses an unknown condition type. '
                'You may need to upgrade to a newer release of the Optimizely SDK.'
            ).format(json.dumps(expected_condition_log))
        )

    def test_exact__user_value__missing(self):
        log_level = 'debug'
        exact_condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', 'exact']]
        user_attributes = {}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": 'Lacerta',
            "type": 'custom_attribute',
            "match": 'exact',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition {} evaluated to UNKNOWN because '
                'no value was passed for user attribute "favorite_constellation".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_greater_than__user_value__missing(self):
        log_level = 'debug'
        gt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'gt']]
        user_attributes = {}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'gt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition {} evaluated to UNKNOWN because no value was passed for user '
                'attribute "meters_travelled".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_less_than__user_value__missing(self):
        log_level = 'debug'
        lt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'lt']]
        user_attributes = {}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'lt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition {} evaluated to UNKNOWN because no value was passed for user attribute '
                '"meters_travelled".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_substring__user_value__missing(self):
        log_level = 'debug'
        substring_condition_list = [['headline_text', 'buy now', 'custom_attribute', 'substring']]
        user_attributes = {}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'headline_text',
            "value": 'buy now',
            "type": 'custom_attribute',
            "match": 'substring',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition {} evaluated to UNKNOWN because no value was passed for '
                'user attribute "headline_text".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_exists__user_value__missing(self):
        exists_condition_list = [['input_value', None, 'custom_attribute', 'exists']]
        user_attributes = {}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, user_attributes, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        self.mock_client_logger.debug.assert_not_called()
        self.mock_client_logger.info.assert_not_called()
        self.mock_client_logger.warning.assert_not_called()

    def test_exact__user_value__None(self):
        log_level = 'debug'
        exact_condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', 'exact']]
        user_attributes = {'favorite_constellation': None}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": 'Lacerta',
            "type": 'custom_attribute',
            "match": 'exact',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because a null value was passed for user attribute '
                '"favorite_constellation".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_greater_than__user_value__None(self):
        log_level = 'debug'
        gt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'gt']]
        user_attributes = {'meters_travelled': None}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'gt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because a null value was passed for '
                'user attribute "meters_travelled".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_less_than__user_value__None(self):
        log_level = 'debug'
        lt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'lt']]
        user_attributes = {'meters_travelled': None}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'lt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because a null value was passed '
                'for user attribute "meters_travelled".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_substring__user_value__None(self):
        log_level = 'debug'
        substring_condition_list = [['headline_text', '12', 'custom_attribute', 'substring']]
        user_attributes = {'headline_text': None}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'headline_text',
            "value": '12',
            "type": 'custom_attribute',
            "match": 'substring',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because a null value was '
                'passed for user attribute "headline_text".'
            ).format(json.dumps(expected_condition_log))
        )

    def test_exists__user_value__None(self):
        exists_condition_list = [['input_value', None, 'custom_attribute', 'exists']]
        user_attributes = {'input_value': None}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exists_condition_list, user_attributes, self.mock_client_logger
        )

        self.assertStrictFalse(evaluator.evaluate(0))

        self.mock_client_logger.debug.assert_not_called()
        self.mock_client_logger.info.assert_not_called()
        self.mock_client_logger.warning.assert_not_called()

    def test_exact__user_value__unexpected_type(self):
        log_level = 'warning'
        exact_condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', 'exact']]
        user_attributes = {'favorite_constellation': {}}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": 'Lacerta',
            "type": 'custom_attribute',
            "match": 'exact',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because a value of type "{}" was passed for '
                'user attribute "favorite_constellation".'
            ).format(json.dumps(expected_condition_log), type({}))
        )

    def test_greater_than__user_value__unexpected_type(self):
        log_level = 'warning'
        gt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'gt']]
        user_attributes = {'meters_travelled': '48'}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'gt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}"'
                ' evaluated to UNKNOWN because a value of type "{}" was passed for user attribute '
                '"meters_travelled".'
            ).format(json.dumps(expected_condition_log), type('48'))
        )

    def test_less_than__user_value__unexpected_type(self):
        log_level = 'warning'
        lt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'lt']]
        user_attributes = {'meters_travelled': True}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'lt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}"'
                ' evaluated to UNKNOWN because a value of type "{}" was passed for user attribute '
                '"meters_travelled".'
            ).format(json.dumps(expected_condition_log), type(True))
        )

    def test_substring__user_value__unexpected_type(self):
        log_level = 'warning'
        substring_condition_list = [['headline_text', '12', 'custom_attribute', 'substring']]
        user_attributes = {'headline_text': 1234}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'headline_text',
            "value": '12',
            "type": 'custom_attribute',
            "match": 'substring',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because a value of type "{}" was passed for '
                'user attribute "headline_text".'
            ).format(json.dumps(expected_condition_log), type(1234))
        )

    def test_exact__user_value__infinite(self):
        log_level = 'warning'
        exact_condition_list = [['meters_travelled', 48, 'custom_attribute', 'exact']]
        user_attributes = {'meters_travelled': float("inf")}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_condition_list, user_attributes, self.mock_client_logger
        )

        self.assertIsNone(evaluator.evaluate(0))

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'exact',
        }

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because the number value for '
                'user attribute "meters_travelled" is not in the range [-2^53, +2^53].'
            ).format(json.dumps(expected_condition_log))
        )

    def test_greater_than__user_value__infinite(self):
        log_level = 'warning'
        gt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'gt']]
        user_attributes = {'meters_travelled': float("nan")}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'gt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" '
                'evaluated to UNKNOWN because the number value for user attribute "meters_travelled" is not'
                ' in the range [-2^53, +2^53].'
            ).format(json.dumps(expected_condition_log))
        )

    def test_less_than__user_value__infinite(self):
        log_level = 'warning'
        lt_condition_list = [['meters_travelled', 48, 'custom_attribute', 'lt']]
        user_attributes = {'meters_travelled': float('-inf')}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            lt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": 48,
            "type": 'custom_attribute',
            "match": 'lt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" '
                'evaluated to UNKNOWN because the number value for user attribute "meters_travelled" is not in '
                'the range [-2^53, +2^53].'
            ).format(json.dumps(expected_condition_log))
        )

    def test_exact__user_value_type_mismatch(self):
        log_level = 'warning'
        exact_condition_list = [['favorite_constellation', 'Lacerta', 'custom_attribute', 'exact']]
        user_attributes = {'favorite_constellation': 5}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": 'Lacerta',
            "type": 'custom_attribute',
            "match": 'exact',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" evaluated to UNKNOWN because a value of type "{}" was passed for '
                'user attribute "favorite_constellation".'
            ).format(json.dumps(expected_condition_log), type(5))
        )

    def test_exact__condition_value_invalid(self):
        log_level = 'warning'
        exact_condition_list = [['favorite_constellation', {}, 'custom_attribute', 'exact']]
        user_attributes = {'favorite_constellation': 'Lacerta'}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": {},
            "type": 'custom_attribute',
            "match": 'exact',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" has an unsupported condition value. You may need to upgrade to a '
                'newer release of the Optimizely SDK.'
            ).format(json.dumps(expected_condition_log))
        )

    def test_exact__condition_value_infinite(self):
        log_level = 'warning'
        exact_condition_list = [['favorite_constellation', float('inf'), 'custom_attribute', 'exact']]
        user_attributes = {'favorite_constellation': 'Lacerta'}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            exact_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'favorite_constellation',
            "value": float('inf'),
            "type": 'custom_attribute',
            "match": 'exact',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" has an unsupported condition value. You may need to upgrade to a '
                'newer release of the Optimizely SDK.'
            ).format(json.dumps(expected_condition_log))
        )

    def test_greater_than__condition_value_invalid(self):
        log_level = 'warning'
        gt_condition_list = [['meters_travelled', True, 'custom_attribute', 'gt']]
        user_attributes = {'meters_travelled': 48}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": True,
            "type": 'custom_attribute',
            "match": 'gt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" has an unsupported condition value. You may need to upgrade to a '
                'newer release of the Optimizely SDK.'
            ).format(json.dumps(expected_condition_log))
        )

    def test_less_than__condition_value_invalid(self):
        log_level = 'warning'
        gt_condition_list = [['meters_travelled', float('nan'), 'custom_attribute', 'lt']]
        user_attributes = {'meters_travelled': 48}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            gt_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'meters_travelled',
            "value": float('nan'),
            "type": 'custom_attribute',
            "match": 'lt',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" has an unsupported condition value. You may need to upgrade to a '
                'newer release of the Optimizely SDK.'
            ).format(json.dumps(expected_condition_log))
        )

    def test_substring__condition_value_invalid(self):
        log_level = 'warning'
        substring_condition_list = [['headline_text', False, 'custom_attribute', 'substring']]
        user_attributes = {'headline_text': 'breaking news'}

        evaluator = condition_helper.CustomAttributeConditionEvaluator(
            substring_condition_list, user_attributes, self.mock_client_logger
        )

        expected_condition_log = {
            "name": 'headline_text',
            "value": False,
            "type": 'custom_attribute',
            "match": 'substring',
        }

        self.assertIsNone(evaluator.evaluate(0))

        mock_log = getattr(self.mock_client_logger, log_level)
        mock_log.assert_called_once_with(
            (
                'Audience condition "{}" has an unsupported condition value. You may need to upgrade to a '
                'newer release of the Optimizely SDK.'
            ).format(json.dumps(expected_condition_log))
        )
