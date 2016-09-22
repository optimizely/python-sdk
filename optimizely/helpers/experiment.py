ALLOWED_EXPERIMENT_STATUS = ['Running']


def is_experiment_running(experiment):
  """ Determine for given experiment if experiment is running.

  Args:
    experiment: Object representing the experiment.

  Returns:
    Boolean representing if experiment is running or not.
  """

  return experiment.status in ALLOWED_EXPERIMENT_STATUS
