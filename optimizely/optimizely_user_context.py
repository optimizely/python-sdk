#    Copyright 2021-2022, Optimizely and contributors
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
from __future__ import annotations
import copy
import threading
from typing import TYPE_CHECKING, Any, Optional, NewType, Dict

from optimizely.decision import optimizely_decision

if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from . import optimizely
    from optimizely.helpers.event_tag_utils import EventTags
    from .logger import Logger


# type for tracking user attributes (essentially a sub-type of dict)
UserAttributes = NewType('UserAttributes', Dict[str, Any])


class OptimizelyUserContext:
    """
    Representation of an Optimizely User Context using which APIs are to be called.
    """

    def __init__(
        self, optimizely_client: optimizely.Optimizely, logger: Logger,
        user_id: str, user_attributes: Optional[UserAttributes] = None
    ):
        """ Create an instance of the Optimizely User Context.

        Args:
          optimizely_client: client used when calling decisions for this user context
          logger: logger for logging
          user_id: user id of this user context
          user_attributes: user attributes to use for this user context

        Returns:
          UserContext instance
        """

        self.client = optimizely_client
        self.logger = logger
        self.user_id = user_id
        self._qualified_segments: list[str] = []

        if not isinstance(user_attributes, dict):
            user_attributes = UserAttributes({})

        self._user_attributes = UserAttributes(user_attributes.copy() if user_attributes else {})
        self.lock = threading.Lock()
        self.forced_decisions_map: dict[
            OptimizelyUserContext.OptimizelyDecisionContext,
            OptimizelyUserContext.OptimizelyForcedDecision
        ] = {}

    # decision context
    class OptimizelyDecisionContext:
        """ Using class with attributes here instead of namedtuple because
            class is extensible, it's easy to add another attribute if we wanted
            to extend decision context.
        """
        def __init__(self, flag_key: str, rule_key: Optional[str] = None):
            self.flag_key = flag_key
            self.rule_key = rule_key

        def __hash__(self) -> int:
            return hash((self.flag_key, self.rule_key))

        def __eq__(self, other: OptimizelyUserContext.OptimizelyDecisionContext) -> bool:  # type: ignore[override]
            return (self.flag_key, self.rule_key) == (other.flag_key, other.rule_key)

    # forced decision
    class OptimizelyForcedDecision:
        def __init__(self, variation_key: str):
            self.variation_key = variation_key

    def _clone(self) -> Optional[OptimizelyUserContext]:
        if not self.client:
            return None

        user_context = OptimizelyUserContext(self.client, self.logger, self.user_id, self.get_user_attributes())

        with self.lock:
            if self.forced_decisions_map:
                # makes sure forced_decisions_map is duplicated without any references
                user_context.forced_decisions_map = copy.deepcopy(self.forced_decisions_map)
            if self._qualified_segments:
                # no need to use deepcopy here as qualified_segments does not contain anything other than strings
                user_context._qualified_segments = self._qualified_segments.copy()

        return user_context

    def get_user_attributes(self) -> UserAttributes:
        with self.lock:
            return UserAttributes(self._user_attributes.copy())

    def set_attribute(self, attribute_key: str, attribute_value: Any) -> None:
        """
        sets a attribute by key for this user context.
        Args:
          attribute_key: key to use for attribute
          attribute_value: attribute value

        Returns:
        None
        """
        with self.lock:
            self._user_attributes[attribute_key] = attribute_value

    def decide(
        self, key: str, options: Optional[list[str]] = None
    ) -> optimizely_decision.OptimizelyDecision:
        """
        Call decide on contained Optimizely object
        Args:
          key: feature key
          options: array of DecisionOption

        Returns:
            Decision object
        """
        if isinstance(options, list):
            options = options[:]

        return self.client._decide(self._clone(), key, options)

    def decide_for_keys(
        self, keys: list[str], options: Optional[list[str]] = None
    ) -> dict[str, optimizely_decision.OptimizelyDecision]:
        """
        Call decide_for_keys on contained optimizely object
        Args:
          keys: array of feature keys
          options: array of DecisionOption

        Returns:
          Dictionary with feature_key keys and Decision object values
        """
        if isinstance(options, list):
            options = options[:]

        return self.client._decide_for_keys(self._clone(), keys, options)

    def decide_all(self, options: Optional[list[str]] = None) -> dict[str, optimizely_decision.OptimizelyDecision]:
        """
        Call decide_all on contained optimizely instance
        Args:
          options: Array of DecisionOption objects

        Returns:
          Dictionary with feature_key keys and Decision object values
        """
        if isinstance(options, list):
            options = options[:]

        return self.client._decide_all(self._clone(), options)

    def track_event(self, event_key: str, event_tags: Optional[EventTags] = None) -> None:
        return self.client.track(event_key, self.user_id, self.get_user_attributes(), event_tags)

    def as_json(self) -> dict[str, Any]:
        return {
            'user_id': self.user_id,
            'attributes': self.get_user_attributes(),
        }

    def set_forced_decision(
        self, decision_context: OptimizelyDecisionContext, decision: OptimizelyForcedDecision
    ) -> bool:
        """
        Sets the forced decision for a given decision context.

        Args:
            decision_context: a decision context.
            decision: a forced decision.

        Returns:
            True if the forced decision has been set successfully.
        """
        with self.lock:
            self.forced_decisions_map[decision_context] = decision

        return True

    def get_forced_decision(self, decision_context: OptimizelyDecisionContext) -> Optional[OptimizelyForcedDecision]:
        """
        Gets the forced decision (variation key) for a given decision context.

        Args:
            decision_context: a decision context.

        Returns:
            A forced_decision or None if forced decisions are not set for the parameters.
        """
        forced_decision = self.find_forced_decision(decision_context)
        return forced_decision

    def remove_forced_decision(self, decision_context: OptimizelyDecisionContext) -> bool:
        """
        Removes the forced decision for a given decision context.

        Args:
            decision_context: a decision context.

        Returns:
            Returns: true if the forced decision has been removed successfully.
        """
        with self.lock:
            if decision_context in self.forced_decisions_map:
                del self.forced_decisions_map[decision_context]
                return True

        return False

    def remove_all_forced_decisions(self) -> bool:
        """
        Removes all forced decisions bound to this user context.

        Returns:
            True if forced decisions have been removed successfully.
        """
        with self.lock:
            self.forced_decisions_map.clear()

        return True

    def find_forced_decision(self, decision_context: OptimizelyDecisionContext) -> Optional[OptimizelyForcedDecision]:
        """
        Gets forced decision from forced decision map.

        Args:
            decision_context: a decision context.

        Returns:
            Forced decision.
        """
        with self.lock:
            if not self.forced_decisions_map:
                return None

            # must allow None to be returned for the Flags only case
            return self.forced_decisions_map.get(decision_context)

    def is_qualified_for(self, segment: str) -> bool:
        """
        Checks is the provided segment is in the qualified_segments list.

        Args:
            segment: a segment name.

        Returns:
            Returns: true if the segment is in the qualified segments list.
        """
        with self.lock:
            return segment in self._qualified_segments

    def get_qualified_segments(self) -> list[str]:
        """
        Gets the qualified segments.

        Returns:
            A list of qualified segment names.
        """
        with self.lock:
            return self._qualified_segments.copy()

    def set_qualified_segments(self, segments: list[str]) -> None:
        """
        Replaces any qualified segments with the provided list of segments.

        Args:
            segments: a list of segment names.

        Returns:
            None.
        """
        with self.lock:
            self._qualified_segments = segments
