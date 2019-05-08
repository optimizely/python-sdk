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


import asyncio
import http
import requests

from .base import BaseDatafileManager


DATAFILE_URL_TEMPLATE = 'https://cdn.optimizely.com/datafiles/{sdk_key}.json'


class PollingDatafileManager(BaseDatafileManager):

  def __init__(self,
               sdk_key=None,
               url=None,
               url_template=None):
    self.is_started = False
    assert sdk_key is not None or url is not None, 'Must provide at least one of sdk_key or url.'
    datafile_url_template = url_template or DATAFILE_URL_TEMPLATE
    if url is None:
      self.datafile_url = datafile_url_template.format(sdk_key=sdk_key)
    else:
      self.datafile_url = url
    self.datafile = None
    self.last_modified = None

  def __del__(self):
    self.stop()

  def set_last_modified(self, response):
    self.last_modified = response.headers['Last-Modified']

  def set_datafile(self, response):
    if response.status_code == http.HTTPStatus.NOT_MODIFIED:
      return
    self.datafile = response.json()

  def fetch_datafile(self):
    request_headers = {
      'If-Modified-Since': self.last_modified
    }
    response = requests.get(self.datafile_url, headers=request_headers)

    if response.status_code == http.HTTPStatus.OK:
      self.set_datafile(response)
      self.set_last_modified(response)

  async def _run(self):
    while True:
      self.fetch_datafile()
      await asyncio.sleep(5)

  def start(self):
    if not self.is_started:
      self.is_started = True
      event_loop = asyncio.get_event_loop()
      event_loop.run_until_complete(self._run())

  def stop(self):
    if self.is_started:
      self.is_started = False
      event_loop = asyncio.get_event_loop()
      event_loop.close()

  def get_datafile(self):
    return self.datafile
