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


import http
import requests
import threading
import time

from . import project_config
from .helpers import enums


DATAFILE_URL_TEMPLATE = 'https://cdn.optimizely.com/datafiles/{sdk_key}.json'


class BaseConfigManager(object):
  def get_config(self):
    raise NotImplementedError


class StaticDatafileManager(BaseConfigManager):

  def __init__(self, datafile):
    self.datafile = datafile

  def get_config(self, *args, **kwargs):
    return project_config.ProjectConfig(self.datafile, *args, **kwargs)


class PollingConfigManager(BaseConfigManager):
  MIN_UPDATE_INTERVAL = 1
  DEFAULT_UPDATE_INTERVAL = 5 * 60

  def __init__(self,
               sdk_key=None,
               update_interval=None,
               url=None,
               url_template=None):
    self._set_datafile_url(sdk_key, url, url_template)
    self._set_update_interval(update_interval)
    self.datafile = None
    self.last_modified = None
    self._polling_thread = threading.Thread(target=self._run)
    self.is_running = False

  def _set_datafile_url(self, sdk_key, url, url_template):
    assert sdk_key is not None or url is not None, 'Must provide at least one of sdk_key or url.'
    url_template = url_template or DATAFILE_URL_TEMPLATE
    if url is None:
      self.datafile_url = url_template.format(sdk_key=sdk_key)
    else:
      self.datafile_url = url

  def _set_update_interval(self, update_interval):
    self.update_interval = update_interval or self.DEFAULT_UPDATE_INTERVAL
    if update_interval < self.MIN_UPDATE_INTERVAL:
      self.update_interval = self.DEFAULT_UPDATE_INTERVAL

  def set_last_modified(self, response):
    self.last_modified = response.headers[enums.HTTPHeaders.LAST_MODIFIED]

  def set_datafile(self, response):
    if response.status_code == http.HTTPStatus.NOT_MODIFIED:
      return
    self.datafile = response.text

  def fetch_datafile(self):
    request_headers = {
      enums.HTTPHeaders.IF_MODIFIED_SINCE: self.last_modified
    }
    response = requests.get(self.datafile_url, headers=request_headers)

    if response.status_code == http.HTTPStatus.OK:
      self.set_datafile(response)
      self.set_last_modified(response)

  def _run(self):
    while self.is_running:
      self.fetch_datafile()
      time.sleep(self.update_interval)

  def start(self):
    if not self.is_running:
      self.is_running= True
      self._polling_thread.start()

  def stop(self):
    if self.is_running:
      self.is_running = False
