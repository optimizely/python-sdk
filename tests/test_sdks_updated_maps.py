import json

import mock

from optimizely.decision.optimizely_decision import OptimizelyDecision
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption as DecideOption
from optimizely.helpers import enums
from . import base
from optimizely import optimizely, decision_service
from optimizely.optimizely_user_context import OptimizelyUserContext
from optimizely.user_profile import UserProfileService


class SampleSdkTests(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self, 'config_test_cases_key')

    def test_decide__flag1(self):
        user_context = self.optimizely.create_user_context("test_user_1")

        expected = OptimizelyDecision(
            variation_key='on',
            rule_key='targeted_delivery',
            enabled=True,
            variables={},
            flag_key='flag_3',
            user_context=user_context
        )

        actual = user_context.decide('flag_3')
        print(expected.user_context.user_id, actual.user_context.user_id)
        self.assertEqual(actual.variation_key, expected.variation_key)
        self.assertEqual(actual.rule_key, expected.rule_key)

    def test_decide__flag2(self):
        user_context = self.optimizely.create_user_context("test_user_1")
        expected = OptimizelyDecision(
            variation_key='on',
            rule_key='targeted_delivery',
            enabled=True,
            variables={},
            flag_key='flag_2',
            user_context=user_context
        )

        actual = user_context.decide('flag_2')
        print(expected.user_context.user_id, actual.user_context.user_id)
        self.assertEqual(actual.variation_key, expected.variation_key)
        self.assertEqual(actual.rule_key, expected.rule_key)

    def test_decide__flag3(self):
        user_context = self.optimizely.create_user_context("test_user_1")
        expected = OptimizelyDecision(
            variation_key='on',
            rule_key='targeted_delivery',
            enabled=True,
            variables={},
            flag_key='flag_1',
            user_context=user_context
        )

        actual = user_context.decide('flag_1')
        print(expected.user_context.user_id, actual.user_context.user_id)
        self.assertEqual(actual.variation_key, expected.variation_key)
        self.assertEqual(actual.rule_key, expected.rule_key)


