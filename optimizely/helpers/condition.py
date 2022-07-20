# Copyright 2016, 2018-2020, 2022, Optimizely
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
import json
import numbers
from typing import TYPE_CHECKING, Any, Callable, Optional
from sys import version_info

from . import validator
from optimizely import optimizely_user_context
from .enums import CommonAudienceEvaluationLogs as audience_logs
from .enums import Errors
from .enums import VersionType


if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from optimizely.logger import Logger


if version_info < (3, 8):
    from typing_extensions import Literal, Final
else:
    from typing import Literal, Final  # type: ignore


class ConditionOperatorTypes:
    AND: Final = 'and'
    OR: Final = 'or'
    NOT: Final = 'not'
    operators = [AND, OR, NOT]


class ConditionMatchTypes:
    EXACT: Final = 'exact'
    EXISTS: Final = 'exists'
    GREATER_THAN: Final = 'gt'
    GREATER_THAN_OR_EQUAL: Final = 'ge'
    LESS_THAN: Final = 'lt'
    LESS_THAN_OR_EQUAL: Final = 'le'
    SEMVER_EQ: Final = 'semver_eq'
    SEMVER_GE: Final = 'semver_ge'
    SEMVER_GT: Final = 'semver_gt'
    SEMVER_LE: Final = 'semver_le'
    SEMVER_LT: Final = 'semver_lt'
    SUBSTRING: Final = 'substring'
    QUALIFIED: Final = 'qualified'


class CustomAttributeConditionEvaluator:
    """ Class encapsulating methods to be used in audience leaf condition evaluation. """

    CONDITION_TYPES: Final = ('custom_attribute', 'third_party_dimension')

    def __init__(
        self,
        condition_data: list[str | list[str]],
        user_context: optimizely_user_context.OptimizelyUserContext,
        logger: Logger
    ):
        self.condition_data = condition_data
        self.user_context = user_context
        self.attributes = user_context.get_user_attributes()
        self.logger = logger

    def _get_condition_json(self, index: int) -> str:
        """ Method to generate json for logging audience condition.

    Args:
      index: Index of the condition.

    Returns:
      String: Audience condition JSON.
    """
        condition = self.condition_data[index]
        condition_log = {
            'name': condition[0],
            'value': condition[1],
            'type': condition[2],
            'match': condition[3],
        }

        return json.dumps(condition_log)

    def is_value_type_valid_for_exact_conditions(self, value: Any) -> bool:
        """ Method to validate if the value is valid for exact match type evaluation.

    Args:
      value: Value to validate.

    Returns:
      Boolean: True if value is a string, boolean, or number. Otherwise False.
    """
        # No need to check for bool since bool is a subclass of int
        if isinstance(value, str) or isinstance(value, (numbers.Integral, float)):
            return True

        return False

    def is_value_a_number(self, value: Any) -> bool:
        if isinstance(value, (numbers.Integral, float)) and not isinstance(value, bool):
            return True

        return False

    def is_pre_release_version(self, version: str) -> bool:
        """ Method to check if given version is pre-release.
            Criteria for pre-release includes:
                - Version includes "-"

        Args:
          version: Given version in string.

        Returns:
          Boolean:
            - True if the given version is pre-release
            - False if it doesn't
        """
        if VersionType.IS_PRE_RELEASE in version:
            user_version_release_index = version.find(VersionType.IS_PRE_RELEASE)
            user_version_build_index = version.find(VersionType.IS_BUILD)
            if (user_version_release_index < user_version_build_index) or (user_version_build_index < 0):
                return True
        return False

    def is_build_version(self, version: str) -> bool:
        """ Method to check given version is a build version.
            Criteria for build version includes:
                - Version includes "+"

        Args:
          version: Given version in string.

        Returns:
          Boolean:
            - True if the given version is a build version
            - False if it doesn't
        """
        if VersionType.IS_BUILD in version:
            user_version_release_index = version.find(VersionType.IS_PRE_RELEASE)
            user_version_build_index = version.find(VersionType.IS_BUILD)
            if (user_version_build_index < user_version_release_index) or (user_version_release_index < 0):
                return True
        return False

    def has_white_space(self, version: str) -> bool:
        """ Method to check if the given version contains " " (white space)

        Args:
          version: Given version in string.

        Returns:
          Boolean:
            - True if the given version does contain whitespace
            - False if it doesn't
        """
        return ' ' in version

    def compare_user_version_with_target_version(
        self, target_version: str, user_version: str
    ) -> Optional[Literal[0] | Literal[1] | Literal[-1]]:
        """ Method to compare user version with target version.

        Args:
          target_version: String representing condition value
          user_version: String representing user value

        Returns:
          Int:
            -  0 if user version is equal to target version.
            -  1 if user version is greater than target version.
            - -1 if user version is less than target version or, in case of exact string match, doesn't match the target
            version.
          None:
            - if the user version value format is not a valid semantic version.
        """
        is_pre_release_in_target_version = self.is_pre_release_version(target_version)
        is_pre_release_in_user_version = self.is_pre_release_version(user_version)
        is_build_in_target_version = self.is_build_version(target_version)

        target_version_parts = self.split_version(target_version)
        if target_version_parts is None:
            return None

        user_version_parts = self.split_version(user_version)
        if user_version_parts is None:
            return None

        user_version_parts_len = len(user_version_parts)

        for (idx, _) in enumerate(target_version_parts):
            if user_version_parts_len <= idx:
                return 1 if is_pre_release_in_target_version or is_build_in_target_version else -1
            elif not user_version_parts[idx].isdigit():
                if user_version_parts[idx] < target_version_parts[idx]:
                    return 1 if is_pre_release_in_target_version and not \
                        is_pre_release_in_user_version else -1
                elif user_version_parts[idx] > target_version_parts[idx]:
                    return -1 if not is_pre_release_in_target_version and \
                        is_pre_release_in_user_version else 1
            else:
                user_version_part = int(user_version_parts[idx])
                target_version_part = int(target_version_parts[idx])
                if user_version_part > target_version_part:
                    return 1
                elif user_version_part < target_version_part:
                    return -1

        # check if user version contains pre-release and target version doesn't
        if is_pre_release_in_user_version and not is_pre_release_in_target_version:
            return -1
        return 0

    def exact_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given exact match condition for the user attributes.

    Args:
      index: Index of the condition to be evaluated.

    Returns:
      Boolean:
        - True if the user attribute value is equal (===) to the condition value.
        - False if the user attribute value is not equal (!==) to the condition value.
      None:
        - if the condition value or user attribute value has an invalid type.
        - if there is a mismatch between the user attribute type and the condition value type.
    """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not self.is_value_type_valid_for_exact_conditions(condition_value) or (
            self.is_value_a_number(condition_value) and not validator.is_finite_number(condition_value)
        ):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_type_valid_for_exact_conditions(user_value) or not validator.are_values_same_type(
            condition_value, user_value
        ):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if self.is_value_a_number(user_value) and not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return condition_value == user_value

    def exists_evaluator(self, index: int) -> bool:
        """ Evaluate the given exists match condition for the user attributes.

      Args:
        index: Index of the condition to be evaluated.

      Returns:
        Boolean: True if the user attributes have a non-null value for the given condition,
                 otherwise False.
    """
        attr_name = self.condition_data[index][0]
        return self.attributes.get(attr_name) is not None

    def greater_than_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given greater than match condition for the user attributes.

      Args:
        index: Index of the condition to be evaluated.

      Returns:
        Boolean:
          - True if the user attribute value is greater than the condition value.
          - False if the user attribute value is less than or equal to the condition value.
        None: if the condition value isn't finite or the user attribute value isn't finite.
    """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value > condition_value  # type: ignore[operator]

    def greater_than_or_equal_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given greater than or equal to match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attribute value is greater than or equal to the condition value.
            - False if the user attribute value is less than the condition value.
            None: if the condition value isn't finite or the user attribute value isn't finite.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value >= condition_value  # type: ignore[operator]

    def less_than_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given less than match condition for the user attributes.

    Args:
      index: Index of the condition to be evaluated.

    Returns:
      Boolean:
        - True if the user attribute value is less than the condition value.
        - False if the user attribute value is greater than or equal to the condition value.
      None: if the condition value isn't finite or the user attribute value isn't finite.
    """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value < condition_value  # type: ignore[operator]

    def less_than_or_equal_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given less than or equal to match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attribute value is less than or equal to the condition value.
            - False if the user attribute value is greater than the condition value.
          None: if the condition value isn't finite or the user attribute value isn't finite.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value <= condition_value  # type: ignore[operator]

    def substring_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given substring match condition for the given user attributes.

    Args:
      index: Index of the condition to be evaluated.

    Returns:
      Boolean:
        - True if the condition value is a substring of the user attribute value.
        - False if the condition value is not a substring of the user attribute value.
      None: if the condition value isn't a string or the user attribute value isn't a string.
    """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not isinstance(condition_value, str):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index),))
            return None

        if not isinstance(user_value, str):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        return condition_value in user_value

    def semver_equal_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given semantic version equal match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is equal (==) to the target version.
            - False if the user version is not equal (!=) to the target version.
          None:
            - if the user version value is not string type or is null.
        """

        condition_name = self.condition_data[index][0]
        target_version = self.condition_data[index][1]
        user_version = self.attributes.get(condition_name)

        if not isinstance(target_version, str):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index), ))
            return None

        if not isinstance(user_version, str):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(
                    self._get_condition_json(index), type(user_version), condition_name
                )
            )
            return None

        result = self.compare_user_version_with_target_version(target_version, user_version)
        if result is None:
            return None

        return result == 0

    def semver_greater_than_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given semantic version greater than match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is greater than the target version.
            - False if the user version is less than or equal to the target version.
          None:
            - if the user version value is not string type or is null.
        """
        condition_name = self.condition_data[index][0]
        target_version = self.condition_data[index][1]
        user_version = self.attributes.get(condition_name)

        if not isinstance(target_version, str):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index), ))
            return None

        if not isinstance(user_version, str):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(
                    self._get_condition_json(index), type(user_version), condition_name
                )
            )
            return None

        result = self.compare_user_version_with_target_version(target_version, user_version)
        if result is None:
            return None

        return result > 0

    def semver_less_than_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given semantic version less than match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is less than the target version.
            - False if the user version is greater than or equal to the target version.
          None:
            - if the user version value is not string type or is null.
        """
        condition_name = self.condition_data[index][0]
        target_version = self.condition_data[index][1]
        user_version = self.attributes.get(condition_name)

        if not isinstance(target_version, str):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index), ))
            return None

        if not isinstance(user_version, str):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(
                    self._get_condition_json(index), type(user_version), condition_name
                )
            )
            return None

        result = self.compare_user_version_with_target_version(target_version, user_version)
        if result is None:
            return None

        return result < 0

    def semver_less_than_or_equal_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given semantic version less than or equal to match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is less than or equal to the target version.
            - False if the user version is greater than the target version.
          None:
            - if the user version value is not string type or is null.
        """
        condition_name = self.condition_data[index][0]
        target_version = self.condition_data[index][1]
        user_version = self.attributes.get(condition_name)

        if not isinstance(target_version, str):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index), ))
            return None

        if not isinstance(user_version, str):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(
                    self._get_condition_json(index), type(user_version), condition_name
                )
            )
            return None

        result = self.compare_user_version_with_target_version(target_version, user_version)
        if result is None:
            return None

        return result <= 0

    def semver_greater_than_or_equal_evaluator(self, index: int) -> Optional[bool]:
        """ Evaluate the given semantic version greater than or equal to match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is greater than or equal to the target version.
            - False if the user version is less than the target version.
          None:
            - if the user version value is not string type or is null.
        """
        condition_name = self.condition_data[index][0]
        target_version = self.condition_data[index][1]
        user_version = self.attributes.get(condition_name)

        if not isinstance(target_version, str):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index), ))
            return None

        if not isinstance(user_version, str):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(
                    self._get_condition_json(index), type(user_version), condition_name
                )
            )
            return None

        result = self.compare_user_version_with_target_version(target_version, user_version)
        if result is None:
            return None

        return result >= 0

    def qualified_evaluator(self, index: int) -> Optional[bool]:
        """ Check if the user is qualifed for the given segment.

        Args:
        index: Index of the condition to be evaluated.

        Returns:
        Boolean:
            - True if the user is qualified.
            - False if the user is not qualified.
        None: if the condition value isn't a string.
        """
        condition_value = self.condition_data[index][1]

        if not isinstance(condition_value, str):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index),))
            return None

        return self.user_context.is_qualified_for(condition_value)

    EVALUATORS_BY_MATCH_TYPE: dict[str, Callable[[CustomAttributeConditionEvaluator, int], Optional[bool]]] = {
        ConditionMatchTypes.EXACT: exact_evaluator,
        ConditionMatchTypes.EXISTS: exists_evaluator,
        ConditionMatchTypes.GREATER_THAN: greater_than_evaluator,
        ConditionMatchTypes.GREATER_THAN_OR_EQUAL: greater_than_or_equal_evaluator,
        ConditionMatchTypes.LESS_THAN: less_than_evaluator,
        ConditionMatchTypes.LESS_THAN_OR_EQUAL: less_than_or_equal_evaluator,
        ConditionMatchTypes.SEMVER_EQ: semver_equal_evaluator,
        ConditionMatchTypes.SEMVER_GE: semver_greater_than_or_equal_evaluator,
        ConditionMatchTypes.SEMVER_GT: semver_greater_than_evaluator,
        ConditionMatchTypes.SEMVER_LE: semver_less_than_or_equal_evaluator,
        ConditionMatchTypes.SEMVER_LT: semver_less_than_evaluator,
        ConditionMatchTypes.SUBSTRING: substring_evaluator,
        ConditionMatchTypes.QUALIFIED: qualified_evaluator
    }

    def split_version(self, version: str) -> Optional[list[str]]:
        """ Method to split the given version.

        Args:
          version: Given version.

        Returns:
          List:
            - The array of version split into smaller parts i.e major, minor, patch etc
          None:
            - if the given version is invalid in format
        """
        target_prefix = version
        target_suffix = []
        target_parts = []

        # check that version shouldn't have white space
        if self.has_white_space(version):
            self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
            return None

        # check for pre release e.g. 1.0.0-alpha where 'alpha' is a pre release
        # otherwise check for build e.g. 1.0.0+001 where 001 is a build metadata
        if self.is_pre_release_version(version) or self.is_build_version(version):
            target_parts = version.split(VersionType.IS_PRE_RELEASE, 1) if self.is_pre_release_version(version) else \
                version.split(VersionType.IS_BUILD, 1)

        # split version into prefix and suffix
        if target_parts:
            if len(target_parts) < 1:
                self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
                return None
            target_prefix = str(target_parts[0])
            target_suffix = target_parts[1:]

        # check dot counts in target_prefix
        dot_count = target_prefix.count(".")
        if dot_count > 2:
            self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
            return None

        target_version_parts = target_prefix.split(".")
        if len(target_version_parts) != dot_count + 1:
            self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
            return None
        for part in target_version_parts:
            if not part.isdigit():
                self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
                return None

        if target_suffix:
            target_version_parts.extend(target_suffix)
        return target_version_parts

    def evaluate(self, index: int) -> Optional[bool]:
        """ Given a custom attribute audience condition and user attributes, evaluate the
        condition against the attributes.

    Args:
      index: Index of the condition to be evaluated.

    Returns:
      Boolean:
        - True if the user attributes match the given condition.
        - False if the user attributes don't match the given condition.
      None: if the user attributes and condition can't be evaluated.
    """

        if self.condition_data[index][2] not in self.CONDITION_TYPES:
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_TYPE.format(self._get_condition_json(index)))
            return None

        condition_match = self.condition_data[index][3]
        if condition_match is None:
            condition_match = ConditionMatchTypes.EXACT

        if condition_match not in self.EVALUATORS_BY_MATCH_TYPE:
            self.logger.warning(audience_logs.UNKNOWN_MATCH_TYPE.format(self._get_condition_json(index)))
            return None

        if condition_match not in (ConditionMatchTypes.EXISTS, ConditionMatchTypes.QUALIFIED):
            attribute_key = self.condition_data[index][0]
            if attribute_key not in self.attributes:
                self.logger.debug(
                    audience_logs.MISSING_ATTRIBUTE_VALUE.format(self._get_condition_json(index), attribute_key)
                )
                return None

            if self.attributes.get(attribute_key) is None:
                self.logger.debug(
                    audience_logs.NULL_ATTRIBUTE_VALUE.format(self._get_condition_json(index), attribute_key)
                )
                return None

        return self.EVALUATORS_BY_MATCH_TYPE[condition_match](self, index)


class ConditionDecoder:
    """ Class which provides an object_hook method for decoding dict
  objects into a list when given a condition_decoder. """

    def __init__(self, condition_decoder: Callable[[dict[str, str]], list[Optional[str]]]):
        self.condition_list: list[Optional[str] | list[str]] = []
        self.index = -1
        self.decoder = condition_decoder

    def object_hook(self, object_dict: dict[str, str]) -> int:
        """ Hook which when passed into a json.JSONDecoder will replace each dict
    in a json string with its index and convert the dict to an object as defined
    by the passed in condition_decoder. The newly created condition object is
    appended to the conditions_list.

    Args:
      object_dict: Dict representing an object.

    Returns:
      An index which will be used as the placeholder in the condition_structure
    """
        instance = self.decoder(object_dict)
        self.condition_list.append(instance)  # type: ignore[arg-type]
        self.index += 1
        return self.index


def _audience_condition_deserializer(obj_dict: dict[str, str]) -> list[Optional[str]]:
    """ Deserializer defining how dict objects need to be decoded for audience conditions.

  Args:
    obj_dict: Dict representing one audience condition.

  Returns:
    List consisting of condition key with corresponding value, type and match.
  """
    return [
        obj_dict.get('name'),
        obj_dict.get('value'),
        obj_dict.get('type'),
        obj_dict.get('match'),
    ]


def loads(conditions_string: str) -> tuple[list[str | list[str]], list[Optional[list[str] | str]]]:
    """ Deserializes the conditions property into its corresponding
  components: the condition_structure and the condition_list.

  Args:
    conditions_string: String defining valid and/or conditions.

  Returns:
    A tuple of (condition_structure, condition_list).
    condition_structure: nested list of operators and placeholders for operands.
    condition_list: list of conditions whose index correspond to the values of the placeholders.
  """
    decoder = ConditionDecoder(_audience_condition_deserializer)

    # Create a custom JSONDecoder using the ConditionDecoder's object_hook method
    # to create the condition_structure as well as populate the condition_list
    json_decoder = json.JSONDecoder(object_hook=decoder.object_hook)

    # Perform the decoding
    condition_structure = json_decoder.decode(conditions_string)
    condition_list = decoder.condition_list

    return (condition_structure, condition_list)
