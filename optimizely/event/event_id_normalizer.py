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

"""Normalization helpers for decision-event ID fields.

This module provides byte-equivalent, cross-SDK normalization for the
``campaign_id``, ``variation_id``, and impression ``entity_id`` fields that
appear in dispatched decision events. See FSSDK-12813.

Rules:
  * A "numeric ID string" is a non-empty :class:`str` consisting entirely of
    decimal digits ``0-9``. Leading zeros are allowed. Whitespace, negatives,
    decimals, and exponents are INVALID.
  * ``campaign_id`` -> when invalid, falls back to ``experiment_id`` (which is
    itself passed through :func:`normalize_string_id`).
  * ``variation_id`` -> when invalid, becomes ``None``.
  * ``entity_id`` on impression events shares the campaign_id normalization
    and is therefore byte-equivalent to the normalized campaign_id for the
    same impression (FR-009).

The normalization path MUST NOT log, warn, or raise. It must never drop or
defer event dispatch.
"""

from __future__ import annotations

from typing import Any, Optional


def is_numeric_id_string(value: Any) -> bool:
    """Return ``True`` if ``value`` is a non-empty decimal-digit string.

    Whitespace, signs, decimal points, exponents, and non-string types all
    return ``False``. Leading zeros are accepted.
    """
    if not isinstance(value, str):
        return False
    if value == '':
        return False
    # ``str.isdigit`` rejects everything except [0-9] characters and the
    # empty string. We've already excluded the empty case above. Note that
    # ``isdigit`` also accepts some non-ASCII digit code points; ``isascii``
    # combined with ``isdigit`` restricts us to plain decimal digits.
    return value.isascii() and value.isdigit()


def normalize_string_id(value: Any) -> Optional[str]:
    """Return ``value`` if it's a numeric ID string, otherwise ``None``."""
    return value if is_numeric_id_string(value) else None


def normalize_campaign_id(campaign_id: Any, experiment_id: Any) -> str:
    """Normalize a decision-event ``campaign_id`` (FR-001/FR-002, FR-009).

    If ``campaign_id`` is a valid numeric ID string it is returned unchanged.
    Otherwise the function falls back to ``experiment_id`` (after applying
    the same validation). If neither is a numeric ID string, an empty string
    is returned so the event still dispatches (FR-006).
    """
    if is_numeric_id_string(campaign_id):
        return campaign_id  # type: ignore[no-any-return]
    if is_numeric_id_string(experiment_id):
        return experiment_id  # type: ignore[no-any-return]
    return ''


def normalize_variation_id(variation_id: Any) -> Optional[str]:
    """Normalize a decision-event ``variation_id`` (FR-003/FR-004).

    Returns the original value if it is a valid numeric ID string. Otherwise
    returns ``None`` so the event payload omits/clears the field for the
    downstream consumer.
    """
    return variation_id if is_numeric_id_string(variation_id) else None
