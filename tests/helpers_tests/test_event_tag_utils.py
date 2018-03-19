# Copyright 2017-2018, Optimizely
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

import mock
import sys
import unittest
from optimizely import logger

from optimizely.helpers import enums
from optimizely.helpers import event_tag_utils


class EventTagUtilsTest(unittest.TestCase):

  def test_get_revenue_value__undefined_args(self):
    """ Test that revenue value is not returned for undefined arguments. """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value(None, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(enums.LogLevels.DEBUG, 'Event tags is undefined.')

  def test_get_revenue_value__invalid_args(self):
    """ Test that revenue value is not returned for invalid arguments. """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value(0.5, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value(65536, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value(9223372036854775807, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value('9223372036854775807', logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value(True, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value(False, logger=logger.SimpleLogger()))
    mock_logger.assert_called_with(enums.LogLevels.DEBUG, 'Event tags is not a dict.')
    self.assertEqual(6, mock_logger.call_count)

  def test_get_revenue_value__no_revenue_tag(self):
    """ Test that revenue value is not returned when there's no revenue event tag. """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value([], logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value({}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value({'non-revenue': 42}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_with(enums.LogLevels.DEBUG, 'The revenue key is not defined in the event tags.')
    self.assertEqual(3, mock_logger.call_count)

  def test_get_revenue_value__boolean_revenue_tag(self):
    """ Test that revenue value is not returned when revenue event tag has boolean value. """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': True}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(
        enums.LogLevels.WARNING,
        'Revenue value is not an integer or float or a string.'
    )

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': False}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(
        enums.LogLevels.WARNING,
        'Revenue value is not an integer or float or a string.'
    )

  def test_get_revenue_value__invalid_revenue_tag(self):
    """ Test that revenue value is not returned when revenue event tag has invalid data type. """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': None}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': [1, 2, 3]}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': {'a', 'b', 'c'}}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_with(
        enums.LogLevels.WARNING,
        'Revenue value is not an integer or float or a string.'
    )
    self.assertEqual(3, mock_logger.call_count)

  def test_get_revenue_value__revenue_tag_invalid_string(self):
    """ Test that revenue value is not returned when revenue event tag has invalid string value. """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': 'string'}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(enums.LogLevels.WARNING, 'Revenue value is not a numeric string.')

  def test_get_revenue_value__revenue_tag_invalid_numeric(self):
    """ Test that revenue value is not returned when revenue event tag has invalid numeric value """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': 0.5}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_revenue_value({'revenue': '0.5'}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_with(enums.LogLevels.WARNING, 'Failed to parse revenue value "0.5" from event tags.')
    self.assertEqual(2, mock_logger.call_count)

  def test_get_revenue_value__revenue_tag_valid_numeric(self):
    """ Test that correct revenue value is returned when revenue event tag has valid numeric value """
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(65536, event_tag_utils.get_revenue_value({'revenue': 65536.0}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(enums.LogLevels.INFO, 'Parsed revenue value "65536" from event tags.')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(65536, event_tag_utils.get_revenue_value({'revenue': '65536.0'}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(enums.LogLevels.INFO, 'Parsed revenue value "65536" from event tags.')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(65536, event_tag_utils.get_revenue_value({'revenue': '65536'}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(enums.LogLevels.INFO, 'Parsed revenue value "65536" from event tags.')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(65536, event_tag_utils.get_revenue_value({'revenue': 65536}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(enums.LogLevels.INFO, 'Parsed revenue value "65536" from event tags.')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(
            9223372036854775807,
            event_tag_utils.get_revenue_value({'revenue': 9223372036854775807}, logger=logger.SimpleLogger())
        )
    mock_logger.assert_called_once_with(
        enums.LogLevels.INFO,
        'Parsed revenue value "9223372036854775807" from event tags.'
    )
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(0, event_tag_utils.get_revenue_value({'revenue': 0.0}, logger=logger.SimpleLogger()))
        self.assertEqual(0, event_tag_utils.get_revenue_value({'revenue': '0.0'}, logger=logger.SimpleLogger()))
        self.assertEqual(0, event_tag_utils.get_revenue_value({'revenue': 0}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_with(enums.LogLevels.INFO, 'Parsed revenue value "0" from event tags.')
    self.assertEqual(3, mock_logger.call_count)

  def test_get_numeric_metric__invalid_args(self):
    """ Test that numeric value is not returned for invalid arguments. """
    call1 = mock.call(enums.LogLevels.DEBUG, 'Event tags is undefined.')
    call2 = mock.call(enums.LogLevels.DEBUG, 'Event tags is not a dictionary.')
    call3 = mock.call(
      enums.LogLevels.WARNING,
      'The provided numeric metric value None is in an invalid format and will not be sent to results.'
    )

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_numeric_value(None, logger=logger.SimpleLogger()))
    mock_logger.assert_has_calls([call1, call3])

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_numeric_value(0.5, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value(65536, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value(65536, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value(9223372036854775807, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value('9223372036854775807', logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value(True, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value(False, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value([], logger=logger.SimpleLogger()))
    mock_logger.assert_has_calls(
        [call2, call3, call2, call3, call2, call3, call2, call3, call2, call3, call2, call3, call2, call3, call2, call3]
    )

  def test_get_numeric_metric__no_value_tag(self):
    """ Test that numeric value is not returned when there's no numeric event tag. """
    call1 = mock.call(enums.LogLevels.DEBUG, 'The numeric metric key is not in event tags.')
    call2 = mock.call(
      enums.LogLevels.WARNING,
      'The provided numeric metric value None is in an invalid format and will not be sent to results.'
    )

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_numeric_value({}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value({'non-value': 42}, logger=logger.SimpleLogger()))
    mock_logger.assert_has_calls([call1, call2, call1, call2])

  def test_get_numeric_metric__invalid_value_tag(self):
    """ Test that numeric value is not returned when value event tag has invalid data type. """
    call1 = mock.call(enums.LogLevels.DEBUG, 'Numeric metric value is not in integer, float, or string form.')
    call2 = mock.call(
        enums.LogLevels.WARNING,
            'The provided numeric metric value None is in an invalid format and will not be sent to results.'
        )
    call3 = mock.call(enums.LogLevels.DEBUG, 'Provided numeric value is a boolean, which is an invalid format.')
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': None}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': True}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': False}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': [1, 2, 3]}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': {'a', 'b', 'c'}}, logger=logger.SimpleLogger()))
    mock_logger.assert_has_calls([call1, call2, call3, call2, call3, call2, call1, call2, call1, call2])

  def test_get_numeric_metric__value_tag(self):
    """ Test that the correct numeric value is returned. """

    # An integer should be cast to a float
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(12345.0, event_tag_utils.get_numeric_value({'value': 12345}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(
        enums.LogLevels.INFO,
        'The numeric metric value 12345.0 will be sent to results.'
    )

    # A string should be cast to a float
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(12345.0, event_tag_utils.get_numeric_value({'value': '12345'}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(
        enums.LogLevels.INFO,
        'The numeric metric value 12345.0 will be sent to results.'
    )
    # Valid float values
    some_float = 1.2345
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(
            some_float,
            event_tag_utils.get_numeric_value({'value': some_float}, logger=logger.SimpleLogger())
        )
    mock_logger.assert_called_once_with(
        enums.LogLevels.INFO,
        'The numeric metric value 1.2345 will be sent to results.'
    )

    max_float = sys.float_info.max
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(
            max_float,
            event_tag_utils.get_numeric_value({'value': max_float}, logger=logger.SimpleLogger())
        )
    mock_logger.assert_called_once_with(enums.LogLevels.INFO,
                 'The numeric metric value {} will be sent to results.'
                 .format(max_float))

    min_float = sys.float_info.min
    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(
            min_float,
            event_tag_utils.get_numeric_value({'value': min_float}, logger=logger.SimpleLogger())
        )
    mock_logger.assert_called_once_with(enums.LogLevels.INFO,
                 'The numeric metric value {} will be sent to results.'
                 .format(min_float))

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertEqual(0.0, event_tag_utils.get_numeric_value({'value': 0.0}, logger=logger.SimpleLogger()))
    mock_logger.assert_called_once_with(enums.LogLevels.INFO, 'The numeric metric value 0.0 will be sent to results.')

    # Invalid values

    call1 = mock.call(enums.LogLevels.DEBUG, 'Provided numeric value is a boolean, which is an invalid format.')
    call2 = mock.call(
      enums.LogLevels.WARNING,
      'The provided numeric metric value None is in an invalid format and will not be sent to results.'
    )
    call3 = mock.call(enums.LogLevels.DEBUG, 'Numeric metric value is not in integer, float, or string form.')
    call4 = mock.call(enums.LogLevels.DEBUG, 'Provided numeric value inf is in an invalid format.')
    call5 = mock.call(enums.LogLevels.DEBUG, 'Value error while casting numeric metric value to a float.')
    call6 = mock.call(enums.LogLevels.DEBUG, 'Provided numeric value nan is in an invalid format.')
    call7 = mock.call(enums.LogLevels.DEBUG, 'Provided numeric value -inf is in an invalid format.')

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logger:
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': False}, logger=logger.SimpleLogger()))
        self.assertIsNone(event_tag_utils.get_numeric_value({'value': None}, logger=logger.SimpleLogger()))
        numeric_value_nan = event_tag_utils.get_numeric_value({'value': float('nan')}, logger=logger.SimpleLogger())
        self.assertIsNone(numeric_value_nan, 'nan numeric value is {}'.format(numeric_value_nan))

        numeric_value_array = event_tag_utils.get_numeric_value({'value': []}, logger=logger.SimpleLogger())
        self.assertIsNone(numeric_value_array, 'Array numeric value is {}'.format(numeric_value_array))

        numeric_value_dict = event_tag_utils.get_numeric_value({'value': []}, logger=logger.SimpleLogger())
        self.assertIsNone(numeric_value_dict, 'Dict numeric value is {}'.format(numeric_value_dict))

        numeric_value_none = event_tag_utils.get_numeric_value({'value': None}, logger=logger.SimpleLogger())
        self.assertIsNone(numeric_value_none, 'None numeric value is {}'.format(numeric_value_none))

        numeric_value_invalid_literal = event_tag_utils.get_numeric_value(
            {'value': '1,234'},
            logger=logger.SimpleLogger()
        )
        self.assertIsNone(numeric_value_invalid_literal, 'Invalid string literal value is {}'
                          .format(numeric_value_invalid_literal))

        numeric_value_overflow = event_tag_utils.get_numeric_value({'value': sys.float_info.max * 10},
                                                                   logger=logger.SimpleLogger())
        self.assertIsNone(numeric_value_overflow, 'Max numeric value is {}'.format(numeric_value_overflow))

        numeric_value_inf = event_tag_utils.get_numeric_value({'value': float('inf')}, logger=logger.SimpleLogger())
        self.assertIsNone(numeric_value_inf, 'Infinity numeric value is {}'.format(numeric_value_inf))

        numeric_value_neg_inf = event_tag_utils.get_numeric_value(
            {'value': float('-inf')},
            logger=logger.SimpleLogger()
        )
        self.assertIsNone(numeric_value_neg_inf, 'Negative infinity numeric value is {}'.format(numeric_value_neg_inf))
    mock_logger.assert_has_calls([call1, call2, call3, call2, call6, call2, call3, call2, call3,
        call2, call3, call2, call5, call2, call4, call2, call4, call2, call7, call2])
