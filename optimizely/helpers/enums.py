# Copyright 2016-2019, Optimizely
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

import logging


class AudienceEvaluationLogs(object):
  AUDIENCE_EVALUATION_RESULT = 'Audience "{}" evaluated to {}.'
  AUDIENCE_EVALUATION_RESULT_COMBINED = 'Audiences for experiment "{}" collectively evaluated to {}.'
  EVALUATING_AUDIENCE = 'Starting to evaluate audience "{}" with conditions: {}.'
  EVALUATING_AUDIENCES_COMBINED = 'Evaluating audiences for experiment "{}": {}.'
  INFINITE_ATTRIBUTE_VALUE = 'Audience condition "{}" evaluated to UNKNOWN because the number value ' \
                         'for user attribute "{}" is not in the range [-2^53, +2^53].'
  MISSING_ATTRIBUTE_VALUE = 'Audience condition {} evaluated to UNKNOWN because no value was passed for '\
                            'user attribute "{}".'
  NULL_ATTRIBUTE_VALUE = 'Audience condition "{}" evaluated to UNKNOWN because a null value was passed '\
                         'for user attribute "{}".'
  UNEXPECTED_TYPE = 'Audience condition "{}" evaluated to UNKNOWN because a value of type "{}" was passed '\
                    'for user attribute "{}".'

  UNKNOWN_CONDITION_TYPE = 'Audience condition "{}" uses an unknown condition type. You may need to upgrade to a '\
                           'newer release of the Optimizely SDK.'
  UNKNOWN_CONDITION_VALUE = 'Audience condition "{}" has an unsupported condition value. You may need to upgrade to a '\
                           'newer release of the Optimizely SDK.'
  UNKNOWN_MATCH_TYPE = 'Audience condition "{}" uses an unknown match type. You may need to upgrade to a '\
                       'newer release of the Optimizely SDK.'


class ConfigManager(object):
  DATAFILE_URL_TEMPLATE = 'https://cdn.optimizely.com/datafiles/{sdk_key}.json'
  # Default config update interval of 5 minutes
  DEFAULT_UPDATE_INTERVAL = 5 * 60
  # Minimum config update interval of 1 second
  MIN_UPDATE_INTERVAL = 1
  # Time in seconds before which request for datafile times out
  REQUEST_TIMEOUT = 10


class ControlAttributes(object):
  BOT_FILTERING = '$opt_bot_filtering'
  BUCKETING_ID = '$opt_bucketing_id'
  USER_AGENT = '$opt_user_agent'


class DatafileVersions(object):
  V2 = '2'
  V3 = '3'
  V4 = '4'


class DecisionNotificationTypes(object):
  AB_TEST = 'ab-test'
  FEATURE = 'feature'
  FEATURE_TEST = 'feature-test'
  FEATURE_VARIABLE = 'feature-variable'


class DecisionSources(object):
  FEATURE_TEST = 'feature-test'
  ROLLOUT = 'rollout'


class Errors(object):
  INVALID_ATTRIBUTE_ERROR = 'Provided attribute is not in datafile.'
  INVALID_ATTRIBUTE_FORMAT = 'Attributes provided are in an invalid format.'
  INVALID_AUDIENCE_ERROR = 'Provided audience is not in datafile.'
  INVALID_DATAFILE = 'Datafile has invalid format. Failing "{}".'
  INVALID_EVENT_TAG_FORMAT = 'Event tags provided are in an invalid format.'
  INVALID_EXPERIMENT_KEY_ERROR = 'Provided experiment is not in datafile.'
  INVALID_EVENT_KEY_ERROR = 'Provided event is not in datafile.'
  INVALID_FEATURE_KEY_ERROR = 'Provided feature key is not in the datafile.'
  INVALID_GROUP_ID_ERROR = 'Provided group is not in datafile.'
  INVALID_INPUT_ERROR = 'Provided "{}" is in an invalid format.'
  INVALID_VARIATION_ERROR = 'Provided variation is not in datafile.'
  INVALID_VARIABLE_KEY_ERROR = 'Provided variable key is not in the feature flag.'
  NONE_FEATURE_KEY_PARAMETER = '"None" is an invalid value for feature key.'
  NONE_USER_ID_PARAMETER = '"None" is an invalid value for user ID.'
  NONE_VARIABLE_KEY_PARAMETER = '"None" is an invalid value for variable key.'
  UNSUPPORTED_DATAFILE_VERSION = 'This version of the Python SDK does not support the given datafile version: "{}".'


class HTTPHeaders(object):
  IF_MODIFIED_SINCE = 'If-Modified-Since'
  LAST_MODIFIED = 'Last-Modified'


class HTTPVerbs(object):
  GET = 'GET'
  POST = 'POST'


class LogLevels(object):
  NOTSET = logging.NOTSET
  DEBUG = logging.DEBUG
  INFO = logging.INFO
  WARNING = logging.WARNING
  ERROR = logging.ERROR
  CRITICAL = logging.CRITICAL


class NotificationTypes(object):
  """ NotificationTypes for the notification_center.NotificationCenter
      format is NOTIFICATION TYPE: list of parameters to callback.

      ACTIVATE (DEPRECATED since 3.1.0) notification listener has the following parameters:
      Experiment experiment, str user_id, dict attributes (can be None), Variation variation, Event event

      DECISION notification listener has the following parameters:
      DecisionNotificationTypes type, str user_id, dict attributes, dict decision_info

      TRACK notification listener has the following parameters:
      str event_key, str user_id, dict attributes (can be None), event_tags (can be None), Event event
  """
  ACTIVATE = 'ACTIVATE:experiment, user_id, attributes, variation, event'
  DECISION = 'DECISION:type, user_id, attributes, decision_info'
  TRACK = 'TRACK:event_key, user_id, attributes, event_tags, event'
