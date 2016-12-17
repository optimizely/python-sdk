# Copyright 2016, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import time
from tabulate import tabulate

from optimizely import optimizely

import data


ITERATIONS = 10


class BenchmarkingTests(object):

  def create_object(self, datafile):
    start_time = time.clock()
    optimizely.Optimizely(json.dumps(datafile))
    end_time = time.clock()
    return (end_time - start_time)

  def create_object_schema_validation_off(self, datafile):
    start_time = time.clock()
    optimizely.Optimizely(json.dumps(datafile), skip_json_validation=True)
    end_time = time.clock()
    return (end_time - start_time)

  def activate_with_no_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.activate('testExperiment2', user_id)
    end_time = time.clock()
    assert variation_key == 'control'
    return (end_time - start_time)

  def activate_with_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.activate('testExperimentWithFirefoxAudience',
                                            user_id, attributes={'browser_type': 'firefox'})
    end_time = time.clock()
    assert variation_key == 'variation'
    return (end_time - start_time)

  def activate_with_forced_variation(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.activate('testExperiment2', user_id)
    end_time = time.clock()
    assert variation_key == 'variation'
    return (end_time - start_time)

  def activate_grouped_experiment_no_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.activate('mutex_exp2', user_id)
    end_time = time.clock()
    assert variation_key == 'b'
    return (end_time - start_time)

  def activate_grouped_experiment_with_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.activate('mutex_exp1', user_id, attributes={'browser_type': 'chrome'})
    end_time = time.clock()
    assert variation_key == 'a'
    return (end_time - start_time)

  def get_variation_with_no_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.get_variation('testExperiment2', user_id)
    end_time = time.clock()
    assert variation_key == 'control'
    return (end_time - start_time)

  def get_variation_with_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.get_variation('testExperimentWithFirefoxAudience',
                                                 user_id, attributes={'browser_type': 'firefox'})
    end_time = time.clock()
    assert variation_key == 'variation'
    return (end_time - start_time)

  def get_variation_with_forced_variation(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.get_variation('testExperiment2', user_id)
    end_time = time.clock()
    assert variation_key == 'variation'
    return (end_time - start_time)

  def get_variation_grouped_experiment_no_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.get_variation('mutex_exp2', user_id)
    end_time = time.clock()
    assert variation_key == 'b'
    return (end_time - start_time)

  def get_variation_grouped_experiment_with_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    variation_key = optimizely_obj.get_variation('mutex_exp1', user_id, attributes={'browser_type': 'chrome'})
    end_time = time.clock()
    assert variation_key == 'a'
    return (end_time - start_time)

  def track_with_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEventWithAudiences', user_id, attributes={'browser_type': 'firefox'})
    end_time = time.clock()
    return (end_time - start_time)

  def track_with_revenue(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEvent', user_id, event_value=666)
    end_time = time.clock()
    return (end_time - start_time)

  def track_with_attributes_and_revenue(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEventWithAudiences', user_id,
                         attributes={'browser_type': 'firefox'}, event_value=666)
    end_time = time.clock()
    return (end_time - start_time)

  def track_no_attributes_no_revenue(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEvent', user_id)
    end_time = time.clock()
    return (end_time - start_time)

  def track_grouped_experiment(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEventWithMultipleGroupedExperiments', user_id)
    end_time = time.clock()
    return (end_time - start_time)

  def track_grouped_experiment_with_attributes(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEventWithMultipleExperiments', user_id, attributes={'browser_type': 'chrome'})
    end_time = time.clock()
    return (end_time - start_time)

  def track_grouped_experiment_with_revenue(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEventWithMultipleGroupedExperiments', user_id, event_value=666)
    end_time = time.clock()
    return (end_time - start_time)

  def track_grouped_experiment_with_attributes_and_revenue(self, optimizely_obj, user_id):
    start_time = time.clock()
    optimizely_obj.track('testEventWithMultipleExperiments', user_id,
                         attributes={'browser_type': 'chrome'}, event_value=666)
    end_time = time.clock()
    return (end_time - start_time)


def compute_average(values):
  """ Given a set of values compute the average.

  Args:
    values: Set of values for which average is to be computed.

  Returns:
    Average of all values.
  """
  return float(sum(values))/len(values)


def compute_median(values):
  """ Given a set of values compute the median.

   Args:
     values: Set of values for which median is to be computed.

  Returns:
    Median of all values.
  """

  sorted_values = sorted(values)
  num1 = (len(values) - 1) / 2
  num2 = len(values) / 2
  return float(sorted_values[num1] + sorted_values[num2])/2


def display_results(results_average, results_median):
  """ Format and print results on screen.

  Args:
    results_average: Dict holding averages.
    results_median: Dict holding medians.
  """

  table_data = []
  table_headers = ['Test Name',
                   '10 Experiment Average', '10 Experiment Median',
                   '25 Experiment Average', '25 Experiment Median',
                   '50 Experiment Average', '50 Experiment Median']
  for test_name, test_method in BenchmarkingTests.__dict__.iteritems():
    if callable(test_method):
      row_data = [test_name]
      for experiment_count in sorted(data.datafiles.keys()):
        row_data.append(results_average.get(experiment_count).get(test_name))
        row_data.append(results_median.get(experiment_count).get(test_name))
      table_data.append(row_data)

  print tabulate(table_data, headers=table_headers)


def run_benchmarking_tests():
  all_test_results_average = {}
  all_test_results_median = {}
  test_data = data.test_data
  for experiment_count in data.datafiles:
    all_test_results_average[experiment_count] = {}
    all_test_results_median[experiment_count] = {}
    for test_name, test_method in BenchmarkingTests.__dict__.iteritems():
      if callable(test_method):
        values = []
        for i in xrange(ITERATIONS):
          values.append(1000 * test_method(BenchmarkingTests(), *test_data.get(test_name).get(experiment_count)))
        time_in_milliseconds_avg = compute_average(values)
        time_in_milliseconds_median = compute_median(values)
        all_test_results_average[experiment_count][test_name] = time_in_milliseconds_avg
        all_test_results_median[experiment_count][test_name] = time_in_milliseconds_median

  display_results(all_test_results_average, all_test_results_median)

if __name__ == '__main__':
  run_benchmarking_tests()
