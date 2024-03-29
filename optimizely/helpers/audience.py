# Copyright 2016, 2018-2022, Optimizely
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
from typing import TYPE_CHECKING, Optional, Sequence, Type

from . import condition as condition_helper
from . import condition_tree_evaluator
from optimizely import optimizely_user_context

if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from optimizely.project_config import ProjectConfig
    from optimizely.logger import Logger
    from optimizely.helpers.enums import ExperimentAudienceEvaluationLogs, RolloutRuleAudienceEvaluationLogs


def does_user_meet_audience_conditions(
    config: ProjectConfig,
    audience_conditions: Optional[Sequence[str | list[str]]],
    audience_logs: Type[ExperimentAudienceEvaluationLogs | RolloutRuleAudienceEvaluationLogs],
    logging_key: str,
    user_context: optimizely_user_context.OptimizelyUserContext,
    logger: Logger
) -> tuple[bool, list[str]]:
    """ Determine for given experiment if user satisfies the audiences for the experiment.

    Args:
        config: project_config.ProjectConfig object representing the project.
        audience_conditions: Audience conditions corresponding to the experiment or rollout rule.
        audience_logs: Log class capturing the messages to be logged .
        logging_key: String representing experiment key or rollout rule. To be used in log messages only.
        attributes: Dict representing user attributes which will be used in determining
                    if the audience conditions are met. If not provided, default to an empty dict.
        logger: Provides a logger to send log messages to.

    Returns:
        Boolean representing if user satisfies audience conditions for any of the audiences or not
        And an array of log messages representing decision making.
    """
    decide_reasons = []
    message = audience_logs.EVALUATING_AUDIENCES_COMBINED.format(logging_key, json.dumps(audience_conditions))
    logger.debug(message)
    decide_reasons.append(message)

    # Return True in case there are no audiences
    if audience_conditions is None or audience_conditions == []:
        message = audience_logs.AUDIENCE_EVALUATION_RESULT_COMBINED.format(logging_key, 'TRUE')
        logger.info(message)
        decide_reasons.append(message)

        return True, decide_reasons

    def evaluate_custom_attr(audience_id: str, index: int) -> Optional[bool]:
        audience = config.get_audience(audience_id)
        if not audience or audience.conditionList is None:
            return None
        custom_attr_condition_evaluator = condition_helper.CustomAttributeConditionEvaluator(
            audience.conditionList, user_context, logger
        )

        return custom_attr_condition_evaluator.evaluate(index)

    def evaluate_audience(audience_id: str) -> Optional[bool]:
        audience = config.get_audience(audience_id)

        if audience is None:
            return None
        _message = audience_logs.EVALUATING_AUDIENCE.format(audience_id, audience.conditions)
        logger.debug(_message)

        result = condition_tree_evaluator.evaluate(
            audience.conditionStructure, lambda index: evaluate_custom_attr(audience_id, index),
        )

        result_str = str(result).upper() if result is not None else 'UNKNOWN'
        _message = audience_logs.AUDIENCE_EVALUATION_RESULT.format(audience_id, result_str)
        logger.debug(_message)

        return result

    eval_result = condition_tree_evaluator.evaluate(audience_conditions, evaluate_audience)
    eval_result = eval_result or False
    message = audience_logs.AUDIENCE_EVALUATION_RESULT_COMBINED.format(logging_key, str(eval_result).upper())
    logger.info(message)
    decide_reasons.append(message)
    return eval_result, decide_reasons
