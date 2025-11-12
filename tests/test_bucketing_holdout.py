# Copyright 2025 Optimizely and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import json
from unittest import mock

from optimizely import bucketer
from optimizely import error_handler
from optimizely import logger
from optimizely import optimizely as optimizely_module
from tests import base


class TestBucketer(bucketer.Bucketer):
    """Helper class for testing with controlled bucket values."""

    def __init__(self):
        super().__init__()
        self._bucket_values = []
        self._bucket_index = 0

    def set_bucket_values(self, values):
        """Set predetermined bucket values for testing."""
        self._bucket_values = values
        self._bucket_index = 0

    def _generate_bucket_value(self, bucketing_id):
        """Override to return controlled bucket values."""
        if not self._bucket_values:
            return super()._generate_bucket_value(bucketing_id)

        value = self._bucket_values[self._bucket_index]
        self._bucket_index = (self._bucket_index + 1) % len(self._bucket_values)
        return value


class BucketerHoldoutTest(base.BaseTest):
    """Tests for Optimizely Bucketer with Holdouts."""

    def setUp(self):
        base.BaseTest.setUp(self)
        self.error_handler = error_handler.NoOpErrorHandler()
        self.mock_logger = mock.MagicMock(spec=logger.Logger)

        # Create a config dict with holdouts that have variations and traffic allocation
        config_dict_with_holdouts = self.config_dict.copy()

        config_dict_with_holdouts['holdouts'] = [
            {
                'id': 'holdout_1',
                'key': 'test_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [
                    {
                        'id': 'var_1',
                        'key': 'control',
                        'variables': []
                    },
                    {
                        'id': 'var_2',
                        'key': 'treatment',
                        'variables': []
                    }
                ],
                'trafficAllocation': [
                    {
                        'entityId': 'var_1',
                        'endOfRange': 5000
                    },
                    {
                        'entityId': 'var_2',
                        'endOfRange': 10000
                    }
                ]
            },
            {
                'id': 'holdout_empty_1',
                'key': 'empty_holdout',
                'status': 'Running',
                'includedFlags': [],
                'excludedFlags': [],
                'audienceIds': [],
                'variations': [],
                'trafficAllocation': []
            }
        ]

        # Convert to JSON and create config
        config_json = json.dumps(config_dict_with_holdouts)
        opt_obj = optimizely_module.Optimizely(config_json)
        self.config = opt_obj.config_manager.get_config()

        self.test_bucketer = TestBucketer()
        self.test_user_id = 'test_user_id'
        self.test_bucketing_id = 'test_bucketing_id'

        # Verify that the config contains holdouts
        self.assertIsNotNone(self.config.holdouts)
        self.assertGreater(len(self.config.holdouts), 0)

    def test_bucket_user_within_valid_traffic_allocation_range(self):
        """Should bucket user within valid traffic allocation range."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Set bucket value to be within first variation's traffic allocation (0-5000 range)
        self.test_bucketer.set_bucket_values([2500])

        variation, reasons = self.test_bucketer.bucket(
            self.config, holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNotNone(variation)
        self.assertEqual(variation['id'], 'var_1')
        self.assertEqual(variation['key'], 'control')

    def test_bucket_returns_none_when_user_outside_traffic_allocation(self):
        """Should return None when user is outside traffic allocation range."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Modify traffic allocation to be smaller
        modified_holdout = copy.deepcopy(holdout)
        modified_holdout['trafficAllocation'] = [
            {
                'entityId': 'var_1',
                'endOfRange': 1000
            }
        ]

        # Set bucket value outside traffic allocation range
        self.test_bucketer.set_bucket_values([1500])

        variation, reasons = self.test_bucketer.bucket(
            self.config, modified_holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNone(variation)

    def test_bucket_returns_none_when_holdout_has_no_traffic_allocation(self):
        """Should return None when holdout has no traffic allocation."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Clear traffic allocation
        modified_holdout = copy.deepcopy(holdout)
        modified_holdout['trafficAllocation'] = []

        self.test_bucketer.set_bucket_values([5000])

        variation, reasons = self.test_bucketer.bucket(
            self.config, modified_holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNone(variation)

    def test_bucket_returns_none_with_invalid_variation_id(self):
        """Should return None when traffic allocation points to invalid variation ID."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Set traffic allocation to point to non-existent variation
        modified_holdout = copy.deepcopy(holdout)
        modified_holdout['trafficAllocation'] = [
            {
                'entityId': 'invalid_variation_id',
                'endOfRange': 10000
            }
        ]

        self.test_bucketer.set_bucket_values([5000])

        variation, reasons = self.test_bucketer.bucket(
            self.config, modified_holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNone(variation)

    def test_bucket_returns_none_when_holdout_has_no_variations(self):
        """Should return None when holdout has no variations."""
        holdout = self.config.get_holdout('holdout_empty_1')
        self.assertIsNotNone(holdout)
        self.assertEqual(len(holdout.get('variations', [])), 0)

        self.test_bucketer.set_bucket_values([5000])

        variation, reasons = self.test_bucketer.bucket(
            self.config, holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNone(variation)

    def test_bucket_returns_none_with_empty_key(self):
        """Should return None when holdout has empty key."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Clear holdout key
        modified_holdout = copy.deepcopy(holdout)
        modified_holdout['key'] = ''

        self.test_bucketer.set_bucket_values([5000])

        variation, reasons = self.test_bucketer.bucket(
            self.config, modified_holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNone(variation)

    def test_bucket_returns_none_with_null_key(self):
        """Should return None when holdout has null key."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Set holdout key to None
        modified_holdout = copy.deepcopy(holdout)
        modified_holdout['key'] = None

        self.test_bucketer.set_bucket_values([5000])

        variation, reasons = self.test_bucketer.bucket(
            self.config, modified_holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNone(variation)

    def test_bucket_user_into_first_variation_with_multiple_variations(self):
        """Should bucket user into first variation with multiple variations."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Verify holdout has multiple variations
        self.assertGreaterEqual(len(holdout['variations']), 2)

        # Test user buckets into first variation
        self.test_bucketer.set_bucket_values([2500])
        variation, reasons = self.test_bucketer.bucket(
            self.config, holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNotNone(variation)
        self.assertEqual(variation['id'], 'var_1')
        self.assertEqual(variation['key'], 'control')

    def test_bucket_user_into_second_variation_with_multiple_variations(self):
        """Should bucket user into second variation with multiple variations."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Verify holdout has multiple variations
        self.assertGreaterEqual(len(holdout['variations']), 2)
        self.assertEqual(holdout['variations'][0]['id'], 'var_1')
        self.assertEqual(holdout['variations'][1]['id'], 'var_2')

        # Test user buckets into second variation (bucket value 7500 should be in 5000-10000 range)
        self.test_bucketer.set_bucket_values([7500])
        variation, reasons = self.test_bucketer.bucket(
            self.config, holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNotNone(variation)
        self.assertEqual(variation['id'], 'var_2')
        self.assertEqual(variation['key'], 'treatment')

    def test_bucket_handles_edge_case_boundary_values(self):
        """Should handle edge case boundary values correctly."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Modify traffic allocation to be 5000 (50%)
        modified_holdout = copy.deepcopy(holdout)
        modified_holdout['trafficAllocation'] = [
            {
                'entityId': 'var_1',
                'endOfRange': 5000
            }
        ]

        # Test exact boundary value (should be included)
        self.test_bucketer.set_bucket_values([4999])
        variation, reasons = self.test_bucketer.bucket(
            self.config, modified_holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNotNone(variation)
        self.assertEqual(variation['id'], 'var_1')

        # Test value just outside boundary (should not be included)
        self.test_bucketer.set_bucket_values([5000])
        variation, reasons = self.test_bucketer.bucket(
            self.config, modified_holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNone(variation)

    def test_bucket_produces_consistent_results_with_same_inputs(self):
        """Should produce consistent results with same inputs."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Create a real bucketer (not test bucketer) for consistent hashing
        real_bucketer = bucketer.Bucketer()
        variation1, reasons1 = real_bucketer.bucket(
            self.config, holdout, self.test_user_id, self.test_bucketing_id
        )
        variation2, reasons2 = real_bucketer.bucket(
            self.config, holdout, self.test_user_id, self.test_bucketing_id
        )

        # Results should be identical
        if variation1:
            self.assertIsNotNone(variation2)
            self.assertEqual(variation1['id'], variation2['id'])
            self.assertEqual(variation1['key'], variation2['key'])
        else:
            self.assertIsNone(variation2)

    def test_bucket_handles_different_bucketing_ids_without_exceptions(self):
        """Should handle different bucketing IDs without exceptions."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        # Create a real bucketer (not test bucketer) for real hashing behavior
        real_bucketer = bucketer.Bucketer()

        # These calls should not raise exceptions
        try:
            real_bucketer.bucket(self.config, holdout, self.test_user_id, 'bucketingId1')
            real_bucketer.bucket(self.config, holdout, self.test_user_id, 'bucketingId2')
        except Exception as e:
            self.fail(f'Bucketing raised an exception: {e}')

    def test_bucket_populates_decision_reasons_properly(self):
        """Should populate decision reasons properly."""
        holdout = self.config.get_holdout('holdout_1')
        self.assertIsNotNone(holdout)

        self.test_bucketer.set_bucket_values([5000])
        variation, reasons = self.test_bucketer.bucket(
            self.config, holdout, self.test_user_id, self.test_bucketing_id
        )

        self.assertIsNotNone(reasons)
        self.assertIsInstance(reasons, list)
        # Decision reasons should be populated from the bucketing process
