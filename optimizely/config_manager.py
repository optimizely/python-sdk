# Copyright 2019-2020, 2022-2023, Optimizely
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

from __future__ import annotations
from abc import ABC, abstractmethod
import numbers
from typing import TYPE_CHECKING, Any, Optional
import requests
import threading
from requests import codes as http_status_codes
from requests import exceptions as requests_exceptions

from . import exceptions as optimizely_exceptions
from . import logger as optimizely_logger
from . import project_config
from .error_handler import NoOpErrorHandler, BaseErrorHandler
from .notification_center import NotificationCenter
from .notification_center_registry import _NotificationCenterRegistry
from .helpers import enums
from .helpers import validator
from .optimizely_config import OptimizelyConfig, OptimizelyConfigService


if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from requests.models import CaseInsensitiveDict


class BaseConfigManager(ABC):
    """ Base class for Optimizely's config manager. """

    def __init__(
        self,
        logger: Optional[optimizely_logger.Logger] = None,
        error_handler: Optional[BaseErrorHandler] = None,
        notification_center: Optional[NotificationCenter] = None
    ):
        """ Initialize config manager.

        Args:
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
            notification_center: Provides instance of notification_center.NotificationCenter.
        """
        self.logger = optimizely_logger.adapt_logger(logger or optimizely_logger.NoOpLogger())
        self.error_handler = error_handler or NoOpErrorHandler()
        self.notification_center = notification_center or NotificationCenter(self.logger)
        self.optimizely_config: Optional[OptimizelyConfig]
        self._validate_instantiation_options()

    def _validate_instantiation_options(self) -> None:
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

    @abstractmethod
    def get_config(self) -> Optional[project_config.ProjectConfig]:
        """ Get config for use by optimizely.Optimizely.
        The config should be an instance of project_config.ProjectConfig."""
        pass

    @abstractmethod
    def get_sdk_key(self) -> Optional[str]:
        """ Get sdk_key for use by optimizely.Optimizely.
        The sdk_key should uniquely identify the datafile for a project and environment combination.
        """
        pass


class StaticConfigManager(BaseConfigManager):
    """ Config manager that returns ProjectConfig based on provided datafile. """

    def __init__(
        self,
        datafile: Optional[str] = None,
        logger: Optional[optimizely_logger.Logger] = None,
        error_handler: Optional[BaseErrorHandler] = None,
        notification_center: Optional[NotificationCenter] = None,
        skip_json_validation: Optional[bool] = False,
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
        super().__init__(
            logger=logger, error_handler=error_handler, notification_center=notification_center,
        )
        self._config: project_config.ProjectConfig = None  # type: ignore[assignment]
        self.optimizely_config: Optional[OptimizelyConfig] = None
        self._sdk_key: Optional[str] = None
        self.validate_schema = not skip_json_validation
        self._set_config(datafile)

    def get_sdk_key(self) -> Optional[str]:
        return self._sdk_key

    def _set_config(self, datafile: Optional[str | bytes]) -> None:
        """ Looks up and sets datafile and config based on response body.

        Args:
            datafile: JSON string representing the Optimizely project.
        """

        if self.validate_schema:
            if not validator.is_datafile_valid(datafile):
                self.logger.error(enums.Errors.INVALID_INPUT.format('datafile'))
                return

        error_msg = None
        error_to_handle: Optional[Exception] = None
        config = None

        try:
            assert datafile is not None
            config = project_config.ProjectConfig(datafile, self.logger, self.error_handler)
        except optimizely_exceptions.UnsupportedDatafileVersionException as error:
            error_msg = error.args[0]
            error_to_handle = error
        except:
            error_msg = enums.Errors.INVALID_INPUT.format('datafile')
            error_to_handle = optimizely_exceptions.InvalidInputException(error_msg)
        finally:
            if error_msg or config is None:
                self.logger.error(error_msg)
                self.error_handler.handle_error(error_to_handle or Exception('Unknown Error'))
                return

        previous_revision = self._config.get_revision() if self._config else None

        if previous_revision == config.get_revision():
            return

        self._config = config
        self._sdk_key = self._sdk_key or config.sdk_key
        self.optimizely_config = OptimizelyConfigService(config, self.logger).get_config()
        self.notification_center.send_notifications(enums.NotificationTypes.OPTIMIZELY_CONFIG_UPDATE)

        internal_notification_center = _NotificationCenterRegistry.get_notification_center(
            self._sdk_key, self.logger
        )
        if internal_notification_center:
            internal_notification_center.send_notifications(enums.NotificationTypes.OPTIMIZELY_CONFIG_UPDATE)

        self.logger.debug(
            'Received new datafile and updated config. '
            f'Old revision number: {previous_revision}. New revision number: {config.get_revision()}.'
        )

    def get_config(self) -> Optional[project_config.ProjectConfig]:
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
        sdk_key: Optional[str] = None,
        datafile: Optional[str] = None,
        update_interval: Optional[float] = None,
        blocking_timeout: Optional[int] = None,
        url: Optional[str] = None,
        url_template: Optional[str] = None,
        logger: Optional[optimizely_logger.Logger] = None,
        error_handler: Optional[BaseErrorHandler] = None,
        notification_center: Optional[NotificationCenter] = None,
        skip_json_validation: Optional[bool] = False,
    ):
        """ Initialize config manager. One of sdk_key or datafile has to be set to be able to use.

        Args:
            sdk_key: Optional string uniquely identifying the datafile. If not provided, datafile must
                     contain a sdk_key.
            datafile: Optional JSON string representing the project. If not provided, sdk_key is required.
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
        super().__init__(
            datafile=datafile,
            logger=logger,
            error_handler=error_handler,
            notification_center=notification_center,
            skip_json_validation=skip_json_validation,
        )
        self._sdk_key = sdk_key or self._sdk_key

        if self._sdk_key is None:
            raise optimizely_exceptions.InvalidInputException(enums.Errors.MISSING_SDK_KEY)

        self.datafile_url = self.get_datafile_url(
            self._sdk_key, url, url_template or self.DATAFILE_URL_TEMPLATE
        )
        self.set_update_interval(update_interval)
        self.set_blocking_timeout(blocking_timeout)
        self.last_modified: Optional[str] = None
        self.stopped = threading.Event()
        self._initialize_thread()
        self._polling_thread.start()

    @staticmethod
    def get_datafile_url(sdk_key: Optional[str], url: Optional[str], url_template: Optional[str]) -> str:
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
                assert url_template is not None
                return url_template.format(sdk_key=sdk_key)
            except (AssertionError, AttributeError, KeyError):
                raise optimizely_exceptions.InvalidInputException(
                    f'Invalid url_template {url_template} provided.'
                )

        return url

    def _set_config(self, datafile: Optional[str | bytes]) -> None:
        """ Looks up and sets datafile and config based on response body.

        Args:
            datafile: JSON string representing the Optimizely project.
        """
        if datafile or self._config_ready_event.is_set():
            super()._set_config(datafile=datafile)
            self._config_ready_event.set()

    def get_config(self) -> Optional[project_config.ProjectConfig]:
        """ Returns instance of ProjectConfig. Returns immediately if project config is ready otherwise
        blocks maximum for value of blocking_timeout in seconds.

        Returns:
            ProjectConfig. None if not set.
        """

        self._config_ready_event.wait(self.blocking_timeout)
        return self._config

    def set_update_interval(self, update_interval: Optional[int | float]) -> None:
        """ Helper method to set frequency at which datafile has to be polled and ProjectConfig updated.

        Args:
            update_interval: Time in seconds after which to update datafile.
        """
        if update_interval is None:
            update_interval = enums.ConfigManager.DEFAULT_UPDATE_INTERVAL
            self.logger.debug(f'Setting config update interval to default value {update_interval}.')

        if not isinstance(update_interval, (int, float)):
            raise optimizely_exceptions.InvalidInputException(
                f'Invalid update_interval "{update_interval}" provided.'
            )

        # If polling interval is less than or equal to 0 then set it to default update interval.
        if update_interval <= 0:
            self.logger.debug(
                f'update_interval value {update_interval} too small. '
                f'Defaulting to {enums.ConfigManager.DEFAULT_UPDATE_INTERVAL}'
            )
            update_interval = enums.ConfigManager.DEFAULT_UPDATE_INTERVAL

        if update_interval < 30:
            self.logger.warning(
                'Polling intervals below 30 seconds are not recommended.'
            )

        self.update_interval = update_interval

    def set_blocking_timeout(self, blocking_timeout: Optional[int | float]) -> None:
        """ Helper method to set time in seconds to block the config call until config has been initialized.

        Args:
            blocking_timeout: Time in seconds to block the config call.
        """
        if blocking_timeout is None:
            blocking_timeout = enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT
            self.logger.debug(f'Setting config blocking timeout to default value {blocking_timeout}.')

        if not isinstance(blocking_timeout, (numbers.Integral, float)):
            raise optimizely_exceptions.InvalidInputException(
                f'Invalid blocking timeout "{blocking_timeout}" provided.'
            )

        # If blocking timeout is less than 0 then set it to default blocking timeout.
        if blocking_timeout < 0:
            self.logger.debug(
                f'blocking timeout value {blocking_timeout} too small. '
                f'Defaulting to {enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT}'
            )
            blocking_timeout = enums.ConfigManager.DEFAULT_BLOCKING_TIMEOUT

        self.blocking_timeout = blocking_timeout

    def set_last_modified(self, response_headers: CaseInsensitiveDict[str]) -> None:
        """ Looks up and sets last modified time based on Last-Modified header in the response.

        Args:
            response_headers: requests.Response.headers
        """
        self.last_modified = response_headers.get(enums.HTTPHeaders.LAST_MODIFIED)

    def _handle_response(self, response: requests.Response) -> None:
        """ Helper method to handle response containing datafile.

        Args:
            response: requests.Response
        """
        try:
            response.raise_for_status()
        except requests_exceptions.RequestException as err:
            self.logger.error(f'Fetching datafile from {self.datafile_url} failed. Error: {err}')
            return

        # Leave datafile and config unchanged if it has not been modified.
        if response.status_code == http_status_codes.not_modified:
            self.logger.debug(f'Not updating config as datafile has not updated since {self.last_modified}.')
            return

        self.set_last_modified(response.headers)
        self._set_config(response.content)

    def fetch_datafile(self) -> None:
        """ Fetch datafile and set ProjectConfig. """

        request_headers = {}
        if self.last_modified:
            request_headers[enums.HTTPHeaders.IF_MODIFIED_SINCE] = self.last_modified

        try:
            response = requests.get(
                self.datafile_url, headers=request_headers, timeout=enums.ConfigManager.REQUEST_TIMEOUT,
            )
        except requests_exceptions.RequestException as err:
            self.logger.error(f'Fetching datafile from {self.datafile_url} failed. Error: {err}')
            return

        self._handle_response(response)

    @property
    def is_running(self) -> bool:
        """ Check if polling thread is alive or not. """
        return self._polling_thread.is_alive()

    def stop(self) -> None:
        """ Stop the polling thread and briefly wait for it to exit. """
        if self.is_running:
            self.stopped.set()
            # no need to wait too long as this exists to avoid interfering with tests
            self._polling_thread.join(timeout=0.2)

    def _run(self) -> None:
        """ Triggered as part of the thread which fetches the datafile and sleeps until next update interval. """
        try:
            while True:
                self.fetch_datafile()
                if self.stopped.wait(self.update_interval):
                    self.stopped.clear()
                    break
        except Exception as err:
            self.logger.error(
                f'Thread for background datafile polling failed. Error: {err}'
            )
            raise

    def start(self) -> None:
        """ Start the config manager and the thread to periodically fetch datafile. """
        if not self.is_running:
            self._polling_thread.start()

    def _initialize_thread(self) -> None:
        self._polling_thread = threading.Thread(target=self._run, daemon=True)


class AuthDatafilePollingConfigManager(PollingConfigManager):
    """ Config manager that polls for authenticated datafile using access token. """

    DATAFILE_URL_TEMPLATE = enums.ConfigManager.AUTHENTICATED_DATAFILE_URL_TEMPLATE

    def __init__(
        self,
        datafile_access_token: str,
        *args: Any,
        **kwargs: Any
    ):
        """ Initialize config manager. One of sdk_key or datafile has to be set to be able to use.

        Args:
            datafile_access_token: String to be attached to the request header to fetch the authenticated datafile.
            *args: Refer to arguments descriptions in PollingConfigManager.
            **kwargs: Refer to keyword arguments descriptions in PollingConfigManager.
        """
        self._set_datafile_access_token(datafile_access_token)
        super().__init__(*args, **kwargs)

    def _set_datafile_access_token(self, datafile_access_token: str) -> None:
        """ Checks for valid access token input and sets it. """
        if not datafile_access_token:
            raise optimizely_exceptions.InvalidInputException(
                'datafile_access_token cannot be empty or None.')
        self.datafile_access_token = datafile_access_token

    def fetch_datafile(self) -> None:
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
            self.logger.error(f'Fetching datafile from {self.datafile_url} failed. Error: {err}')
            return

        self._handle_response(response)
