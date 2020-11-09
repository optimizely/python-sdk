# Copyright 2019, Optimizely
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

from . import base
from optimizely import logger
from optimizely.user_context import UserContext
from optimizely.optimizely import Optimizely


class UserContextTests(base.BaseTest):
    def setUp(self):
        base.BaseTest.setUp(self, 'config_dict_with_multiple_experiments')
        self.logger = logger.NoOpLogger()

    def test_user_context(self):
        """
        tests user context creating and attributes
        """
        uc = UserContext(self.optimizely, "test_user")
        self.assertEqual(uc.user_attributes, {}, "should have created default empty")
        self.assertEqual(uc.user_id, "test_user", "should have same user id")
        uc.set_attribute("key", "value")
        self.assertEqual(uc.user_attributes["key"], "value", "should have added attribute")
        uc.set_attribute("key", "value2")
        self.assertEqual(uc.user_attributes["key"], "value2", "should have new attribute")
