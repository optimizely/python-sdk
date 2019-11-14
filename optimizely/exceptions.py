# Copyright 2016-2019, Optimizely
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


class InvalidAttributeException(Exception):
    """ Raised when provided attribute is invalid. """

    pass


class InvalidAudienceException(Exception):
    """ Raised when provided audience is invalid. """

    pass


class InvalidEventException(Exception):
    """ Raised when provided event key is invalid. """

    pass


class InvalidEventTagException(Exception):
    """ Raised when provided event tag is invalid. """

    pass


class InvalidExperimentException(Exception):
    """ Raised when provided experiment key is invalid. """

    pass


class InvalidGroupException(Exception):
    """ Raised when provided group ID is invalid. """

    pass


class InvalidInputException(Exception):
    """ Raised when provided datafile, event dispatcher, logger, event processor or error handler is invalid. """

    pass


class InvalidVariationException(Exception):
    """ Raised when provided variation is invalid. """

    pass


class UnsupportedDatafileVersionException(Exception):
    """ Raised when provided version in datafile is not supported. """

    pass
