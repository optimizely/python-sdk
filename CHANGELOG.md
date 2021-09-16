# Optimizely Python SDK Changelog

## 3.10.0
September 16th, 2021

### New Features
* Added new public properties to OptimizelyConfig. 
  - sdk_key and environment_key [#338] (https://github.com/optimizely/python-sdk/pull/338)
  - attributes and events [#339] (https://github.com/optimizely/python-sdk/pull/339)
  - experiment_rules, delivery_rules, audiences and audiences in OptimizelyExperiment 
    - [#342] (https://github.com/optimizely/python-sdk/pull/342)
    - [#351] (https://github.com/optimizely/python-sdk/pull/351/files)
* For details please refer to our documentation page:
  - Python-sdk: [https://docs.developers.optimizely.com/full-stack/docs/optimizelyconfig-python]

* OptimizelyFeature.experiments_map of OptimizelyConfig is now deprecated. Please use OptimizelyFeature.experiment_rules and OptimizelyFeature.delivery_rules. [#360] (https://github.com/optimizely/python-sdk/pull/360)

### Bug Fixes
* Fix event processor negative timeout interval when retrieving events from queue. [#356] (https://github.com/optimizely/python-sdk/pull/356)

## 3.9.1
July 14th, 2021

### Bug Fixes:
* Fixed issue with serving incorrect variation in projects containing multiple flags with duplicate keys. [#347] (https://github.com/optimizely/python-sdk/pull/347)
* Fixed issue with serving incorrect variation in create_impression_event in user_event_factory.py. [#350] (https://github.com/optimizely/python-sdk/pull/350)

## 3.9.0
June 1st, 2021

### New Features
* Added support for multiple concurrent prioritized experiments per flag. [#322](https://github.com/optimizely/python-sdk/pull/322)

## 3.8.0
February 12th, 2021

### New Features
* New Features
Introducing a new primary interface for retrieving feature flag status, configuration and associated experiment decisions for users ([#309](https://github.com/optimizely/python-sdk/pull/309)). The new `OptimizelyUserContext` class is instantiated with `create_user_context` and exposes the following APIs to get `OptimizelyDecision`:

    - set_attribute
    - decide
    - decide_all
    - decide_for_keys
    - track_event

For details, refer to our documentation page: https://docs.developers.optimizely.com/full-stack/v4.0/docs/python-sdk.

## 3.7.1
November 19th, 2020

### Bug Fixes:
* Added "enabled" field to decision metadata structure. [#306](https://github.com/optimizely/python-sdk/pull/306)

## 3.7.0
November 2nd, 2020

### New Features
* Added support for upcoming application-controlled introduction of tracking for non-experiment Flag decisions. [#300](https://github.com/optimizely/python-sdk/pull/300)

## 3.6.0
October 1st, 2020

### New Features:
* Version targeting using semantic version syntax. [#293](https://github.com/optimizely/python-sdk/pull/293)
* Datafile accessor API added to access current config as a JSON string. [#283](https://github.com/optimizely/python-sdk/pull/283)

### Bug Fixes:
* Fixed package installation for Python 3.4 and pypy. [#298](https://github.com/optimizely/python-sdk/pull/298)

## 3.5.2
July 14th, 2020

### Bug Fixes:
* Fixed handling of network and no status code errors when polling for datafile in `PollingConfigManager` and `AuthDatafilePollingConfigManager`. ([#287](https://github.com/optimizely/python-sdk/pull/287))

## 3.5.1
July 10th, 2020

### Bug Fixes:
* Fixed HTTP request exception handling in `PollingConfigManager`. ([#285](https://github.com/optimizely/python-sdk/pull/285))

## 3.5.0
July 9th, 2020

### New Features:
* Introduced 2 APIs to interact with feature variables:
  * `get_feature_variable_json` allows you to get value for JSON variables related to a feature.
  * `get_all_feature_variables` gets values for all variables under a feature.
* Added support for fetching authenticated datafiles. `AuthDatafilePollingConfigManager` is a new config manager that allows you to poll for a datafile belonging to a secure environment. You can create a client by setting the `datafile_access_token`.

### Bug Fixes:
* Fixed log messages for targeted rollouts evaluation. ([#268](https://github.com/optimizely/python-sdk/pull/268))

## 3.4.2
June 11th, 2020

### Bug Fixes:
* Adjusted log level for audience evaluation logs. ([#267](https://github.com/optimizely/python-sdk/pull/267))

## 3.4.1
March 19th, 2020

### Bug Fixes:
* Updated `jsonschema` to address [installation issue](https://github.com/optimizely/python-sdk/issues/232).

## 3.4.0
January 27th, 2020

### New Features:
* Added a new API to get project configuration static data.
  * Call `get_optimizely_config()` to get a snapshot of project configuration static data.
  * It returns an `OptimizelyConfig` instance which includes a datafile revision number, all experiments, and feature flags mapped by their key values.
  * Added caching for `get_optimizely_config()` - `OptimizelyConfig` object will be cached and reused for the lifetime of the datafile.
  * For details, refer to our documentation page: [https://docs.developers.optimizely.com/full-stack/docs/optimizelyconfig-python](https://docs.developers.optimizely.com/full-stack/docs/optimizelyconfig-python).


## 3.3.1
December 16th, 2019

### Bug Fixes:
* Fixed [installation issue](https://github.com/optimizely/python-sdk/issues/220) on Windows. ([#224](https://github.com/optimizely/python-sdk/pull/224))
* Fixed batch event processor deadline reset issue. ([#227](https://github.com/optimizely/python-sdk/pull/227))
* Added more batch event processor debug messages. ([#227](https://github.com/optimizely/python-sdk/pull/227))

## 3.3.0
October 28th, 2019

### New Features:
* Added support for event batching via the event processor.
  * Events generated by methods like `activate`, `track`, and `is_feature_enabled` will be held in a queue until the configured batch size is reached, or the configured flush interval has elapsed. Then, they will be batched into a single payload and sent to the event dispatcher.
  * To configure event batching, set the `batch_size` and `flush_interval` properties when initializing instance of [BatchEventProcessor](https://github.com/optimizely/python-sdk/blob/3.3.x/optimizely/event/event_processor.py#L45).
  * Event batching is disabled by default. You can pass in instance of `BatchEventProcessor` when creating `Optimizely` instance to enable event batching.
  * Users can subscribe to `LogEvent` notification to be notified of whenever a payload consisting of a batch of user events is handed off to the event dispatcher to send to Optimizely's backend.
* Introduced blocking timeout in `PollingConfigManager`. By default, calls to `get_config` will block for maximum of 10 seconds until config is available. 

### Bug Fixes:
* Fixed incorrect log message when numeric metric is not used. ([#217](https://github.com/optimizely/python-sdk/pull/217))

## 3.2.0
August 27th, 2019

### New Features:
* Added support for automatic datafile management via [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L151):
  * The [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L151) is an implementation of the [BaseConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L32).
  * Users may provide one of datafile or SDK key (sdk_key) or both to `optimizely.Optimizely`. Based on that, the SDK will use the [StaticConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L73) or the [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L151). Refer to the [README](README.md) for more instructions.
  * An initial datafile can be provided to the `PollingConfigManager` to bootstrap before making HTTP requests for the hosted datafile.
  * Requests for the datafile are made in a separate thread and are scheduled with fixed delay.
  * Configuration updates can be subscribed to by adding the OPTIMIZELY_CONFIG_UPDATE notification listener.
* Introduced `Optimizely.get_feature_variable` API.  ([#191](https://github.com/optimizely/python-sdk/pull/191))

### Deprecated:

* `NotificationCenter.clear_notifications` is deprecated as of this release. Please use `NotificationCenter.clear_notification_listeners`.  ([#182](https://github.com/optimizely/python-sdk/pull/182))
* `NotificationCenter.clear_all_notifications` is deprecated as of this release. Please use `NotificationCenter.clear_all_notification_listeners`.  ([#182](https://github.com/optimizely/python-sdk/pull/182))

## 3.2.0b1
July 26th, 2019

### New Features:
* Added support for automatic datafile management via [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L151):
  * The [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L151) is an implementation of the [BaseConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L32).
  * Users may provide one of datafile or SDK key (sdk_key) or both to `optimizely.Optimizely`. Based on that, the SDK will use the [StaticConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L73) or the [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/3.2.x/optimizely/config_manager.py#L151). Refer to the [README](README.md) for more instructions.
  * An initial datafile can be provided to the `PollingConfigManager` to bootstrap before making HTTP requests for the hosted datafile.
  * Requests for the datafile are made in a separate thread and are scheduled with fixed delay.
  * Configuration updates can be subscribed to by adding the OPTIMIZELY_CONFIG_UPDATE notification listener.
* Introduced `Optimizely.get_feature_variable` API.  ([#191](https://github.com/optimizely/python-sdk/pull/191))

### Deprecated:

* `NotificationCenter.clear_notifications` is deprecated as of this release. Please use `NotificationCenter.clear_notification_listeners`.  ([#182](https://github.com/optimizely/python-sdk/pull/182))
* `NotificationCenter.clear_all_notifications` is deprecated as of this release. Please use `NotificationCenter.clear_all_notification_listeners`.  ([#182](https://github.com/optimizely/python-sdk/pull/182))

## 3.1.0
May 3rd, 2019

### New Features:
* Introduced Decision notification listener to be able to record:
  * Variation assignments for users activated in an experiment.
  * Feature access for users.
  * Feature variable value for users.

### Bug Fixes:
* Feature variable APIs now return default variable value when featureEnabled property is false.  ([#171](https://github.com/optimizely/python-sdk/pull/171))

### Deprecated:
* Activate notification listener is deprecated as of this release.  Recommendation is to use the new Decision notification listener.  Activate notification listener will be removed in the next major release.

## 3.0.0
March 1st, 2019

The 3.0 release improves event tracking and supports additional audience
targeting functionality.

### New Features:
* Event tracking:
  * The `track` method now dispatches its conversion event *unconditionally*, without first determining whether the user is targeted by a known experiment that uses the event. This may increase outbound network traffic.
  * In Optimizely results, conversion events sent by 3.0 SDKs don\'t explicitly name the experiments and variations that are currently targeted to the user. Instead, conversions are automatically attributed to variations that the user has previously seen, as long as those variations were served via 3.0 SDKs or by other clients capable of automatic attribution, and as long as our backend actually received the impression events for those variations.
  * Altogether, this allows you to track conversion events and attribute them to variations even when you don't know all of a user's attribute values, and even if the user's attribute values or the experiment's configuration have changed such that the user is no longer affected by the experiment. As a result, **you may observe an increase in the conversion rate for previously-instrumented events.** If that is undesirable, you can reset the results of previously-running experiments after upgrading to the 3.0 SDK.  -   This will also allow you to attribute events to variations from other Optimizely projects in your account, even though those experiments don't appear in the same datafile.
  * Note that for results segmentation in Optimizely results, the user attribute values from one event are automatically applied to all other events in the same session, as long as the events in question were actually received by our backend. This behavior was already in place and is not affected by the 3.0 release.
* Support for all types of attribute values, not just strings.
  * All values are passed through to notification listeners.
  * Strings, booleans, and valid numbers are passed to the event dispatcher and can be used for Optimizely results segmentation.  A valid number is a finite float or numbers.Integral in the inclusive range \[-2 ^ 53, 2 ^ 53\].
  * Strings, booleans, and valid numbers are relevant for audience conditions.
* Support for additional matchers in audience conditions:
  * An `exists` matcher that passes if the user has a non-null value for the targeted user attribute and fails otherwise.
  * A `substring` matcher that resolves if the user has a string value for the targeted attribute.
    * `gt` (greater than) and `lt` (less than) matchers that resolve if the user has a valid number value for the targeted attribute.  A valid number is a finite float or numbers.Integral in the inclusive range \[-2 ^ 53, 2 ^ 53\].
    * The original (`exact`) matcher can now be used to target booleans and valid numbers, not just strings.
* Support for A/B tests, feature tests, and feature rollouts whose audiences are combined using `"and"` and `"not"` operators, not just the `"or"` operator.
* Datafile-version compatibility check: The SDK will remain uninitialized (i.e., will gracefully fail to activate experiments and features) if given a datafile version greater than 4.
* Updated Pull Request template and commit message guidelines.

### Breaking Changes:
* Conversion events sent by 3.0 SDKs don\'t explicitly name the experiments and variations that are currently targeted to the user, so these events are unattributed in raw events data export. You must use the new *results* export to determine the variations to which events have been attributed.
* Previously, notification listeners were only given string-valued user attributes because only strings could be passed into various method calls. That is no longer the case. You may pass non-string attribute values, and if you do, you must update your notification listeners to be able to receive whatever values you pass in.

### Bug Fixes:
* Experiments and features can no longer activate when a negatively targeted attribute has a missing, null, or malformed value.
  * Audience conditions (except for the new `exists` matcher) no longer resolve to `false` when they fail to find an legitimate value for the targeted user attribute. The result remains `null` (unknown). Therefore, an audience that negates such a condition (using the `"not"` operator) can no longer resolve to `true` unless there is an unrelated branch in the condition tree that itself resolves to `true`.
* Updated the default event dispatcher to log an error if the request resolves to HTTP 4xx or 5xx.  ([#140](https://github.com/optimizely/python-sdk/pull/140))
* All methods now validate that user IDs are strings and that experiment keys, feature keys, feature variable keys, and event keys are non-empty strings.

## 2.1.1
August 21st, 2018

* Fix: record conversions for all experiments using an event when using track([#136](https://github.com/optimizely/python-sdk/pull/136)).

## 2.1.0
July 2nd, 2018

* Introduced support for bot filtering ([#121](https://github.com/optimizely/python-sdk/pull/121)).
* Overhauled logging to use standard Python logging ([#123](https://github.com/optimizely/python-sdk/pull/123)).

## 2.0.1
June 19th, 2018

* Fix: send impression event for Feature Test when Feature is disabled ([#128](https://github.com/optimizely/python-sdk/pull/128)).

## 2.0.0
April 12th, 2018

This major release introduces APIs for Feature Management. It also
introduces some breaking changes listed below.

### New Features
* Introduced the `is_feature_enabled` API to determine whether to show a feature to a user or not.

```
    is_enabled = optimizel_client.is_feature_enabled('my_feature_key', 'my_user', user_attributes)
```

* All enabled features for the user can be retrieved by calling:

```
    enabled_features = optimizely_client.get_enabled_features('my_user', user_attributes)
```
* Introduced Feature Variables to configure or parameterize a feature.  There are four variable types: `String`, `Integer`, `Double`, `Boolean`.

```
    string_variable = optimizely_client.get_feature_variable_string('my_feature_key', 'string_variable_key', 'my_user')
    integer_variable = optimizely_client.get_feature_variable_integer('my_feature_key', 'integer_variable_key', 'my_user')
    double_variable = optimizely_client.get_feature_variable_double('my_feature_key', 'double_variable_key', 'my_user')
    boolean_variable = optimizely_client.get_feature_variable_boolean('my_feature_key', 'boolean_variable_key', 'my_user')
```

### Breaking changes
* The `track` API with revenue value as a stand-alone parameter has been removed. The revenue value should be passed in as an entry in the event tags dict. The key for the revenue tag is `revenue` and the passed in value will be treated by Optimizely as the value for computing results.

```
    event_tags = {
      'revenue': 1200
    }

    optimizely_client.track('event_key', 'my_user', user_attributes, event_tags)
```

## 2.0.0b1
March 29th, 2018

This beta release introduces APIs for Feature Management. It also
introduces some breaking changes listed below.

### New Features
* Introduced the `is_feature_enabled` API to determine whether to show a feature to a user or not.
```
    is_enabled = optimizel_client.is_feature_enabled('my_feature_key', 'my_user', user_attributes)
```

* All enabled features for the user can be retrieved by calling:

```
    enabled_features = optimizely_client.get_enabled_features('my_user', user_attributes)
```

* Introduced Feature Variables to configure or parameterize a feature.  There are four variable types: `String`, `Integer`, `Double`, `Boolean`.

```
    string_variable = optimizely_client.get_feature_variable_string('my_feature_key', 'string_variable_key', 'my_user')
    integer_variable = optimizely_client.get_feature_variable_integer('my_feature_key', 'integer_variable_key', 'my_user')
    double_variable = optimizely_client.get_feature_variable_double('my_feature_key', 'double_variable_key', 'my_user')
    boolean_variable = optimizely_client.get_feature_variable_boolean('my_feature_key', 'boolean_variable_key', 'my_user')
```

### Breaking changes
* The `track` API with revenue value as a stand-alone parameter has been removed. The revenue value should be passed in as an entry in the event tags dict. The key for the revenue tag is `revenue` and the passed in value will be treated by Optimizely as the value for computing results.

```
    event_tags = {
      'revenue': 1200
    }

    optimizely_client.track('event_key', 'my_user', user_attributes, event_tags)
```

## 1.4.0

* Added support for IP anonymization.
* Added support for notification listeners.
* Added support for bucketing ID.
* Updated mmh3 to handle installation failures on Windows 10.

## 1.3.0

* Introduced support for forced bucketing.
* Introduced support for numeric metrics.
* Updated event builder to support new endpoint.

## 1.2.1

* Removed older feature flag parsing.

## 1.2.0

* Added user profile service.

## 1.1.1

* Updated datafile parsing to be able to handle additional fields.
* Deprecated Classic project support.

## 1.1.0

* Included datafile revision information in log events.
* Added event tags to track API to allow users to pass in event metadata.
* Deprecated the `event_value` parameter from the track method. Should use `event_tags` to pass in event value instead.
* Updated event logging endpoint to logx.optimizely.com.

## 1.0.0

* Introduced support for Full Stack projects in Optimizely X. No breaking changes from previous version.
* Introduced more graceful exception handling in instantiation and core methods.
* Updated whitelisting to precede audience matching.

## 0.1.3

* Added support for v2 endpoint and datafile.
* Updated dispatch_event to consume an Event object instead of url and params. The Event object comprises of four properties: url (string representing URL to dispatch event to), params (dict representing the params to be set for the event), http_verb (one of 'GET' or 'POST') and headers (header values to be sent along).
* Fixed issue with tracking events for experiments in groups.

## 0.1.2

* Updated requirements file.

## 0.1.1

* Introduced option to skip JSON schema validation.

## 0.1.0

* Beta release of the Python SDK for server-side testing.
