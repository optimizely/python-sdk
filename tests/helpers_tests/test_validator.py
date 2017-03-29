# Copyright 2016-2017, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from optimizely import error_handler
from optimizely import event_dispatcher
from optimizely import logger
from optimizely import project_config
from optimizely.helpers import validator

from tests import base


class ValidatorTest(base.BaseTest):

  def test_is_datafile_valid__returns_true(self):
    """ Test that valid datafile returns True. """

    self.assertTrue(validator.is_datafile_valid(json.dumps(self.config_dict)))

  def test_is_datafile_valid__returns_false(self):
    """ Test that invalid datafile returns False. """

    self.assertFalse(validator.is_datafile_valid(json.dumps({
      'invalid_key': 'invalid_value'
    })))

  def test_is_event_dispatcher_valid__returns_true(self):
    """ Test that valid event_dispatcher returns True. """

    self.assertTrue(validator.is_event_dispatcher_valid(event_dispatcher.EventDispatcher))

  def test_is_event_dispatcher_valid__returns_false(self):
    """ Test that invalid event_dispatcher returns False. """

    class CustomEventDispatcher(object):
      def some_other_method(self):
        pass

    self.assertFalse(validator.is_event_dispatcher_valid(CustomEventDispatcher))

  def test_is_logger_valid__returns_true(self):
    """ Test that valid logger returns True. """

    self.assertTrue(validator.is_logger_valid(logger.NoOpLogger))

  def test_is_logger_valid__returns_false(self):
    """ Test that invalid logger returns False. """

    class CustomLogger(object):
      def some_other_method(self):
        pass

    self.assertFalse(validator.is_logger_valid(CustomLogger))

  def test_is_error_handler_valid__returns_true(self):
    """ Test that valid error_handler returns True. """

    self.assertTrue(validator.is_error_handler_valid(error_handler.NoOpErrorHandler))

  def test_is_error_handler_valid__returns_false(self):
    """ Test that invalid error_handler returns False. """

    class CustomErrorHandler(object):
      def some_other_method(self):
        pass

    self.assertFalse(validator.is_error_handler_valid(CustomErrorHandler))

  def test_are_attributes_valid__returns_true(self):
    """ Test that valid attributes returns True. """

    self.assertTrue(validator.are_attributes_valid({'key': 'value'}))

  def test_are_attributes_valid__returns_false(self):
    """ Test that invalid attributes returns False. """

    self.assertFalse(validator.are_attributes_valid('key:value'))
    self.assertFalse(validator.are_attributes_valid(['key', 'value']))
    self.assertFalse(validator.are_attributes_valid(42))

  def test_are_event_tags_valid__returns_true(self):
    """ Test that valid event tags returns True. """

    self.assertTrue(validator.are_event_tags_valid({'key': 'value', 'revenue': 0}))

  def test_are_event_tags_valid__returns_false(self):
    """ Test that invalid event tags returns False. """

    self.assertFalse(validator.are_event_tags_valid('key:value'))
    self.assertFalse(validator.are_event_tags_valid(['key', 'value']))
    self.assertFalse(validator.are_event_tags_valid(42))


class DatafileValidationTests(base.BaseTest):

  def test_is_datafile_valid__returns_true(self):
    """ Test that valid datafile returns True. """

    self.assertTrue(validator.is_datafile_valid(json.dumps(self.config_dict)))

  def test_is_datafile_valid__returns_false(self):
    """ Test that invalid datafile returns False. """

    # When schema is not valid
    self.assertFalse(validator.is_datafile_valid(json.dumps({
      'invalid_key': 'invalid_value'
    })))

    # When schema is valid, but datafile has unsupported version
    self.config_dict['version'] = project_config.UNSUPPORTED_VERSIONS[0]
    self.assertFalse(validator.is_datafile_valid(json.dumps(self.config_dict)))
