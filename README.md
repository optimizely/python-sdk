#Optimizely Python SDK 
[![Build Status](https://travis-ci.com/optimizely/optimizely-testing-sdk-python.svg?token=xoLe5GgfDMgLPXDntAq3&branch=master)](https://travis-ci.com/optimizely/optimizely-testing-sdk-python)
[![Coverage Status](https://coveralls.io/repos/github/optimizely/optimizely-testing-sdk-python/badge.svg?branch=master&t=YTzJg8)](https://coveralls.io/github/optimizely/optimizely-testing-sdk-python?branch=master)
[![Apache 2.0](https://img.shields.io/github/license/nebula-plugins/gradle-extra-configurations-plugin.svg)](http://www.apache.org/licenses/LICENSE-2.0) 

This Python SDK is an interface to the Optimizely testing framework allowing you to setup and manage your Custom experiments.

###Installing the SDK

Build the SDK using the following command:
```
python setup.py sdist
```

This will create a tarball under `dist/`

Install the SDK by typing the following command:
```
pip install optimizely-testing-sdk-python-{VERSION}.tar.gz
```

The install command will set up all requisite packages.

###Using the SDK

Instructions on using the SDK can be found [here](http://developers.optimizely.com/server/reference/index).

###Unit tests

#####Run all tests
You can trigger all unit tests by typing the following command:
```
nosetests
```

#####Run all tests in file
In order to run all tests under a particular test file you can run the following command:
```
nosetests tests.<file_name_without_extension>
```

For example to run all tests under `test_event`, the command would be:
```
nosetests tests.test_event
```

#####Run all tests under class
In order to run all tests under a particular class of tests you can run the following command:
```
nosetests tests.<file_name_without_extension>:ClassName
```

For example to run all tests under `test_event.EventTest`, the command would be:
```
nosetests tests.test_event:EventTest
```

#####Run single test
In order to run one single test the command would be:
```
nosetests tests.<file_name_without_extension>:ClassName:test_name
```

For example in order to run `test_event.EventTest.test_dispatch`, the command would be:
```
nosetests tests.test_event:EventTest.test_dispatch
```
