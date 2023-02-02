# Copyright 2023, Optimizely
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

import json
from unittest import mock
import copy

from optimizely.notification_center_registry import _NotificationCenterRegistry
from optimizely.notification_center import NotificationCenter
from optimizely.optimizely import Optimizely
from optimizely.helpers.enums import NotificationTypes, Errors
from .base import BaseTest


class NotificationCenterRegistryTest(BaseTest):
    def test_get_notification_center(self):
        logger = mock.MagicMock()
        sdk_key = 'test'
        client = Optimizely(sdk_key=sdk_key, logger=logger)
        notification_center = _NotificationCenterRegistry.get_notification_center(sdk_key, logger)
        self.assertIsInstance(notification_center, NotificationCenter)
        config_notifications = notification_center.notification_listeners[NotificationTypes.OPTIMIZELY_CONFIG_UPDATE]

        self.assertIn((mock.ANY, client._update_odp_config_on_datafile_update), config_notifications)

        logger.error.assert_not_called()

        _NotificationCenterRegistry.get_notification_center(None, logger)

        logger.error.assert_called_once_with(f'{Errors.MISSING_SDK_KEY} ODP may not work properly without it.')

        client.close()

    def test_only_one_notification_center_created(self):
        logger = mock.MagicMock()
        sdk_key = 'single'
        notification_center = _NotificationCenterRegistry.get_notification_center(sdk_key, logger)
        client = Optimizely(sdk_key=sdk_key, logger=logger)

        self.assertIs(notification_center, _NotificationCenterRegistry.get_notification_center(sdk_key, logger))

        logger.error.assert_not_called()

        client.close()

    def test_remove_notification_center(self):
        logger = mock.MagicMock()
        sdk_key = 'segments-test'
        test_datafile = json.dumps(self.config_dict_with_audience_segments)
        test_response = self.fake_server_response(status_code=200, content=test_datafile)
        notification_center = _NotificationCenterRegistry.get_notification_center(sdk_key, logger)

        with mock.patch('requests.get', return_value=test_response), \
             mock.patch.object(notification_center, 'send_notifications') as mock_send:

            client = Optimizely(sdk_key=sdk_key, logger=logger)
            client.config_manager.get_config()

            mock_send.assert_called_once()
            mock_send.reset_mock()

            _NotificationCenterRegistry.remove_notification_center(sdk_key)
            self.assertNotIn(notification_center, _NotificationCenterRegistry._notification_centers)

            revised_datafile = copy.deepcopy(self.config_dict_with_audience_segments)
            revised_datafile['revision'] = str(int(revised_datafile['revision']) + 1)

            # trigger notification
            client.config_manager._set_config(json.dumps(revised_datafile))
            mock_send.assert_not_called()

        logger.error.assert_not_called()

        client.close()
