# Copyright 2021, Optimizely
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

from optimizely.decision.optimizely_decision import OptimizelyDecision
from optimizely.helpers import enums
from . import base
from optimizely import optimizely, decision_service
from optimizely.optimizely_user_context import OptimizelyUserContext


class UserContextTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self, 'config_dict_with_multiple_experiments')

    def compare_opt_decisions(self, expected, actual):
        self.assertEqual(expected.variation_key, actual.variation_key)
        self.assertEqual(expected.enabled, actual.enabled)
        self.assertEqual(expected.rule_key, actual.rule_key)
        self.assertEqual(expected.flag_key, actual.flag_key)
        self.assertEqual(expected.variables, actual.variables)
        self.assertEqual(expected.user_context.user_id, actual.user_context.user_id)
        self.assertEqual(expected.user_context.get_user_attributes(), actual.user_context.get_user_attributes())

    def test_user_context(self):
        """
        tests user context creating and setting attributes
        """
        uc = OptimizelyUserContext(self.optimizely, "test_user")
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

        # user id should be as provided in constructor
        self.assertEqual("test_user", uc.user_id)

        # set attribute
        uc.set_attribute("browser", "chrome")
        self.assertEqual("chrome", uc.get_user_attributes()["browser"], )

        # set another attribute
        uc.set_attribute("color", "red")
        self.assertEqual("chrome", uc.get_user_attributes()["browser"])
        self.assertEqual("red", uc.get_user_attributes()["color"])

        # override existing attribute
        uc.set_attribute("browser", "firefox")
        self.assertEqual("firefox", uc.get_user_attributes()["browser"])
        self.assertEqual("red", uc.get_user_attributes()["color"])

    def test_attributes_are_cloned_when_passed_to_user_context(self):
        user_id = 'test_user'
        attributes = {"browser": "chrome"}
        uc = OptimizelyUserContext(self.optimizely, user_id, attributes)
        self.assertEqual(attributes, uc.get_user_attributes())
        attributes['new_key'] = 'test_value'
        self.assertNotEqual(attributes, uc.get_user_attributes())

    def test_attributes_default_to_dict_when_passes_as_non_dict(self):
        uc = OptimizelyUserContext(self.optimizely, "test_user", True)
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

        uc = OptimizelyUserContext(self.optimizely, "test_user", 10)
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

        uc = OptimizelyUserContext(self.optimizely, "test_user", 'helloworld')
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

        uc = OptimizelyUserContext(self.optimizely, "test_user", [])
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

    def test_user_context_is_cloned_when_passed_to_optimizely_APIs(self):
        """ Test that the user context in decide response is not the same object on which
    the decide was called """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context('test_user')

        # decide
        decision = user_context.decide('test_feature_in_rollout')
        self.assertNotEqual(user_context, decision.user_context)

        # decide_all
        decisions = user_context.decide_all()
        self.assertNotEqual(user_context, decisions['test_feature_in_rollout'].user_context)

        # decide_for_keys
        decisions = user_context.decide_for_keys(['test_feature_in_rollout'])
        self.assertNotEqual(user_context, decisions['test_feature_in_rollout'].user_context)

    def test_decide__SDK_not_ready(self):
        opt_obj = optimizely.Optimizely("")
        user_context = opt_obj.create_user_context('test_user')

        expected = OptimizelyDecision(
            variation_key=None,
            rule_key=None,
            enabled=False,
            variables={},
            flag_key='test_feature',
            user_context=user_context
        )

        actual = user_context.decide('test_feature')

        self.compare_opt_decisions(expected, actual)

        self.assertIn(
            'Optimizely SDK not configured properly yet.',
            actual.reasons
        )

    def test_decide__invalid_flag_key(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context('test_user', {'some-key': 'some-value'})

        expected = OptimizelyDecision(
            variation_key=None,
            rule_key=None,
            enabled=False,
            variables={},
            flag_key=123,
            user_context=user_context
        )

        actual = user_context.decide(123)

        self.compare_opt_decisions(expected, actual)

        self.assertIn(
            'No flag was found for key "123".',
            actual.reasons
        )

    def test_decide__unknown_flag_key(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context('test_user')

        expected = OptimizelyDecision(
            variation_key=None,
            rule_key=None,
            enabled=False,
            variables={},
            flag_key='unknown_flag_key',
            user_context=user_context
        )

        actual = user_context.decide('unknown_flag_key')

        self.compare_opt_decisions(expected, actual)

        self.assertIn(
            'No flag was found for key "unknown_flag_key".',
            actual.reasons
        )

    def test_decide__feature_test(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=(decision_service.Decision(mock_experiment, mock_variation,
                                                        enums.DecisionSources.FEATURE_TEST), []),
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:

            user_context = opt_obj.create_user_context('test_user', {'browser': 'chrome'})
            actual = user_context.decide('test_feature_in_experiment')

        expected_variables = {
            'is_working': True,
            'environment': 'staging',
            'cost': 10.02,
            'count': 4243,
            'variable_without_usage': 45,
            'object': {"test": 123},
            'true_object': {"true_test": 1.4}
        }

        expected = OptimizelyDecision(
            variation_key='variation',
            rule_key='test_experiment',
            enabled=True,
            variables=expected_variables,
            flag_key='test_feature_in_experiment',
            user_context=user_context
        )

        self.compare_opt_decisions(expected, actual)

        # assert notification
        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            {'browser': 'chrome'},
            {
                'flag_key': expected.flag_key,
                'enabled': expected.enabled,
                'variation_key': expected.variation_key,
                'rule_key': expected.rule_key,
                'reasons': expected.reasons,
                'decision_event_dispatched': True,
                'variables': expected.variables,
            },
        )

        # assert event count
        self.assertEqual(1, mock_send_event.call_count)

        # assert event payload
        mock_send_event.assert_called_with(
            project_config,
            mock_experiment,
            mock_variation,
            expected.flag_key,
            expected.rule_key,
            'feature-test',
            expected.enabled,
            'test_user',
            {'browser': 'chrome'}
        )

    def test_decide__feature_test__send_flag_decision_false(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        project_config.send_flag_decisions = False

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=(decision_service.Decision(mock_experiment, mock_variation,
                                                        enums.DecisionSources.FEATURE_TEST), []),
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:

            user_context = opt_obj.create_user_context('test_user')
            actual = user_context.decide('test_feature_in_experiment')

        expected_variables = {
            'is_working': True,
            'environment': 'staging',
            'cost': 10.02,
            'count': 4243,
            'variable_without_usage': 45,
            'object': {"test": 123},
            'true_object': {"true_test": 1.4}
        }

        expected = OptimizelyDecision(
            variation_key='variation',
            rule_key='test_experiment',
            enabled=True,
            variables=expected_variables,
            flag_key='test_feature_in_experiment',
            user_context=user_context
        )

        self.compare_opt_decisions(expected, actual)

        # assert notification count
        self.assertEqual(1, mock_broadcast_decision.call_count)

        # assert event count
        self.assertEqual(1, mock_send_event.call_count)

    def test_decide_feature_rollout(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        with mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:

            user_attributes = {'test_attribute': 'test_value_1'}
            user_context = opt_obj.create_user_context('test_user', user_attributes)
            actual = user_context.decide('test_feature_in_rollout')

        expected_variables = {
            'is_running': True,
            'message': 'Hello audience',
            'price': 39.99,
            'count': 399,
            'object': {"field": 12}
        }

        expected = OptimizelyDecision(
            variation_key='211129',
            rule_key='211127',
            enabled=True,
            variables=expected_variables,
            flag_key='test_feature_in_rollout',
            user_context=user_context
        )

        self.compare_opt_decisions(expected, actual)

        # assert notification count
        self.assertEqual(1, mock_broadcast_decision.call_count)

        # assert notification
        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            user_attributes,
            {
                'flag_key': expected.flag_key,
                'enabled': expected.enabled,
                'variation_key': expected.variation_key,
                'rule_key': expected.rule_key,
                'reasons': expected.reasons,
                'decision_event_dispatched': True,
                'variables': expected.variables,
            },
        )

        # assert event count
        self.assertEqual(1, mock_send_event.call_count)

        # assert event payload
        expected_experiment = project_config.get_experiment_from_key(expected.rule_key)
        expected_var = project_config.get_variation_from_key(expected.rule_key, expected.variation_key)
        mock_send_event.assert_called_with(
            project_config,
            expected_experiment,
            expected_var,
            expected.flag_key,
            expected.rule_key,
            'rollout',
            expected.enabled,
            'test_user',
            user_attributes
        )

    def test_decide_feature_rollout__send_flag_decision_false(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        project_config.send_flag_decisions = False

        with mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:

            user_attributes = {'test_attribute': 'test_value_1'}
            user_context = opt_obj.create_user_context('test_user', user_attributes)
            actual = user_context.decide('test_feature_in_rollout')

        expected_variables = {
            'is_running': True,
            'message': 'Hello audience',
            'price': 39.99,
            'count': 399,
            'object': {"field": 12}
        }

        expected = OptimizelyDecision(
            variation_key='211129',
            rule_key='211127',
            enabled=True,
            variables=expected_variables,
            flag_key='test_feature_in_rollout',
            user_context=user_context
        )

        self.compare_opt_decisions(expected, actual)

        # assert notification count
        self.assertEqual(1, mock_broadcast_decision.call_count)

        # assert notification
        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            user_attributes,
            {
                'flag_key': expected.flag_key,
                'enabled': expected.enabled,
                'variation_key': expected.variation_key,
                'rule_key': expected.rule_key,
                'reasons': expected.reasons,
                'decision_event_dispatched': False,
                'variables': expected.variables,
            },
        )

        # assert event count
        self.assertEqual(0, mock_send_event.call_count)
