# Copyright 2016, 2018-2020, Optimizely
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


def does_user_meet_audience_conditions(config,
                                       audience_conditions,
                                       audience_logs,
                                       logging_key,
                                       attributes,
                                       logger):
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
        Boolean representing if user satisfies audience conditions for any of the audiences or not.
    """
    logger.debug(audience_logs.EVALUATING_AUDIENCES_COMBINED.format(logging_key, json.dumps(audience_conditions)))

    # Return True in case there are no audiences
    if audience_conditions is None or audience_conditions == []:
        logger.info(audience_logs.AUDIENCE_EVALUATION_RESULT_COMBINED.format(logging_key, 'TRUE'))

        return True

    if attributes is None:
        attributes = {}

    def evaluate_custom_attr(audience_id, index):
        audience = config.get_audience(audience_id)
        custom_attr_condition_evaluator = condition_helper.CustomAttributeConditionEvaluator(
            audience.conditionList, attributes, logger
        )

        return custom_attr_condition_evaluator.evaluate(index)

    def evaluate_audience(audience_id):
        audience = config.get_audience(audience_id)

        if audience is None:
            return None

        logger.debug(audience_logs.EVALUATING_AUDIENCE.format(audience_id, audience.conditions))

        result = condition_tree_evaluator.evaluate(
            audience.conditionStructure, lambda index: evaluate_custom_attr(audience_id, index),
        )

        result_str = str(result).upper() if result is not None else 'UNKNOWN'
        logger.debug(audience_logs.AUDIENCE_EVALUATION_RESULT.format(audience_id, result_str))

        return result

    eval_result = condition_tree_evaluator.evaluate(audience_conditions, evaluate_audience)
    eval_result = eval_result or False
    logger.info(audience_logs.AUDIENCE_EVALUATION_RESULT_COMBINED.format(logging_key, str(eval_result).upper()))
    return eval_result
