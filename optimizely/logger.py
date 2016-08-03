import inspect
import logging

from .helpers import enums


class BaseLogger(object):
  """ Class encapsulating logging functionality. Override with your own logger providing log method. """

  @staticmethod
  def log(*args):
    pass


class NoOpLogger(BaseLogger):
  """ Class providing log method which logs nothing. """


class SimpleLogger(BaseLogger):
  """ Class providing log method which logs to stdout. """

  def __init__(self, min_level=enums.LogLevels.INFO):
    logging.basicConfig(level=min_level,
                        format='%(levelname)-8s %(asctime)s %(message)s')

  def log(self, log_level, message):
    # Figure out calling method and format message to include that information before logging
    caller = inspect.stack()[1][0]
    info = inspect.getframeinfo(caller)
    self.logger = logging.getLogger()
    message = '%s:%s:%s' % (info.filename, info.lineno, message)
    self.logger.log(log_level, message)
