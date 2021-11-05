#    Copyright 2021, Optimizely and contributors
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

from . import logger
from .decision.optimizely_decision_message import OptimizelyDecisionMessage
from .helpers import enums


class OptimizelyUserContext(object):
    """
    Representation of an Optimizely User Context using which APIs are to be called.
    """

    def __init__(self, optimizely_client, user_id, user_attributes=None):
        """ Create an instance of the Optimizely User Context.

        Args:
          optimizely_client: client used when calling decisions for this user context
          user_id: user id of this user context
          user_attributes: user attributes to use for this user context

        Returns:
          UserContext instance
        """

        self.client = optimizely_client
        self.user_id = user_id

        if not isinstance(user_attributes, dict):
            user_attributes = {}

        self._user_attributes = user_attributes.copy() if user_attributes else {}
        self.lock = threading.Lock()
        self.forced_decisions = {}
        self.log = logger.SimpleLogger(min_level=enums.LogLevels.INFO)

    # decision context
    class OptimizelyDecisionContext(object):
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

        user_context = OptimizelyUserContext(self.client, self.user_id, self.get_user_attributes())

        if self.forced_decisions:
            user_context.forced_decisions = copy.deepcopy(self.forced_decisions)

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

    def set_forced_decision(self, OptimizelyDecisionContext, OptimizelyForcedDecision):
        """
        Sets the forced decision for a given decision context.

        Args:
            OptimizelyDecisionContext: a decision context.
            OptimizelyForcedDecision: a forced decision.

        Returns:
            True if the forced decision has been set successfully.
        """
        config = self.client.get_optimizely_config()

        if self.client is None or config is None:
            self.log.logger.error(OptimizelyDecisionMessage.SDK_NOT_READY)
            return False

        context = OptimizelyDecisionContext
        decision = OptimizelyForcedDecision

        self.forced_decisions[context] = decision

        return True

    def get_forced_decision(self, OptimizelyDecisionContext):
        """
        Gets the forced decision (variation key) for a given decision context.

        Args:
            OptimizelyDecisionContext: a decision context.

        Returns:
            A variation key or None if forced decisions are not set for the parameters.
        """
        config = self.client.get_optimizely_config()

        if self.client is None or config is None:
            self.log.logger.error(OptimizelyDecisionMessage.SDK_NOT_READY)
            return None

        forced_decision_key = self.find_forced_decision(OptimizelyDecisionContext)

        return forced_decision_key if forced_decision_key else None

    def remove_forced_decision(self, OptimizelyDecisionContext):
        """
        Removes the forced decision for a given flag and an optional rule.

        Args:
            OptimizelyDecisionContext: a decision context.

        Returns:
            Returns: true if the forced decision has been removed successfully.
        """
        config = self.client.get_optimizely_config()

        if self.client is None or config is None:
            self.log.logger.error(OptimizelyDecisionMessage.SDK_NOT_READY)
            return False

        if self.forced_decisions.get(OptimizelyDecisionContext):
            del self.forced_decisions[OptimizelyDecisionContext]
            return True

        return False

    def remove_all_forced_decisions(self):
        """
        Removes all forced decisions bound to this user context.

        Returns:
            True if forced decisions have been removed successfully.
        """
        config = self.client.get_optimizely_config()

        if self.client is None or config is None:
            self.log.logger.error(OptimizelyDecisionMessage.SDK_NOT_READY)
            return False

        self.forced_decisions.clear()

        return True

    def find_forced_decision(self, OptimizelyDecisionContext):

        if not self.forced_decisions:
            return None

        # must allow None to be returned for the Flags only case
        return self.forced_decisions.get(OptimizelyDecisionContext)

    def find_validated_forced_decision(self, OptimizelyDecisionContext, options):

        reasons = []

        forced_decision_response = self.find_forced_decision(OptimizelyDecisionContext)

        flag_key = OptimizelyDecisionContext.flag_key
        rule_key = OptimizelyDecisionContext.rule_key

        if forced_decision_response:
            variation = self.client.get_flag_variation_by_key(flag_key, forced_decision_response.variation_key)
            if variation:
                if rule_key:
                    user_has_forced_decision = enums.ForcedDecisionLogs \
                        .USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED.format(forced_decision_response.variation_key,
                                                                             flag_key,
                                                                             rule_key,
                                                                             self.user_id)

                else:
                    user_has_forced_decision = enums.ForcedDecisionLogs \
                        .USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED.format(forced_decision_response.variation_key,
                                                                                flag_key,
                                                                                self.user_id)

                reasons.append(user_has_forced_decision)
                self.log.logger.debug(user_has_forced_decision)

            return variation, reasons

        else:
            if rule_key:
                user_has_forced_decision_but_invalid = enums.ForcedDecisionLogs \
                    .USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED_BUT_INVALID.format(flag_key,
                                                                                     rule_key,
                                                                                     self.user_id)
            else:
                user_has_forced_decision_but_invalid = enums.ForcedDecisionLogs \
                    .USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED_BUT_INVALID.format(flag_key, self.user_id)

            reasons.append(user_has_forced_decision_but_invalid)
            self.log.logger.debug(user_has_forced_decision_but_invalid)

            return None, reasons
