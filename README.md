# Optimizely Python SDK

[![PyPI version](https://badge.fury.io/py/optimizely-sdk.svg)](https://pypi.org/project/optimizely-sdk)
[![Build Status](https://github.com/optimizely/python-sdk/actions/workflows/python.yml/badge.svg?branch=master)](https://github.com/optimizely/python-sdk/actions/workflows/python.yml?query=branch%3Amaster)
[![Coverage Status](https://coveralls.io/repos/github/optimizely/python-sdk/badge.svg)](https://coveralls.io/github/optimizely/python-sdk)
[![Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)

This repository houses the Python SDK for use with Optimizely Feature Experimentation and Optimizely Full Stack (legacy).

Optimizely Feature Experimentation is an A/B testing and feature management tool for product development teams that enables you to experiment at every step. Using Optimizely Feature Experimentation allows for every feature on your roadmap to be an opportunity to discover hidden insights. Learn more at [Optimizely.com](https://www.optimizely.com/products/experiment/feature-experimentation/), or see the [developer documentation](https://docs.developers.optimizely.com/experimentation/v4.0.0-full-stack/docs/welcome).

Optimizely Rollouts is [free feature flags](https://www.optimizely.com/free-feature-flagging/) for development teams. You can easily roll out and roll back features in any application without code deploys, mitigating risk for every feature on your roadmap.

## Get Started

Refer to the [Python SDK's developer documentation](https://docs.developers.optimizely.com/experimentation/v4.0.0-full-stack/docs/python-sdk) for detailed instructions on getting started with using the SDK.

### Requirements

Version `5.0+`: Python 3.8+, PyPy 3.8+

Version `4.0+`: Python 3.7+, PyPy 3.7+

Version `3.0+`: Python 2.7+, PyPy 3.4+

### Install the SDK

The SDK is available through [PyPi](https://pypi.python.org/pypi?name=optimizely-sdk&:action=display).

To install:

    pip install optimizely-sdk

### Feature Management Access

To access the Feature Management configuration in the Optimizely
dashboard, please contact your Optimizely customer success manager.

## Use the Python SDK

### Initialization

You can initialize the Optimizely instance in three ways: with a datafile, by providing an sdk_key, or by providing an implementation of
[BaseConfigManager](https://github.com/optimizely/python-sdk/tree/master/optimizely/config_manager.py#L32).
Each method is described below.

1.  Initialize Optimizely with a datafile. This datafile will be used as
    the source of ProjectConfig throughout the life of Optimizely instance:

        optimizely.Optimizely(
          datafile
        )

2.  Initialize Optimizely by providing an \'sdk_key\'. This will
    initialize a PollingConfigManager that makes an HTTP GET request to
    the URL (formed using your provided sdk key and the
    default datafile CDN URL template) to asynchronously download the
    project datafile at regular intervals and update ProjectConfig when
    a new datafile is received. A hard-coded datafile can also be
    provided along with the sdk_key that will be used
    initially before any update:

        optimizely.Optimizely(
          sdk_key='put_your_sdk_key_here'
        )

    If providing a datafile, the initialization will look like:

        optimizely.Optimizely(
          datafile=datafile,
          sdk_key='put_your_sdk_key_here'
        )

3.  Initialize Optimizely by providing a ConfigManager that implements
    [BaseConfigManager](https://github.com/optimizely/python-sdk/tree/master/optimizely/config_manager.py#L34).
    You may use our [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/master/optimizely/config_manager.py#L150) or
    [AuthDatafilePollingConfigManager](https://github.com/optimizely/python-sdk/blob/master/optimizely/config_manager.py#L375) as needed:

        optimizely.Optimizely(
          config_manager=custom_config_manager
        )

### PollingConfigManager

The [PollingConfigManager](https://github.com/optimizely/python-sdk/blob/master/optimizely/config_manager.py#L150) asynchronously polls for
datafiles from a specified URL at regular intervals by making HTTP requests.

    polling_config_manager = PollingConfigManager(
        sdk_key=None,
        datafile=None,
        update_interval=None,
        url=None,
        url_template=None,
        logger=None,
        error_handler=None,
        notification_center=None,
        skip_json_validation=False
    )

**Note**: You must provide either the sdk_key or URL. If
you provide both, the URL takes precedence.

**sdk_key** The sdk_key is used to compose the outbound
HTTP request to the default datafile location on the Optimizely CDN.

**datafile** You can provide an initial datafile to bootstrap the
`ProjectConfigManager` so that it can be used immediately. The initial
datafile also serves as a fallback datafile if HTTP connection cannot be
established. The initial datafile will be discarded after the first
successful datafile poll.

**update_interval** The update_interval is used to specify a fixed
delay in seconds between consecutive HTTP requests for the datafile.

**url** The target URL from which to request the datafile.

**url_template** A string with placeholder `{sdk_key}` can be provided
so that this template along with the provided sdk key is
used to form the target URL.

You may also provide your own logger, error_handler, or
notification_center.

### AuthDatafilePollingConfigManager

The [AuthDatafilePollingConfigManager](https://github.com/optimizely/python-sdk/blob/master/optimizely/config_manager.py#L375)
implements `PollingConfigManager` and asynchronously polls for authenticated datafiles from a specified URL at regular intervals
by making HTTP requests.

    auth_datafile_polling_config_manager = AuthDatafilePollingConfigManager(
        datafile_access_token,
        *args,
        **kwargs
    )

**Note**: To use [AuthDatafilePollingConfigManager](#authdatafilepollingconfigmanager), you must create a secure environment for
your project and generate an access token for your datafile.

**datafile_access_token** The datafile_access_token is attached to the outbound HTTP request header to authorize the request and fetch the datafile.

### Advanced configuration

The following properties can be set to override the default
configurations for [PollingConfigManager](#pollingconfigmanager) and [AuthDatafilePollingConfigManager](#authdatafilepollingconfigmanager).

| **Property Name** |                                                                                    **Default Value**                                                                                    |                        **Description**                         |
| :---------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------: |
|      sdk_key      |                                                                                          None                                                                                           |                   Optimizely project SDK key                   |
|     datafile      |                                                                                          None                                                                                           | Initial datafile, typically sourced from a local cached source |
|  update_interval  |                                                                                        5 minutes                                                                                        |          Fixed delay between fetches for the datafile          |
|        url        |                                                                                          None                                                                                           |      Custom URL location from which to fetch the datafile      |
|   url_template    | `PollingConfigManager:`<br/>https://cdn.optimizely.com/datafiles/{sdk_key}.json<br/>`AuthDatafilePollingConfigManager:`<br/>https://config.optimizely.com/datafiles/auth/{sdk_key}.json |             Parameterized datafile URL by SDK key              |

A notification signal will be triggered whenever a _new_ datafile is
fetched and Project Config is updated. To subscribe to these
notifications, use:

```
notification_center.add_notification_listener(NotificationTypes.OPTIMIZELY_CONFIG_UPDATE, update_callback)
```

For Further details see the Optimizely [Feature Experimentation documentation](https://docs.developers.optimizely.com/experimentation/v4.0.0-full-stack/docs/welcome)
to learn how to set up your first Python project and use the SDK.

## SDK Development

### Building the SDK

Build and install the SDK with pip, using the following command:

    pip install -e .

### Unit Tests

#### Running all tests

To get test dependencies installed, use a modified version of the
install command:

    pip install -e '.[test]'

You can run all unit tests with:

    pytest

#### Running all tests in a file

To run all tests under a particular test file you can use the following
command:

    pytest tests.<file_name_without_extension>

For example, to run all tests under `test_event_builder`, the command would be:

    pytest tests/test_event_builder.py

#### Running all tests under a class

To run all tests under a particular class of tests you can use the
following command:

    pytest tests/<file_name_with_extension>::ClassName

For example, to run all tests under `test_event_builder.EventTest`, the command
would be:

    pytest tests/test_event_builder.py::EventTest

#### Running a single test

To run a single test you can use the following command:

    pytest tests/<file_name_with_extension>::ClassName::test_name

For example, to run `test_event_builder.EventTest.test_init`, the command
would be:

    pytest tests/test_event_builder.py::EventTest::test_init

### Contributing

Please see [CONTRIBUTING](https://github.com/optimizely/python-sdk/blob/master/CONTRIBUTING.md).

### Credits

This software incorporates code from the following open source projects:

requests (Apache-2.0 License: https://github.com/psf/requests/blob/master/LICENSE)

idna (BSD 3-Clause License https://github.com/kjd/idna/blob/master/LICENSE.md)

### Other Optimizely SDKs

- Agent - https://github.com/optimizely/agent

- Android - https://github.com/optimizely/android-sdk

- C# - https://github.com/optimizely/csharp-sdk

- Flutter - https://github.com/optimizely/optimizely-flutter-sdk

- Go - https://github.com/optimizely/go-sdk

- Java - https://github.com/optimizely/java-sdk

- JavaScript - https://github.com/optimizely/javascript-sdk

- PHP - https://github.com/optimizely/php-sdk

- Python - https://github.com/optimizely/python-sdk

- React - https://github.com/optimizely/react-sdk

- Ruby - https://github.com/optimizely/ruby-sdk

- Swift - https://github.com/optimizely/swift-sdk
