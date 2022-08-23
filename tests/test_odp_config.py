# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
from tests import base
from optimizely.odp.odp_config import OdpConfig


class OdpConfigTest(base.BaseTest):
    api_host = 'test-host'
    api_key = 'test-key'
    segments_to_check = ['test-segment']

    def test_init_config(self):
        config = OdpConfig(self.api_key, self.api_host, self.segments_to_check)

        self.assertEqual(config.get_api_key(), self.api_key)
        self.assertEqual(config.get_api_host(), self.api_host)
        self.assertEqual(config.get_segments_to_check(), self.segments_to_check)

    def test_update_config(self):
        config = OdpConfig()
        updated = config.update(self.api_key, self.api_host, self.segments_to_check)

        self.assertStrictTrue(updated)
        self.assertEqual(config.get_api_key(), self.api_key)
        self.assertEqual(config.get_api_host(), self.api_host)
        self.assertEqual(config.get_segments_to_check(), self.segments_to_check)

        updated = config.update(self.api_key, self.api_host, self.segments_to_check)
        self.assertStrictFalse(updated)