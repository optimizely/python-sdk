class InvalidAttributeException(Exception):
  """ Raised when provided attribute is invalid. """
  pass


class InvalidExperimentException(Exception):
  """ Raised when provided experiment key is invalid. """
  pass


class InvalidGoalException(Exception):
  """ Raised when provided event key is invalid. """
  pass


class InvalidVariationException(Exception):
  """ Raised when provided variation is invalid. """
  pass
