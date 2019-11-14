# Copyright 2016, 2018-2019, Optimizely
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
import warnings

from .helpers import enums


_DEFAULT_LOG_FORMAT = '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s:%(message)s'


def reset_logger(name, level=None, handler=None):
    """
  Make a standard python logger object with default formatter, handler, etc.

  Defaults are:
    - level == logging.INFO
    - handler == logging.StreamHandler()

  Args:
    name: a logger name.
    level: an optional initial log level for this logger.
    handler: an optional initial handler for this logger.

  Returns: a standard python logger with a single handler.

  """
    # Make the logger and set its level.
    if level is None:
        level = logging.INFO
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Make the handler and attach it.
    handler = handler or logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_DEFAULT_LOG_FORMAT))

    # We don't use ``.addHandler``, since this logger may have already been
    # instantiated elsewhere with a different handler. It should only ever
    # have one, not many.
    logger.handlers = [handler]
    return logger


class BaseLogger(object):
    """ Class encapsulating logging functionality. Override with your own logger providing log method. """

    @staticmethod
    def log(*args):
        pass  # pragma: no cover


class NoOpLogger(BaseLogger):
    """ Class providing log method which logs nothing. """

    def __init__(self):
        self.logger = reset_logger(
            name='.'.join([__name__, self.__class__.__name__]), level=logging.NOTSET, handler=logging.NullHandler(),
        )


class SimpleLogger(BaseLogger):
    """ Class providing log method which logs to stdout. """

    def __init__(self, min_level=enums.LogLevels.INFO):
        self.level = min_level
        self.logger = reset_logger(name='.'.join([__name__, self.__class__.__name__]), level=min_level)

    def log(self, log_level, message):
        # Log a deprecation/runtime warning.
        # Clients should be using standard loggers instead of this wrapper.
        warning = '{} is deprecated. Please use standard python loggers.'.format(self.__class__)
        warnings.warn(warning, DeprecationWarning)

        # Log the message.
        self.logger.log(log_level, message)


def adapt_logger(logger):
    """
  Adapt our custom logger.BaseLogger object into a standard logging.Logger object.

  Adaptations are:
    - NoOpLogger turns into a logger with a single NullHandler.
    - SimpleLogger turns into a logger with a StreamHandler and level.

  Args:
    logger: Possibly a logger.BaseLogger, or a standard python logging.Logger.

  Returns: a standard python logging.Logger.

  """
    if isinstance(logger, logging.Logger):
        return logger

    # Use the standard python logger created by these classes.
    if isinstance(logger, (SimpleLogger, NoOpLogger)):
        return logger.logger

    # Otherwise, return whatever we were given because we can't adapt.
    return logger
