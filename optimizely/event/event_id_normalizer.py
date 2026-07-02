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
appear in dispatched decision events.

Rules:
  * ``campaign_id`` and impression ``entity_id`` accept **any non-empty
    string** (numeric like ``"12345"`` or opaque like ``"default-12345"`` /
    ``"layer_abc"``). The fallback to ``experiment_id`` fires ONLY when the
    value is the empty string, ``None``, or missing. Non-string types are
    out of scope for this normalization path (the upstream datafile
    producer delivers string or null values).
  * ``variation_id`` retains the stricter contract: it MUST be a non-empty
    string of decimal digits ``0-9`` (leading zeros allowed). Empty,
    whitespace, non-string, and non-numeric inputs are normalized to
    ``None`` so the wire payload carries an explicit null.
  * ``entity_id`` on impression events shares the campaign_id normalization
    and is therefore byte-equivalent to the normalized campaign_id for the
    same impression.

The normalization path MUST NOT log, warn, or raise. It must never drop or
defer event dispatch.
"""


from sys import version_info
from typing import Any, Optional

if version_info < (3, 10):
    from typing_extensions import TypeGuard
else:
    from typing import TypeGuard


def is_non_empty_string(value: Any) -> TypeGuard[str]:
    """Return ``True`` if ``value`` is a non-empty :class:`str`.
    Any non-empty string is accepted regardless of
    character content (IDs may be opaque, e.g. ``"default-12345"``).
    """
    return isinstance(value, str) and value != ''


def is_numeric_id_string(value: Any) -> TypeGuard[str]:
    """Return ``True`` if ``value`` is a non-empty decimal-digit string.
    Whitespace, signs, decimal points, exponents
    and non-string types all return ``False``. Leading
    zeros are accepted.
    """
    if not isinstance(value, str):
        return False
    if value == '':
        return False
    return value.isascii() and value.isdigit()


def normalize_campaign_id(campaign_id: Any, experiment_id: Any) -> str:
    """Normalize a decision-event ``campaign_id``.

    Returns ``campaign_id`` unchanged when it is a non-empty string (any
    character content — numeric like ``"12345"`` or opaque like
    ``"default-12345"``). Otherwise falls back to ``experiment_id`` (when it
    is itself a non-empty string). If neither is a non-empty string, returns
    an empty string so the event still dispatches.
    """
    if is_non_empty_string(campaign_id):
        return campaign_id
    if is_non_empty_string(experiment_id):
        return experiment_id
    return ''


def normalize_variation_id(variation_id: Any) -> Optional[str]:
    """Normalize a decision-event ``variation_id``.

    Returns the original value if it is a valid numeric ID string. Otherwise
    returns ``None`` so the event payload carries an explicit null for the
    downstream consumer.
    """
    return variation_id if is_numeric_id_string(variation_id) else None
