# Copyright 2019, 2022, Optimizely
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

from __future__ import annotations
import json
from numbers import Integral
from typing import TYPE_CHECKING, Any, Optional


if TYPE_CHECKING:
    from optimizely.helpers.event_tag_utils import EventTags


class EventBatch:
    """ Class respresenting Event Batch. """

    def __init__(
        self,
        account_id: str,
        project_id: str,
        revision: str,
        client_name: str,
        client_version: str,
        anonymize_ip: bool,
        enrich_decisions: bool = True,
        visitors: Optional[list[Visitor]] = None,
    ):
        self.account_id = account_id
        self.project_id = project_id
        self.revision = revision
        self.client_name = client_name
        self.client_version = client_version
        self.anonymize_ip = anonymize_ip
        self.enrich_decisions = enrich_decisions
        self.visitors = visitors or []

    def __eq__(self, other: object) -> bool:
        batch_obj = self.get_event_params()
        return batch_obj == other

    def _dict_clean(self, obj: list[tuple[str, Any]]) -> dict[str, Any]:
        """ Helper method to remove keys from dictionary with None values. """

        result = {}
        for k, v in obj:
            if v is None and k in ['revenue', 'value', 'tags', 'decisions']:
                continue
            else:
                result[k] = v
        return result

    def get_event_params(self) -> dict[str, Any]:
        """ Method to return valid params for LogEvent payload. """

        return json.loads(  # type: ignore[no-any-return]
            json.dumps(self.__dict__, default=lambda o: o.__dict__),
            object_pairs_hook=self._dict_clean,
        )


class Decision:
    """ Class respresenting Decision. """

    def __init__(self, campaign_id: str, experiment_id: str, variation_id: str, metadata: Metadata):
        self.campaign_id = campaign_id
        self.experiment_id = experiment_id
        self.variation_id = variation_id
        self.metadata = metadata


class Metadata:
    """ Class respresenting Metadata. """

    def __init__(self, flag_key: str, rule_key: str, rule_type: str, variation_key: str, enabled: bool):
        self.flag_key = flag_key
        self.rule_key = rule_key
        self.rule_type = rule_type
        self.variation_key = variation_key
        self.enabled = enabled


class Snapshot:
    """ Class representing Snapshot. """

    def __init__(self, events: list[SnapshotEvent], decisions: Optional[list[Decision]] = None):
        self.events = events
        self.decisions = decisions


class SnapshotEvent:
    """ Class representing Snapshot Event. """

    def __init__(
        self,
        entity_id: str,
        uuid: str,
        key: str,
        timestamp: int,
        revenue: Optional[Integral] = None,
        value: Any = None,
        tags: Optional[EventTags] = None
    ):
        self.entity_id = entity_id
        self.uuid = uuid
        self.key = key
        self.timestamp = timestamp
        self.revenue = revenue
        self.value = value
        self.tags = tags


class Visitor:
    """ Class representing Visitor. """

    def __init__(self, snapshots: list[Snapshot], attributes: list[VisitorAttribute], visitor_id: str):
        self.snapshots = snapshots
        self.attributes = attributes
        self.visitor_id = visitor_id


class VisitorAttribute:
    """ Class representing Visitor Attribute. """

    def __init__(self, entity_id: str, key: str, attribute_type: str, value: Any):
        self.entity_id = entity_id
        self.key = key
        self.type = attribute_type
        self.value = value
