# Copyright 2016-2021, Optimizely
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
from sys import version_info

if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final  # type: ignore


class CommonAudienceEvaluationLogs:
    AUDIENCE_EVALUATION_RESULT: Final = 'Audience "{}" evaluated to {}.'
    EVALUATING_AUDIENCE: Final = 'Starting to evaluate audience "{}" with conditions: {}.'
    INFINITE_ATTRIBUTE_VALUE: Final = (
        'Audience condition "{}" evaluated to UNKNOWN because the number value '
        'for user attribute "{}" is not in the range [-2^53, +2^53].'
    )
    MISSING_ATTRIBUTE_VALUE: Final = (
        'Audience condition {} evaluated to UNKNOWN because no value was passed for ' 'user attribute "{}".'
    )
    NULL_ATTRIBUTE_VALUE: Final = (
        'Audience condition "{}" evaluated to UNKNOWN because a null value was passed ' 'for user attribute "{}".'
    )
    UNEXPECTED_TYPE: Final = (
        'Audience condition "{}" evaluated to UNKNOWN because a value of type "{}" was passed '
        'for user attribute "{}".'
    )

    UNKNOWN_CONDITION_TYPE: Final = (
        'Audience condition "{}" uses an unknown condition type. You may need to upgrade to a '
        'newer release of the Optimizely SDK.'
    )
    UNKNOWN_CONDITION_VALUE: Final = (
        'Audience condition "{}" has an unsupported condition value. You may need to upgrade to a '
        'newer release of the Optimizely SDK.'
    )
    UNKNOWN_MATCH_TYPE: Final = (
        'Audience condition "{}" uses an unknown match type. You may need to upgrade to a '
        'newer release of the Optimizely SDK.'
    )


class ExperimentAudienceEvaluationLogs(CommonAudienceEvaluationLogs):
    AUDIENCE_EVALUATION_RESULT_COMBINED: Final = 'Audiences for experiment "{}" collectively evaluated to {}.'
    EVALUATING_AUDIENCES_COMBINED: Final = 'Evaluating audiences for experiment "{}": {}.'


class RolloutRuleAudienceEvaluationLogs(CommonAudienceEvaluationLogs):
    AUDIENCE_EVALUATION_RESULT_COMBINED: Final = 'Audiences for rule {} collectively evaluated to {}.'
    EVALUATING_AUDIENCES_COMBINED: Final = 'Evaluating audiences for rule {}: {}.'


class ConfigManager:
    AUTHENTICATED_DATAFILE_URL_TEMPLATE: Final = 'https://config.optimizely.com/datafiles/auth/{sdk_key}.json'
    AUTHORIZATION_HEADER_DATA_TEMPLATE: Final = 'Bearer {datafile_access_token}'
    DATAFILE_URL_TEMPLATE: Final = 'https://cdn.optimizely.com/datafiles/{sdk_key}.json'
    # Default time in seconds to block the 'get_config' method call until 'config' instance has been initialized.
    DEFAULT_BLOCKING_TIMEOUT: Final = 10
    # Default config update interval of 5 minutes
    DEFAULT_UPDATE_INTERVAL: Final = 5 * 60
    # Time in seconds before which request for datafile times out
    REQUEST_TIMEOUT: Final = 10


class ControlAttributes:
    BOT_FILTERING: Final = '$opt_bot_filtering'
    BUCKETING_ID: Final = '$opt_bucketing_id'
    USER_AGENT: Final = '$opt_user_agent'


class DatafileVersions:
    V2: Final = '2'
    V3: Final = '3'
    V4: Final = '4'


class DecisionNotificationTypes:
    AB_TEST: Final = 'ab-test'
    ALL_FEATURE_VARIABLES: Final = 'all-feature-variables'
    FEATURE: Final = 'feature'
    FEATURE_TEST: Final = 'feature-test'
    FEATURE_VARIABLE: Final = 'feature-variable'
    FLAG: Final = 'flag'


class DecisionSources:
    EXPERIMENT: Final = 'experiment'
    FEATURE_TEST: Final = 'feature-test'
    ROLLOUT: Final = 'rollout'


class Errors:
    INVALID_ATTRIBUTE: Final = 'Provided attribute is not in datafile.'
    INVALID_ATTRIBUTE_FORMAT: Final = 'Attributes provided are in an invalid format.'
    INVALID_AUDIENCE: Final = 'Provided audience is not in datafile.'
    INVALID_EVENT_TAG_FORMAT: Final = 'Event tags provided are in an invalid format.'
    INVALID_EXPERIMENT_KEY: Final = 'Provided experiment is not in datafile.'
    INVALID_EVENT_KEY: Final = 'Provided event is not in datafile.'
    INVALID_FEATURE_KEY: Final = 'Provided feature key is not in the datafile.'
    INVALID_GROUP_ID: Final = 'Provided group is not in datafile.'
    INVALID_INPUT: Final = 'Provided "{}" is in an invalid format.'
    INVALID_OPTIMIZELY: Final = 'Optimizely instance is not valid. Failing "{}".'
    INVALID_PROJECT_CONFIG: Final = 'Invalid config. Optimizely instance is not valid. Failing "{}".'
    INVALID_VARIATION: Final = 'Provided variation is not in datafile.'
    INVALID_VARIABLE_KEY: Final = 'Provided variable key is not in the feature flag.'
    NONE_FEATURE_KEY_PARAMETER: Final = '"None" is an invalid value for feature key.'
    NONE_USER_ID_PARAMETER: Final = '"None" is an invalid value for user ID.'
    NONE_VARIABLE_KEY_PARAMETER: Final = '"None" is an invalid value for variable key.'
    UNSUPPORTED_DATAFILE_VERSION: Final = (
        'This version of the Python SDK does not support the given datafile version: "{}".')
    FETCH_SEGMENTS_FAILED: Final = 'Audience segments fetch failed ({}).'
    ODP_EVENT_FAILED: Final = 'ODP event send failed ({}).'
    ODP_NOT_INTEGRATED: Final = 'ODP is not integrated.'
    ODP_NOT_ENABLED: Final = 'ODP is not enabled.'
    ODP_INVALID_DATA: Final = 'ODP data is not valid.'
    ODP_INVALID_ACTION: Final = 'ODP action is not valid (cannot be empty).'
    MISSING_SDK_KEY: Final = 'SDK key not provided/cannot be found in the datafile.'


class ForcedDecisionLogs:
    USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED: Final = (
        'Variation ({}) is mapped to flag ({}), rule ({}) and user ({}) '
        'in the forced decision map.')
    USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED: Final = (
        'Variation ({}) is mapped to flag ({}) and user ({}) '
        'in the forced decision map.')
    USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED_BUT_INVALID: Final = (
        'Invalid variation is mapped to flag ({}), rule ({}) '
        'and user ({}) in the forced decision map.')
    USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED_BUT_INVALID: Final = (
        'Invalid variation is mapped to flag ({}) '
        'and user ({}) in the forced decision map.')


class HTTPHeaders:
    AUTHORIZATION: Final = 'Authorization'
    IF_MODIFIED_SINCE: Final = 'If-Modified-Since'
    LAST_MODIFIED: Final = 'Last-Modified'


class HTTPVerbs:
    GET: Final = 'GET'
    POST: Final = 'POST'


class LogLevels:
    NOTSET: Final = logging.NOTSET
    DEBUG: Final = logging.DEBUG
    INFO: Final = logging.INFO
    WARNING: Final = logging.WARNING
    ERROR: Final = logging.ERROR
    CRITICAL: Final = logging.CRITICAL


class NotificationTypes:
    """ NotificationTypes for the notification_center.NotificationCenter
      format is NOTIFICATION TYPE: list of parameters to callback.

      ACTIVATE (DEPRECATED since 3.1.0) notification listener has the following parameters:
      Experiment experiment, str user_id, dict attributes (can be None), Variation variation, Event event

      DECISION notification listener has the following parameters:
      DecisionNotificationTypes type, str user_id, dict attributes, dict decision_info

      OPTIMIZELY_CONFIG_UPDATE notification listener has no associated parameters.

      TRACK notification listener has the following parameters:
      str event_key, str user_id, dict attributes (can be None), event_tags (can be None), Event event

      LOG_EVENT notification listener has the following parameter(s):
      LogEvent log_event
  """

    ACTIVATE: Final = 'ACTIVATE:experiment, user_id, attributes, variation, event'
    DECISION: Final = 'DECISION:type, user_id, attributes, decision_info'
    OPTIMIZELY_CONFIG_UPDATE: Final = 'OPTIMIZELY_CONFIG_UPDATE'
    TRACK: Final = 'TRACK:event_key, user_id, attributes, event_tags, event'
    LOG_EVENT: Final = 'LOG_EVENT:log_event'


class VersionType:
    IS_PRE_RELEASE: Final = '-'
    IS_BUILD: Final = '+'


class EventDispatchConfig:
    """Event dispatching configs."""
    REQUEST_TIMEOUT: Final = 10


class OdpEventApiConfig:
    """ODP Events API configs."""
    REQUEST_TIMEOUT: Final = 10


class OdpSegmentApiConfig:
    """ODP Segments API configs."""
    REQUEST_TIMEOUT: Final = 10


class OdpEventManagerConfig:
    """ODP Event Manager configs."""
    DEFAULT_QUEUE_CAPACITY: Final = 1000
    DEFAULT_BATCH_SIZE: Final = 10
    DEFAULT_FLUSH_INTERVAL: Final = 1
    DEFAULT_RETRY_COUNT: Final = 3


class OdpManagerConfig:
    """ODP Manager configs."""
    KEY_FOR_USER_ID: Final = 'fs_user_id'
    EVENT_TYPE: Final = 'fullstack'


class OdpSegmentsCacheConfig:
    """ODP Segment Cache configs."""
    DEFAULT_CAPACITY: Final = 10_000
    DEFAULT_TIMEOUT_SECS: Final = 600
