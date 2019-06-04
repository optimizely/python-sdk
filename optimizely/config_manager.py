# Copyright 2019, Optimizely
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
import requests
import threading
import time
from requests import codes as http_status_codes
from requests import exceptions as requests_exceptions

from . import exceptions as optimizely_exceptions
from . import logger as optimizely_logger
from . import project_config
from .error_handler import NoOpErrorHandler as noop_error_handler
from .helpers import enums


ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class BaseConfigManager(ABC):
    """ Base class for Optimizely's config manager. """

    def __init__(self,
                 logger=None,
                 error_handler=None):
        """ Initialize config manager.

        Args:
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
        """
        self.logger = logger or optimizely_logger.adapt_logger(logger or optimizely_logger.NoOpLogger())
        self.error_handler = error_handler or noop_error_handler

    @abc.abstractmethod
    def get_config(self):
        """ Get config for use by optimizely.Optimizely.
        The config should be an instance of project_config.ProjectConfig."""
        pass


class StaticConfigManager(BaseConfigManager):
    """ Config manager that returns ProjectConfig based on provided datafile. """

    def __init__(self,
                 datafile=None,
                 logger=None,
                 error_handler=None):
        """ Initialize config manager. Datafile has to be provided to use.

        Args:
            datafile: JSON string representing the Optimizely project.
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
        """
        super(StaticConfigManager, self).__init__(logger=logger, error_handler=error_handler)
        self._config = None
        if datafile:
          self._config = project_config.ProjectConfig(datafile, self.logger, self.error_handler)

    def get_config(self):
        """ Returns instance of ProjectConfig.

        Returns:
          ProjectConfig.
        """
        return self._config


class PollingConfigManager(BaseConfigManager):
    """ Config manager that polls for the datafile and updated ProjectConfig based on an update interval. """

    def __init__(self,
                 sdk_key=None,
                 datafile=None,
                 update_interval=None,
                 url=None,
                 url_template=None,
                 logger=None,
                 error_handler=None):
        """ Initialize config manager. One of sdk_key or url has to be set to be able to use.

        Args:
          sdk_key: Optional string uniquely identifying the datafile.
          datafile: Optional JSON string representing the project.
          update_interval: Optional floating point number representing time interval in seconds
                           at which to request datafile and set ProjectConfig.
          url: Optional string representing URL from where to fetch the datafile. If set it supersedes the sdk_key.
          url_template: Optional string template which in conjunction with sdk_key
                        determines URL from where to fetch the datafile.
          logger: Provides a logger instance.
          error_handler: Provides a handle_error method to handle exceptions.
        """
        super(PollingConfigManager, self).__init__(logger=logger, error_handler=error_handler)
        self.datafile_url = self.get_datafile_url(sdk_key, url,
                                                  url_template or enums.ConfigManager.DATAFILE_URL_TEMPLATE)
        self.set_update_interval(update_interval)
        self.last_modified = None
        self._datafile = datafile
        self._config = None
        self._polling_thread = threading.Thread(target=self._run)
        self._polling_thread.setDaemon(True)
        if self._datafile:
          self.set_config(self._datafile)

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
                    'Invalid url_template {} provided.'.format(url_template))

        return url

    def set_update_interval(self, update_interval):
        """ Helper method to set frequency at which datafile has to be polled and ProjectConfig updated.

        Args:
          update_interval: Time in seconds after which to update datafile.
        """
        self.update_interval = update_interval or enums.ConfigManager.DEFAULT_UPDATE_INTERVAL

        # If polling interval is less than minimum allowed interval then set it to default update interval.
        if self.update_interval < enums.ConfigManager.MIN_UPDATE_INTERVAL:
            self.logger.debug('Invalid update_interval {} provided. Defaulting to {}'.format(
                update_interval,
                enums.ConfigManager.DEFAULT_UPDATE_INTERVAL)
            )
            self.update_interval = enums.ConfigManager.DEFAULT_UPDATE_INTERVAL

    def set_last_modified(self, response_headers):
        """ Looks up and sets last modified time based on Last-Modified header in the response.

         Args:
           response_headers: requests.Response.headers
         """
        self.last_modified = response_headers.get(enums.HTTPHeaders.LAST_MODIFIED)

    def set_config(self, datafile):
        """ Looks up and sets datafile and config based on response body.

         Args:
           datafile: JSON string representing the Optimizely project.
         """
        # TODO(ali): Add validation here to make sure that we do not update datafile and config if not a valid datafile.
        self._datafile = datafile
        # TODO(ali): Add notification listener.
        self._config = project_config.ProjectConfig(self._datafile, self.logger, self.error_handler)
        self.logger.debug('Received new datafile and updated config.')

    def get_config(self):
        """ Returns instance of ProjectConfig.

        Returns:
          ProjectConfig.
        """
        return self._config

    def _handle_response(self, response):
        """ Helper method to handle response containing datafile.

        Args:
            response: requests.Response
        """
        try:
            response.raise_for_status()
        except requests_exceptions.HTTPError as err:
            self.logger.error('Fetching datafile from {} failed. Error: {}'.format(self.datafile_url, str(err)))
            return

        # Leave datafile and config unchanged if it has not been modified.
        if response.status_code == http_status_codes.not_modified:
            self.logger.debug('Not updating config as datafile has not updated since {}.'.format(self.last_modified))
            return

        self.set_last_modified(response.headers)
        self.set_config(response.content)

    def fetch_datafile(self):
        """ Fetch datafile and set ProjectConfig. """

        request_headers = {}
        if self.last_modified:
            request_headers[enums.HTTPHeaders.IF_MODIFIED_SINCE] = self.last_modified

        response = requests.get(self.datafile_url,
                                headers=request_headers,
                                timeout=enums.ConfigManager.REQUEST_TIMEOUT)
        self._handle_response(response)

    @property
    def is_running(self):
        """ Check if polling thread is alive or not. """
        return self._polling_thread.is_alive()

    def _run(self):
        """ Triggered as part of the thread which fetches the datafile and sleeps until next update interval. """
        while self.is_running:
            self.fetch_datafile()
            time.sleep(self.update_interval)

    def start(self):
        """ Start the config manager and the thread to periodically fetch datafile. """
        if not self.is_running:
            self._polling_thread.start()
