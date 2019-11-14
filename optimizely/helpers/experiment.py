# Copyright 2016, Optimizely
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

ALLOWED_EXPERIMENT_STATUS = ['Running']


def is_experiment_running(experiment):
    """ Determine for given experiment if experiment is running.

  Args:
    experiment: Object representing the experiment.

  Returns:
    Boolean representing if experiment is running or not.
  """

    return experiment.status in ALLOWED_EXPERIMENT_STATUS
