# Optimizely Python SDK

[![PyPI version](https://badge.fury.io/py/optimizely-sdk.svg)](https://pypi.org/project/optimizely-sdk)
[![Build Status](https://travis-ci.org/optimizely/python-sdk.svg?branch=master)](https://travis-ci.org/optimizely/python-sdk)
[![Coverage Status](https://coveralls.io/repos/github/optimizely/python-sdk/badge.svg)](https://coveralls.io/github/optimizely/python-sdk)
[![Documentation Status](https://readthedocs.org/projects/optimizely-python-sdk/badge/?version=latest)](https://optimizely-python-sdk.readthedocs.io/en/latest/?badge=latest)
[![Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)

This repository houses the official Python SDK for use with Optimizely
Full Stack and Optimizely Rollouts.

Optimizely Full Stack is A/B testing and feature flag management for
product development teams. Experiment in any application. Make every
feature on your roadmap an opportunity to learn. Learn more at
<https://www.optimizely.com/platform/full-stack/>, or see the [Full
Stack
documentation](https://docs.developers.optimizely.com/full-stack/docs).

Optimizely Rollouts is free feature flags for development teams. Easily
roll out and roll back features in any application without code deploys.
Mitigate risk for every feature on your roadmap. Learn more at
<https://www.optimizely.com/rollouts/>, or see the [Rollouts
documentation](https://docs.developers.optimizely.com/rollouts/docs).

## Getting Started

### Installing the SDK

The SDK is available through [PyPi](https://pypi.python.org/pypi?name=optimizely-sdk&:action=display).

To install:

    pip install optimizely-sdk

### Feature Management Access

To access the Feature Management configuration in the Optimizely
dashboard, please contact your Optimizely account executive.

### Using the SDK

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

#### PollingConfigManager

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

#### AuthDatafilePollingConfigManager

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

#### Advanced configuration

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

For Further details see the Optimizely [Full Stack documentation](https://docs.developers.optimizely.com/full-stack/docs)
to learn how to set up your first Python project and use the SDK.

## Development

### Building the SDK

Build and install the SDK with pip, using the following command:

    pip install -e .

### Unit tests

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
