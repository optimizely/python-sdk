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

from sys import version_info

if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final  # type: ignore


class OptimizelyDecisionMessage:
    SDK_NOT_READY: Final = 'Optimizely SDK not configured properly yet.'
    FLAG_KEY_INVALID: Final = 'No flag was found for key "{}".'
    VARIABLE_VALUE_INVALID: Final = 'Variable value for key "{}" is invalid or wrong type.'
