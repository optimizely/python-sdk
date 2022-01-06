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

import copy
import threading


class OptimizelyUserContext(object):
    """
    Representation of an Optimizely User Context using which APIs are to be called.
    """

    def __init__(self, optimizely_client, logger, user_id, user_attributes=None):
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

        if not isinstance(user_attributes, dict):
            user_attributes = {}

        self._user_attributes = user_attributes.copy() if user_attributes else {}
        self.lock = threading.Lock()
        self.forced_decisions_map = {}

    # decision context
    class OptimizelyDecisionContext(object):
        """ Using class with attributes here instead of namedtuple because
            class is extensible, it's easy to add another attribute if we wanted
            to extend decision context.
        """
        def __init__(self, flag_key, rule_key=None):
            self.flag_key = flag_key
            self.rule_key = rule_key

        def __hash__(self):
            return hash((self.flag_key, self.rule_key))

        def __eq__(self, other):
            return (self.flag_key, self.rule_key) == (other.flag_key, other.rule_key)

    # forced decision
    class OptimizelyForcedDecision(object):
        def __init__(self, variation_key):
            self.variation_key = variation_key

    def _clone(self):
        if not self.client:
            return None

        user_context = OptimizelyUserContext(self.client, self.logger, self.user_id, self.get_user_attributes())

        with self.lock:
            if self.forced_decisions_map:
                user_context.forced_decisions_map = copy.deepcopy(self.forced_decisions_map)

        return user_context

    def get_user_attributes(self):
        with self.lock:
            return self._user_attributes.copy()

    def set_attribute(self, attribute_key, attribute_value):
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

    def decide(self, key, options=None):
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

    def decide_for_keys(self, keys, options=None):
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

    def decide_all(self, options=None):
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

    def track_event(self, event_key, event_tags=None):
        return self.client.track(event_key, self.user_id, self.get_user_attributes(), event_tags)

    def as_json(self):
        return {
            'user_id': self.user_id,
            'attributes': self.get_user_attributes(),
        }

    def set_forced_decision(self, decision_context, decision):
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

    def get_forced_decision(self, decision_context):
        """
        Gets the forced decision (variation key) for a given decision context.

        Args:
            decision_context: a decision context.

        Returns:
            A forced_decision or None if forced decisions are not set for the parameters.
        """
        forced_decision = self.find_forced_decision(decision_context)
        return forced_decision

    def remove_forced_decision(self, decision_context):
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

    def remove_all_forced_decisions(self):
        """
        Removes all forced decisions bound to this user context.

        Returns:
            True if forced decisions have been removed successfully.
        """
        with self.lock:
            self.forced_decisions_map.clear()

        return True

    def find_forced_decision(self, decision_context):
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
