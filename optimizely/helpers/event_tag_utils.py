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

  if not isinstance(raw_value, numbers.Integral):
    return None

  return raw_value

def get_numeric_value(event_tags):
  if event_tags is None:
    return None

  if not isinstance(event_tags, dict):
    return None

  if NUMERIC_METRIC_TYPE not in event_tags:
    return None

  raw_value = event_tags[NUMERIC_METRIC_TYPE]

  # python float includes double precision
  if not isinstance(raw_value, float):
    return None

  return raw_value