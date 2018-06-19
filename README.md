# Optimizely Python SDK
[![PyPI version](https://badge.fury.io/py/optimizely-sdk.svg)](https://pypi.org/project/optimizely-sdk)
[![Build Status](https://travis-ci.org/optimizely/python-sdk.svg?branch=master)](https://travis-ci.org/optimizely/python-sdk)
[![Coverage Status](https://coveralls.io/repos/github/optimizely/python-sdk/badge.svg)](https://coveralls.io/github/optimizely/python-sdk)
[![Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)

This repository houses the Python SDK for Optimizely Full Stack.

## Getting Started

### Installing the SDK

The SDK is available through [PyPi](https://pypi.python.org/pypi?name=optimizely-sdk&:action=display). To install:

```
pip install optimizely-sdk
```

### Feature Management Access
To access the Feature Management configuration in the Optimizely dashboard, please contact your Optimizely account executive.

### Using the SDK
See the Optimizely Full Stack [developer documentation](http://developers.optimizely.com/server/reference/index.html) to learn how to set up your first Python project and use the SDK.

## Development

### Building the SDK

Build the SDK using the following command:

```
python setup.py sdist
```

This will create a tarball under `dist/`

You can then install the SDK and its dependencies with:

```
pip install dist/optimizely-sdk-{VERSION}.tar.gz
```

### Unit tests

##### Running all tests
You can run all unit tests with:

```
nosetests
```

##### Running all tests in a file
To run all tests under a particular test file you can use the following command:

```
nosetests tests.<file_name_without_extension>
```

For example, to run all tests under `test_event`, the command would be:

```
nosetests tests.test_event
```

##### Running all tests under a class
To run all tests under a particular class of tests you can use the following command:

```
nosetests tests.<file_name_without_extension>:ClassName
```

For example, to run all tests under `test_event.EventTest`, the command would be:
```
nosetests tests.test_event:EventTest
```

##### Running a single test
To run a single test you can use the following command:

```
nosetests tests.<file_name_without_extension>:ClassName.test_name
```

For example, to run `test_event.EventTest.test_dispatch`, the command would be:

```
nosetests tests.test_event:EventTest.test_dispatch
```

### Contributing

Please see [CONTRIBUTING](CONTRIBUTING.md).
