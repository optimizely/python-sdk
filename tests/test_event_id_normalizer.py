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

"""Unit tests for :mod:`optimizely.event.event_id_normalizer`."""

import unittest

from optimizely.event import event_id_normalizer


class IsNonEmptyStringTest(unittest.TestCase):
    """Cover :func:`event_id_normalizer.is_non_empty_string`.

    Any non-empty string is valid for ``campaign_id`` / ``entity_id`` — IDs
    may be numeric like ``"12345"`` or opaque like ``"default-12345"``.
    """

    def test_returns_true_for_numeric_string(self):
        self.assertTrue(event_id_normalizer.is_non_empty_string('12345'))

    def test_returns_true_for_opaque_string(self):
        # Opaque IDs are explicitly valid for campaign_id / entity_id.
        self.assertTrue(event_id_normalizer.is_non_empty_string('default-12345'))
        self.assertTrue(event_id_normalizer.is_non_empty_string('layer_abc'))
        self.assertTrue(event_id_normalizer.is_non_empty_string('abc'))

    def test_returns_true_for_whitespace_string(self):
        # Whitespace is a non-empty string and so is accepted;
        # character-content validation is deferred upstream.
        self.assertTrue(event_id_normalizer.is_non_empty_string(' '))

    def test_returns_false_for_empty_string(self):
        self.assertFalse(event_id_normalizer.is_non_empty_string(''))

    def test_returns_false_for_none(self):
        self.assertFalse(event_id_normalizer.is_non_empty_string(None))

    def test_returns_false_for_non_string_types(self):
        # Non-string types are rejected so the fallback path fires.
        self.assertFalse(event_id_normalizer.is_non_empty_string(12345))
        self.assertFalse(event_id_normalizer.is_non_empty_string(123.0))
        self.assertFalse(event_id_normalizer.is_non_empty_string(True))
        self.assertFalse(event_id_normalizer.is_non_empty_string(['123']))
        self.assertFalse(event_id_normalizer.is_non_empty_string({'id': '123'}))


class IsNumericIdStringTest(unittest.TestCase):
    """Cover :func:`event_id_normalizer.is_numeric_id_string` edge cases.

    Used only for ``variation_id``, which retains the strict
    decimal-digit contract.
    """

    def test_returns_true_for_decimal_digit_string(self):
        self.assertTrue(event_id_normalizer.is_numeric_id_string('12345'))

    def test_returns_true_for_single_digit(self):
        self.assertTrue(event_id_normalizer.is_numeric_id_string('0'))
        self.assertTrue(event_id_normalizer.is_numeric_id_string('9'))

    def test_returns_true_for_leading_zeros(self):
        # Leading zeros are explicitly allowed.
        self.assertTrue(event_id_normalizer.is_numeric_id_string('007'))
        self.assertTrue(event_id_normalizer.is_numeric_id_string('00000'))

    def test_returns_false_for_empty_string(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string(''))

    def test_returns_false_for_none(self):
        self.assertFalse(event_id_normalizer.is_numeric_id_string(None))

    def test_returns_false_for_int(self):
        # The value must be a string.
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
    """Cover :func:`event_id_normalizer.normalize_campaign_id`.

    Any non-empty string is valid for campaign_id — fallback to
    ``experiment_id`` fires only on empty/None/missing.
    """

    def test_returns_campaign_id_when_numeric(self):
        self.assertEqual(
            '111182',
            event_id_normalizer.normalize_campaign_id('111182', '111127'),
        )

    def test_returns_campaign_id_when_opaque_string(self):
        # Opaque IDs (e.g. holdout layer IDs) pass through.
        self.assertEqual(
            'default-12345',
            event_id_normalizer.normalize_campaign_id('default-12345', '111127'),
        )
        self.assertEqual(
            'layer_abc',
            event_id_normalizer.normalize_campaign_id('layer_abc', '111127'),
        )

    def test_returns_campaign_id_when_whitespace_string(self):
        # Whitespace is non-empty; passes through (validation deferred upstream).
        self.assertEqual(
            ' ',
            event_id_normalizer.normalize_campaign_id(' ', '111127'),
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

    def test_falls_back_to_opaque_experiment_id(self):
        # Both fields may be opaque non-numeric strings.
        self.assertEqual(
            'exp_42',
            event_id_normalizer.normalize_campaign_id('', 'exp_42'),
        )

    def test_returns_empty_string_when_both_empty_or_none(self):
        # Do not drop / fail dispatch; return ''.
        self.assertEqual('', event_id_normalizer.normalize_campaign_id(None, None))
        self.assertEqual('', event_id_normalizer.normalize_campaign_id('', ''))
        self.assertEqual('', event_id_normalizer.normalize_campaign_id(None, ''))

    def test_preserves_leading_zeros(self):
        self.assertEqual(
            '007',
            event_id_normalizer.normalize_campaign_id('007', '111127'),
        )


class NormalizeVariationIdTest(unittest.TestCase):
    """Cover :func:`event_id_normalizer.normalize_variation_id`.

    ``variation_id`` retains the strict numeric-string contract.
    """

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


if __name__ == '__main__':
    unittest.main()
