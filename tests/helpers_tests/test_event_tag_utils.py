# Copyright 2017, Optimizely
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

from optimizely.helpers import event_tag_utils

class EventTagUtilsTest(unittest.TestCase):

  def test_get_revenue_value__invalid_args(self):
    """ Test that revenue value is not returned for invalid arguments. """
    self.assertIsNone(event_tag_utils.get_revenue_value(None))
    self.assertIsNone(event_tag_utils.get_revenue_value(0.5))
    self.assertIsNone(event_tag_utils.get_revenue_value(65536))
    self.assertIsNone(event_tag_utils.get_revenue_value(9223372036854775807))
    self.assertIsNone(event_tag_utils.get_revenue_value('9223372036854775807'))
    self.assertIsNone(event_tag_utils.get_revenue_value(True))
    self.assertIsNone(event_tag_utils.get_revenue_value(False))

  def test_get_revenue_value__no_revenue_tag(self):
    """ Test that revenue value is not returned when there's no revenue event tag. """
    self.assertIsNone(event_tag_utils.get_revenue_value([]))
    self.assertIsNone(event_tag_utils.get_revenue_value({}))
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': 42}))

  def test_get_revenue_value__invalid_revenue_tag(self):
    """ Test that revenue value is not returned when revenue event tag has invalid data type. """
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': None}))
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': 0.5}))
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': '65536'}))
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': True}))
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': False}))
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': [1, 2, 3]}))
    self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': {'a', 'b', 'c'}}))

  def test_get_revenue_value__revenue_tag(self):
    """ Test that correct revenue value is returned. """
    self.assertEqual(0, event_tag_utils.get_revenue_value({'revenue': 0}))
    self.assertEqual(65536, event_tag_utils.get_revenue_value({'revenue': 65536}))
    self.assertEqual(9223372036854775807, event_tag_utils.get_revenue_value({'revenue': 9223372036854775807}))
