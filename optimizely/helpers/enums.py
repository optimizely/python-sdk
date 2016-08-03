import logging


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
  INVALID_EXPERIMENT_KEY_ERROR = 'Provided experiment is not in datafile.'
  INVALID_EVENT_KEY_ERROR = 'Provided event is not in datafile.'
  INVALID_GROUP_ID_ERROR = 'Provided group is not in datafile.'
  INVALID_VARIATION_ERROR = 'Provided variation is not in datafile.'
