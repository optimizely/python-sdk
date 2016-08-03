ALLOWED_EXPERIMENT_STATUS = ['Running']


def is_experiment_running(config, experiment_key):
  """ Determine for given experiment if experiment is running.

  Args:
    config: project_config.ProjectConfig object representing the project.
    experiment_key: Key representing experiment for which user is to be bucketed.

  Returns:
    Boolean representing if experiment is running or not.
  """

  return config.get_experiment_status(experiment_key) in ALLOWED_EXPERIMENT_STATUS
