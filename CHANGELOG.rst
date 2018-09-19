2.1.1
-----

August 21st, 2018

-  Fix: record conversions for all experiments using an event when using
   track(\ `#136`_).

.. _section-1:

2.1.0
-----

July 2nd, 2018

-  Introduced support for bot filtering (`#121`_).
-  Overhauled logging to use standard Python logging (`#123`_).

.. _section-2:

2.0.1
-----

June 19th, 2018

-  Fix: send impression event for Feature Test when Feature is disabled
   (`#128`_).

.. _section-3:

2.0.0
-----

April 12th, 2018

This major release introduces APIs for Feature Management. It also
introduces some breaking changes listed below.

New Features
~~~~~~~~~~~~

-  Introduced the ``is_feature_enabled`` API to determine whether to
   show a feature to a user or not.

::

   is_enabled = optimizel_client.is_feature_enabled('my_feature_key', 'my_user', user_attributes)

-  All enabled features for the user can be retrieved by calling:

::

   enabled_features = optimizely_client.get_enabled_features('my_user', user_attributes)

-  Introduced Feature Variables to configure or parameterize a feature.
   There are four variable types: ``String``, ``Integer``, ``Double``,
   ``Boolean``.

::

   string_variable = optimizely_client.get_feature_variable_string('my_feature_key', 'string_variable_key', 'my_user')
   integer_variable = optimizely_client.get_feature_variable_integer('my_feature_key', 'integer_variable_key', 'my_user')
   double_variable = optimizely_client.get_feature_variable_double('my_feature_key', 'double_variable_key', 'my_user')
   boolean_variable = optimizely_client.get_feature_variable_boolean('my_feature_key', 'boolean_variable_key', 'my_user')

Breaking changes
~~~~~~~~~~~~~~~~

-  The ``track`` API with revenue value as a stand-alone parameter has
   been removed. The revenue value should be passed in as an entry in
   the event tags dict. The key for the revenue tag is ``revenue`` and
   the passed in value will be treated by Optimizely as the value for
   computing results.

::

   event_tags = {
     'revenue': 1200
   }

   optimizely_client.track('event_key', 'my_user', user_attributes, event_tags)

2.0.0b1
-------

March 29th, 2018

This beta release introduces APIs for Feature Management. It also
introduces some breaking changes listed below.

.. _new-features-1:

New Features
~~~~~~~~~~~~

-  Introduced the ``is_feature_enabled`` API to determine whether to
   show a feature to a user or not.

::

   is_enabled = optimizel_client.is_feature_enabled('my_feature_key', 'my_user', user_attributes)

-  All enabled features for the user can be retrieved by calling:

::

   enabled_features = optimizely_client.get_enabled_features('my_user', user_attributes)

-  Introduced Feature Variables to configure or parameterize a feature.
   There are four variable types: ``String``, ``Integer``, ``Double``,
   ``Boolean``. \``\` string_variable =
   optimizely_client.get_feature_variable_string(‘my_feature_key’,
   ‘string_variable_key’, ‘my_user’) integer_variable =
   optimizely_client.get_feature_variable_integer(’my_fea

.. _#136: https://github.com/optimizely/python-sdk/pull/136
.. _#121: https://github.com/optimizely/python-sdk/pull/121
.. _#123: https://github.com/optimizely/python-sdk/pull/123
.. _#128: https://github.com/optimizely/python-sdk/pull/128