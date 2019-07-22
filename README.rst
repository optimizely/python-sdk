Optimizely Python SDK
=====================

|PyPI version| |Build Status| |Coverage Status| |Apache 2.0|

This repository houses the official Python SDK for use with Optimizely Full Stack and Optimizely Rollouts.

Optimizely Full Stack is A/B testing and feature flag management for product development teams. Experiment in any application. Make every feature on your roadmap an opportunity to learn. Learn more at https://www.optimizely.com/platform/full-stack/, or see the `Full Stack documentation`_.

Optimizely Rollouts is free feature flags for development teams. Easily roll out and roll back features in any application without code deploys. Mitigate risk for every feature on your roadmap. Learn more at https://www.optimizely.com/rollouts/, or see the `Rollouts documentation`_.

Getting Started
---------------

Installing the SDK
~~~~~~~~~~~~~~~~~~

The SDK is available through `PyPi`_. To install:

::

   pip install optimizely-sdk

Feature Management Access
~~~~~~~~~~~~~~~~~~~~~~~~~

To access the Feature Management configuration in the Optimizely
dashboard, please contact your Optimizely account executive.

Using the SDK
~~~~~~~~~~~~~

See the Optimizely `Full Stack documentation`_ to learn how to
set up your first Python project and use the SDK.

Development
-----------

Building the SDK
~~~~~~~~~~~~~~~~

Build and install the SDK with pip, using the following command:

::

   pip install -e .

Unit tests
~~~~~~~~~~

Running all tests
'''''''''''''''''

To get test dependencies installed, use a modified version of the
install command:

::

   pip install -e .[test]

You can run all unit tests with:

::

   nosetests

Running all tests in a file
'''''''''''''''''''''''''''

To run all tests under a particular test file you can use the following
command:

::

   nosetests tests.<file_name_without_extension>

For example, to run all tests under ``test_event``, the command would
be:

::

   nosetests tests.test_event

Running all tests under a class
'''''''''''''''''''''''''''''''

To run all tests under a particular class of tests you can use the
following command:

::

   nosetests tests.<file_name_without_extension>:ClassName

For example, to run all tests under ``test_event.EventTest``, the
command would be:

::

   nosetests tests.test_event:EventTest

Running a single test
'''''''''''''''''''''

To run a single test you can use the following command:

::

   nosetests tests.<file_name_without_extension>:ClassName.test_name

For example, to run ``test_event.EventTest.test_dispatch``, the command
would be:

::

   nosetests tests.test_event:EventTest.test_dispatch

Contributing
~~~~~~~~~~~~

Please see `CONTRIBUTING`_.

.. _PyPi: https://pypi.python.org/pypi?name=optimizely-sdk&:action=display
.. _Full Stack documentation: https://docs.developers.optimizely.com/full-stack/docs
.. _Rollouts documentation: https://docs.developers.optimizely.com/rollouts/docs
.. _CONTRIBUTING: CONTRIBUTING.rst

.. |PyPI version| image:: https://badge.fury.io/py/optimizely-sdk.svg
   :target: https://pypi.org/project/optimizely-sdk
.. |Build Status| image:: https://travis-ci.org/optimizely/python-sdk.svg?branch=master
   :target: https://travis-ci.org/optimizely/python-sdk
.. |Coverage Status| image:: https://coveralls.io/repos/github/optimizely/python-sdk/badge.svg
   :target: https://coveralls.io/github/optimizely/python-sdk
.. |Apache 2.0| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: http://www.apache.org/licenses/LICENSE-2.0
