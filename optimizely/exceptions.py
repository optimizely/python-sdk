class InvalidAttributeException(Exception):
  """ Raised when provided attribute is invalid. """
  pass


class InvalidAudienceException(Exception):
  """ Raised when provided audience is invalid. """
  pass


class InvalidExperimentException(Exception):
  """ Raised when provided experiment key is invalid. """
  pass


class InvalidEventException(Exception):
  """ Raised when provided event key is invalid. """
  pass


class InvalidGroupException(Exception):
  """ Raised when provided group ID is invalid. """
  pass


class InvalidInputException(Exception):
  """ Raised when provided datafile, event dispatcher, logger or error handler is invalid. """
  pass


class InvalidVariationException(Exception):
  """ Raised when provided variation is invalid. """
  pass
