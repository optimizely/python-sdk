# Copyright 2021, 2022, Optimizely
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

from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from optimizely.optimizely_user_context import OptimizelyUserContext


class OptimizelyDecision:
    def __init__(
        self,
        variation_key: Optional[str] = None,
        enabled: bool = False,
        variables: Optional[dict[str, Any]] = None,
        rule_key: Optional[str] = None,
        flag_key: Optional[str] = None,
        user_context: Optional[OptimizelyUserContext] = None,
        reasons: Optional[list[str]] = None
    ):
        self.variation_key = variation_key
        self.enabled = enabled
        self.variables = variables or {}
        self.rule_key = rule_key
        self.flag_key = flag_key
        self.user_context = user_context
        self.reasons = reasons or []

    def as_json(self) -> dict[str, Any]:
        return {
            'variation_key': self.variation_key,
            'enabled': self.enabled,
            'variables': self.variables,
            'rule_key': self.rule_key,
            'flag_key': self.flag_key,
            'user_context': self.user_context.as_json() if self.user_context else None,
            'reasons': self.reasons
        }

    @classmethod
    def new_error_decision(cls, key: str, user: OptimizelyUserContext, reasons: list[str]) -> OptimizelyDecision:
        """Create a new OptimizelyDecision representing an error state.
        Args:
            key: The flag key
            user: The user context
            reasons: List of reasons explaining the error
        Returns:
            OptimizelyDecision with error state values
        """
        return cls(
            variation_key=None,
            enabled=False,
            variables={},
            rule_key=None,
            flag_key=key,
            user_context=user,
            reasons=reasons if reasons else []
        )
