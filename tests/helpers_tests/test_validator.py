import json

from optimizely import error_handler
from optimizely import event_dispatcher
from optimizely import logger
from optimizely.helpers import validator

from tests import base


class ValidatorTest(base.BaseTestV1):

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


class DatafileV2ValidationTests(base.BaseTestV2):

  def test_is_datafile_valid__returns_true(self):
    """ Test that valid datafile returns True. """

    self.assertTrue(validator.is_datafile_valid(json.dumps(self.config_dict)))

  def test_is_datafile_valid__returns_false(self):
    """ Test that invalid datafile returns False. """

    self.assertFalse(validator.is_datafile_valid(json.dumps({
      'invalid_key': 'invalid_value'
    })))

