ALLOWED_EXPERIMENT_STATUS = ['Running']


def is_experiment_running(experiment):
  """ Determine for given experiment if experiment is running.

  Args:
    experiment: Object representing the experiment.

  Returns:
    Boolean representing if experiment is running or not.
  """

  return experiment.status in ALLOWED_EXPERIMENT_STATUS


def is_user_in_forced_variation(forced_variations, user_id):
  """ Determine if the user is in a forced variation.

  Args:
    forced_variations: Dict representing forced variations for the experiment.
    user_id: User to check for in whitelist.

  Returns:
    Boolean depending on whether user is in forced variation or not.
  """

  if forced_variations and user_id in forced_variations:
    return True

  return False
