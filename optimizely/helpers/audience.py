# Copyright 2016, 2018, Optimizely
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

from . import condition as condition_helper


def is_match(audience, attributes):
  """ Given audience information and user attributes determine if user meets the conditions.

  Args:
    audience: Dict representing the audience.
    attributes: Dict representing user attributes which will be used in determining if the audience conditions are met.

  Return:
    Boolean representing if user satisfies audience conditions or not.
  """
  condition_tree_evaluator = condition_helper.ConditionTreeEvaluator()
  custom_attr_condition_evaluator = condition_helper.CustomAttributeConditionEvaluator(
    audience.conditionList, attributes)

  is_match = condition_tree_evaluator.evaluate(
    audience.conditionStructure,
    lambda index: custom_attr_condition_evaluator.evaluate(index)
  )

  return is_match or False


def is_user_in_experiment(config, experiment, attributes):
  """ Determine for given experiment if user satisfies the audiences for the experiment.

  Args:
    config: project_config.ProjectConfig object representing the project.
    experiment: Object representing the experiment.
    attributes: Dict representing user attributes which will be used in determining
                if the audience conditions are met. If not provided, default to an empty dict.

  Returns:
    Boolean representing if user satisfies audience conditions for any of the audiences or not.
  """

  # Return True in case there are no audiences
  if not experiment.audienceIds:
    return True

  if attributes is None:
    attributes = {}

  # Return True if conditions for any one audience are met
  for audience_id in experiment.audienceIds:
    audience = config.get_audience(audience_id)

    if is_match(audience, attributes):
      return True

  return False
