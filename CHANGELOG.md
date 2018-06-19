## 2.0.1
June 19th, 2018

- Fix: send impression event for Feature Test when Feature is disabled ([#128](https://github.com/optimizely/python-sdk/pull/128)).

## 2.0.0
April 12th, 2018

This major release introduces APIs for Feature Management. It also introduces some breaking changes listed below.

### New Features
- Introduced the `is_feature_enabled` API to determine whether to show a feature to a user or not.
```
is_enabled = optimizel_client.is_feature_enabled('my_feature_key', 'my_user', user_attributes)
```

- All enabled features for the user can be retrieved by calling:
```
enabled_features = optimizely_client.get_enabled_features('my_user', user_attributes)
```

- Introduced Feature Variables to configure or parameterize a feature. There are four variable types: `String`, `Integer`, `Double`, `Boolean`.
```
string_variable = optimizely_client.get_feature_variable_string('my_feature_key', 'string_variable_key', 'my_user')
integer_variable = optimizely_client.get_feature_variable_integer('my_feature_key', 'integer_variable_key', 'my_user')
double_variable = optimizely_client.get_feature_variable_double('my_feature_key', 'double_variable_key', 'my_user')
boolean_variable = optimizely_client.get_feature_variable_boolean('my_feature_key', 'boolean_variable_key', 'my_user')
```

### Breaking changes
- The `track` API with revenue value as a stand-alone parameter has been removed. The revenue value should be passed in as an entry in the event tags dict. The key for the revenue tag is `revenue` and the passed in value will be treated by Optimizely as the value for computing results.
```
event_tags = {
  'revenue': 1200
}

optimizely_client.track('event_key', 'my_user', user_attributes, event_tags)
```

## 2.0.0b1
March 29th, 2018

This beta release introduces APIs for Feature Management. It also introduces some breaking changes listed below.

### New Features
- Introduced the `is_feature_enabled` API to determine whether to show a feature to a user or not.
```
is_enabled = optimizel_client.is_feature_enabled('my_feature_key', 'my_user', user_attributes)
```

- All enabled features for the user can be retrieved by calling:
```
enabled_features = optimizely_client.get_enabled_features('my_user', user_attributes)
```

- Introduced Feature Variables to configure or parameterize a feature. There are four variable types: `String`, `Integer`, `Double`, `Boolean`.
```
string_variable = optimizely_client.get_feature_variable_string('my_feature_key', 'string_variable_key', 'my_user')
integer_variable = optimizely_client.get_feature_variable_integer('my_feature_key', 'integer_variable_key', 'my_user')
double_variable = optimizely_client.get_feature_variable_double('my_feature_key', 'double_variable_key', 'my_user')
boolean_variable = optimizely_client.get_feature_variable_boolean('my_feature_key', 'boolean_variable_key', 'my_user')
```

### Breaking changes
- The `track` API with revenue value as a stand-alone parameter has been removed. The revenue value should be passed in as an entry in the event tags dict. The key for the revenue tag is `revenue` and the passed in value will be treated by Optimizely as the value for computing results.
```
event_tags = {
  'revenue': 1200
}

optimizely_client.track('event_key', 'my_user', user_attributes, event_tags)
```

## 1.4.0
- Added support for IP anonymization.
- Added support for notification listeners.
- Added support for bucketing ID.
- Updated mmh3 to handle installation failures on Windows 10.

## 1.3.0
- Introduced support for forced bucketing.
- Introduced support for numeric metrics.
- Updated event builder to support new endpoint.

## 1.2.1
- Removed older feature flag parsing.

## 1.2.0
- Added user profile service.

## 1.1.1
- Updated datafile parsing to be able to handle additional fields.
- Deprecated Classic project support.

## 1.1.0
- Included datafile revision information in log events.
- Added event tags to track API to allow users to pass in event metadata.
- Deprecated the `event_value` parameter from the track method. Should use `event_tags` to pass in event value instead.
- Updated event logging endpoint to logx.optimizely.com.

## 1.0.0
- Introduced support for Full Stack projects in Optimizely X. No breaking changes from previous version.
- Introduced more graceful exception handling in instantiation and core methods.
- Updated whitelisting to precede audience matching.

## 0.1.3
- Added support for v2 endpoint and datafile.
- Updated dispatch_event to consume an Event object instead of url and params. The Event object comprises of four properties: url (string representing URL to dispatch event to), params (dict representing the params to be set for the event), http_verb (one of 'GET' or 'POST') and headers (header values to be sent along).
- Fixed issue with tracking events for experiments in groups.

## 0.1.2
- Updated requirements file.

## 0.1.1
- Introduced option to skip JSON schema validation.

## 0.1.0
- Beta release of the Python SDK for server-side testing.