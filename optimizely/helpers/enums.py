import logging


class HTTPVerbs(object):
  GET = 'GET'
  POST = 'POST'


class LogLevels(object):
  NOTSET = logging.NOTSET
  DEBUG = logging.DEBUG
  INFO = logging.INFO
  WARNING = logging.WARNING
  ERROR = logging.ERROR
  CRITICAL = logging.CRITICAL


class Errors(object):
  INVALID_INPUT_ERROR = 'Provided "{}" is in an invalid format.'
  INVALID_ATTRIBUTE_ERROR = 'Provided attribute is not in datafile.'
  INVALID_ATTRIBUTE_FORMAT = 'Attributes provided are in an invalid format.'
  INVALID_AUDIENCE_ERROR = 'Provided audience is not in datafile.'
  INVALID_EXPERIMENT_KEY_ERROR = 'Provided experiment is not in datafile.'
  INVALID_EVENT_KEY_ERROR = 'Provided event is not in datafile.'
  INVALID_DATAFILE = 'Datafile has invalid format. Failing "{}".'
  INVALID_GROUP_ID_ERROR = 'Provided group is not in datafile.'
  INVALID_VARIATION_ERROR = 'Provided variation is not in datafile.'
  UNSUPPORTED_DATAFILE_VERSION = 'Provided datafile has unsupported version.'
