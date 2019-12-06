# Copyright 2019, Optimizely
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

class OptimizelyConfig(object):
    def __init__(self, revision, experiments_map, features_map):
        self.revision = revision
        self.experimentsMap = experiments_map
        self.featuresMap = features_map

class OptimizelyExperiment(object):
    def __init__(self, id, key, variations_map):
        self.id = id
        self.key = key
        self.variationsMap = variations_map

class OptimizelyFeature(object):
    def __init__(self, id, key, experiments_map, variables_map):
        self.id = id
        self.key = key
        self.experimentsMap = experiments_map
        self.variablesMap = variables_map

class OptimizelyVariation(object):
    def __init__(self, id, key, feature_enabled, variables_map):
        self.id = id
        self.key = key
        self.featureEnabled = feature_enabled
        self.variablesMap = variables_map

class OptimizelyVariable(object):
    def __init__(self, id, key, type, value):
        self.id = id
        self.key = key
        self.type = type
        self.value = value


class OptimizelyConfigBuilder(object):

    def __init__(self, project_config):
        self.experiments = project_config.experiments
        self.feature_flags = project_config.feature_flags
        self.groups = project_config.groups
        self.revision = project_config.revision

    def get_optimizely_config(self):
        experiments_map = self._get_experiments_map()
        features_map = self._get_features_map(experiments_map)

        return OptimizelyConfig(self.revision, experiments_map, features_map)

    def _get_feature_variable_by_id(self, variable_id, feature_flag):
        for variable in feature_flag.get('variables', []):
            if variable_id == variable['id']:
                return variable
        return None

    def _get_featureflag_by_experiment_id(self, experiment_id):
        for feature in self.feature_flags:
            for id in feature['experimentIds']:
                if id == experiment_id:
                    return feature
        return None

    def _get_experiment_by_id(self, experiment_id, experiments_map):
        for experiment in experiments_map.values():
            if experiment.id == experiment_id:
                return experiment

        return None

    def _get_variables_map(self, variation, experiment):
        feature_flag = self._get_featureflag_by_experiment_id(experiment['id'])
        if feature_flag is None:
            return {}

        # set default variables for each variation
        variables_map = {}
        for variable in feature_flag.get('variables', []):
            opt_variable = OptimizelyVariable(
                variable['id'], variable['key'], variable['type'], variable['defaultValue']
            )
            variables_map[variable['key']] = opt_variable


        # set variation specific variable value if any
        if variation.get('featureEnabled', None):
            for variable in variation.get('variables', []):
                feature_variable = self._get_feature_variable_by_id(variable['id'], feature_flag)
                variables_map[feature_variable['key']].value = variable['value']

        return variables_map      

    def _get_variations_map(self, experiment):
        variations_map = {}

        for variation in experiment.get('variations', []):
            variables_map = self._get_variables_map(variation, experiment)
            feature_enabled = variation.get('featureEnabled', None)

            optly_variation = OptimizelyVariation(
                variation['id'], variation['key'], feature_enabled, variables_map
            )

            variations_map[variation['key']] = optly_variation

        return variations_map

    def _get_all_experiments(self):
        experiments = self.experiments

        for group in self.groups:
            experiments = experiments + group.experiments

        return experiments

    def _get_experiments_map(self):
        experiments_map = {}
        all_experiments = self._get_all_experiments()
        
        for exp in all_experiments:
            optly_exp = OptimizelyExperiment(
                exp['id'], exp['key'], self._get_variations_map(exp)
            )

            experiments_map[exp['key']] = optly_exp

        return experiments_map

    def _get_features_map(self, experiments_map):
        features_map = {}

        for feature in self.feature_flags:
            exp_map = {}
            for experiment_id in feature.get('experimentIds', []):
                optly_exp = self._get_experiment_by_id(experiment_id, experiments_map)
                exp_map[optly_exp.key] = optly_exp



            variables_map = {}
            for variable in feature['variables']:
                optly_variable = OptimizelyVariable(
                    variable['id'], variable['key'], variable['type'], variable['defaultValue']
                )

                variables_map[variable['key']] = optly_variable


            optly_feature = OptimizelyFeature(
                feature['id'], feature['key'], exp_map, variables_map
            )

            features_map[feature['key']] = optly_feature

        
        return features_map
