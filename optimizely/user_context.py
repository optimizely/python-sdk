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


class UserContext(object):
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
        self.user_attributes = user_attributes.copy() if user_attributes else {}

    def set_attribute(self, attribute_key, attribute_value):
        """
        sets a attribute by key for this user context.
        Args:
          attribute_key: key to use for attribute
          attribute_value: attribute value

        Returns:
        None
        """
        self.user_attributes[attribute_key] = attribute_value

    def decide(self, key, options=None):
        """
        Call decide on contained Optimizely object
        Args:
          key: feature key
          options: array of DecisionOption

        Returns:
            Decision object
        """
        return self.client.decide(self, key, options)

    def decide_for_keys(self, keys, options=None):
        """
        Call decide_for_keys on contained optimizely object
        Args:
          keys: array of feature keys
          options: array of DecisionOption

        Returns:
          Dictionary with feature_key keys and Decision object values
        """
        return self.client.decide_for_keys(self, keys, options)

    def decide_all(self, options=None):
        """
        Call decide_all on contained optimizely instance
        Args:
          options: Array of DecisionOption objects

        Returns:
          Dictionary with feature_key keys and Decision object values
        """
        return self.client.decide_all(self, options)

    def track_event(self, event_key, event_tags=None):
        return self.client.track(event_key, self.user_id, self.user_attributes, event_tags)

    def as_json(self):
        return {
            'user_id': self.user_id,
            'attributes': self.user_attributes,
        }
