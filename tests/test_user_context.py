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
import threading

from optimizely import optimizely, decision_service
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption as DecideOption
from optimizely.decision.optimizely_decision import OptimizelyDecision
from optimizely.helpers import enums
from optimizely.optimizely_user_context import OptimizelyUserContext
from optimizely.user_profile import UserProfileService
from . import base


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
        uc = OptimizelyUserContext(self.optimizely, None, "test_user")
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

    def test_user_and_attributes_as_json(self):
        """
        tests user context as json
        """
        uc = OptimizelyUserContext(self.optimizely, None, "test_user")

        # set an attribute
        uc.set_attribute("browser", "safari")

        # set expected json obj
        expected_json = {
            "user_id": uc.user_id,
            "attributes": uc.get_user_attributes(),
        }

        self.assertEqual(uc.as_json(), expected_json)

    def test_attributes_are_cloned_when_passed_to_user_context(self):
        user_id = 'test_user'
        attributes = {"browser": "chrome"}
        uc = OptimizelyUserContext(self.optimizely, None, user_id, attributes)
        self.assertEqual(attributes, uc.get_user_attributes())
        attributes['new_key'] = 'test_value'
        self.assertNotEqual(attributes, uc.get_user_attributes())

    def test_attributes_default_to_dict_when_passes_as_non_dict(self):
        uc = OptimizelyUserContext(self.optimizely, None, "test_user", True)
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

        uc = OptimizelyUserContext(self.optimizely, None, "test_user", 10)
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

        uc = OptimizelyUserContext(self.optimizely, None, "test_user", 'helloworld')
        # user attribute should be empty dict
        self.assertEqual({}, uc.get_user_attributes())

        uc = OptimizelyUserContext(self.optimizely, None, "test_user", [])
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

    def test_decide_feature_null_variation(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        mock_experiment = None
        mock_variation = None

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=(decision_service.Decision(mock_experiment, mock_variation,
                                                        enums.DecisionSources.ROLLOUT), []),
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:

            user_context = opt_obj.create_user_context('test_user', {'browser': 'chrome'})
            actual = user_context.decide('test_feature_in_experiment')

        expected_variables = {
            'is_working': True,
            'environment': 'devel',
            'cost': 10.99,
            'count': 999,
            'variable_without_usage': 45,
            'object': {"test": 12},
            'true_object': {"true_test": 23.54}
        }

        expected = OptimizelyDecision(
            variation_key=None,
            rule_key=None,
            enabled=False,
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
            '',
            'rollout',
            expected.enabled,
            'test_user',
            {'browser': 'chrome'}
        )

    def test_decide_feature_null_variation__send_flag_decision_false(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        project_config.send_flag_decisions = False

        mock_experiment = None
        mock_variation = None

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=(decision_service.Decision(mock_experiment, mock_variation,
                                                        enums.DecisionSources.ROLLOUT), []),
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:

            user_context = opt_obj.create_user_context('test_user', {'browser': 'chrome'})
            actual = user_context.decide('test_feature_in_experiment')

        expected_variables = {
            'is_working': True,
            'environment': 'devel',
            'cost': 10.99,
            'count': 999,
            'variable_without_usage': 45,
            'object': {"test": 12},
            'true_object': {"true_test": 23.54}
        }

        expected = OptimizelyDecision(
            variation_key=None,
            rule_key=None,
            enabled=False,
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
                'decision_event_dispatched': False,
                'variables': expected.variables,
            },
        )

        # assert event count
        self.assertEqual(0, mock_send_event.call_count)

    def test_decide__option__disable_decision_event(self):
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
            actual = user_context.decide('test_feature_in_experiment', ['DISABLE_DECISION_EVENT'])

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
                'decision_event_dispatched': False,
                'variables': expected.variables,
            },
        )

        # assert event count
        self.assertEqual(0, mock_send_event.call_count)

    def test_decide__default_option__disable_decision_event(self):
        opt_obj = optimizely.Optimizely(
            datafile=json.dumps(self.config_dict_with_features),
            default_decide_options=['DISABLE_DECISION_EVENT']
        )
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
                'decision_event_dispatched': False,
                'variables': expected.variables,
            },
        )

        # assert event count
        self.assertEqual(0, mock_send_event.call_count)

    def test_decide__option__exclude_variables(self):
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
            actual = user_context.decide('test_feature_in_experiment', ['EXCLUDE_VARIABLES'])

        expected_variables = {}

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

    def test_decide__option__include_reasons__feature_test(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user', {'browser': 'chrome'})
        actual = user_context.decide('test_feature_in_experiment', ['INCLUDE_REASONS'])

        expected_reasons = [
            'Evaluating audiences for experiment "test_experiment": [].',
            'Audiences for experiment "test_experiment" collectively evaluated to TRUE.',
            'User "test_user" is in variation "control" of experiment test_experiment.'
        ]

        self.assertEqual(expected_reasons, actual.reasons)

    def test_decide__option__include_reasons__feature_rollout(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_attributes = {'test_attribute': 'test_value_1'}
        user_context = opt_obj.create_user_context('test_user', user_attributes)
        actual = user_context.decide('test_feature_in_rollout', ['INCLUDE_REASONS'])

        expected_reasons = [
            'Evaluating audiences for rule 1: ["11154"].',
            'Audiences for rule 1 collectively evaluated to TRUE.',
            'User "test_user" meets audience conditions for targeting rule 1.',
            'User "test_user" bucketed into a targeting rule 1.'
        ]

        self.assertEqual(expected_reasons, actual.reasons)

    def test_decide__option__enabled_flags_only(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        expected_experiment = project_config.get_experiment_from_key('211127')
        expected_var = project_config.get_variation_from_key('211127', '211229')

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=(decision_service.Decision(expected_experiment, expected_var,
                                                        enums.DecisionSources.ROLLOUT), []),
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:

            user_attributes = {'test_attribute': 'test_value_1'}
            user_context = opt_obj.create_user_context('test_user', user_attributes)
            actual = user_context.decide('test_feature_in_rollout', 'ENABLED_FLAGS_ONLY')

        expected_variables = {
            'is_running': False,
            'message': 'Hello',
            'price': 99.99,
            'count': 999,
            'object': {"field": 1}
        }

        expected = OptimizelyDecision(
            variation_key='211229',
            rule_key='211127',
            enabled=False,
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

    def test_decide__default_options__with__options(self):
        opt_obj = optimizely.Optimizely(
            datafile=json.dumps(self.config_dict_with_features),
            default_decide_options=['DISABLE_DECISION_EVENT']
        )
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
            actual = user_context.decide('test_feature_in_experiment', ['EXCLUDE_VARIABLES'])

        expected_variables = {}

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
                'decision_event_dispatched': False,
                'variables': expected.variables,
            },
        )

        # assert event count
        self.assertEqual(0, mock_send_event.call_count)

    def test_decide_for_keys(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user')

        mocked_decision_1 = OptimizelyDecision(flag_key='test_feature_in_experiment', enabled=True)
        mocked_decision_2 = OptimizelyDecision(flag_key='test_feature_in_rollout', enabled=False)

        def side_effect(*args, **kwargs):
            flag = args[1]
            if flag == 'test_feature_in_experiment':
                return mocked_decision_1
            else:
                return mocked_decision_2

        with mock.patch(
            'optimizely.optimizely.Optimizely._decide', side_effect=side_effect
        ) as mock_decide, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext._clone',
            return_value=user_context
        ):

            flags = ['test_feature_in_rollout', 'test_feature_in_experiment']
            options = []
            decisions = user_context.decide_for_keys(flags, options)

        self.assertEqual(2, len(decisions))

        mock_decide.assert_any_call(
            user_context,
            'test_feature_in_experiment',
            options
        )

        mock_decide.assert_any_call(
            user_context,
            'test_feature_in_rollout',
            options
        )

        self.assertEqual(mocked_decision_1, decisions['test_feature_in_experiment'])
        self.assertEqual(mocked_decision_2, decisions['test_feature_in_rollout'])

    def test_decide_for_keys__option__enabled_flags_only(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user')

        mocked_decision_1 = OptimizelyDecision(flag_key='test_feature_in_experiment', enabled=True)
        mocked_decision_2 = OptimizelyDecision(flag_key='test_feature_in_rollout', enabled=False)

        def side_effect(*args, **kwargs):
            flag = args[1]
            if flag == 'test_feature_in_experiment':
                return mocked_decision_1
            else:
                return mocked_decision_2

        with mock.patch(
            'optimizely.optimizely.Optimizely._decide', side_effect=side_effect
        ) as mock_decide, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext._clone',
            return_value=user_context
        ):

            flags = ['test_feature_in_rollout', 'test_feature_in_experiment']
            options = ['ENABLED_FLAGS_ONLY']
            decisions = user_context.decide_for_keys(flags, options)

        self.assertEqual(1, len(decisions))

        mock_decide.assert_any_call(
            user_context,
            'test_feature_in_experiment',
            options
        )

        mock_decide.assert_any_call(
            user_context,
            'test_feature_in_rollout',
            options
        )

        self.assertEqual(mocked_decision_1, decisions['test_feature_in_experiment'])

    def test_decide_for_keys__default_options__with__options(self):
        opt_obj = optimizely.Optimizely(
            datafile=json.dumps(self.config_dict_with_features),
            default_decide_options=['ENABLED_FLAGS_ONLY']
        )

        user_context = opt_obj.create_user_context('test_user')

        with mock.patch(
            'optimizely.optimizely.Optimizely._decide'
        ) as mock_decide, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext._clone',
            return_value=user_context
        ):

            flags = ['test_feature_in_experiment']
            options = ['EXCLUDE_VARIABLES']
            user_context.decide_for_keys(flags, options)

        mock_decide.assert_called_with(
            user_context,
            'test_feature_in_experiment',
            ['EXCLUDE_VARIABLES']
        )

    def test_decide_for_all(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user')

        with mock.patch(
            'optimizely.optimizely.Optimizely._decide_for_keys', return_value='response from decide_for_keys'
        ) as mock_decide, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext._clone',
            return_value=user_context
        ):

            options = ['DISABLE_DECISION_EVENT']
            decisions = user_context.decide_all(options)

        mock_decide.assert_called_with(
            user_context,
            [
                'test_feature_in_experiment',
                'test_feature_in_rollout',
                'test_feature_in_group',
                'test_feature_in_experiment_and_rollout',
                'test_feature_in_exclusion_group',
                'test_feature_in_multiple_experiments'
            ],
            options
        )

        self.assertEqual('response from decide_for_keys', decisions)

    def test_decide_options_bypass_UPS(self):
        user_id = 'test_user'

        lookup_profile = {
            'user_id': user_id,
            'experiment_bucket_map': {
                '111127': {
                    'variation_id': '111128'
                }
            }
        }

        save_profile = []

        class Ups(UserProfileService):

            def lookup(self, user_id):
                return lookup_profile

            def save(self, user_profile):
                print(user_profile)
                save_profile.append(user_profile)

        ups = Ups()
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features), user_profile_service=ups)
        project_config = opt_obj.config_manager.get_config()

        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        with mock.patch(
                'optimizely.bucketer.Bucketer.bucket',
                return_value=(mock_variation, []),
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ), mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ):
            user_context = opt_obj.create_user_context(user_id)
            options = [
                'IGNORE_USER_PROFILE_SERVICE'
            ]

            actual = user_context.decide('test_feature_in_experiment', options)

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

        self.assertEqual([], save_profile)

    def test_decide_reasons__hit_everyone_else_rule__fails_bucketing(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_attributes = {}
        user_context = opt_obj.create_user_context('test_user', user_attributes)
        actual = user_context.decide('test_feature_in_rollout', ['INCLUDE_REASONS'])

        expected_reasons = [
            'Evaluating audiences for rule 1: ["11154"].', 'Audiences for rule 1 collectively evaluated to FALSE.',
            'User "test_user" does not meet audience conditions for targeting rule 1.',
            'Evaluating audiences for rule 2: ["11159"].', 'Audiences for rule 2 collectively evaluated to FALSE.',
            'User "test_user" does not meet audience conditions for targeting rule 2.',
            'Evaluating audiences for rule Everyone Else: [].',
            'Audiences for rule Everyone Else collectively evaluated to TRUE.',
            'User "test_user" meets audience conditions for targeting rule Everyone Else.',
            'Bucketed into an empty traffic range. Returning nil.'
        ]

        self.assertEqual(expected_reasons, actual.reasons)

    def test_decide_reasons__hit_everyone_else_rule(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_attributes = {}
        user_context = opt_obj.create_user_context('abcde', user_attributes)
        actual = user_context.decide('test_feature_in_rollout', ['INCLUDE_REASONS'])

        expected_reasons = [
            'Evaluating audiences for rule 1: ["11154"].',
            'Audiences for rule 1 collectively evaluated to FALSE.',
            'User "abcde" does not meet audience conditions for targeting rule 1.',
            'Evaluating audiences for rule 2: ["11159"].',
            'Audiences for rule 2 collectively evaluated to FALSE.',
            'User "abcde" does not meet audience conditions for targeting rule 2.',
            'Evaluating audiences for rule Everyone Else: [].',
            'Audiences for rule Everyone Else collectively evaluated to TRUE.',
            'User "abcde" meets audience conditions for targeting rule Everyone Else.',
            'User "abcde" bucketed into a targeting rule Everyone Else.'
        ]

        self.assertEqual(expected_reasons, actual.reasons)

    def test_decide_reasons__hit_rule2__fails_bucketing(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_attributes = {'test_attribute': 'test_value_2'}
        user_context = opt_obj.create_user_context('test_user', user_attributes)
        actual = user_context.decide('test_feature_in_rollout', ['INCLUDE_REASONS'])

        expected_reasons = [
            'Evaluating audiences for rule 1: ["11154"].', 'Audiences for rule 1 collectively evaluated to FALSE.',
            'User "test_user" does not meet audience conditions for targeting rule 1.',
            'Evaluating audiences for rule 2: ["11159"].', 'Audiences for rule 2 collectively evaluated to TRUE.',
            'User "test_user" meets audience conditions for targeting rule 2.',
            'Bucketed into an empty traffic range. Returning nil.',
            'User "test_user" not bucketed into a targeting rule 2. Checking "Everyone Else" rule now.',
            'Evaluating audiences for rule Everyone Else: [].',
            'Audiences for rule Everyone Else collectively evaluated to TRUE.',
            'User "test_user" meets audience conditions for targeting rule Everyone Else.',
            'Bucketed into an empty traffic range. Returning nil.'
        ]

        self.assertEqual(expected_reasons, actual.reasons)

    def test_decide_reasons__hit_user_profile_service(self):
        user_id = 'test_user'

        lookup_profile = {
            'user_id': user_id,
            'experiment_bucket_map': {
                '111127': {
                    'variation_id': '111128'
                }
            }
        }

        save_profile = []

        class Ups(UserProfileService):

            def lookup(self, user_id):
                return lookup_profile

            def save(self, user_profile):
                print(user_profile)
                save_profile.append(user_profile)

        ups = Ups()
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features), user_profile_service=ups)

        user_context = opt_obj.create_user_context(user_id)
        options = ['INCLUDE_REASONS']

        actual = user_context.decide('test_feature_in_experiment', options)

        expected_reasons = [
            'Returning previously activated variation ID "control" of experiment '
            '"test_experiment" for user "test_user" from user profile.'
        ]

        self.assertEqual(expected_reasons, actual.reasons)

    def test_decide_reasons__forced_variation(self):
        user_id = 'test_user'

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context(user_id)
        options = ['INCLUDE_REASONS']

        opt_obj.set_forced_variation('test_experiment', user_id, 'control')

        actual = user_context.decide('test_feature_in_experiment', options)

        expected_reasons = [
            'Variation "control" is mapped to experiment "test_experiment" and '
            'user "test_user" in the forced variation map'
        ]

        self.assertEqual(expected_reasons, actual.reasons)

    def test_decide_reasons__whitelisted_variation(self):
        user_id = 'user_1'

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context(user_id)
        options = ['INCLUDE_REASONS']

        actual = user_context.decide('test_feature_in_experiment', options)
        expected_reasons = ['User "user_1" is forced in variation "control".']

        self.assertEqual(expected_reasons, actual.reasons)

    def test_init__invalid_default_decide_options(self):
        """
            Test to confirm that default decide options passed not as a list will trigger setting
            self.deafulat_decide_options as an empty list.
        """
        invalid_decide_options = {"testKey": "testOption"}

        mock_client_logger = mock.MagicMock()
        with mock.patch('optimizely.logger.reset_logger', return_value=mock_client_logger):
            opt_obj = optimizely.Optimizely(default_decide_options=invalid_decide_options)

        self.assertEqual(opt_obj.default_decide_options, [])

    def test_decide_experiment(self):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')
        with mock.patch(
            'optimizely.decision_service.DecisionService.get_variation_for_feature',
            return_value=(decision_service.Decision(mock_experiment,
                                                    mock_variation, enums.DecisionSources.FEATURE_TEST), []),
        ):
            user_context = opt_obj.create_user_context('test_user')
            decision = user_context.decide('test_feature_in_experiment', [DecideOption.DISABLE_DECISION_EVENT])
            self.assertTrue(decision.enabled, "decision should be enabled")

    def test_forced_decision_return_status__valid_datafile(self):
        """
        Should return valid status for valid datafile in forced decision calls.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_rollout', None)
        decision = OptimizelyUserContext.OptimizelyForcedDecision('211129')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, '211129')
        status = user_context.remove_forced_decision(context)
        self.assertTrue(status)
        status = user_context.remove_all_forced_decisions()
        self.assertTrue(status)

    def test_should_return_valid_decision_after_setting_and_removing_forced_decision(self):
        """
        Should return valid forced decision after setting and removing forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_experiment', None)
        decision = OptimizelyUserContext.OptimizelyForcedDecision('211129')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, '211129')

        with mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'optimizely.optimizely.Optimizely._send_impression_event'
        ) as mock_send_event:
            decide_decision = user_context.decide('test_feature_in_experiment', ['INCLUDE_REASONS'])

            self.assertEqual(decide_decision.variation_key, 'control')
            self.assertEqual(decide_decision.rule_key, 'test_experiment')
            self.assertFalse(decide_decision.enabled)
            self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment')
            self.assertEqual(decide_decision.user_context.user_id, 'test_user')
            self.assertEqual(decide_decision.user_context.get_user_attributes(), {})
            self.assertEqual(decide_decision.reasons, [
                'Invalid variation is mapped to flag (test_feature_in_experiment) '
                'and user (test_user) in the forced decision map.',
                'Evaluating audiences for experiment "test_experiment": [].',
                'Audiences for experiment "test_experiment" collectively evaluated to TRUE.',
                'User "test_user" is in variation "control" of experiment test_experiment.'])

        expected_variables = {
            'is_working': True,
            'environment': 'devel',
            'cost': 10.99,
            'count': 999,
            'variable_without_usage': 45,
            'object': {'test': 12},
            'true_object': {'true_test': 23.54}
        }

        expected = OptimizelyDecision(
            variation_key='control',
            rule_key='test_experiment',
            enabled=False,
            variables=expected_variables,
            flag_key='test_feature_in_experiment',
            user_context=user_context,
            reasons=['Invalid variation is mapped to flag (test_feature_in_experiment) '
                     'and user (test_user) in the forced decision map.',
                     'Evaluating audiences for experiment "test_experiment": [].',
                     'Audiences for experiment "test_experiment" collectively evaluated to TRUE.',
                     'User "test_user" is in variation "control" of experiment test_experiment.']
        )

        # assert notification count
        self.assertEqual(1, mock_broadcast_decision.call_count)

        # assert notification
        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            {},
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

        expected_experiment = project_config.get_experiment_from_key(expected.rule_key)
        expected_var = project_config.get_variation_from_key('test_experiment', expected.variation_key)

        mock_send_event.assert_called_with(
            project_config,
            expected_experiment,
            expected_var,
            expected.flag_key,
            'test_experiment',
            'feature-test',
            expected.enabled,
            'test_user',
            {}
        )

        self.assertTrue('User "test_user" is in variation "control" of experiment test_experiment.'
                        in decide_decision.reasons)

        status = user_context.remove_forced_decision(context)
        self.assertTrue(status)

        decide_decision = user_context.decide('test_feature_in_experiment', ['INCLUDE_REASONS'])

        self.assertEqual(decide_decision.variation_key, 'control')
        self.assertEqual(decide_decision.rule_key, 'test_experiment')
        self.assertFalse(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})

    def test_should_return_valid_delivery_rule_decision_after_setting_forced_decision(self):
        """
        Should return valid delivery rule decision after setting forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_experiment', None)
        decision = OptimizelyUserContext.OptimizelyForcedDecision('211129')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, '211129')

        decide_decision = user_context.decide('test_feature_in_experiment', ['INCLUDE_REASONS'])
        self.assertEqual(decide_decision.variation_key, 'control')
        self.assertEqual(decide_decision.rule_key, 'test_experiment')
        self.assertFalse(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})
        self.assertEqual(decide_decision.reasons, [
            'Invalid variation is mapped to flag (test_feature_in_experiment) and user (test_user) in the '
            'forced decision map.', 'Evaluating audiences for experiment "test_experiment": [].',
            'Audiences for experiment "test_experiment" collectively evaluated to TRUE.',
            'User "test_user" is in variation "control" of experiment test_experiment.'])
        status = user_context.remove_forced_decision(context)
        self.assertTrue(status)

        decide_decision = user_context.decide('test_feature_in_experiment', ['INCLUDE_REASONS'])
        self.assertEqual(decide_decision.variation_key, 'control')
        self.assertEqual(decide_decision.rule_key, 'test_experiment')
        self.assertFalse(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})

        expected_reasons = [
            'Evaluating audiences for experiment "test_experiment": [].',
            'Audiences for experiment "test_experiment" collectively evaluated to TRUE.',
            'User "test_user" is in variation "control" of experiment test_experiment.']
        self.assertEqual(decide_decision.reasons, expected_reasons)

    def test_should_return_valid_experiment_decision_after_setting_forced_decision(self):
        """
        Should return valid experiment decision after setting forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_experiment_and_rollout',
                                                                  'group_exp_2')
        decision = OptimizelyUserContext.OptimizelyForcedDecision('group_exp_2_variation')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, 'group_exp_2_variation')

        decide_decision = user_context.decide('test_feature_in_experiment_and_rollout', ['INCLUDE_REASONS'])
        self.assertEqual(decide_decision.variation_key, 'group_exp_2_variation')
        self.assertEqual(decide_decision.rule_key, 'group_exp_2')
        self.assertFalse(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment_and_rollout')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})
        self.assertTrue(set(decide_decision.reasons).issuperset(set([
            'Variation (group_exp_2_variation) is mapped to flag '
            '(test_feature_in_experiment_and_rollout), rule (group_exp_2) and '
            'user (test_user) in the forced decision map.'
        ])))
        status = user_context.remove_forced_decision(context)
        self.assertTrue(status)

        decide_decision = user_context.decide('test_feature_in_experiment_and_rollout', ['INCLUDE_REASONS'])
        self.assertEqual(decide_decision.variation_key, 'group_exp_2_control')
        self.assertEqual(decide_decision.rule_key, 'group_exp_2')
        self.assertFalse(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment_and_rollout')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})

        expected_reasons = [
            'Evaluating audiences for experiment "group_exp_2": [].',
            'Audiences for experiment "group_exp_2" collectively evaluated to TRUE.',
            'User "test_user" is in experiment group_exp_2 of group 19228.',
            'User "test_user" is in variation "group_exp_2_control" of experiment group_exp_2.'
        ]

        self.assertEqual(decide_decision.reasons, expected_reasons)

    def test_should_return_valid_decision_after_setting_variation_of_different_experiment_in_forced_decision(self):
        """
        Should return valid decision after setting setting variation of different experiment in forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_experiment_and_rollout',
                                                                  'group_exp_2')
        decision = OptimizelyUserContext.OptimizelyForcedDecision('211129')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, '211129')

        decide_decision = user_context.decide('test_feature_in_experiment_and_rollout', ['INCLUDE_REASONS'])

        self.assertEqual(decide_decision.variation_key, '211129')
        self.assertEqual(decide_decision.rule_key, 'group_exp_2')
        self.assertTrue(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment_and_rollout')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})

    def test_should_return_valid_decision_after_setting_invalid_delivery_rule_variation_in_forced_decision(self):
        """
        Should return valid decision after setting invalid delivery rule variation in forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_rollout', '211127')
        decision = OptimizelyUserContext.OptimizelyForcedDecision('invalid')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, 'invalid')

        decide_decision = user_context.decide('test_feature_in_rollout', ['INCLUDE_REASONS'])

        self.assertEqual(decide_decision.variation_key, None)
        self.assertEqual(decide_decision.rule_key, None)
        self.assertFalse(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_rollout')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})
        self.assertTrue(set(decide_decision.reasons).issuperset(set([
            'Invalid variation is mapped to flag (test_feature_in_rollout), '
            'rule (211127) and user (test_user) in the forced decision map.'
        ])))

    def test_should_return_valid_decision_after_setting_invalid_experiment_rule_variation_in_forced_decision(self):
        """
        Should return valid decision after setting invalid experiment rule variation in forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_experiment',
                                                                  'test_experiment')
        decision = OptimizelyUserContext.OptimizelyForcedDecision('invalid')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, 'invalid')

        decide_decision = user_context.decide('test_feature_in_experiment', ['INCLUDE_REASONS'])
        self.assertEqual(decide_decision.variation_key, 'control')
        self.assertEqual(decide_decision.rule_key, 'test_experiment')
        self.assertFalse(decide_decision.enabled)

        self.assertEqual(decide_decision.flag_key, 'test_feature_in_experiment')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})

        expected_reasons = [
            'Invalid variation is mapped to flag (test_feature_in_experiment), rule (test_experiment) '
            'and user (test_user) in the forced decision map.',
            'Evaluating audiences for experiment "test_experiment": [].',
            'Audiences for experiment "test_experiment" collectively evaluated to TRUE.',
            'User "test_user" is in variation "control" of experiment test_experiment.'
        ]

        self.assertEqual(decide_decision.reasons, expected_reasons)

    def test_conflicts_return_valid_decision__forced_decision(self):
        """
        Should return valid forced decision after setting conflicting forced decisions.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context_with_flag = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_rollout', None)
        decision_for_flag = OptimizelyUserContext.OptimizelyForcedDecision('211129')

        context_with_rule = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_rollout', '211127')
        decision_for_rule = OptimizelyUserContext.OptimizelyForcedDecision('211229')

        status = user_context.set_forced_decision(context_with_flag, decision_for_flag)
        self.assertTrue(status)

        status = user_context.set_forced_decision(context_with_rule, decision_for_rule)
        self.assertTrue(status)

        decide_decision = user_context.decide('test_feature_in_rollout', ['INCLUDE_REASONS'])
        self.assertEqual(decide_decision.variation_key, '211129')
        self.assertIsNone(decide_decision.rule_key)
        self.assertTrue(decide_decision.enabled)
        self.assertEqual(decide_decision.flag_key, 'test_feature_in_rollout')
        self.assertEqual(decide_decision.user_context.user_id, 'test_user')
        self.assertEqual(decide_decision.user_context.get_user_attributes(), {})
        self.assertTrue(set(decide_decision.reasons).issuperset(set([
            'Variation (211129) is mapped to flag (test_feature_in_rollout) and '
            'user (test_user) in the forced decision map.'
        ])))

    def test_get_forced_decision_return_valid_decision__forced_decision(self):
        """
        Should return valid forced decision on getting forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context_with_flag_1 = OptimizelyUserContext.OptimizelyDecisionContext('f1', None)
        decision_for_flag_1 = OptimizelyUserContext.OptimizelyForcedDecision('v1')

        context_with_flag_2 = OptimizelyUserContext.OptimizelyDecisionContext('f1', None)
        decision_for_flag_2 = OptimizelyUserContext.OptimizelyForcedDecision('v2')
        status = user_context.set_forced_decision(context_with_flag_1, decision_for_flag_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_flag_1)
        self.assertEqual(status.variation_key, decision_for_flag_1.variation_key)

        status = user_context.set_forced_decision(context_with_flag_2, decision_for_flag_2)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_flag_2)
        self.assertEqual(status.variation_key, decision_for_flag_2.variation_key)

        context_with_rule_1 = OptimizelyUserContext.OptimizelyDecisionContext('f1', 'r1')
        decision_for_rule_1 = OptimizelyUserContext.OptimizelyForcedDecision('v3')

        context_with_rule_2 = OptimizelyUserContext.OptimizelyDecisionContext('f1', 'r2')
        decision_for_rule_2 = OptimizelyUserContext.OptimizelyForcedDecision('v4')

        status = user_context.set_forced_decision(context_with_rule_1, decision_for_rule_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_rule_1)
        self.assertEqual(status.variation_key, decision_for_rule_1.variation_key)

        status = user_context.set_forced_decision(context_with_rule_2, decision_for_rule_2)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_rule_2)
        self.assertEqual(status.variation_key, decision_for_rule_2.variation_key)

        status = user_context.get_forced_decision(context_with_flag_1)
        self.assertEqual(status.variation_key, decision_for_flag_2.variation_key)

    def test_remove_forced_decision_return_valid_decision__forced_decision(self):
        """
        Should remove forced decision on removing forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context_with_flag_1 = OptimizelyUserContext.OptimizelyDecisionContext('f1', None)
        decision_for_flag_1 = OptimizelyUserContext.OptimizelyForcedDecision('v1')

        status = user_context.set_forced_decision(context_with_flag_1, decision_for_flag_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_flag_1)
        self.assertEqual(status.variation_key, decision_for_flag_1.variation_key)

        status = user_context.remove_forced_decision(context_with_flag_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_flag_1)
        self.assertIsNone(status)

        context_with_rule_1 = OptimizelyUserContext.OptimizelyDecisionContext('f1', 'r1')
        decision_for_rule_1 = OptimizelyUserContext.OptimizelyForcedDecision('v3')

        status = user_context.set_forced_decision(context_with_rule_1, decision_for_rule_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_rule_1)
        self.assertEqual(status.variation_key, decision_for_rule_1.variation_key)

        status = user_context.remove_forced_decision(context_with_rule_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_rule_1)
        self.assertIsNone(status)

        status = user_context.get_forced_decision(context_with_flag_1)
        self.assertIsNone(status)

    def test_remove_all_forced_decision_return_valid_decision__forced_decision(self):
        """
        Should remove all forced decision on removing all forced decision.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context_with_flag_1 = OptimizelyUserContext.OptimizelyDecisionContext('f1', None)
        decision_for_flag_1 = OptimizelyUserContext.OptimizelyForcedDecision('v1')

        status = user_context.remove_all_forced_decisions()
        self.assertTrue(status)

        status = user_context.set_forced_decision(context_with_flag_1, decision_for_flag_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_flag_1)
        self.assertEqual(status.variation_key, decision_for_flag_1.variation_key)

        context_with_rule_1 = OptimizelyUserContext.OptimizelyDecisionContext('f1', 'r1')
        decision_for_rule_1 = OptimizelyUserContext.OptimizelyForcedDecision('v3')

        status = user_context.set_forced_decision(context_with_rule_1, decision_for_rule_1)
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_rule_1)
        self.assertEqual(status.variation_key, decision_for_rule_1.variation_key)

        status = user_context.remove_all_forced_decisions()
        self.assertTrue(status)

        status = user_context.get_forced_decision(context_with_rule_1)
        self.assertIsNone(status)

        status = user_context.get_forced_decision(context_with_flag_1)
        self.assertIsNone(status)

        status = user_context.remove_all_forced_decisions()
        self.assertTrue(status)

    def test_forced_decision_return_status(self):
        """
        Should return valid status for a valid datafile in forced decision calls.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context = OptimizelyUserContext.OptimizelyDecisionContext('test_feature_in_rollout', None)
        decision = OptimizelyUserContext.OptimizelyForcedDecision('211129')

        status = user_context.set_forced_decision(context, decision)
        self.assertTrue(status)
        status = user_context.get_forced_decision(context)
        self.assertEqual(status.variation_key, '211129')
        status = user_context.remove_forced_decision(context)
        self.assertTrue(status)
        status = user_context.remove_all_forced_decisions()
        self.assertTrue(status)

    def test_forced_decision_clone_return_valid_forced_decision(self):
        """
        Should return valid forced decision on cloning.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})

        context_with_flag = OptimizelyUserContext.OptimizelyDecisionContext('f1', None)
        decision_for_flag = OptimizelyUserContext.OptimizelyForcedDecision('v1')
        context_with_rule = OptimizelyUserContext.OptimizelyDecisionContext('f1', 'r1')
        decision_for_rule = OptimizelyUserContext.OptimizelyForcedDecision('v2')
        context_with_empty_rule = OptimizelyUserContext.OptimizelyDecisionContext('f1', '')
        decision_for_empty_rule = OptimizelyUserContext.OptimizelyForcedDecision('v3')

        user_context.set_forced_decision(context_with_flag, decision_for_flag)
        user_context.set_forced_decision(context_with_rule, decision_for_rule)
        user_context.set_forced_decision(context_with_empty_rule, decision_for_empty_rule)

        user_context_2 = user_context._clone()
        self.assertEqual(user_context_2.user_id, 'test_user')
        self.assertEqual(user_context_2.get_user_attributes(), {})
        self.assertIsNotNone(user_context_2.forced_decisions_map)

        self.assertEqual(user_context_2.get_forced_decision(context_with_flag).variation_key, 'v1')
        self.assertEqual(user_context_2.get_forced_decision(context_with_rule).variation_key, 'v2')
        self.assertEqual(user_context_2.get_forced_decision(context_with_empty_rule).variation_key, 'v3')

        context_with_rule = OptimizelyUserContext.OptimizelyDecisionContext('x', 'y')
        decision_for_rule = OptimizelyUserContext.OptimizelyForcedDecision('z')
        user_context.set_forced_decision(context_with_rule, decision_for_rule)
        self.assertEqual(user_context.get_forced_decision(context_with_rule).variation_key, 'z')
        self.assertIsNone(user_context_2.get_forced_decision(context_with_rule))

    def test_forced_decision_sync_return_correct_number_of_calls(self):
        """
        Should return valid number of call on running forced decision calls in thread.
        """
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context("test_user", {})
        context_1 = OptimizelyUserContext.OptimizelyDecisionContext('f1', None)
        decision_1 = OptimizelyUserContext.OptimizelyForcedDecision('v1')
        context_2 = OptimizelyUserContext.OptimizelyDecisionContext('f2', None)
        decision_2 = OptimizelyUserContext.OptimizelyForcedDecision('v1')

        with mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext.set_forced_decision'
        ) as set_forced_decision_mock, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext.get_forced_decision'
        ) as get_forced_decision_mock, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext.remove_forced_decision'
        ) as remove_forced_decision_mock, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext.remove_all_forced_decisions'
        ) as remove_all_forced_decisions_mock, mock.patch(
            'optimizely.optimizely_user_context.OptimizelyUserContext._clone'
        ) as clone_mock:
            def set_forced_decision_loop(user_context, context, decision):
                for x in range(100):
                    user_context.set_forced_decision(context, decision)

            def get_forced_decision_loop(user_context, context):
                for x in range(100):
                    user_context.get_forced_decision(context)

            def remove_forced_decision_loop(user_context, context):
                for x in range(100):
                    user_context.remove_forced_decision(context)

            def remove_all_forced_decisions_loop(user_context):
                for x in range(100):
                    user_context.remove_all_forced_decisions()

            def clone_loop(user_context):
                for x in range(100):
                    user_context._clone()

            # custom call counter because the mock call_count is not thread safe
            class MockCounter:
                def __init__(self):
                    self.lock = threading.Lock()
                    self.call_count = 0

                def increment(self, *args):
                    with self.lock:
                        self.call_count += 1

            set_forced_decision_counter = MockCounter()
            get_forced_decision_counter = MockCounter()
            remove_forced_decision_counter = MockCounter()
            remove_all_forced_decisions_counter = MockCounter()
            clone_counter = MockCounter()

            set_forced_decision_mock.side_effect = set_forced_decision_counter.increment
            get_forced_decision_mock.side_effect = get_forced_decision_counter.increment
            remove_forced_decision_mock.side_effect = remove_forced_decision_counter.increment
            remove_all_forced_decisions_mock.side_effect = remove_all_forced_decisions_counter.increment
            clone_mock.side_effect = clone_counter.increment

            set_thread_1 = threading.Thread(target=set_forced_decision_loop, args=(user_context, context_1, decision_1))
            set_thread_2 = threading.Thread(target=set_forced_decision_loop, args=(user_context, context_2, decision_2))
            set_thread_3 = threading.Thread(target=get_forced_decision_loop, args=(user_context, context_1))
            set_thread_4 = threading.Thread(target=get_forced_decision_loop, args=(user_context, context_2))
            set_thread_5 = threading.Thread(target=remove_forced_decision_loop, args=(user_context, context_1))
            set_thread_6 = threading.Thread(target=remove_forced_decision_loop, args=(user_context, context_2))
            set_thread_7 = threading.Thread(target=remove_all_forced_decisions_loop, args=(user_context,))
            set_thread_8 = threading.Thread(target=clone_loop, args=(user_context,))

            # Starting the threads
            set_thread_1.start()
            set_thread_2.start()
            set_thread_3.start()
            set_thread_4.start()
            set_thread_5.start()
            set_thread_6.start()
            set_thread_7.start()
            set_thread_8.start()

            # Waiting for all the threads to finish executing
            set_thread_1.join()
            set_thread_2.join()
            set_thread_3.join()
            set_thread_4.join()
            set_thread_5.join()
            set_thread_6.join()
            set_thread_7.join()
            set_thread_8.join()

        self.assertEqual(200, set_forced_decision_counter.call_count)
        self.assertEqual(200, get_forced_decision_counter.call_count)
        self.assertEqual(200, remove_forced_decision_counter.call_count)
        self.assertEqual(100, remove_all_forced_decisions_counter.call_count)
        self.assertEqual(100, clone_counter.call_count)
