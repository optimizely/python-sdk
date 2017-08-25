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
