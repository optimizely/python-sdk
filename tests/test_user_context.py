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

from optimizely import optimizely
from optimizely.optimizely_user_context import OptimizelyUserContext
from . import base


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

    def test_user_context_calls_optimizely_API_and_returns_response(self):
        opt_obj = optimizely.Optimizely(json.dumps(self.config_dict_with_features))
        user_context = opt_obj.create_user_context('test_user')

        # decide
        with mock.patch(
            'optimizely.optimizely.Optimizely._decide',
            return_value='I am response from decide API'
        ):
            response = user_context.decide('test_feature_in_rollout')

        self.assertEquals('I am response from decide API', response)

        # decide_all
        with mock.patch(
            'optimizely.optimizely.Optimizely._decide_all',
            return_value='I am response from decide All API'
        ):
            response = user_context.decide_all()

        self.assertEquals('I am response from decide All API', response)

        # decide_for_keys
        with mock.patch(
            'optimizely.optimizely.Optimizely._decide_for_keys',
            return_value='I am response from decide for keys API'
        ):
            response = user_context.decide_for_keys(['test_feature_in_rollout'])

        self.assertEquals('I am response from decide for keys API', response)

        # track event
        with mock.patch(
            'optimizely.optimizely.Optimizely.track',
            return_value='I am response from track API'
        ):
            response = user_context.track_event('some_event')

        self.assertEquals('I am response from track API', response)
