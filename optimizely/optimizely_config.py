# Copyright 2020-2021, Optimizely
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

import copy
from .helpers.condition import ConditionOperatorTypes

from .project_config import ProjectConfig


class OptimizelyConfig(object):
    def __init__(self, revision, experiments_map, features_map, datafile=None,
                 sdk_key=None, environment_key=None, attributes=None, events=None,
                 audiences=None):
        self.revision = revision

        # This experiments_map is for experiments of legacy projects only.
        # For flag projects, experiment keys are not guaranteed to be unique
        # across multiple flags, so this map may not include all experiments
        # when keys conflict.
        self.experiments_map = experiments_map

        self.features_map = features_map
        self._datafile = datafile
        self.sdk_key = sdk_key or ''
        self.environment_key = environment_key or ''
        self.attributes = attributes or []
        self.events = events or []
        self.audiences = audiences or []

    def get_datafile(self):
        """ Get the datafile associated with OptimizelyConfig.

        Returns:
            A JSON string representation of the environment's datafile.
        """
        return self._datafile


class OptimizelyExperiment(object):
    def __init__(self, id, key, variations_map, audiences=''):
        self.id = id
        self.key = key
        self.variations_map = variations_map
        self.audiences = audiences


class OptimizelyFeature(object):
    def __init__(self, id, key, experiments_map, variables_map):
        self.id = id
        self.key = key

        # This experiments_map is now deprecated,
        # Please use delivery_rules and experiment_rules
        self.experiments_map = experiments_map

        self.variables_map = variables_map
        self.delivery_rules = []
        self.experiment_rules = []


class OptimizelyVariation(object):
    def __init__(self, id, key, feature_enabled, variables_map):
        self.id = id
        self.key = key
        self.feature_enabled = feature_enabled
        self.variables_map = variables_map


class OptimizelyVariable(object):
    def __init__(self, id, key, variable_type, value):
        self.id = id
        self.key = key
        self.type = variable_type
        self.value = value


class OptimizelyAttribute(object):
    def __init__(self, id, key):
        self.id = id
        self.key = key


class OptimizelyEvent(object):
    def __init__(self, id, key, experiment_ids):
        self.id = id
        self.key = key
        self.experiment_ids = experiment_ids


class OptimizelyAudience(object):
    def __init__(self, id, name, conditions):
        self.id = id
        self.name = name
        self.conditions = conditions


class OptimizelyConfigService(object):
    """ Class encapsulating methods to be used in creating instance of OptimizelyConfig. """

    def __init__(self, project_config):
        """
        Args:
            project_config ProjectConfig
        """
        self.is_valid = True

        if not isinstance(project_config, ProjectConfig):
            self.is_valid = False
            return

        self._datafile = project_config.to_datafile()
        self.experiments = project_config.experiments
        self.feature_flags = project_config.feature_flags
        self.groups = project_config.groups
        self.revision = project_config.revision
        self.sdk_key = project_config.sdk_key
        self.environment_key = project_config.environment_key
        self.attributes = project_config.attributes
        self.events = project_config.events
        self.rollouts = project_config.rollouts

        self._create_lookup_maps()

        '''
            Merging typed_audiences with audiences from project_config.
            The typed_audiences has higher precedence.
        '''
        optly_typed_audiences = []
        id_lookup_dict = {}
        for typed_audience in project_config.typed_audiences:
            optly_audience = OptimizelyAudience(
                typed_audience.get('id'),
                typed_audience.get('name'),
                typed_audience.get('conditions')
            )
            optly_typed_audiences.append(optly_audience)
            id_lookup_dict[typed_audience.get('id')] = typed_audience.get('id')

        for old_audience in project_config.audiences:
            # check if old_audience.id exists in new_audiences.id from typed_audiences
            if old_audience.get('id') not in id_lookup_dict and old_audience.get('id') != "$opt_dummy_audience":
                # Convert audiences lists to OptimizelyAudience array
                optly_audience = OptimizelyAudience(
                    old_audience.get('id'),
                    old_audience.get('name'),
                    old_audience.get('conditions')
                )
                optly_typed_audiences.append(optly_audience)

        self.audiences = optly_typed_audiences

    def replace_ids_with_names(self, conditions, audiences_map):
        '''
            Gets conditions and audiences_map [id:name]

            Returns:
                a string of conditions with id's swapped with names
                or empty string if no conditions found.

        '''
        if conditions is not None:
            return self.stringify_conditions(conditions, audiences_map)
        else:
            return ''

    def lookup_name_from_id(self, audience_id, audiences_map):
        '''
            Gets and audience ID and audiences map

            Returns:
                The name corresponding to the ID
                or '' if not found.
        '''
        name = None
        try:
            name = audiences_map[audience_id]
        except KeyError:
            name = audience_id

        return name

    def stringify_conditions(self, conditions, audiences_map):
        '''
            Gets a list of conditions from an entities.Experiment
            and an audiences_map [id:name]

            Returns:
                A string of conditions and names for the provided
                list of conditions.
        '''
        ARGS = ConditionOperatorTypes.operators
        operand = 'OR'
        conditions_str = ''
        length = len(conditions)

        # Edge cases for lengths 0, 1 or 2
        if length == 0:
            return ''
        if length == 1 and conditions[0] not in ARGS:
            return '"' + self.lookup_name_from_id(conditions[0], audiences_map) + '"'
        if length == 2 and conditions[0] in ARGS and \
            type(conditions[1]) is not list and \
                conditions[1] not in ARGS:
            if conditions[0] != "not":
                return '"' + self.lookup_name_from_id(conditions[1], audiences_map) + '"'
            else:
                return conditions[0].upper() + \
                    ' "' + self.lookup_name_from_id(conditions[1], audiences_map) + '"'
        # If length is 2 (where the one elemnt is a list) or greater
        if length > 1:
            for i in range(length):
                # Operand is handled here and made Upper Case
                if conditions[i] in ARGS:
                    operand = conditions[i].upper()
                else:
                    # Check if element is a list or not
                    if type(conditions[i]) == list:
                        # Check if at the end or not to determine where to add the operand
                        # Recursive call to call stringify on embedded list
                        if i + 1 < length:
                            conditions_str += '(' + self.stringify_conditions(conditions[i], audiences_map) + ') '
                        else:
                            conditions_str += operand + \
                                ' (' + self.stringify_conditions(conditions[i], audiences_map) + ')'
                    # If the item is not a list, we process as an audience ID and retrieve the name
                    else:
                        audience_name = self.lookup_name_from_id(conditions[i], audiences_map)
                        if audience_name is not None:
                            # Below handles all cases for one ID or greater
                            if i + 1 < length - 1:
                                conditions_str += '"' + audience_name + '" ' + operand + ' '
                            elif i + 1 == length:
                                conditions_str += operand + ' "' + audience_name + '"'
                            else:
                                conditions_str += '"' + audience_name + '" '

        return conditions_str or ''

    def get_config(self):
        """ Gets instance of OptimizelyConfig

        Returns:
            Optimizely Config instance or None if OptimizelyConfigService is invalid.
        """

        if not self.is_valid:
            return None

        experiments_key_map, experiments_id_map = self._get_experiments_maps()
        features_map = self._get_features_map(experiments_id_map)

        return OptimizelyConfig(
            self.revision,
            experiments_key_map,
            features_map,
            self._datafile,
            self.sdk_key,
            self.environment_key,
            self._get_attributes_list(self.attributes),
            self._get_events_list(self.events),
            self.audiences
        )

    def _create_lookup_maps(self):
        """ Creates lookup maps to avoid redundant iteration of config objects.  """

        self.exp_id_to_feature_map = {}
        self.feature_key_variable_key_to_variable_map = {}
        self.feature_key_variable_id_to_variable_map = {}
        self.feature_id_variable_id_to_feature_variables_map = {}
        self.feature_id_variable_key_to_feature_variables_map = {}

        for feature in self.feature_flags:
            for experiment_id in feature['experimentIds']:
                self.exp_id_to_feature_map[experiment_id] = feature

            variables_key_map = {}
            variables_id_map = {}
            for variable in feature.get('variables', []):
                opt_variable = OptimizelyVariable(
                    variable['id'], variable['key'], variable['type'], variable['defaultValue']
                )
                variables_key_map[variable['key']] = opt_variable
                variables_id_map[variable['id']] = opt_variable

            self.feature_id_variable_id_to_feature_variables_map[feature['id']] = variables_id_map
            self.feature_id_variable_key_to_feature_variables_map[feature['id']] = variables_key_map
            self.feature_key_variable_key_to_variable_map[feature['key']] = variables_key_map
            self.feature_key_variable_id_to_variable_map[feature['key']] = variables_id_map

    def _get_variables_map(self, experiment, variation, feature_id=None):
        """ Gets variables map for given experiment and variation.

        Args:
            experiment dict -- Experiment parsed from the datafile.
            variation dict -- Variation of the given experiment.

        Returns:
            dict - Map of variable key to OptimizelyVariable for the given variation.
        """
        variables_map = {}

        feature_flag = self.exp_id_to_feature_map.get(experiment['id'], None)
        if feature_flag is None and feature_id is None:
            return {}

        # set default variables for each variation
        if feature_id:
            variables_map = copy.deepcopy(self.feature_id_variable_key_to_feature_variables_map[feature_id])
        else:
            variables_map = copy.deepcopy(self.feature_key_variable_key_to_variable_map[feature_flag['key']])

            # set variation specific variable value if any
            if variation.get('featureEnabled'):
                for variable in variation.get('variables', []):
                    feature_variable = self.feature_key_variable_id_to_variable_map[feature_flag['key']][variable['id']]
                    variables_map[feature_variable.key].value = variable['value']

        return variables_map

    def _get_variations_map(self, experiment, feature_id=None):
        """ Gets variation map for the given experiment.

        Args:
            experiment dict -- Experiment parsed from the datafile.

        Returns:
            dict -- Map of variation key to OptimizelyVariation.
        """
        variations_map = {}

        for variation in experiment.get('variations', []):
            variables_map = self._get_variables_map(experiment, variation, feature_id)
            feature_enabled = variation.get('featureEnabled', None)

            optly_variation = OptimizelyVariation(
                variation['id'], variation['key'], feature_enabled, variables_map
            )

            variations_map[variation['key']] = optly_variation

        return variations_map

    def _get_all_experiments(self):
        """ Gets all experiments in the project config.

        Returns:
            list -- List of dicts of experiments.
        """
        experiments = self.experiments

        for group in self.groups:
            experiments = experiments + group['experiments']

        return experiments

    def _get_experiments_maps(self):
        """ Gets maps for all the experiments in the project config and
        updates the experiment with updated experiment audiences string.

        Returns:
            dict, dict -- experiment key/id to OptimizelyExperiment maps.
        """
        # Key map is required for the OptimizelyConfig response.
        experiments_key_map = {}
        # Id map comes in handy to figure out feature experiment.
        experiments_id_map = {}
        # Audiences map to use for updating experiments with new audience conditions string
        audiences_map = {}

        # Build map from OptimizelyAudience array
        for optly_audience in self.audiences:
            audiences_map[optly_audience.id] = optly_audience.name

        all_experiments = self._get_all_experiments()
        for exp in all_experiments:
            optly_exp = OptimizelyExperiment(
                exp['id'], exp['key'], self._get_variations_map(exp)
            )
            # Updating each OptimizelyExperiment
            audiences = self.replace_ids_with_names(exp.get('audienceConditions', []), audiences_map)
            optly_exp.audiences = audiences or ''

            experiments_key_map[exp['key']] = optly_exp
            experiments_id_map[exp['id']] = optly_exp

        return experiments_key_map, experiments_id_map

    def _get_features_map(self, experiments_id_map):
        """ Gets features map for the project config.

        Args:
            experiments_id_map dict -- experiment id to OptimizelyExperiment map

        Returns:
            dict -- feaure key to OptimizelyFeature map
        """
        features_map = {}
        experiment_rules = []

        for feature in self.feature_flags:

            delivery_rules = self._get_delivery_rules(self.rollouts, feature.get('rolloutId'), feature['id'])
            experiment_rules = []

            exp_map = {}
            for experiment_id in feature.get('experimentIds', []):
                optly_exp = experiments_id_map[experiment_id]
                exp_map[optly_exp.key] = optly_exp
                experiment_rules.append(optly_exp)

            variables_map = self.feature_key_variable_key_to_variable_map[feature['key']]

            optly_feature = OptimizelyFeature(
                feature['id'], feature['key'], exp_map, variables_map
            )
            optly_feature.experiment_rules = experiment_rules
            optly_feature.delivery_rules = delivery_rules

            features_map[feature['key']] = optly_feature

        return features_map

    def _get_delivery_rules(self, rollouts, rollout_id, feature_id):
        """ Gets an array of rollouts for the project config

        returns:
            an array of OptimizelyExperiments as delivery rules.
        """
        # Return list for delivery rules
        delivery_rules = []
        # Audiences map to use for updating experiments with new audience conditions string
        audiences_map = {}

        # Gets a rollout based on provided rollout_id
        rollout = [rollout for rollout in rollouts if rollout.get('id') == rollout_id]

        if rollout:
            rollout = rollout[0]
            # Build map from OptimizelyAudience array
            for optly_audience in self.audiences:
                audiences_map[optly_audience.id] = optly_audience.name

            # Get the experiments for that rollout
            experiments = rollout.get('experiments')
            if experiments:
                for experiment in experiments:
                    optly_exp = OptimizelyExperiment(
                        experiment['id'], experiment['key'], self._get_variations_map(experiment, feature_id)
                    )
                    audiences = self.replace_ids_with_names(experiment.get('audienceConditions', []), audiences_map)
                    optly_exp.audiences = audiences

                    delivery_rules.append(optly_exp)

        return delivery_rules

    def _get_attributes_list(self, attributes):
        """ Gets attributes list for the project config

        Returns:
            List - OptimizelyAttributes
        """
        attributes_list = []

        for attribute in attributes:
            optly_attribute = OptimizelyAttribute(
                attribute['id'],
                attribute['key']
            )
            attributes_list.append(optly_attribute)

        return attributes_list

    def _get_events_list(self, events):
        """ Gets events list for the project_config

        Returns:
            List - OptimizelyEvents
        """
        events_list = []

        for event in events:
            optly_event = OptimizelyEvent(
                event['id'],
                event['key'],
                event['experimentIds']
            )
            events_list.append(optly_event)

        return events_list
