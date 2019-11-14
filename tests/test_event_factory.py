# Copyright 2019, Optimizely
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

import mock
import time
import unittest
import uuid
from operator import itemgetter

from optimizely import logger
from optimizely import version
from optimizely.event.event_factory import EventFactory
from optimizely.event.log_event import LogEvent
from optimizely.event.user_event_factory import UserEventFactory
from . import base


class LogEventTest(unittest.TestCase):
    def test_init(self):
        url = 'event.optimizely.com'
        params = {'a': '111001', 'n': 'test_event', 'g': '111028', 'u': 'oeutest_user'}
        http_verb = 'POST'
        headers = {'Content-Type': 'application/json'}
        event_obj = LogEvent(url, params, http_verb=http_verb, headers=headers)
        self.assertEqual(url, event_obj.url)
        self.assertEqual(params, event_obj.params)
        self.assertEqual(http_verb, event_obj.http_verb)
        self.assertEqual(headers, event_obj.headers)


class EventFactoryTest(base.BaseTest):
    def setUp(self, *args, **kwargs):
        base.BaseTest.setUp(self, 'config_dict_with_multiple_experiments')
        self.logger = logger.NoOpLogger()
        self.uuid = str(uuid.uuid4())
        self.timestamp = int(round(time.time() * 1000))

    def _validate_event_object(self, event_obj, expected_url, expected_params, expected_verb, expected_headers):
        """ Helper method to validate properties of the event object. """

        self.assertEqual(expected_url, event_obj.url)

        expected_params['visitors'][0]['attributes'] = sorted(
            expected_params['visitors'][0]['attributes'], key=itemgetter('key')
        )
        event_obj.params['visitors'][0]['attributes'] = sorted(
            event_obj.params['visitors'][0]['attributes'], key=itemgetter('key')
        )
        self.assertEqual(expected_params, event_obj.params)

        self.assertEqual(expected_verb, event_obj.http_verb)
        self.assertEqual(expected_headers, event_obj.headers)

    def test_create_impression_event(self):
        """ Test that create_impression_event creates LogEvent object with right params. """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_impression_event(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                '111129',
                'test_user',
                None,
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_impression_event__with_attributes(self):
        """ Test that create_impression_event creates Event object
    with right params when attributes are provided. """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'}
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_impression_event(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                '111129',
                'test_user',
                {'test_attribute': 'test_value'},
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_impression_event_when_attribute_is_not_in_datafile(self):
        """ Test that create_impression_event creates Event object
      with right params when attribute is not in the datafile. """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_impression_event(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                '111129',
                'test_user',
                {'do_you_know_me': 'test_value'},
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_impression_event_calls_is_attribute_valid(self):
        """ Test that create_impression_event calls is_attribute_valid and
    creates Event object with only those attributes for which is_attribute_valid is True."""

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 5.5, 'entity_id': '111198', 'key': 'double_key'},
                        {'type': 'custom', 'value': True, 'entity_id': '111196', 'key': 'boolean_key'},
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        def side_effect(*args, **kwargs):
            attribute_key = args[0]
            if attribute_key == 'boolean_key' or attribute_key == 'double_key':
                return True

            return False

            attributes = {
                'test_attribute': 'test_value',
                'boolean_key': True,
                'integer_key': 0,
                'double_key': 5.5,
            }

            with mock.patch('time.time', return_value=42.123), mock.patch(
                'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
            ), mock.patch(
                'optimizely.helpers.validator.is_attribute_valid', side_effect=side_effect,
            ):

                event_obj = UserEventFactory.create_impression_event(
                    self.project_config,
                    self.project_config.get_experiment_from_key('test_experiment'),
                    '111129',
                    'test_user',
                    attributes,
                )

            log_event = EventFactory.create_log_event(event_obj, self.logger)

            self._validate_event_object(
                log_event,
                EventFactory.EVENT_ENDPOINT,
                expected_params,
                EventFactory.HTTP_VERB,
                EventFactory.HTTP_HEADERS,
            )

    def test_create_impression_event__with_user_agent_when_bot_filtering_is_enabled(self,):
        """ Test that create_impression_event creates Event object
    with right params when user agent attribute is provided and
    bot filtering is enabled """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'Edge', 'entity_id': '$opt_user_agent', 'key': '$opt_user_agent'},
                        {
                            'type': 'custom',
                            'value': True,
                            'entity_id': '$opt_bot_filtering',
                            'key': '$opt_bot_filtering',
                        },
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.project_config.ProjectConfig.get_bot_filtering_value', return_value=True,
        ):
            event_obj = UserEventFactory.create_impression_event(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                '111129',
                'test_user',
                {'$opt_user_agent': 'Edge'},
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_impression_event__with_empty_attributes_when_bot_filtering_is_enabled(self,):
        """ Test that create_impression_event creates Event object
    with right params when empty attributes are provided and
    bot filtering is enabled """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {
                            'type': 'custom',
                            'value': True,
                            'entity_id': '$opt_bot_filtering',
                            'key': '$opt_bot_filtering',
                        }
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.project_config.ProjectConfig.get_bot_filtering_value', return_value=True,
        ):
            event_obj = UserEventFactory.create_impression_event(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                '111129',
                'test_user',
                None,
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_impression_event__with_user_agent_when_bot_filtering_is_disabled(self,):
        """ Test that create_impression_event creates Event object
    with right params when user agent attribute is provided and
    bot filtering is disabled """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {
                            'type': 'custom',
                            'value': 'Chrome',
                            'entity_id': '$opt_user_agent',
                            'key': '$opt_user_agent',
                        },
                        {
                            'type': 'custom',
                            'value': False,
                            'entity_id': '$opt_bot_filtering',
                            'key': '$opt_bot_filtering',
                        },
                    ],
                    'snapshots': [
                        {
                            'decisions': [
                                {'variation_id': '111129', 'experiment_id': '111127', 'campaign_id': '111182'}
                            ],
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111182',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'campaign_activated',
                                }
                            ],
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.project_config.ProjectConfig.get_bot_filtering_value', return_value=False,
        ):
            event_obj = UserEventFactory.create_impression_event(
                self.project_config,
                self.project_config.get_experiment_from_key('test_experiment'),
                '111129',
                'test_user',
                {'$opt_user_agent': 'Chrome'},
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_conversion_event(self):
        """ Test that create_conversion_event creates Event object
    with right params when no attributes are provided. """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_conversion_event(
                self.project_config, 'test_event', 'test_user', None, None
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_conversion_event__with_attributes(self):
        """ Test that create_conversion_event creates Event object
    with right params when attributes are provided. """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'test_value', 'entity_id': '111094', 'key': 'test_attribute'}
                    ],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_conversion_event(
                self.project_config, 'test_event', 'test_user', {'test_attribute': 'test_value'}, None,
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_conversion_event__with_user_agent_when_bot_filtering_is_enabled(self,):
        """ Test that create_conversion_event creates Event object
    with right params when user agent attribute is provided and
    bot filtering is enabled """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {'type': 'custom', 'value': 'Edge', 'entity_id': '$opt_user_agent', 'key': '$opt_user_agent'},
                        {
                            'type': 'custom',
                            'value': True,
                            'entity_id': '$opt_bot_filtering',
                            'key': '$opt_bot_filtering',
                        },
                    ],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.project_config.ProjectConfig.get_bot_filtering_value', return_value=True,
        ):
            event_obj = UserEventFactory.create_conversion_event(
                self.project_config, 'test_event', 'test_user', {'$opt_user_agent': 'Edge'}, None,
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_conversion_event__with_user_agent_when_bot_filtering_is_disabled(self,):
        """ Test that create_conversion_event creates Event object
    with right params when user agent attribute is provided and
    bot filtering is disabled """

        expected_params = {
            'account_id': '12001',
            'project_id': '111001',
            'visitors': [
                {
                    'visitor_id': 'test_user',
                    'attributes': [
                        {
                            'type': 'custom',
                            'value': 'Chrome',
                            'entity_id': '$opt_user_agent',
                            'key': '$opt_user_agent',
                        },
                        {
                            'type': 'custom',
                            'value': False,
                            'entity_id': '$opt_bot_filtering',
                            'key': '$opt_bot_filtering',
                        },
                    ],
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                }
                            ]
                        }
                    ],
                }
            ],
            'client_name': 'python-sdk',
            'client_version': version.__version__,
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ), mock.patch(
            'optimizely.project_config.ProjectConfig.get_bot_filtering_value', return_value=False,
        ):
            event_obj = UserEventFactory.create_conversion_event(
                self.project_config, 'test_event', 'test_user', {'$opt_user_agent': 'Chrome'}, None,
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_conversion_event__with_event_tags(self):
        """ Test that create_conversion_event creates Event object
    with right params when event tags are provided. """

        expected_params = {
            'client_version': version.__version__,
            'project_id': '111001',
            'visitors': [
                {
                    'attributes': [
                        {'entity_id': '111094', 'type': 'custom', 'value': 'test_value', 'key': 'test_attribute'}
                    ],
                    'visitor_id': 'test_user',
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'tags': {'non-revenue': 'abc', 'revenue': 4200, 'value': 1.234},
                                    'timestamp': 42123,
                                    'revenue': 4200,
                                    'value': 1.234,
                                    'key': 'test_event',
                                    'entity_id': '111095',
                                }
                            ]
                        }
                    ],
                }
            ],
            'account_id': '12001',
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_conversion_event(
                self.project_config,
                'test_event',
                'test_user',
                {'test_attribute': 'test_value'},
                {'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'},
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_conversion_event__with_invalid_event_tags(self):
        """ Test that create_conversion_event creates Event object
    with right params when event tags are provided. """

        expected_params = {
            'client_version': version.__version__,
            'project_id': '111001',
            'visitors': [
                {
                    'attributes': [
                        {'entity_id': '111094', 'type': 'custom', 'value': 'test_value', 'key': 'test_attribute'}
                    ],
                    'visitor_id': 'test_user',
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'timestamp': 42123,
                                    'entity_id': '111095',
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'key': 'test_event',
                                    'tags': {'non-revenue': 'abc', 'revenue': '4200', 'value': True},
                                }
                            ]
                        }
                    ],
                }
            ],
            'account_id': '12001',
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_conversion_event(
                self.project_config,
                'test_event',
                'test_user',
                {'test_attribute': 'test_value'},
                {'revenue': '4200', 'value': True, 'non-revenue': 'abc'},
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )

    def test_create_conversion_event__when_event_is_used_in_multiple_experiments(self):
        """ Test that create_conversion_event creates Event object with
    right params when multiple experiments use the same event. """

        expected_params = {
            'client_version': version.__version__,
            'project_id': '111001',
            'visitors': [
                {
                    'attributes': [
                        {'entity_id': '111094', 'type': 'custom', 'value': 'test_value', 'key': 'test_attribute'}
                    ],
                    'visitor_id': 'test_user',
                    'snapshots': [
                        {
                            'events': [
                                {
                                    'uuid': 'a68cf1ad-0393-4e18-af87-efe8f01a7c9c',
                                    'tags': {'non-revenue': 'abc', 'revenue': 4200, 'value': 1.234},
                                    'timestamp': 42123,
                                    'revenue': 4200,
                                    'value': 1.234,
                                    'key': 'test_event',
                                    'entity_id': '111095',
                                }
                            ]
                        }
                    ],
                }
            ],
            'account_id': '12001',
            'client_name': 'python-sdk',
            'enrich_decisions': True,
            'anonymize_ip': False,
            'revision': '42',
        }

        with mock.patch('time.time', return_value=42.123), mock.patch(
            'uuid.uuid4', return_value='a68cf1ad-0393-4e18-af87-efe8f01a7c9c'
        ):
            event_obj = UserEventFactory.create_conversion_event(
                self.project_config,
                'test_event',
                'test_user',
                {'test_attribute': 'test_value'},
                {'revenue': 4200, 'value': 1.234, 'non-revenue': 'abc'},
            )

        log_event = EventFactory.create_log_event(event_obj, self.logger)

        self._validate_event_object(
            log_event, EventFactory.EVENT_ENDPOINT, expected_params, EventFactory.HTTP_VERB, EventFactory.HTTP_HEADERS,
        )
