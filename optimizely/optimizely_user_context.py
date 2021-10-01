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
from collections import namedtuple

from optimizely import logger
from .decision.optimizely_decision_message import OptimizelyDecisionMessage
from .helpers import enums


class OptimizelyUserContext(object):
    """
    Representation of an Optimizely User Context using which APIs are to be called.
    """
    forced_decisions = []

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

    log = logger.SimpleLogger(min_level=enums.LogLevels.INFO)

    ForcedDecision = namedtuple('ForcedDecision', 'flag_key rule_key variation_key')

    def _clone(self):
        if not self.client:
            return None

        user_context = OptimizelyUserContext(self.client, self.user_id, self.get_user_attributes())

        if len(self.forced_decisions) > 0:
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

    def set_forced_decision(self, flag_key, rule_key, variation_key):
        """
        Sets the forced decision (variation key) for a given flag and an optional rule.

        Args:
            flag_key: A flag key.
            rule_key: An experiment or delivery rule key (optional).
            variation_key: A variation key.

        Returns:
            True if the forced decision has been set successfully.
        """
        config = self.client.get_optimizely_config()

        if self.client is None or config is None:
            self.log.logger.error(OptimizelyDecisionMessage.SDK_NOT_READY)
            return False

        for decision in self.forced_decisions:
            if decision.flag_key == flag_key and decision.rule_key == rule_key:
                self.forced_decisions.variation_key = variation_key
            return True

        self.forced_decisions.append(self.ForcedDecision(flag_key, rule_key, variation_key))

        return True

    def get_forced_decision(self, flag_key, rule_key):
        """
        Sets the forced decision (variation key) for a given flag and an optional rule.

        Args:
            flag_key: A flag key.
            rule_key: An experiment or delivery rule key (optional).

        Returns:
            A variation key or None if forced decisions are not set for the parameters.
        """
        config = self.client.get_optimizely_config()

        if self.client is None or config is None:
            self.log.logger.error(OptimizelyDecisionMessage.SDK_NOT_READY)
            return None

        return self.find_forced_decision(flag_key, rule_key)

    def remove_forced_decision(self, flag_key, rule_key):
        """
        Removes the forced decision for a given flag and an optional rule.

        Args:
            flag_key: A flag key.
            rule_key: An experiment or delivery rule key (optional).

        Returns:
            Returns: true if the forced decision has been removed successfully.
        """
        config = self.client.get_optimizely_config()

        if self.client is None or config is None:
            self.log.logger.error(OptimizelyDecisionMessage.SDK_NOT_READY)
            return False

        # remove() built-in function by default removes the first occurrence of the element that meets the condition
        for decision in self.forced_decisions:
            if decision.flag_key == flag_key and decision.rule_key == rule_key:
                self.forced_decisions.remove(decision)
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

    def find_forced_decision(self, flag_key, rule_key):

        if len(self.forced_decisions) == 0:
            return None

        variation = ""
        for decision in self.forced_decisions:
            if decision.flag_key == flag_key and decision.rule_key == rule_key:
                variation = decision.variation_key
        return variation

    def find_validated_forced_decision(self, flag_key, rule_key, options):

        reasons = []

        variation_key = self.find_forced_decision(flag_key, rule_key)

        if variation_key:
            variation = self.client.get_flag_variation_by_key(flag_key, variation_key)
            if rule_key:
                user_has_forced_decision = enums.ForcedDecisionNotificationTypes.USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED.format(
                    variation_key,
                    flag_key,
                    rule_key,
                    self.user_id)

            else:
                user_has_forced_decision = enums.ForcedDecisionNotificationTypes.USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED.format(
                    variation_key,
                    flag_key,
                    self.user_id
                )

            reasons.append(user_has_forced_decision)
            self.log.logger.info(user_has_forced_decision)

            return variation, reasons

        else:
            if rule_key:
                user_has_forced_decision_but_invalid = enums.ForcedDecisionNotificationTypes.USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED_BUT_INVALID.format(
                    flag_key,
                    rule_key,
                    self.user_id
                )
            else:
                user_has_forced_decision_but_invalid = enums.ForcedDecisionNotificationTypes.USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED_BUT_INVALID.format(
                    flag_key,
                    self.user_id
                )

            reasons.append(user_has_forced_decision_but_invalid)
            self.log.logger.info(user_has_forced_decision_but_invalid)

        return None, reasons
