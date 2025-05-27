# Copyright 2025 Optimizely
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
import uuid
import json
import hashlib

from typing import Optional, List, TypedDict
from optimizely.cmab.cmab_client import DefaultCmabClient
from optimizely.odp.lru_cache import LRUCache
from optimizely.optimizely_user_context import OptimizelyUserContext, UserAttributes
from optimizely.project_config import ProjectConfig
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption
from optimizely import logger as _logging


class CmabDecision(TypedDict):
    variation_id: str
    cmab_uuid: str


class CmabCacheValue(TypedDict):
    attributes_hash: str
    variation_id: str
    cmab_uuid: str


class DefaultCmabService:
    def __init__(self, cmab_cache: LRUCache[str, CmabCacheValue],
                 cmab_client: DefaultCmabClient, logger: Optional[_logging.Logger] = None):
        self.cmab_cache = cmab_cache
        self.cmab_client = cmab_client
        self.logger = logger

    def get_decision(self, project_config: ProjectConfig, user_context: OptimizelyUserContext,
                     rule_id: str, options: List[str]) -> CmabDecision:

        filtered_attributes = self._filter_attributes(project_config, user_context, rule_id)

        if OptimizelyDecideOption.IGNORE_CMAB_CACHE in options:
            return self._fetch_decision(rule_id, user_context.user_id, filtered_attributes)

        if OptimizelyDecideOption.RESET_CMAB_CACHE in options:
            self.cmab_cache.reset()

        cache_key = self._get_cache_key(user_context.user_id, rule_id)

        if OptimizelyDecideOption.INVALIDATE_USER_CMAB_CACHE in options:
            self.cmab_cache.remove(cache_key)

        cached_value = self.cmab_cache.lookup(cache_key)

        attributes_hash = self._hash_attributes(filtered_attributes)

        if cached_value:
            if cached_value['attributes_hash'] == attributes_hash:
                return CmabDecision(variation_id=cached_value['variation_id'], cmab_uuid=cached_value['cmab_uuid'])
            elif OptimizelyDecideOption.INVALIDATE_USER_CMAB_CACHE not in options:
                self.cmab_cache.remove(cache_key)

        cmab_decision = self._fetch_decision(rule_id, user_context.user_id, filtered_attributes)
        self.cmab_cache.save(cache_key, {
            'attributes_hash': attributes_hash,
            'variation_id': cmab_decision['variation_id'],
            'cmab_uuid': cmab_decision['cmab_uuid'],
        })
        return cmab_decision

    def _fetch_decision(self, rule_id: str, user_id: str, attributes: UserAttributes) -> CmabDecision:
        cmab_uuid = str(uuid.uuid4())
        variation_id = self.cmab_client.fetch_decision(rule_id, user_id, attributes, cmab_uuid)
        cmab_decision = CmabDecision(variation_id=variation_id, cmab_uuid=cmab_uuid)
        return cmab_decision

    def _filter_attributes(self, project_config: ProjectConfig,
                           user_context: OptimizelyUserContext, rule_id: str) -> UserAttributes:
        user_attributes = user_context.get_user_attributes()
        filtered_user_attributes = UserAttributes({})

        experiment = project_config.experiment_id_map.get(rule_id)
        if not experiment or not experiment.cmab:
            return filtered_user_attributes

        cmab_attribute_ids = experiment.cmab['attributeIds']
        for attribute_id in cmab_attribute_ids:
            attribute = project_config.attribute_id_map.get(attribute_id)
            if attribute and attribute.key in user_attributes:
                filtered_user_attributes[attribute.key] = user_attributes[attribute.key]

        return filtered_user_attributes

    def _get_cache_key(self, user_id: str, rule_id: str) -> str:
        return f"{len(user_id)}-{user_id}-{rule_id}"

    def _hash_attributes(self, attributes: UserAttributes) -> str:
        sorted_attrs = json.dumps(attributes, sort_keys=True)
        return hashlib.md5(sorted_attrs.encode()).hexdigest()
