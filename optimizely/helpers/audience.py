# Copyright 2016, 2018-2019, Optimizely
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

import json

from . import condition as condition_helper
from . import condition_tree_evaluator
from .enums import AudienceEvaluationLogs as audience_logs


def is_user_in_experiment(config, experiment, attributes, logger):
  """ Determine for given experiment if user satisfies the audiences for the experiment.

  Args:
    config: project_config.ProjectConfig object representing the project.
    experiment: Object representing the experiment.
    attributes: Dict representing user attributes which will be used in determining
                if the audience conditions are met. If not provided, default to an empty dict.
    logger: Provides a logger to send log messages to.

  Returns:
    Boolean representing if user satisfies audience conditions for any of the audiences or not.
  """

  audience_conditions = experiment.getAudienceConditionsOrIds()

  logger.debug(audience_logs.EVALUATING_AUDIENCES_COMBINED.format(
    experiment.key,
    json.dumps(audience_conditions)
  ))

  # Return True in case there are no audiences
  if audience_conditions is None or audience_conditions == []:
    logger.info(audience_logs.AUDIENCE_EVALUATION_RESULT_COMBINED.format(
      experiment.key,
      'TRUE'
    ))

    return True

  if attributes is None:
    attributes = {}

  def evaluate_custom_attr(audienceId, index):
    audience = config.get_audience(audienceId)
    custom_attr_condition_evaluator = condition_helper.CustomAttributeConditionEvaluator(
      audience.conditionList, attributes, logger)

    return custom_attr_condition_evaluator.evaluate(index)

  def evaluate_audience(audienceId):
    audience = config.get_audience(audienceId)

    if audience is None:
      return None

    logger.debug(audience_logs.EVALUATING_AUDIENCE.format(audienceId, audience.conditions))

    result = condition_tree_evaluator.evaluate(
      audience.conditionStructure,
      lambda index: evaluate_custom_attr(audienceId, index)
    )

    result_str = str(result).upper() if result is not None else 'UNKNOWN'
    logger.info(audience_logs.AUDIENCE_EVALUATION_RESULT.format(audienceId, result_str))

    return result

  eval_result = condition_tree_evaluator.evaluate(
    audience_conditions,
    evaluate_audience
  )

  eval_result = eval_result or False

  logger.info(audience_logs.AUDIENCE_EVALUATION_RESULT_COMBINED.format(
      experiment.key,
      str(eval_result).upper()
    ))

  return eval_result
