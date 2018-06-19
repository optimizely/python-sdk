# Copyright 2016-2017, Optimizely
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
  UNSUPPORTED_DATAFILE_VERSION = 'Provided datafile has unsupported version. ' \
                                 'Please use SDK version 1.1.0 or earlier for datafile version 1.'


class NotificationTypes(object):
  """ NotificationTypes for the notification_center.NotificationCenter
      format is NOTIFICATION TYPE: list of parameters to callback.

      ACTIVATE notification listener has the following parameters:
      Experiment experiment, str user_id, dict attributes (can be None), Variation variation, Event event
      TRACK notification listener has the following parameters:
      str event_key, str user_id, dict attributes (can be None), event_tags (can be None), Event event
  """
  ACTIVATE = "ACTIVATE:experiment, user_id, attributes, variation, event"
  TRACK = "TRACK:event_key, user_id, attributes, event_tags, event"
