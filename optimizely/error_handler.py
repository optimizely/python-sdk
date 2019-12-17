# Copyright 2016, Optimizely
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


class BaseErrorHandler(object):
    """ Class encapsulating exception handling functionality.
  Override with your own exception handler providing handle_error method. """

    @staticmethod
    def handle_error(*args):
        pass


class NoOpErrorHandler(BaseErrorHandler):
    """ Class providing handle_error method which suppresses the error. """


class RaiseExceptionErrorHandler(BaseErrorHandler):
    """ Class providing handle_error method which raises provided exception. """

    @staticmethod
    def handle_error(error):
        raise error
