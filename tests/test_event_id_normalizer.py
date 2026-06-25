# Copyright 2026, Optimizely
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

"""Unit tests for :mod:`optimizely.event.event_id_normalizer` (FSSDK-12813)."""

import unittest

from optimizely.event import event_id_normalizer


class IsNumericIdStringTest(unittest.TestCase):
    """Cover :func:`event_id_normalizer.is_numeric_id_string` edge cases."""

    def test_returns_true_for_decimal_digit_string(self):
        self.assertTrue(event_id_normalizer.is_numeric_id_string('12345'))

    def test_returns_true_for_single_digit(self):
        self.assertTrue(event_id_normalizer.is_numeric_id_string('0'))
        self.assertTrue(event_id_normalizer.is_numeric_id_string('9'))

    def test_returns_true_for_leading_zeros(self):
        # FR-001 explicitly allows leading zeros.
        self.assertTrue(event_id_normalizer.is_numeric_id_string('007'))
        self.assertTrue(event_id_normalizer.is_numeric_id_string('00000'))

    def test_returns_false_for_empty_string(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string(''))

    def test_returns_false_for_none(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string(None))

    def test_returns_false_for_int(self):
        # FR-001 requires the value to be a string.
        self.assertFalse(event_id_normalizer.is_numeric_id_string(12345))
        self.assertFalse(event_id_normalizer.is_numeric_id_string(0))

    def test_returns_false_for_float(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string(123.0))

    def test_returns_false_for_bool(self):
        # ``bool`` is a subclass of ``int`` but is still not a ``str``.
        self.assertFalse(event_id_normalizer.is_numeric_id_string(True))
        self.assertFalse(event_id_normalizer.is_numeric_id_string(False))

    def test_returns_false_for_whitespace(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string(' '))
        self.assertFalse(event_id_normalizer.is_numeric_id_string(' 123'))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('123 '))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('1 2'))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('\t'))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('\n'))

    def test_returns_false_for_signed_numbers(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string('-1'))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('+1'))

    def test_returns_false_for_decimals(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string('1.0'))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('.5'))

    def test_returns_false_for_exponents(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string('1e5'))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('1E5'))

    def test_returns_false_for_hex(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string('0x1A'))
        self.assertFalse(event_id_normalizer.is_numeric_id_string('abc'))

    def test_returns_false_for_unicode_digits(self):
        # ``str.isdigit`` is True for many non-ASCII digit code points; the
        # normalizer must reject these because the wire format expects ASCII.
        self.assertFalse(event_id_normalizer.is_numeric_id_string('٠١'))  # Arabic-Indic 01
        self.assertFalse(event_id_normalizer.is_numeric_id_string('²'))  # superscript 2

    def test_returns_false_for_collections(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string(['123']))
        self.assertFalse(event_id_normalizer.is_numeric_id_string({'id': '123'}))
        self.assertFalse(event_id_normalizer.is_numeric_id_string(('1',)))


class NormalizeCampaignIdTest(unittest.TestCase):
    """Cover :func:`event_id_normalizer.normalize_campaign_id` per FR-001/002, FR-009."""

    def test_returns_campaign_id_when_valid(self):
        self.assertEqual(
            '111182',
            event_id_normalizer.normalize_campaign_id('111182', '111127'),
        )

    def test_falls_back_to_experiment_id_when_campaign_id_empty(self):
        self.assertEqual(
            '111127',
            event_id_normalizer.normalize_campaign_id('', '111127'),
        )

    def test_falls_back_to_experiment_id_when_campaign_id_none(self):
        self.assertEqual(
            '111127',
            event_id_normalizer.normalize_campaign_id(None, '111127'),
        )

    def test_falls_back_to_experiment_id_when_campaign_id_non_numeric(self):
        self.assertEqual(
            '111127',
            event_id_normalizer.normalize_campaign_id('abc', '111127'),
        )

    def test_falls_back_to_experiment_id_when_campaign_id_whitespace(self):
        self.assertEqual(
            '111127',
            event_id_normalizer.normalize_campaign_id(' ', '111127'),
        )

    def test_falls_back_to_experiment_id_when_campaign_id_int(self):
        # An int input is invalid (FR-001 requires a string).
        self.assertEqual(
            '111127',
            event_id_normalizer.normalize_campaign_id(111182, '111127'),
        )

    def test_returns_empty_string_when_both_invalid(self):
        # Do not drop / fail dispatch (FR-006); return ''.
        self.assertEqual('', event_id_normalizer.normalize_campaign_id(None, None))
        self.assertEqual('', event_id_normalizer.normalize_campaign_id('', ''))
        self.assertEqual('', event_id_normalizer.normalize_campaign_id('abc', 'xyz'))

    def test_preserves_leading_zeros(self):
        self.assertEqual(
            '007',
            event_id_normalizer.normalize_campaign_id('007', '111127'),
        )


class NormalizeVariationIdTest(unittest.TestCase):
    """Cover :func:`event_id_normalizer.normalize_variation_id` per FR-003/004."""

    def test_returns_variation_id_when_valid(self):
        self.assertEqual(
            '111129',
            event_id_normalizer.normalize_variation_id('111129'),
        )

    def test_returns_none_when_empty(self):
        self.assertIsNone(event_id_normalizer.normalize_variation_id(''))

    def test_returns_none_when_none(self):
        self.assertIsNone(event_id_normalizer.normalize_variation_id(None))

    def test_returns_none_when_non_string(self):
        self.assertIsNone(event_id_normalizer.normalize_variation_id(111129))
        self.assertIsNone(event_id_normalizer.normalize_variation_id(123.0))
        self.assertIsNone(event_id_normalizer.normalize_variation_id(True))

    def test_returns_none_when_non_numeric(self):
        self.assertIsNone(event_id_normalizer.normalize_variation_id('variation_a'))
        self.assertIsNone(event_id_normalizer.normalize_variation_id('abc'))

    def test_returns_none_when_whitespace(self):
        self.assertIsNone(event_id_normalizer.normalize_variation_id(' '))
        self.assertIsNone(event_id_normalizer.normalize_variation_id('  111129'))

    def test_returns_none_when_signed(self):
        self.assertIsNone(event_id_normalizer.normalize_variation_id('-111129'))

    def test_preserves_leading_zeros(self):
        self.assertEqual('007', event_id_normalizer.normalize_variation_id('007'))


class NormalizeStringIdTest(unittest.TestCase):
    """Cover the generic :func:`event_id_normalizer.normalize_string_id` helper."""

    def test_returns_value_when_valid(self):
        self.assertEqual('42', event_id_normalizer.normalize_string_id('42'))

    def test_returns_none_when_invalid(self):
        self.assertIsNone(event_id_normalizer.normalize_string_id(''))
        self.assertIsNone(event_id_normalizer.normalize_string_id(None))
        self.assertIsNone(event_id_normalizer.normalize_string_id('xx'))


if __name__ == '__main__':
    unittest.main()
