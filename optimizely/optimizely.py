from . import bucketer
from . import event_builder
from . import exceptions
from . import project_config
from .error_handler import NoOpErrorHandler as noop_error_handler
from .event_dispatcher import EventDispatcher as default_event_dispatcher
from .helpers import audience
from .helpers import enums
from .helpers import experiment
from .helpers import validator
from .logger import NoOpLogger as noop_logger


class Optimizely(object):
  """ Class encapsulating all SDK functionality. """

  def __init__(self, datafile, event_dispatcher=None, logger=None, error_handler=None, skip_json_validation=False):
    """ Optimizely init method for managing Custom projects.

    Args:
      datafile: JSON string representing the project.
      event_dispatcher: Provides a dispatch_event method which if given a URL and params sends a request to it.
      logger: Optional param which provides a log method to log messages. By default nothing would be logged.
      error_handler: Optional param which provides a handle_error method to handle exceptions.
                     By default all exceptions will be suppressed.
      skip_json_validation: Optional boolean param which allows skipping JSON schema validation upon object invocation.
                            By default JSON schema validation will be performed.
    """

    self.event_dispatcher = event_dispatcher or default_event_dispatcher
    self.logger = logger or noop_logger
    self.error_handler = error_handler or noop_error_handler
    self._validate_inputs(datafile, skip_json_validation)

    self.config = project_config.ProjectConfig(datafile, self.logger, self.error_handler)
    self.bucketer = bucketer.Bucketer(self.config)
    self.event_builder = event_builder.EventBuilder(self.config, self.bucketer)

  def _validate_inputs(self, datafile, skip_json_validation):
    """ Helper method to validate all input parameters.

    Args:
      datafile: JSON string representing the project.
      skip_json_validation: Boolean representing whether JSON schema validation needs to be skipped or not.

    Raises:
      Exception if provided input is invalid.
    """

    if not skip_json_validation and not validator.is_datafile_valid(datafile):
      raise Exception(enums.Errors.INVALID_INPUT_ERROR.format('datafile'))

    if not validator.is_event_dispatcher_valid(self.event_dispatcher):
      raise Exception(enums.Errors.INVALID_INPUT_ERROR.format('event_dispatcher'))

    if not validator.is_logger_valid(self.logger):
      raise Exception(enums.Errors.INVALID_INPUT_ERROR.format('logger'))

    if not validator.is_error_handler_valid(self.error_handler):
      raise Exception(enums.Errors.INVALID_INPUT_ERROR.format('error_handler'))

  def _validate_preconditions(self, experiment_key, user_id, attributes):
    """ Helper method to validate all pre-conditions before we go ahead to bucket user.

    Args:
      experiment_key: Key representing the experiment.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Boolean depending upon whether all conditions are met or not.
    """

    if attributes and not validator.are_attributes_valid(attributes):
      self.logger.log(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')
      self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_FORMAT))
      return False

    if not experiment.is_experiment_running(self.config, experiment_key):
      self.logger.log(enums.LogLevels.INFO, 'Experiment "%s" is not running.' % experiment_key)
      return False

    if not audience.is_user_in_experiment(self.config, experiment_key, attributes):
      self.logger.log(
        enums.LogLevels.INFO,
        'User "%s" does not meet conditions to be in experiment "%s".' % (user_id, experiment_key)
      )
      return False

    return True

  def activate(self, experiment_key, user_id, attributes=None):
    """ Buckets visitor and sends impression event to Optimizely.

    Args:
      experiment_key: Experiment which needs to be activated.
      user_id: ID for user.
      attributes: Dict representing user attributes and values which need to be recorded.

    Returns:
      Variation key representing the variation the user will be bucketed in.
      None if user is not in experiment or if experiment is not Running.
    """

    if not self._validate_preconditions(experiment_key, user_id, attributes):
      self.logger.log(enums.LogLevels.INFO, 'Not activating user "%s".' % user_id)
      return None

    variation_id = self.bucketer.bucket(experiment_key, user_id)

    if not variation_id:
      self.logger.log(enums.LogLevels.INFO, 'Not activating user "%s".' % user_id)
      return None

    # Create and dispatch impression event
    impression_event = self.event_builder.create_impression_event(experiment_key, variation_id, user_id, attributes)
    self.logger.log(enums.LogLevels.INFO, 'Activating user "%s" in experiment "%s".' % (user_id, experiment_key))
    self.logger.log(enums.LogLevels.DEBUG,
                    'Dispatching impression event to URL %s with params %s.' % (impression_event.get_url(),
                                                                                impression_event.get_params()))
    self.event_dispatcher.dispatch_event(impression_event.get_url(), impression_event.get_params())

    return self.config.get_variation_key_from_id(experiment_key, variation_id)

  def track(self, event_key, user_id,  attributes=None, event_value=None):
    """ Send conversion event to Optimizely.

    Args:
      event_key: Goal key representing the event which needs to be recorded.
      user_id: ID for user.
      attributes: Dict representing visitor attributes and values which need to be recorded.
      event_value: Value associated with the event. Can be used to represent revenue in cents.
    """

    if attributes and not validator.are_attributes_valid(attributes):
      self.logger.log(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')
      self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE_FORMAT))
      return

    experiment_ids = self.config.get_experiment_ids_for_goal(event_key)
    if not experiment_ids:
      self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for event "%s".' % (user_id, event_key))
      return

    # filter out experiments that are not running or that do not include the user in audience conditions
    valid_experiments = []
    for experiment_id in experiment_ids:
      experiment_key = self.config.get_experiment_key(experiment_id)
      if not self._validate_preconditions(experiment_key, user_id, attributes):
        self.logger.log(enums.LogLevels.INFO, 'Not tracking user "%s" for experiment "%s".' % (user_id, experiment_key))
        continue
      valid_experiments.append((experiment_id, experiment_key))

    # Create and dispatch conversion event if there are valid experiments
    if valid_experiments:
      conversion_event = self.event_builder.create_conversion_event(event_key, user_id, attributes, event_value,
                                                                    valid_experiments)
      self.logger.log(enums.LogLevels.INFO, 'Tracking event "%s" for user "%s".' % (event_key, user_id))
      self.logger.log(enums.LogLevels.DEBUG,
                      'Dispatching conversion event to URL %s with params %s.' % (conversion_event.get_url(),
                                                                                  conversion_event.get_params()))
      self.event_dispatcher.dispatch_event(conversion_event.get_url(), conversion_event.get_params())

  def get_variation(self, experiment_key, user_id, attributes=None):
    """ Gets variation where visitor will be bucketed.

    Args:
      experiment_key: Experiment for which visitor variation needs to be determined.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Variation key representing the variation the user will be bucketed in.
      None if user is not in experiment or if experiment is not Running.
    """

    if not self._validate_preconditions(experiment_key, user_id, attributes):
      return None
    variation_id = self.bucketer.bucket(experiment_key, user_id)
    return self.config.get_variation_key_from_id(experiment_key, variation_id)
