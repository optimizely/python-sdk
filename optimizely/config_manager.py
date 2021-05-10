# Copyright 2019-2020, Optimizely
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

import abc
import numbers
import requests
import threading
import time
from requests import codes as http_status_codes
from requests import exceptions as requests_exceptions

from . import exceptions as optimizely_exceptions
from . import logger as optimizely_logger
from . import project_config
from .error_handler import NoOpErrorHandler
from .notification_center import NotificationCenter
from .helpers import enums
from .helpers import validator
from .optimizely_config import OptimizelyConfigService

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class BaseConfigManager(ABC):
    """ Base class for Optimizely's config manager. """

    def __init__(self, logger=None, error_handler=None, notification_center=None):
        """ Initialize config manager.

        Args:
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
            notification_center: Provides instance of notification_center.NotificationCenter.
        """
        self.logger = optimizely_logger.adapt_logger(logger or optimizely_logger.NoOpLogger())
        self.error_handler = error_handler or NoOpErrorHandler()
        self.notification_center = notification_center or NotificationCenter(self.logger)
        self._validate_instantiation_options()

    def _validate_instantiation_options(self):
        """ Helper method to validate all parameters.

        Raises:
            Exception if provided options are invalid.
        """
        if not validator.is_logger_valid(self.logger):
            raise optimizely_exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('logger'))

        if not validator.is_error_handler_valid(self.error_handler):
            raise optimizely_exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('error_handler'))

        if not validator.is_notification_center_valid(self.notification_center):
            raise optimizely_exceptions.InvalidInputException(enums.Errors.INVALID_INPUT.format('notification_center'))

    @abc.abstractmethod
    def get_config(self):
        """ Get config for use by optimizely.Optimizely.
        The config should be an instance of project_config.ProjectConfig."""
        pass


class StaticConfigManager(BaseConfigManager):
    """ Config manager that returns ProjectConfig based on provided datafile. """

    def __init__(
        self, datafile=None, logger=None, error_handler=None, notification_center=None, skip_json_validation=False,
    ):
        """ Initialize config manager. Datafile has to be provided to use.

        Args:
            datafile: JSON string representing the Optimizely project.
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
            notification_center: Notification center to generate config update notification.
            skip_json_validation: Optional boolean param which allows skipping JSON schema
                                  validation upon object invocation. By default
                                  JSON schema validation will be performed.
        """
        super(StaticConfigManager, self).__init__(
            logger=logger, error_handler=error_handler, notification_center=notification_center,
        )
        self._config = None
        self.optimizely_config = None
        self.validate_schema = not skip_json_validation
        self._set_config(datafile)

    def _set_config(self, datafile):
        """ Looks up and sets datafile and config based on response body.

        Args:
            datafile: JSON string representing the Optimizely project.
        """

        if self.validate_schema:
            if not validator.is_datafile_valid(datafile):
                self.logger.error(enums.Errors.INVALID_INPUT.format('datafile'))
                return

        error_msg = None
        error_to_handle = None
        config = None

        try:
            config = project_config.ProjectConfig(datafile, self.logger, self.error_handler)
        except optimizely_exceptions.UnsupportedDatafileVersionException as error:
            error_msg = error.args[0]
            error_to_handle = error
        except:
            error_msg = enums.Errors.INVALID_INPUT.format('datafile')
            error_to_handle = optimizely_exceptions.InvalidInputException(error_msg)
        finally:
            if error_msg:
                self.logger.error(error_msg)
                self.error_handler.handle_error(error_to_handle)
                return

        previous_revision = self._config.get_revision() if self._config else None

        if previous_revision == config.get_revision():
            return

        self._config = config
        self.optimizely_config = OptimizelyConfigService(config).get_config()
        self.notification_center.send_notifications(enums.NotificationTypes.OPTIMIZELY_CONFIG_UPDATE)
        self.logger.debug(
            'Received new datafile and updated config. '
            'Old revision number: {}. New revision number: {}.'.format(previous_revision, config.get_revision())
        )

    def get_config(self):
        """ Returns instance of ProjectConfig.

        Returns:
            ProjectConfig. None if not set.
        """

        return self._config


class PollingConfigManager(StaticConfigManager):
    """ Config manager that polls for the datafile and updated ProjectConfig based on an update interval. """

    DATAFILE_URL_TEMPLATE = enums.ConfigManager.DATAFILE_URL_TEMPLATE

    def __init__(
        self,
        sdk_key=None,
        datafile=None,
        update_interval=None,
        blocking_timeout=None,
        url=None,
        url_template=None,
        logger=None,
        error_handler=None,
        notification_center=None,
        skip_json_validation=False,
    ):
        """ Initialize config manager. One of sdk_key or url has to be set to be able to use.

        Args:
            sdk_key: Optional string uniquely identifying the datafile.
            datafile: Optional JSON string representing the project.
            update_interval: Optional floating point number representing time interval in seconds
                             at which to request datafile and set ProjectConfig.
            blocking_timeout: Optional Time in seconds to block the get_config call until config object
                              has been initialized.
            url: Optional string representing URL from where to fetch the datafile. If set it supersedes the sdk_key.
            url_template: Optional string template which in conjunction with sdk_key
                          determines URL from where to fetch the datafile.
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
            notification_center: Notification center to generate config update notification.
            skip_json_validation: Optional boolean param which allows skipping JSON schema
                                  validation upon object invocation. By default
                                  JSON schema validation will be performed.

        """
        self._config_ready_event = threading.Event()
        super(PollingConfigManager, self).__init__(
            datafile=datafile,
            logger=logger,
            error_handler=error_handler,
            notification_center=notification_center,
            skip_json_validation=skip_json_validation,
        )
        self.datafile_url = self.get_datafile_url(
            sdk_key, url, url_template or self.DATAFILE_URL_TEMPLATE
        )
        self.set_update_interval(update_interval)
        self.set_blocking_timeout(blocking_timeout)
        self.last_modified = None
        self._polling_thread = threading.Thread(target=self._run)
        self._polling_thread.setDaemon(True)
        self._polling_thread.start()

    @staticmethod
    def get_datafile_url(sdk_key, url, url_template):
        """ Helper method to determine URL from where to fetch the datafile.

        Args:
          sdk_key: Key uniquely identifying the datafile.
          url: String representing URL from which to fetch the datafile.
          url_template: String representing template which is filled in with
                        SDK key to determine URL from which to fetch the datafile.

        Returns:
          String representing URL to fetch datafile from.

        Raises:
          optimizely.exceptions.InvalidInputException if:
          - One of sdk_key or url is not provided.
          - url_template is invalid.
        """
        # Ensure that either is provided by the user.
        if sdk_key is None and url is None:
            raise optimizely_exceptions.InvalidInputException('Must provide at least one of sdk_key or url.')

        # Return URL if one is provided or use template and SDK key to get it.
        if url is None:
            try:
                return url_template.format(sdk_key=sdk_key)
            except (AttributeError, KeyError):
                raise optimizely_exceptions.InvalidInputException(
                    'Invalid url_template {} provided.'.format(url_template)
                )

        return url

    def _set_config(self, datafile):
        """ Looks up and sets datafile and config based on response body.

        Args:
            datafile: JSON string representing the Optimizely project.
        """
        if datafile or self._config_ready_event.is_set():
            super(PollingConfigManager, self)._set_config(datafile=datafile)
            self._config_ready_event.set()

    def get_config(self):
        """ Returns instance of ProjectConfig. Returns immediately if project config is ready otherwise
        blocks maximum for value of blocking_timeout in seconds.

        Returns:
            ProjectConfig. None if not set.
        """

        self._config_ready_event.wait(self.blocking_timeout)
        return self._config

    def set_update_interval(self, update_interval):
        """ Helper method to set frequency at which datafile has to be polled and ProjectConfig updated.

        Args:
            update_interval: Time in seconds after which to update datafile.
        """
        if update_interval is None:
            update_interval = enums.ConfigManager.DEFAULT_UPDATE_INTERVAL
            self.logger.debug('Setting config update interval to default value {}.'.format(update_interval))

        if not isinstance(update_interval, (int, float)):
            raise optimizely_exceptions.InvalidInputException(
                'Invalid update_interval "{}" provided.'.format(update_interval)
            )

        # If polling interval is less than or equal to 0 then set it to default update interval.
        if update_interval <= 0:
            self.logger.debug(
                'update_interval value {} too small. Defaulting to {}'.format(
                    update_interval, enums.ConfigManager.DEFAULT_UPDATE_INTERVAL
                )
            )
            update_interval = enums.ConfigManager.DEFAULT_UPDATE_INTERVAL

        self.update_interval = update_interval

    def set_blocking_timeout(self, blocking_timeout):
        """ Helper method to set time in seconds to block the config call until config has been initialized.

        Args:
            blocking_timeout: Time in seconds to block the config call.
        """
        if blocking_timeout is None:
            blocking_timeout = enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT
            self.logger.debug('Setting config blocking timeout to default value {}.'.format(blocking_timeout))

        if not isinstance(blocking_timeout, (numbers.Integral, float)):
            raise optimizely_exceptions.InvalidInputException(
                'Invalid blocking timeout "{}" provided.'.format(blocking_timeout)
            )

        # If blocking timeout is less than 0 then set it to default blocking timeout.
        if blocking_timeout < 0:
            self.logger.debug(
                'blocking timeout value {} too small. Defaulting to {}'.format(
                    blocking_timeout, enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT
                )
            )
            blocking_timeout = enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT

        self.blocking_timeout = blocking_timeout

    def set_last_modified(self, response_headers):
        """ Looks up and sets last modified time based on Last-Modified header in the response.

        Args:
            response_headers: requests.Response.headers
        """
        self.last_modified = response_headers.get(enums.HTTPHeaders.LAST_MODIFIED)

    def _handle_response(self, response):
        """ Helper method to handle response containing datafile.

        Args:
            response: requests.Response
        """
        try:
            response.raise_for_status()
        except requests_exceptions.RequestException as err:
            self.logger.error('Fetching datafile from {} failed. Error: {}'.format(self.datafile_url, str(err)))
            return

        # Leave datafile and config unchanged if it has not been modified.
        if response.status_code == http_status_codes.not_modified:
            self.logger.debug('Not updating config as datafile has not updated since {}.'.format(self.last_modified))
            return

        self.set_last_modified(response.headers)
        self._set_config(response.content)

    def fetch_datafile(self):
        """ Fetch datafile and set ProjectConfig. """

        request_headers = {}
        if self.last_modified:
            request_headers[enums.HTTPHeaders.IF_MODIFIED_SINCE] = self.last_modified

        try:
            response = requests.get(
                self.datafile_url, headers=request_headers, timeout=enums.ConfigManager.REQUEST_TIMEOUT,
            )
        except requests_exceptions.RequestException as err:
            self.logger.error('Fetching datafile from {} failed. Error: {}'.format(self.datafile_url, str(err)))
            return

        self._handle_response(response)

    @property
    def is_running(self):
        """ Check if polling thread is alive or not. """
        return self._polling_thread.is_alive()

    def _run(self):
        """ Triggered as part of the thread which fetches the datafile and sleeps until next update interval. """
        try:
            while self.is_running:
                self.fetch_datafile()
                time.sleep(self.update_interval)
        except (OSError, OverflowError) as err:
            self.logger.error(
                'Error in time.sleep. ' 'Provided update_interval value may be too big. Error: {}'.format(str(err))
            )
            raise

    def start(self):
        """ Start the config manager and the thread to periodically fetch datafile. """
        if not self.is_running:
            self._polling_thread.start()


class AuthDatafilePollingConfigManager(PollingConfigManager):
    """ Config manager that polls for authenticated datafile using access token. """

    DATAFILE_URL_TEMPLATE = enums.ConfigManager.AUTHENTICATED_DATAFILE_URL_TEMPLATE

    def __init__(
        self,
        datafile_access_token,
        *args,
        **kwargs
    ):
        """ Initialize config manager. One of sdk_key or url has to be set to be able to use.

        Args:
            datafile_access_token: String to be attached to the request header to fetch the authenticated datafile.
            *args: Refer to arguments descriptions in PollingConfigManager.
            **kwargs: Refer to keyword arguments descriptions in PollingConfigManager.
        """
        self._set_datafile_access_token(datafile_access_token)
        super(AuthDatafilePollingConfigManager, self).__init__(*args, **kwargs)

    def _set_datafile_access_token(self, datafile_access_token):
        """ Checks for valid access token input and sets it. """
        if not datafile_access_token:
            raise optimizely_exceptions.InvalidInputException(
                'datafile_access_token cannot be empty or None.')
        self.datafile_access_token = datafile_access_token

    def fetch_datafile(self):
        """ Fetch authenticated datafile and set ProjectConfig. """
        request_headers = {
            enums.HTTPHeaders.AUTHORIZATION: enums.ConfigManager.AUTHORIZATION_HEADER_DATA_TEMPLATE.format(
                datafile_access_token=self.datafile_access_token
            )
        }

        if self.last_modified:
            request_headers[enums.HTTPHeaders.IF_MODIFIED_SINCE] = self.last_modified

        try:
            response = requests.get(
                self.datafile_url, headers=request_headers, timeout=enums.ConfigManager.REQUEST_TIMEOUT,
            )
        except requests_exceptions.RequestException as err:
            self.logger.error('Fetching datafile from {} failed. Error: {}'.format(self.datafile_url, str(err)))
            return

        self._handle_response(response)
