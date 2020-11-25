#    Copyright 2020, Optimizely and contributors
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
        TODO: call optimizely_clieint.decide
        Args:
          key:
          options:

        Returns:

        """

    def decide_for_keys(self, keys, options=None):
        """
        TODO: call optimizely_client.decide_for_keys
        Args:
          keys:
          options:

        Returns:

      """

    def decide_all(self, options=None):
        """
        TODO: call optimize_client.decide_all
        Args:
          options:

        Returns:

        """

    def track_event(self, event_key, event_tags=None):
        self.optimizely_client.track(event_key, self.user_id, self.user_attributes, event_tags)
