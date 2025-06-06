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


class OptimizelyDecideOption:
    DISABLE_DECISION_EVENT: Final = 'DISABLE_DECISION_EVENT'
    ENABLED_FLAGS_ONLY: Final = 'ENABLED_FLAGS_ONLY'
    IGNORE_USER_PROFILE_SERVICE: Final = 'IGNORE_USER_PROFILE_SERVICE'
    INCLUDE_REASONS: Final = 'INCLUDE_REASONS'
    EXCLUDE_VARIABLES: Final = 'EXCLUDE_VARIABLES'
    IGNORE_CMAB_CACHE: Final = "IGNORE_CMAB_CACHE"
    RESET_CMAB_CACHE: Final = "RESET_CMAB_CACHE"
    INVALIDATE_USER_CMAB_CACHE: Final = "INVALIDATE_USER_CMAB_CACHE"
