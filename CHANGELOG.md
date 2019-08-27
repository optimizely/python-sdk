# Optimizely Python SDK Changelog

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
  * Strings, booleans, and valid numbers are passed to the event dispatcher and can be used for Optimizely results segmentation.  A valid number is a finite float or numbers.Integral in the inclusive range \[-2⁵³, 2⁵³\].
  * Strings, booleans, and valid numbers are relevant for audience conditions.
* Support for additional matchers in audience conditions:
  * An `exists` matcher that passes if the user has a non-null value for the targeted user attribute and fails otherwise.
  * A `substring` matcher that resolves if the user has a string value for the targeted attribute.
    * `gt` (greater than) and `lt` (less than) matchers that resolve if the user has a valid number value for the targeted attribute.  A valid number is a finite float or numbers.Integral in the inclusive range \[-2⁵³, 2⁵³\].
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
