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

from . import enums
import math
import numbers

REVENUE_METRIC_TYPE = 'revenue'
NUMERIC_METRIC_TYPE = 'value'


def get_revenue_value(event_tags):
    if event_tags is None:
        return None

    if not isinstance(event_tags, dict):
        return None

    if REVENUE_METRIC_TYPE not in event_tags:
        return None

    raw_value = event_tags[REVENUE_METRIC_TYPE]

    if isinstance(raw_value, bool):
        return None

    if not isinstance(raw_value, numbers.Integral):
        return None

    return raw_value


def get_numeric_value(event_tags, logger=None):
    """
  A smart getter of the numeric value from the event tags.

  Args:
      event_tags: A dictionary of event tags.
      logger: Optional logger.

  Returns:
      A float numeric metric value is returned when the provided numeric
      metric value is in the following format:
          - A string (properly formatted, e.g., no commas)
          - An integer
          - A float or double
      None is returned when the provided numeric metric values is in
      the following format:
          - None
          - A boolean
          - inf, -inf, nan
          - A string not properly formatted (e.g., '1,234')
          - Any values that cannot be cast to a float (e.g., an array or dictionary)
  """

    logger_message_debug = None
    numeric_metric_value = None

    if event_tags is None:
        return numeric_metric_value
    elif not isinstance(event_tags, dict):
        if logger:
            logger.log(enums.LogLevels.ERROR, 'Event tags is not a dictionary.')
        return numeric_metric_value
    elif NUMERIC_METRIC_TYPE not in event_tags:
        return numeric_metric_value
    else:
        numeric_metric_value = event_tags[NUMERIC_METRIC_TYPE]
        try:
            if isinstance(numeric_metric_value, (numbers.Integral, float, str)):
                # Attempt to convert the numeric metric value to a float
                # (if it isn't already a float).
                cast_numeric_metric_value = float(numeric_metric_value)

                # If not a float after casting, then make everything else a None.
                # Other potential values are nan, inf, and -inf.
                if not isinstance(cast_numeric_metric_value, float) or \
                   math.isnan(cast_numeric_metric_value) or \
                   math.isinf(cast_numeric_metric_value):
                    logger_message_debug = 'Provided numeric value {} is in an invalid format.'.format(
                        numeric_metric_value
                    )
                    numeric_metric_value = None
                else:
                    # Handle booleans as a special case.
                    # They are treated like an integer in the cast, but we do not want to cast this.
                    if isinstance(numeric_metric_value, bool):
                        logger_message_debug = 'Provided numeric value is a boolean, which is an invalid format.'
                        numeric_metric_value = None
                    else:
                        numeric_metric_value = cast_numeric_metric_value
            else:
                logger_message_debug = 'Numeric metric value is not in integer, float, or string form.'
                numeric_metric_value = None

        except ValueError:
            logger_message_debug = 'Value error while casting numeric metric value to a float.'
            numeric_metric_value = None

    # Log all potential debug messages while converting the numeric value to a float.
    if logger and logger_message_debug:
        logger.log(enums.LogLevels.DEBUG, logger_message_debug)

    # Log the final numeric metric value
    if numeric_metric_value is not None:
        if logger:
            logger.log(
                enums.LogLevels.INFO,
                'The numeric metric value {} will be sent to results.'.format(numeric_metric_value),
            )
    else:
        if logger:
            logger.log(
                enums.LogLevels.WARNING,
                'The provided numeric metric value {} is in an invalid format and will not be sent to results.'.format(
                    numeric_metric_value
                ),
            )

    return numeric_metric_value
