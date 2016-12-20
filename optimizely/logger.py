# Copyright 2016, Optimizely
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
