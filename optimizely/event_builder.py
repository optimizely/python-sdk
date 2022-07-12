# Copyright 2016-2019, 2022, Optimizely
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
import time
from typing import TYPE_CHECKING, Any, Optional
import uuid
from sys import version_info

from . import version
from .helpers import enums
from .helpers import event_tag_utils
from .helpers import validator

if version_info < (3, 8):
    from typing_extensions import Final, Literal
else:
    from typing import Final, Literal  # type: ignore

if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from .entities import Experiment
    from .optimizely_user_context import UserAttributes
    from .project_config import ProjectConfig


class Event:
    """ Representation of an event which can be sent to the Optimizely logging endpoint. """

    def __init__(
        self,
        url: str,
        params: dict[str, Any],
        http_verb: Optional[Literal['POST', 'GET']] = None,
        headers: Optional[dict[str, str]] = None
    ):
        self.url = url
        self.params = params
        self.http_verb = http_verb or 'GET'
        self.headers = headers


class EventBuilder:
    """ Class which encapsulates methods to build events for tracking
  impressions and conversions using the new V3 event API (batch). """

    EVENTS_URL: Final = 'https://logx.optimizely.com/v1/events'
    HTTP_VERB: Final = 'POST'
    HTTP_HEADERS: Final = {'Content-Type': 'application/json'}

    class EventParams:
        ACCOUNT_ID: Final = 'account_id'
        PROJECT_ID: Final = 'project_id'
        EXPERIMENT_ID: Final = 'experiment_id'
        CAMPAIGN_ID: Final = 'campaign_id'
        VARIATION_ID: Final = 'variation_id'
        END_USER_ID: Final = 'visitor_id'
        ENRICH_DECISIONS: Final = 'enrich_decisions'
        EVENTS: Final = 'events'
        EVENT_ID: Final = 'entity_id'
        ATTRIBUTES: Final = 'attributes'
        DECISIONS: Final = 'decisions'
        TIME: Final = 'timestamp'
        KEY: Final = 'key'
        TAGS: Final = 'tags'
        UUID: Final = 'uuid'
        USERS: Final = 'visitors'
        SNAPSHOTS: Final = 'snapshots'
        SOURCE_SDK_TYPE: Final = 'client_name'
        SOURCE_SDK_VERSION: Final = 'client_version'
        CUSTOM: Final = 'custom'
        ANONYMIZE_IP: Final = 'anonymize_ip'
        REVISION: Final = 'revision'

    def _get_attributes_data(
        self, project_config: ProjectConfig, attributes: UserAttributes
    ) -> list[dict[str, Any]]:
        """ Get attribute(s) information.

    Args:
      project_config: Instance of ProjectConfig.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      List consisting of valid attributes for the user. Empty otherwise.
    """

        params = []

        if isinstance(attributes, dict):
            for attribute_key in attributes.keys():
                attribute_value = attributes.get(attribute_key)
                # Omit attribute values that are not supported by the log endpoint.
                if validator.is_attribute_valid(attribute_key, attribute_value):
                    attribute_id = project_config.get_attribute_id(attribute_key)
                    if attribute_id:
                        params.append(
                            {
                                'entity_id': attribute_id,
                                'key': attribute_key,
                                'type': self.EventParams.CUSTOM,
                                'value': attribute_value,
                            }
                        )

        # Append Bot Filtering Attribute
        bot_filtering_value = project_config.get_bot_filtering_value()
        if isinstance(bot_filtering_value, bool):
            params.append(
                {
                    'entity_id': enums.ControlAttributes.BOT_FILTERING,
                    'key': enums.ControlAttributes.BOT_FILTERING,
                    'type': self.EventParams.CUSTOM,
                    'value': bot_filtering_value,
                }
            )

        return params

    def _get_time(self) -> int:
        """ Get time in milliseconds to be added.

    Returns:
      int Current time in milliseconds.
    """

        return int(round(time.time() * 1000))

    def _get_common_params(
        self, project_config: ProjectConfig, user_id: str, attributes: UserAttributes
    ) -> dict[str, Any]:
        """ Get params which are used same in both conversion and impression events.

    Args:
      project_config: Instance of ProjectConfig.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
     Dict consisting of parameters common to both impression and conversion events.
    """
        common_params: dict[str, Any] = {
            self.EventParams.PROJECT_ID: project_config.get_project_id(),
            self.EventParams.ACCOUNT_ID: project_config.get_account_id(),
        }

        visitor = {
            self.EventParams.END_USER_ID: user_id,
            self.EventParams.SNAPSHOTS: [],
        }

        common_params[self.EventParams.USERS] = []
        common_params[self.EventParams.USERS].append(visitor)
        common_params[self.EventParams.USERS][0][self.EventParams.ATTRIBUTES] = self._get_attributes_data(
            project_config, attributes
        )

        common_params[self.EventParams.SOURCE_SDK_TYPE] = 'python-sdk'
        common_params[self.EventParams.ENRICH_DECISIONS] = True
        common_params[self.EventParams.SOURCE_SDK_VERSION] = version.__version__
        common_params[self.EventParams.ANONYMIZE_IP] = project_config.get_anonymize_ip_value()
        common_params[self.EventParams.REVISION] = project_config.get_revision()

        return common_params

    def _get_required_params_for_impression(
        self, experiment: Experiment, variation_id: str
    ) -> dict[str, list[dict[str, str | int]]]:
        """ Get parameters that are required for the impression event to register.

    Args:
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.

    Returns:
      Dict consisting of decisions and events info for impression event.
    """
        snapshot: dict[str, list[dict[str, str | int]]] = {}

        snapshot[self.EventParams.DECISIONS] = [
            {
                self.EventParams.EXPERIMENT_ID: experiment.id,
                self.EventParams.VARIATION_ID: variation_id,
                self.EventParams.CAMPAIGN_ID: experiment.layerId,
            }
        ]

        snapshot[self.EventParams.EVENTS] = [
            {
                self.EventParams.EVENT_ID: experiment.layerId,
                self.EventParams.TIME: self._get_time(),
                self.EventParams.KEY: 'campaign_activated',
                self.EventParams.UUID: str(uuid.uuid4()),
            }
        ]

        return snapshot

    def _get_required_params_for_conversion(
        self, project_config: ProjectConfig, event_key: str, event_tags: event_tag_utils.EventTags
    ) -> dict[str, list[dict[str, Any]]]:
        """ Get parameters that are required for the conversion event to register.

    Args:
      project_config: Instance of ProjectConfig.
      event_key: Key representing the event which needs to be recorded.
      event_tags: Dict representing metadata associated with the event.

    Returns:
      Dict consisting of the decisions and events info for conversion event.
    """
        snapshot = {}
        event = project_config.get_event(event_key)

        event_dict: dict[str, Any] = {
            self.EventParams.EVENT_ID: event.id if event else None,
            self.EventParams.TIME: self._get_time(),
            self.EventParams.KEY: event_key,
            self.EventParams.UUID: str(uuid.uuid4()),
        }

        if event_tags:
            revenue_value = event_tag_utils.get_revenue_value(event_tags)
            if revenue_value is not None:
                event_dict[event_tag_utils.REVENUE_METRIC_TYPE] = revenue_value

            numeric_value = event_tag_utils.get_numeric_value(event_tags, project_config.logger)
            if numeric_value is not None:
                event_dict[event_tag_utils.NUMERIC_METRIC_TYPE] = numeric_value

            if len(event_tags) > 0:
                event_dict[self.EventParams.TAGS] = event_tags

        snapshot[self.EventParams.EVENTS] = [event_dict]
        return snapshot

    def create_impression_event(
        self, project_config: ProjectConfig, experiment: Experiment,
        variation_id: str, user_id: str, attributes: UserAttributes
    ) -> Event:
        """ Create impression Event to be sent to the logging endpoint.

    Args:
      project_config: Instance of ProjectConfig.
      experiment: Experiment for which impression needs to be recorded.
      variation_id: ID for variation which would be presented to user.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Event object encapsulating the impression event.
    """

        params = self._get_common_params(project_config, user_id, attributes)
        impression_params = self._get_required_params_for_impression(experiment, variation_id)

        params[self.EventParams.USERS][0][self.EventParams.SNAPSHOTS].append(impression_params)

        return Event(self.EVENTS_URL, params, http_verb=self.HTTP_VERB, headers=self.HTTP_HEADERS)

    def create_conversion_event(
        self, project_config: ProjectConfig, event_key: str,
        user_id: str, attributes: UserAttributes, event_tags: event_tag_utils.EventTags
    ) -> Event:
        """ Create conversion Event to be sent to the logging endpoint.

    Args:
      project_config: Instance of ProjectConfig.
      event_key: Key representing the event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing user attributes and values.
      event_tags: Dict representing metadata associated with the event.

    Returns:
      Event object encapsulating the conversion event.
    """

        params = self._get_common_params(project_config, user_id, attributes)
        conversion_params = self._get_required_params_for_conversion(project_config, event_key, event_tags)

        params[self.EventParams.USERS][0][self.EventParams.SNAPSHOTS].append(conversion_params)
        return Event(self.EVENTS_URL, params, http_verb=self.HTTP_VERB, headers=self.HTTP_HEADERS)
