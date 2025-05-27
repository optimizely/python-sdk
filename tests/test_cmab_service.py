# Copyright 2025, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest
from unittest.mock import MagicMock
from optimizely.cmab.cmab_service import DefaultCmabService
from optimizely.optimizely_user_context import OptimizelyUserContext
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption
from optimizely.odp.lru_cache import LRUCache
from optimizely.cmab.cmab_client import DefaultCmabClient
from optimizely.project_config import ProjectConfig
from optimizely.entities import Attribute


class TestDefaultCmabService(unittest.TestCase):
    def setUp(self):
        self.mock_cmab_cache = MagicMock(spec=LRUCache)
        self.mock_cmab_client = MagicMock(spec=DefaultCmabClient)
        self.mock_logger = MagicMock()

        self.cmab_service = DefaultCmabService(
            cmab_cache=self.mock_cmab_cache,
            cmab_client=self.mock_cmab_client,
            logger=self.mock_logger
        )

        self.mock_project_config = MagicMock(spec=ProjectConfig)
        self.mock_user_context = MagicMock(spec=OptimizelyUserContext)
        self.mock_user_context.user_id = 'user123'
        self.mock_user_context.get_user_attributes.return_value = {'age': 25, 'location': 'USA'}

        # Setup mock experiment and attribute mapping
        self.mock_project_config.experiment_id_map = {
            'exp1': MagicMock(cmab={'attributeIds': ['66', '77']})
        }
        attr1 = Attribute(id="66", key="age")
        attr2 = Attribute(id="77", key="location")
        self.mock_project_config.attribute_id_map = {
            "66": attr1,
            "77": attr2
        }

    def test_returns_decision_from_cache_when_valid(self):
        expected_key = self.cmab_service._get_cache_key("user123", "exp1")
        expected_attributes = {"age": 25, "location": "USA"}
        expected_hash = self.cmab_service._hash_attributes(expected_attributes)

        self.mock_cmab_cache.lookup.return_value = {
            "attributes_hash": expected_hash,
            "variation_id": "varA",
            "cmab_uuid": "uuid-123"
        }

        decision = self.cmab_service.get_decision(
            self.mock_project_config, self.mock_user_context, "exp1", []
        )

        self.mock_cmab_cache.lookup.assert_called_once_with(expected_key)
        self.assertEqual(decision["variation_id"], "varA")
        self.assertEqual(decision["cmab_uuid"], "uuid-123")

    def test_ignores_cache_when_option_given(self):
        self.mock_cmab_client.fetch_decision.return_value = "varB"
        expected_attributes = {"age": 25, "location": "USA"}

        decision = self.cmab_service.get_decision(
            self.mock_project_config,
            self.mock_user_context,
            "exp1",
            [OptimizelyDecideOption.IGNORE_CMAB_CACHE]
        )

        self.assertEqual(decision["variation_id"], "varB")
        self.assertIn('cmab_uuid', decision)
        self.mock_cmab_client.fetch_decision.assert_called_once_with(
            "exp1",
            self.mock_user_context.user_id,
            expected_attributes,
            decision["cmab_uuid"]
        )

    def test_invalidates_user_cache_when_option_given(self):
        self.mock_cmab_client.fetch_decision.return_value = "varC"
        self.mock_cmab_cache.lookup.return_value = None
        self.cmab_service.get_decision(
            self.mock_project_config,
            self.mock_user_context,
            "exp1",
            [OptimizelyDecideOption.INVALIDATE_USER_CMAB_CACHE]
        )

        key = self.cmab_service._get_cache_key("user123", "exp1")
        self.mock_cmab_cache.remove.assert_called_with(key)
        self.mock_cmab_cache.remove.assert_called_once()

    def test_resets_cache_when_option_given(self):
        self.mock_cmab_client.fetch_decision.return_value = "varD"

        decision = self.cmab_service.get_decision(
            self.mock_project_config,
            self.mock_user_context,
            "exp1",
            [OptimizelyDecideOption.RESET_CMAB_CACHE]
        )

        self.mock_cmab_cache.reset.assert_called_once()
        self.assertEqual(decision["variation_id"], "varD")
        self.assertIn('cmab_uuid', decision)

    def test_new_decision_when_hash_changes(self):
        self.mock_cmab_cache.lookup.return_value = {
            "attributes_hash": "old_hash",
            "variation_id": "varA",
            "cmab_uuid": "uuid-123"
        }
        self.mock_cmab_client.fetch_decision.return_value = "varE"

        user_attrs = {"age": 25, "location": "USA"}
        expected_hash = self.cmab_service._hash_attributes(user_attrs)
        expected_key = self.cmab_service._get_cache_key("user123", "exp1")

        decision = self.cmab_service.get_decision(self.mock_project_config, self.mock_user_context, "exp1", [])
        self.mock_cmab_cache.remove.assert_called_once_with(expected_key)
        self.mock_cmab_cache.save.assert_called_once_with(
            expected_key,
            {
                "cmab_uuid": decision["cmab_uuid"],
                "variation_id": decision["variation_id"],
                "attributes_hash": expected_hash
            }
        )
        self.assertEqual(decision["variation_id"], "varE")

    def test_filter_attributes_returns_correct_subset(self):
        filtered = self.cmab_service._filter_attributes(self.mock_project_config, self.mock_user_context, "exp1")
        self.assertEqual(filtered["age"], 25)
        self.assertEqual(filtered["location"], "USA")

    def test_filter_attributes_empty_when_no_cmab(self):
        self.mock_project_config.experiment_id_map["exp1"].cmab = None
        filtered = self.cmab_service._filter_attributes(self.mock_project_config, self.mock_user_context, "exp1")
        self.assertEqual(filtered, {})

    def test_hash_attributes_produces_stable_output(self):
        attrs = {"b": 2, "a": 1}
        hash1 = self.cmab_service._hash_attributes(attrs)
        hash2 = self.cmab_service._hash_attributes({"a": 1, "b": 2})
        self.assertEqual(hash1, hash2)
