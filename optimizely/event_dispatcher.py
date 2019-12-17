# Copyright 2016, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import requests

from requests import exceptions as request_exception

from .helpers import enums

REQUEST_TIMEOUT = 10


class EventDispatcher(object):
    @staticmethod
    def dispatch_event(event):
        """ Dispatch the event being represented by the Event object.

    Args:
      event: Object holding information about the request to be dispatched to the Optimizely backend.
    """

        try:
            if event.http_verb == enums.HTTPVerbs.GET:
                requests.get(event.url, params=event.params, timeout=REQUEST_TIMEOUT).raise_for_status()
            elif event.http_verb == enums.HTTPVerbs.POST:
                requests.post(
                    event.url, data=json.dumps(event.params), headers=event.headers, timeout=REQUEST_TIMEOUT,
                ).raise_for_status()

        except request_exception.RequestException as error:
            logging.error('Dispatch event failed. Error: %s' % str(error))
