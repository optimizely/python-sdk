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
from . import condition_tree_evaluator


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
  audience_conditions = experiment.getAudienceConditionsOrIds()
  if not audience_conditions:
    return True

  if attributes is None:
    attributes = {}

  def evaluate_custom_attr(audienceIdToConditionIndexDict):
    audienceId = list(audienceIdToConditionIndexDict.keys())[0]
    index = audienceIdToConditionIndexDict[audienceId]

    audience = config.get_audience(audienceId)
    custom_attr_condition_evaluator = condition_helper.CustomAttributeConditionEvaluator(
      audience.conditionList, attributes)

    return custom_attr_condition_evaluator.evaluate(index)

  def evaluate_audience(audienceId):
    audience = config.get_audience(audienceId)

    return condition_tree_evaluator.evaluate(
      audience.conditionStructure,
      lambda index: evaluate_custom_attr({audienceId: index})
    )

  eval_result = condition_tree_evaluator.evaluate(
    audience_conditions,
    lambda audienceId: evaluate_audience(audienceId)
  )

  return eval_result or False
