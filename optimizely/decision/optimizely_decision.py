# Copyright 2021, Optimizely
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


class OptimizelyDecision(object):
    def __init__(self, variation_key=None, enabled=None,
                 variables=None, rule_key=None, flag_key=None, user_context=None, reasons=None):
        self.variation_key = variation_key
        self.enabled = enabled or False
        self.variables = variables or {}
        self.rule_key = rule_key
        self.flag_key = flag_key
        self.user_context = user_context
        self.reasons = reasons or []

    def as_json(self):
        return {
            'variation_key': self.variation_key,
            'enabled': self.enabled,
            'variables': self.variables,
            'rule_key': self.rule_key,
            'flag_key': self.flag_key,
            'user_context': self.user_context.as_json(),
            'reasons': self.reasons
        }
