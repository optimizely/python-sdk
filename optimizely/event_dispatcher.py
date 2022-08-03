# Copyright 2016, 2022, Optimizely
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
from sys import version_info

import requests
from requests import exceptions as request_exception

from . import event_builder
from .helpers.enums import HTTPVerbs, EventDispatchConfig

if version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol  # type: ignore


class CustomEventDispatcher(Protocol):
    """Interface for a custom event dispatcher and required method `dispatch_event`. """

    def dispatch_event(self, event: event_builder.Event) -> None:
        ...


class EventDispatcher:

    @staticmethod
    def dispatch_event(event: event_builder.Event) -> None:
        """ Dispatch the event being represented by the Event object.

    Args:
      event: Object holding information about the request to be dispatched to the Optimizely backend.
    """
        try:
            if event.http_verb == HTTPVerbs.GET:
                requests.get(event.url, params=event.params,
                             timeout=EventDispatchConfig.REQUEST_TIMEOUT).raise_for_status()
            elif event.http_verb == HTTPVerbs.POST:
                requests.post(
                    event.url, data=json.dumps(event.params), headers=event.headers,
                    timeout=EventDispatchConfig.REQUEST_TIMEOUT,
                ).raise_for_status()

        except request_exception.RequestException as error:
            logging.error(f'Dispatch event failed. Error: {error}')
