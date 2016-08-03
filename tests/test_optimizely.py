import json
import mock

from optimizely import error_handler
from optimizely import exceptions
from optimizely import logger
from optimizely import optimizely
from optimizely import version
from optimizely.helpers import enums
from . import base


class OptimizelyTest(base.BaseTest):

  def test_init__invalid_datafile__raises(self):
    """ Test that invalid datafile raises Exception on init. """

    with self.assertRaises(Exception) as cm:
      optimizely.Optimizely('invalid_datafile')

    self.assertEqual('Provided "datafile" is in an invalid format.', str(cm.exception))

  def test_init__invalid_event_dispatcher__raises(self):
    """ Test that invalid event_dispatcher raises Exception on init. """

    class InvalidDispatcher(object):
      pass

    with self.assertRaises(Exception) as cm:
      optimizely.Optimizely(json.dumps(self.config_dict), event_dispatcher=InvalidDispatcher)

    self.assertEqual('Provided "event_dispatcher" is in an invalid format.', str(cm.exception))

  def test_init__invalid_logger__raises(self):
    """ Test that invalid logger raises Exception on init. """

    class InvalidLogger(object):
      pass

    with self.assertRaises(Exception) as cm:
      optimizely.Optimizely(json.dumps(self.config_dict), logger=InvalidLogger)

    self.assertEqual('Provided "logger" is in an invalid format.', str(cm.exception))

  def test_init__invalid_error_handler__raises(self):
    """ Test that invalid error_handler raises Exception on init. """

    class InvalidErrorHandler(object):
      pass

    with self.assertRaises(Exception) as cm:
      optimizely.Optimizely(json.dumps(self.config_dict), error_handler=InvalidErrorHandler)

    self.assertEqual('Provided "error_handler" is in an invalid format.', str(cm.exception))

  def test_skip_json_validation_true(self):
    """ Test that on setting skip_json_validation to true, JSON schema validation is not performed. """

    with mock.patch('optimizely.helpers.validator.is_datafile_valid') as mock_datafile_validation:
      optimizely.Optimizely(json.dumps(self.config_dict), skip_json_validation=True)

    self.assertEqual(0, mock_datafile_validation.call_count)

  def test_activate(self):
    """ Test that activate calls dispatch_event with right params and returns expected variation. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check,\
        mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111129') as mock_bucket,\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'visitor-event',
      'x111127': '111129',
      'g': '111127',
      'u': 'test_user',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    mock_audience_check.assert_called_once_with(self.project_config, 'test_experiment', None)
    mock_bucket.assert_called_once_with('test_experiment', 'test_user')
    mock_dispatch_event.assert_called_once_with('https://111001.log.optimizely.com/event', expected_params)

  def test_activate__with_attributes__audience_match(self):
    """ Test that activate calls dispatch_event with right params and returns expected
    variation when attributes are provided and audience conditions are met. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True) as mock_audience_check,\
        mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111129') as mock_bucket,\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user',
                                                             {'test_attribute': 'test_value'}))

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'visitor-event',
      'x111127': '111129',
      'g': '111127',
      'u': 'test_user',
      's11133': 'test_value',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    mock_audience_check.assert_called_once_with(self.project_config, 'test_experiment',
                                                {'test_attribute': 'test_value'})
    mock_bucket.assert_called_once_with('test_experiment', 'test_user')
    mock_dispatch_event.assert_called_once_with('https://111001.log.optimizely.com/event', expected_params)

  def test_activate__with_attributes__no_audience_match(self):
    """ Test that activate returns None when audience conditions do not match. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=False) as mock_audience_check:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user',
                                                 attributes={'test_attribute': 'test_value'}))
    mock_audience_check.assert_called_once_with(self.project_config, 'test_experiment',
                                                {'test_attribute': 'test_value'})

  def test_activate__with_attributes__invalid_attributes(self):
    """ Test that activate returns None and does not bucket or dispatch event when attributes are invalid. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket,\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user', attributes='invalid'))

    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_activate__experiment_not_running(self):
    """ Test that activate returns None when experiment is not Running. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True),\
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user',
                                                 attributes={'test_attribute': 'test_value'}))
    mock_is_experiment_running.assert_called_once_with(self.project_config, 'test_experiment')

  def test_activate__bucketer_returns_none(self):
    """ Test that activate returns None when user is in no variation. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True),\
        mock.patch('optimizely.bucketer.Bucketer.bucket', return_value=None) as mock_bucket,\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user',
                                                 attributes={'test_attribute': 'test_value'}))
    mock_bucket.assert_called_once_with('test_experiment', 'test_user')
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_track__with_attributes(self):
    """ Test that track calls dispatch_event with right params when attributes are provided. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111128') as mock_bucket,\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'})

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'test_event',
      'x111127': '111128',
      'g': '111095',
      'u': 'test_user',
      's11133': 'test_value',
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    mock_bucket.assert_called_once_with('test_experiment', 'test_user')
    mock_dispatch_event.assert_called_once_with('https://111001.log.optimizely.com/event', expected_params)

  def test_track__with_attributes__no_audience_match(self):
    """ Test that track does not call dispatch_event when audience conditions do not match. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111128') as mock_bucket,\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'wrong_test_value'})

    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_track__with_attributes__invalid_attributes(self):
    """ Test that track does not bucket or dispatch event if attributes are invalid. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket,\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes='invalid')

    self.assertEqual(0, mock_bucket.call_count)
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_track__with_event_value(self):
    """ Test that track calls dispatch_event with right params when event_value information is provided. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111128') as mock_bucket,\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user', attributes={'test_attribute': 'test_value'}, event_value=4200)

    expected_params = {
      'd': '12001',
      'a': '111001',
      'n': 'test_event',
      'x111127': '111128',
      'g': '111095,111096',
      'u': 'test_user',
      's11133': 'test_value',
      'v': 4200,
      'time': 42,
      'src': 'python-sdk-{version}'.format(version=version.__version__)
    }
    mock_bucket.assert_called_once_with('test_experiment', 'test_user')
    mock_dispatch_event.assert_called_once_with('https://111001.log.optimizely.com/event', expected_params)

  def test_track__experiment_not_running(self):
    """ Test that track does not call dispatch_event when experiment is not running. """

    with mock.patch('optimizely.helpers.experiment.is_experiment_running',
                    return_value=False) as mock_is_experiment_running,\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event') as mock_dispatch_event:
      self.optimizely.track('test_event', 'test_user')

    mock_is_experiment_running.assert_called_once_with(self.project_config, 'test_experiment')
    self.assertEqual(0, mock_dispatch_event.call_count)

  def test_get_variation__audience_match_and_experiment_running(self):
    """ Test that get variation retrieves expected variation
    when audience conditions are met and experiment is running. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111129') as mock_bucket:
      self.assertEqual('variation', self.optimizely.get_variation('test_experiment', 'test_user',
                                                                  attributes={'test_attribute': 'test_value'}))

    mock_bucket.assert_called_once_with('test_experiment', 'test_user')

  def test_get_variation__with_attributes__invalid_attributes(self):
    """ Test that get variation returns None and does not bucket when attributes are invalid. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket') as mock_bucket:
      self.assertIsNone(self.optimizely.activate('test_experiment', 'test_user', attributes='invalid'))

    self.assertEqual(0, mock_bucket.call_count)

  def test_get_variation__no_audience_match(self):
    """ Test that get variation returns None when audience conditions are not met. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111129') as mock_bucket:
      self.assertIsNone(self.optimizely.get_variation('test_experiment', 'test_user',
                                                      attributes={'test_attribute': 'wrong_test_value'}))

    self.assertEqual(0, mock_bucket.call_count)

  def test_get_variation__experiment_not_running(self):
    """ Test that get variation returns None when experiment is not running. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111129') as mock_bucket,\
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.assertIsNone(self.optimizely.get_variation('test_experiment', 'test_user',
                                                      attributes={'test_attribute': 'test_value'}))

    self.assertEqual(0, mock_bucket.call_count)
    mock_is_experiment_running.assert_called_once_with(self.project_config, 'test_experiment')

  def test_custom_logger(self):
    """ Test creating Optimizely object with a custom logger. """

    class CustomLogger(object):
      @staticmethod
      def log(log_message):
        return log_message

    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict), logger=CustomLogger)
    self.assertEqual('test_message', self.optimizely.logger.log('test_message'))

  def test_custom_error_handler(self):
    """ Test creating Optimizely object with a custom error handler. """

    class CustomExceptionHandler(object):
      @staticmethod
      def handle_error(error):
        return error

    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict), error_handler=CustomExceptionHandler)
    self.assertEqual('test_message', self.optimizely.error_handler.handle_error('test_message'))


class OptimizelyWithExceptionTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict),
                                            error_handler=error_handler.RaiseExceptionErrorHandler)

  def test_activate__with_attributes__invalid_attributes(self):
    """ Test that activate raises exception if attributes are in invalid format. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException, enums.Errors.INVALID_ATTRIBUTE_FORMAT,
                            self.optimizely.activate, 'test_experiment', 'test_user', attributes='invalid')

  def test_track__with_attributes__invalid_attributes(self):
    """ Test that track raises exception if attributes are in invalid format. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException, enums.Errors.INVALID_ATTRIBUTE_FORMAT,
                            self.optimizely.track, 'test_event', 'test_user', attributes='invalid')

  def test_get_variation__with_attributes__invalid_attributes(self):
    """ Test that get variation raises exception if attributes are in invalid format. """

    self.assertRaisesRegexp(exceptions.InvalidAttributeException, enums.Errors.INVALID_ATTRIBUTE_FORMAT,
                            self.optimizely.get_variation, 'test_experiment', 'test_user', attributes='invalid')


class OptimizelyWithLoggingTest(base.BaseTest):

  def setUp(self):
    base.BaseTest.setUp(self)
    self.optimizely = optimizely.Optimizely(json.dumps(self.config_dict), logger=logger.SimpleLogger())
    self.project_config = self.optimizely.config

  def test_activate(self):
    """ Test that expected log messages are logged during activate. """

    with mock.patch('optimizely.helpers.audience.is_user_in_experiment', return_value=True),\
        mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111129'),\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event'),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.assertEqual('variation', self.optimizely.activate('test_experiment', 'test_user'))

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.INFO, 'Activating user "test_user" in experiment "test_experiment".'),
                     mock_logging.call_args_list[0])
    (debug_level, debug_message) = mock_logging.call_args_list[1][0]
    self.assertEqual(enums.LogLevels.DEBUG, debug_level)
    self.assertRegexpMatches(debug_message,
                             'Dispatching impression event to URL https://111001.log.optimizely.com/event with params')

  def test_track(self):
    """ Test that expected log messages are logged during track. """

    with mock.patch('optimizely.bucketer.Bucketer.bucket', return_value='111128'),\
        mock.patch('time.time', return_value=42),\
        mock.patch('optimizely.event_dispatcher.EventDispatcher.dispatch_event'),\
        mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.track('test_event', 'test_user')

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock.call(enums.LogLevels.INFO,
                     'User "test_user" does not meet conditions to be in experiment "test_experiment".'),
                     mock_logging.call_args_list[0])
    self.assertEqual(mock.call(enums.LogLevels.INFO,
                     'Not tracking user "test_user" for experiment "test_experiment".'),
                     mock_logging.call_args_list[1])

  def test_activate__invalid_attributes(self):
    """ Test that expected log messages are logged during activate when attributes are in invalid format. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.activate('test_experiment', 'test_user', attributes='invalid')

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock_logging.call_args_list[0],
                     mock.call(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.'))
    self.assertEqual(mock_logging.call_args_list[1],
                     mock.call(enums.LogLevels.INFO, 'Not activating user "test_user".'))

  def test_activate__experiment_not_running(self):
    """ Test that expected log messages are logged during activate when experiment is not running. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging,\
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'})

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock_logging.call_args_list[0],
                     mock.call(enums.LogLevels.INFO, 'Experiment "test_experiment" is not running.'))
    self.assertEqual(mock_logging.call_args_list[1],
                     mock.call(enums.LogLevels.INFO, 'Not activating user "test_user".'))
    mock_is_experiment_running.assert_called_once_with(self.project_config, 'test_experiment')

  def test_activate__no_audience_match(self):
    """ Test that expected log messages are logged during activate when audience conditions are not met. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.activate('test_experiment', 'test_user', attributes={'test_attribute': 'wrong_test_value'})

    self.assertEqual(2, mock_logging.call_count)
    self.assertEqual(mock_logging.call_args_list[0],
                     mock.call(enums.LogLevels.INFO,
                               'User "test_user" does not meet conditions to be in experiment "test_experiment".'))
    self.assertEqual(mock_logging.call_args_list[1],
                     mock.call(enums.LogLevels.INFO, 'Not activating user "test_user".'))

  def test_track__invalid_attributes(self):
    """ Test that expected log messages are logged during track when attributes are in invalid format. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.track('test_event', 'test_user', attributes='invalid')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')

  def test_get_variation__invalid_attributes(self):
    """ Test that expected log messages are logged during get variation when attributes are in invalid format. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.get_variation('test_experiment', 'test_user', attributes='invalid')

    mock_logging.assert_called_once_with(enums.LogLevels.ERROR, 'Provided attributes are in an invalid format.')

  def test_get_variation__experiment_not_running(self):
    """ Test that expected log messages are logged during get variation when experiment is not running. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging,\
        mock.patch('optimizely.helpers.experiment.is_experiment_running',
                   return_value=False) as mock_is_experiment_running:
      self.optimizely.get_variation('test_experiment', 'test_user', attributes={'test_attribute': 'test_value'})

    mock_logging.assert_called_once_with(enums.LogLevels.INFO, 'Experiment "test_experiment" is not running.')
    mock_is_experiment_running.assert_called_once_with(self.project_config, 'test_experiment')

  def test_get_variation__no_audience_match(self):
    """ Test that expected log messages are logged during get variation when audience conditions are not met. """

    with mock.patch('optimizely.logger.SimpleLogger.log') as mock_logging:
      self.optimizely.get_variation('test_experiment', 'test_user', attributes={'test_attribute': 'wrong_test_value'})

    mock_logging.assert_called_once_with(
      enums.LogLevels.INFO,
      'User "test_user" does not meet conditions to be in experiment "test_experiment".'
    )
