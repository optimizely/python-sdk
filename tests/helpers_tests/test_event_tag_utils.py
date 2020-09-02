# Copyright 2017, Optimizely
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

import sys
import unittest


from optimizely.helpers import event_tag_utils
from optimizely.logger import NoOpLogger


class EventTagUtilsTest(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        self.logger = NoOpLogger()

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
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': None}))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': 0.5}))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': '65536'}))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': True}))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': False}))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': [1, 2, 3]}))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': {'a', 'b', 'c'}}))

    def test_get_revenue_value__revenue_tag(self):
        """ Test that correct revenue value is returned. """
        self.assertEqual(0, event_tag_utils.get_revenue_value({'revenue': 0}))
        self.assertEqual(65536, event_tag_utils.get_revenue_value({'revenue': 65536}))
        self.assertEqual(
            9223372036854775807, event_tag_utils.get_revenue_value({'revenue': 9223372036854775807}),
        )

    def test_get_numeric_metric__invalid_args(self):
        """ Test that numeric value is not returned for invalid arguments. """
        self.assertIsNone(event_tag_utils.get_numeric_value(None))
        self.assertIsNone(event_tag_utils.get_numeric_value(0.5))
        self.assertIsNone(event_tag_utils.get_numeric_value(65536))
        self.assertIsNone(event_tag_utils.get_numeric_value(9223372036854775807))
        self.assertIsNone(event_tag_utils.get_numeric_value('9223372036854775807'))
        self.assertIsNone(event_tag_utils.get_numeric_value(True))
        self.assertIsNone(event_tag_utils.get_numeric_value(False))

    def test_get_numeric_metric__no_value_tag(self):
        """ Test that numeric value is not returned when there's no numeric event tag. """
        self.assertIsNone(event_tag_utils.get_numeric_value([]))
        self.assertIsNone(event_tag_utils.get_numeric_value({}))
        self.assertIsNone(event_tag_utils.get_numeric_value({'non-value': 42}))

    def test_get_numeric_metric__invalid_value_tag(self):
        """ Test that numeric value is not returned when value event tag has invalid data type. """
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': None}))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': True}))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': False}))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': [1, 2, 3]}))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': {'a', 'b', 'c'}}))

    def test_get_numeric_metric__value_tag(self):
        """ Test that the correct numeric value is returned. """

        # An integer should be cast to a float
        self.assertEqual(
            12345.0, event_tag_utils.get_numeric_value({'value': 12345}),
        )

        # A string should be cast to a float
        self.assertEqual(
            12345.0, event_tag_utils.get_numeric_value({'value': '12345'}, self.logger),
        )

        # Valid float values
        some_float = 1.2345
        self.assertEqual(
            some_float, event_tag_utils.get_numeric_value({'value': some_float}, self.logger),
        )

        max_float = sys.float_info.max
        self.assertEqual(
            max_float, event_tag_utils.get_numeric_value({'value': max_float}, self.logger),
        )

        min_float = sys.float_info.min
        self.assertEqual(
            min_float, event_tag_utils.get_numeric_value({'value': min_float}, self.logger),
        )

        # Invalid values
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': False}, self.logger))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': None}, self.logger))

        numeric_value_nan = event_tag_utils.get_numeric_value({'value': float('nan')}, self.logger)
        self.assertIsNone(numeric_value_nan, 'nan numeric value is {}'.format(numeric_value_nan))

        numeric_value_array = event_tag_utils.get_numeric_value({'value': []}, self.logger)
        self.assertIsNone(numeric_value_array, 'Array numeric value is {}'.format(numeric_value_array))

        numeric_value_dict = event_tag_utils.get_numeric_value({'value': []}, self.logger)
        self.assertIsNone(numeric_value_dict, 'Dict numeric value is {}'.format(numeric_value_dict))

        numeric_value_none = event_tag_utils.get_numeric_value({'value': None}, self.logger)
        self.assertIsNone(numeric_value_none, 'None numeric value is {}'.format(numeric_value_none))

        numeric_value_invalid_literal = event_tag_utils.get_numeric_value(
            {'value': '1,234'}, self.logger
        )
        self.assertIsNone(
            numeric_value_invalid_literal, 'Invalid string literal value is {}'.format(numeric_value_invalid_literal),
        )

        numeric_value_overflow = event_tag_utils.get_numeric_value(
            {'value': sys.float_info.max * 10}, self.logger
        )
        self.assertIsNone(
            numeric_value_overflow, 'Max numeric value is {}'.format(numeric_value_overflow),
        )

        numeric_value_inf = event_tag_utils.get_numeric_value({'value': float('inf')}, self.logger)
        self.assertIsNone(numeric_value_inf, 'Infinity numeric value is {}'.format(numeric_value_inf))

        numeric_value_neg_inf = event_tag_utils.get_numeric_value(
            {'value': float('-inf')}, self.logger
        )
        self.assertIsNone(
            numeric_value_neg_inf, 'Negative infinity numeric value is {}'.format(numeric_value_neg_inf),
        )

        self.assertEqual(
            0.0, event_tag_utils.get_numeric_value({'value': 0.0}, self.logger),
        )
