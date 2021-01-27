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
import logging

import mock

from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption as DecideOption
from optimizely.event.event_factory import EventFactory
from optimizely.helpers import enums
from optimizely.user_profile import UserProfileService, UserProfile
from . import base
from optimizely import logger, optimizely, decision_service
from optimizely.optimizely_user_context import OptimizelyUserContext


class UserContextTest(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self, 'config_dict_with_multiple_experiments')

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

    def test_decide_feature_test(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=decision_service.Decision(mock_experiment, mock_variation,
                                                       enums.DecisionSources.FEATURE_TEST),
        ):
            user_context = opt_obj.create_user_context('test_user')
            decision = user_context.decide('test_feature_in_experiment', [DecideOption.DISABLE_DECISION_EVENT])
            self.assertTrue(decision.enabled, "decision should be enabled")

    def test_decide_rollout(self):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user')
        decision = user_context.decide('test_feature_in_rollout')
        self.assertFalse(decision.enabled)
        self.assertEqual(decision.flag_key, 'test_feature_in_rollout')

    def test_decide_for_keys(self):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user')
        decisions = user_context.decide_for_keys(['test_feature_in_rollout', 'test_feature_in_experiment'])
        self.assertTrue(len(decisions) == 2)

        self.assertFalse(decisions['test_feature_in_rollout'].enabled)
        self.assertEqual(decisions['test_feature_in_rollout'].flag_key, 'test_feature_in_rollout')

        self.assertFalse(decisions['test_feature_in_experiment'].enabled)
        self.assertEqual(decisions['test_feature_in_experiment'].flag_key, 'test_feature_in_experiment')

    def test_decide_all(self):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user')
        decisions = user_context.decide_all()
        self.assertTrue(len(decisions) == 4)

        self.assertFalse(decisions['test_feature_in_rollout'].enabled)
        self.assertEqual(decisions['test_feature_in_rollout'].flag_key, 'test_feature_in_rollout')

        self.assertFalse(decisions['test_feature_in_experiment'].enabled)
        self.assertEqual(decisions['test_feature_in_experiment'].flag_key, 'test_feature_in_experiment')

        self.assertFalse(decisions['test_feature_in_group'].enabled)
        self.assertEqual(decisions['test_feature_in_group'].flag_key, 'test_feature_in_group')

        self.assertFalse(decisions['test_feature_in_experiment_and_rollout'].enabled)
        self.assertEqual(decisions['test_feature_in_experiment_and_rollout'].flag_key,
                         'test_feature_in_experiment_and_rollout')

    def test_decide_all_enabled_only(self):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        user_context = opt_obj.create_user_context('test_user')
        decisions = user_context.decide_all([DecideOption.ENABLED_FLAGS_ONLY])
        self.assertTrue(len(decisions) == 0)

    def test_track(self):
        """ Test that the feature is enabled for the user if bucketed into variation of a rollout.
    Also confirm that no impression event is processed. """

        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))

        with mock.patch('time.time', return_value=42), mock.patch(
                'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch('optimizely.event.event_processor.ForwardingEventProcessor.process') as mock_process:
            user_context = opt_obj.create_user_context('test_user')
            user_context.track_event('test_event')

        log_event = EventFactory.create_log_event(mock_process.call_args[0][0], opt_obj.logger)
        self.assertEqual(log_event.params['visitors'][0]['visitor_id'], 'test_user')
        self.assertEqual(log_event.params['visitors'][0]['snapshots'][0]['events'][0]['timestamp'], 42000)
        self.assertEqual(log_event.params['visitors'][0]['snapshots'][0]['events'][0]['uuid'],
                         'a68cf1ad-0393-4e18-af87-efe8f01a7c9c')
        self.assertEqual(log_event.params['visitors'][0]['snapshots'][0]['events'][0]['key'], 'test_event')

    def test_decide_sendEvent(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        # Assert that featureEnabled property is True
        self.assertTrue(mock_variation.featureEnabled)

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            context = opt_obj.create_user_context('test_user')
            decision = context.decide('test_feature_in_experiment')
            self.assertTrue(decision.enabled)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            {},
            {
                'flag_key': 'test_feature_in_experiment',
                'enabled': True,
                'variation_key': decision.variation_key,
                'rule_key': decision.rule_key,
                'reasons': decision.reasons,
                'decision_event_dispatched': True,
                'variables': decision.variables,
            },
        )
        # Check that impression event is sent for rollout and send_flag_decisions = True
        self.assertEqual(1, mock_process.call_count)

    def test_decide_doNotSendEvent_withOption(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        project_config = opt_obj.config_manager.get_config()

        mock_experiment = project_config.get_experiment_from_key('test_experiment')
        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        # Assert that featureEnabled property is True
        self.assertTrue(mock_variation.featureEnabled)

        with mock.patch(
                'optimizely.decision_service.DecisionService.get_variation_for_feature',
                return_value=decision_service.Decision(mock_experiment, mock_variation, enums.DecisionSources.ROLLOUT),
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            context = opt_obj.create_user_context('test_user')
            decision = context.decide('test_feature_in_experiment', [DecideOption.DISABLE_DECISION_EVENT])
            self.assertTrue(decision.enabled)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            {},
            {
                'flag_key': 'test_feature_in_experiment',
                'enabled': True,
                'variation_key': decision.variation_key,
                'rule_key': decision.rule_key,
                'reasons': decision.reasons,
                'decision_event_dispatched': False,
                'variables': decision.variables,

            },
        )

        # Check that impression event is NOT sent for rollout and send_flag_decisions = True
        # with disable decision event decision option
        self.assertEqual(0, mock_process.call_count)

    def test_decide_options_bypass_UPS(self):
        user_id = 'test_user'
        experiment_bucket_map = {'111127': {'variation_id': '111128'}}

        profile = UserProfile(user_id, experiment_bucket_map=experiment_bucket_map)

        class Ups(UserProfileService):

            def lookup(self, user_id):
                return profile

            def save(self, user_profile):
                super(Ups, self).save(user_profile)

        ups = Ups()
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features), user_profile_service=ups)
        project_config = opt_obj.config_manager.get_config()

        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        # Assert that featureEnabled property is True
        self.assertTrue(mock_variation.featureEnabled)

        with mock.patch(
                'optimizely.bucketer.Bucketer.bucket',
                return_value=mock_variation,
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            context = opt_obj.create_user_context(user_id)
            decision = context.decide('test_feature_in_experiment', [DecideOption.DISABLE_DECISION_EVENT,
                                                                     DecideOption.IGNORE_USER_PROFILE_SERVICE,
                                                                     DecideOption.EXCLUDE_VARIABLES])
            self.assertTrue(decision.enabled)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            {},
            {
                'flag_key': 'test_feature_in_experiment',
                'enabled': True,
                'variation_key': decision.variation_key,
                'rule_key': decision.rule_key,
                'reasons': decision.reasons,
                'decision_event_dispatched': False,
                'variables': decision.variables,

            },
        )

        # Check that impression event is NOT sent for rollout and send_flag_decisions = True
        # with disable decision event decision option
        self.assertEqual(0, mock_process.call_count)

    def test_decide_options_reasons(self):
        user_id = 'test_user'
        experiment_bucket_map = {'111127': {'variation_id': '111128'}}

        profile = UserProfile(user_id, experiment_bucket_map=experiment_bucket_map)

        class Ups(UserProfileService):

            def lookup(self, user_id):
                return profile

            def save(self, user_profile):
                super(Ups, self).save(user_profile)

        ups = Ups()
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features),
                                        logger=logger.SimpleLogger(min_level=logging.DEBUG),
                                        user_profile_service=ups)
        project_config = opt_obj.config_manager.get_config()

        mock_variation = project_config.get_variation_from_id('test_experiment', '111129')

        # Assert that featureEnabled property is True
        self.assertTrue(mock_variation.featureEnabled)

        with mock.patch(
                'optimizely.bucketer.Bucketer.bucket',
                return_value=mock_variation,
        ), mock.patch(
            'optimizely.event.event_processor.ForwardingEventProcessor.process'
        ) as mock_process, mock.patch(
            'optimizely.notification_center.NotificationCenter.send_notifications'
        ) as mock_broadcast_decision, mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'time.time', return_value=42
        ):
            context = opt_obj.create_user_context(user_id)
            decision = context.decide('test_feature_in_experiment', [DecideOption.DISABLE_DECISION_EVENT,
                                                                     DecideOption.IGNORE_USER_PROFILE_SERVICE,
                                                                     DecideOption.EXCLUDE_VARIABLES,
                                                                     DecideOption.INCLUDE_REASONS])
            self.assertTrue(decision.enabled)

        mock_broadcast_decision.assert_called_with(
            enums.NotificationTypes.DECISION,
            'flag',
            'test_user',
            {},
            {
                'flag_key': 'test_feature_in_experiment',
                'enabled': True,
                'variation_key': decision.variation_key,
                'rule_key': decision.rule_key,
                'reasons': decision.reasons,
                'decision_event_dispatched': False,
                'variables': decision.variables,

            },
        )

        # Check that impression event is NOT sent for rollout and send_flag_decisions = True
        # with disable decision event decision option
        self.assertEqual(0, mock_process.call_count)
