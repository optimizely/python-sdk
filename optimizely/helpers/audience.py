from . import condition as condition_helper


def is_match(audience, attributes):
  """ Given audience information and user attributes determine if user meets the conditions.

  Args:
    audience: Dict representing the audience.
    attributes: Dict representing user attributes which will be used in determining if the audience conditions are met.

  Return:
    Boolean representing if user satisfies audience conditions or not.
  """
  condition_evaluator = condition_helper.ConditionEvaluator(audience.conditionList, attributes)
  return condition_evaluator.evaluate(audience.conditionStructure)


def is_user_in_experiment(config, experiment, attributes):
  """ Determine for given experiment if user satisfies the audiences for the experiment.

  Args:
    config: project_config.ProjectConfig object representing the project.
    experiment: Object representing the experiment.
    attributes: Dict representing user attributes which will be used in determining if the audience conditions are met.

  Returns:
    Boolean representing if user satisfies audience conditions for any of the audiences or not.
  """

  # Return True in case there are no audiences
  if not experiment.audienceIds:
    return True

  # Return False if there are audiences, but no attributes
  if not attributes:
    return False

  # Return True if conditions for any one audience are met
  for audience_id in experiment.audienceIds:
    audience = config.get_audience(audience_id)

    if is_match(audience, attributes):
      return True

  return False
