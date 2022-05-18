# Copyright 2016, 2018, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import unittest
import uuid

from unittest import mock

from optimizely import logger as _logger


class SimpleLoggerTests(unittest.TestCase):
    def test_log__deprecation_warning(self):
        """Test that SimpleLogger now outputs a deprecation warning on ``.log`` calls."""
        simple_logger = _logger.SimpleLogger()
        actual_log_patch = mock.patch.object(simple_logger, 'logger')
        warnings_patch = mock.patch('warnings.warn')
        with warnings_patch as patched_warnings, actual_log_patch as log_patch:
            simple_logger.log(logging.INFO, 'Message')

        msg = "<class 'optimizely.logger.SimpleLogger'> is deprecated. " "Please use standard python loggers."
        patched_warnings.assert_called_once_with(msg, DeprecationWarning)
        log_patch.log.assert_called_once_with(logging.INFO, 'Message')


class AdaptLoggerTests(unittest.TestCase):
    def test_adapt_logger__standard_logger(self):
        """Test that adapt_logger does nothing to standard python loggers."""
        logger_name = str(uuid.uuid4())
        standard_logger = logging.getLogger(logger_name)
        adapted = _logger.adapt_logger(standard_logger)
        self.assertIs(standard_logger, adapted)

    def test_adapt_logger__simple(self):
        """Test that adapt_logger returns a standard python logger from a SimpleLogger."""
        simple_logger = _logger.SimpleLogger()
        standard_logger = _logger.adapt_logger(simple_logger)

        # adapt_logger knows about the loggers attached to this class.
        self.assertIs(simple_logger.logger, standard_logger)

        # Verify the standard properties of the logger.
        self.assertIsInstance(standard_logger, logging.Logger)
        self.assertEqual('optimizely.logger.SimpleLogger', standard_logger.name)
        self.assertEqual(logging.INFO, standard_logger.level)

        # Should have a single StreamHandler with our default formatting.
        self.assertEqual(1, len(standard_logger.handlers))
        handler = standard_logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(
            '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s:%(message)s', handler.formatter._fmt,
        )

    def test_adapt_logger__noop(self):
        """Test that adapt_logger returns a standard python logger from a NoOpLogger."""
        noop_logger = _logger.NoOpLogger()
        standard_logger = _logger.adapt_logger(noop_logger)

        # adapt_logger knows about the loggers attached to this class.
        self.assertIs(noop_logger.logger, standard_logger)

        # Verify properties of the logger
        self.assertIsInstance(standard_logger, logging.Logger)
        self.assertEqual('optimizely.logger.NoOpLogger', standard_logger.name)
        self.assertEqual(logging.NOTSET, standard_logger.level)

        # Should have a single NullHandler (with a default formatter).
        self.assertEqual(1, len(standard_logger.handlers))
        handler = standard_logger.handlers[0]
        self.assertIsInstance(handler, logging.NullHandler)
        self.assertEqual(
            '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s:%(message)s', handler.formatter._fmt,
        )

    def test_adapt_logger__unknown(self):
        """Test that adapt_logger gives back things it can't adapt."""
        obj = object()
        value = _logger.adapt_logger(obj)
        self.assertIs(obj, value)


class GetLoggerTests(unittest.TestCase):
    def test_reset_logger(self):
        """Test that reset_logger gives back a standard python logger with defaults."""
        logger_name = str(uuid.uuid4())
        logger = _logger.reset_logger(logger_name)
        self.assertEqual(logger_name, logger.name)
        self.assertEqual(1, len(logger.handlers))
        handler = logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(
            '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s:%(message)s', handler.formatter._fmt,
        )

    def test_reset_logger__replaces_handlers(self):
        """Test that reset_logger replaces existing handlers with a StreamHandler."""
        logger_name = f'test-logger-{uuid.uuid4()}'
        logger = logging.getLogger(logger_name)
        logger.handlers = [logging.StreamHandler() for _ in range(10)]

        reset_logger = _logger.reset_logger(logger_name)
        self.assertEqual(1, len(reset_logger.handlers))

        handler = reset_logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(
            '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s:%(message)s', handler.formatter._fmt,
        )

    def test_reset_logger__with_handler__existing(self):
        """Test that reset_logger deals with provided handlers correctly."""
        existing_handler = logging.NullHandler()
        logger_name = f'test-logger-{uuid.uuid4()}'
        reset_logger = _logger.reset_logger(logger_name, handler=existing_handler)
        self.assertEqual(1, len(reset_logger.handlers))

        handler = reset_logger.handlers[0]
        self.assertIs(existing_handler, handler)
        self.assertEqual(
            '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s:%(message)s', handler.formatter._fmt,
        )

    def test_reset_logger__with_level(self):
        """Test that reset_logger sets log levels correctly."""
        logger_name = f'test-logger-{uuid.uuid4()}'
        reset_logger = _logger.reset_logger(logger_name, level=logging.DEBUG)
        self.assertEqual(logging.DEBUG, reset_logger.level)
