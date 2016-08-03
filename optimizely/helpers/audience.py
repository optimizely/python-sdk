from . import condition as condition_helper


def is_match(audience, attributes):
  """ Given audience information and user attributes determine if user meets the conditions.

  Args:
    audience: Dict representing the audience.
    attributes: Dict representing user attributes which will be used in determining if the audience conditions are met.

  Return:
    Boolean representing if user satisfies audience conditions or not.
  """
  condition_evaluator = condition_helper.ConditionEvaluator(audience.get('conditionList'), attributes)
  return condition_evaluator.evaluate(audience.get('conditionStructure'))


def is_user_in_experiment(config, experiment_key, attributes):
  """ Determine for given experiment if user satisfies the audiences for the experiment.

  Args:
    config: project_config.ProjectConfig object representing the project.
    experiment_key: Key representing experiment for which user is to be bucketed.
    attributes: Dict representing user attributes which will be used in determining if the audience conditions are met.

  Returns:
    Boolean representing if user satisfies audience conditions for any of the audiences or not.
  """

  audience_ids = config.get_audience_ids_for_experiment(experiment_key)

  # Return True in case there are no audiences
  if not audience_ids:
    return True

  # Return False if there are audiences, but no attributes
  if not attributes:
    return False

  # Return True if conditions for any one audience are met
  for audience_id in audience_ids:
    audience = config.get_audience_object_from_id(audience_id)

    if is_match(audience, attributes):
      return True

  return False
