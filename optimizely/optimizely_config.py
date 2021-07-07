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
                 audiences=None, delivery_rules=None):
        self.revision = revision
        self.experiments_map = experiments_map
        self.features_map = features_map
        self._datafile = datafile
        self.sdk_key = sdk_key
        self.environment_key = environment_key
        self.attributes = attributes or []
        self.events = events or []
        self.audiences = audiences or []
        self.delivery_rules = delivery_rules or []

    def get_datafile(self):
        """ Get the datafile associated with OptimizelyConfig.

        Returns:
            A JSON string representation of the environment's datafile.
        """
        return self._datafile

    def get_sdk_key(self):
        """ Get the sdk key associated with OptimizelyConfig.

        Returns:
            A string containing sdk key.
        """
        return self.sdk_key

    def get_environment_key(self):
        """ Get the environemnt key associated with OptimizelyConfig.

        Returns:
            A string containing environment key.
        """
        return self.environment_key

    def get_attributes(self):
        """ Get the attributes associated with OptimizelyConfig

        returns:
            A list of attributes.
        """
        return self.attributes

    def get_events(self):
        """ Get the events associated with OptimizelyConfig

        returns:
            A list of events.
        """
        return self.events

    def get_audiences(self):
        """ Get the audiences associated with OptimizelyConfig

        returns:
            A list of audiences.
        """
        return self.audiences

    def get_delivery_rules(self):
        """ Get the delivery rules list associated with OptimizelyConfig

        Returns:
            List of OptimizelyExperiments as DeliveryRules from Rollouts
        """
        return self.delivery_rules


class OptimizelyExperiment(object):
    def __init__(self, id, key, variations_map):
        self.id = id
        self.key = key
        self.variations_map = variations_map
        self.audiences = ""


class OptimizelyFeature(object):
    def __init__(self, id, key, experiments_map, variables_map):
        self.id = id
        self.key = key
        self.experiments_map = experiments_map
        self.variables_map = variables_map


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
            The typed_audiences has higher presidence.
        '''

        typed_audiences = project_config.typed_audiences[:]
        optly_typed_audiences = []
        for typed_audience in typed_audiences:
            optly_audience = OptimizelyAudience(
                typed_audience.get('id'),
                typed_audience.get('name'),
                typed_audience.get('conditions')
            )
            optly_typed_audiences.append(optly_audience)

        for old_audience in project_config.audiences:
            # check if old_audience.id exists in new_audiences.id from typed_audiences
            if len([new_audience for new_audience in project_config.typed_audiences
                    if new_audience.get('id') == old_audience.get('id')]) == 0:
                if old_audience.get('id') == "$opt_dummy_audience":
                    continue
                else:
                    # Convert audiences lists to OptimizelyAudience array
                    optly_audience = OptimizelyAudience(
                        old_audience.get('id'),
                        old_audience.get('name'),
                        old_audience.get('conditions')
                    )
                    optly_typed_audiences.append(optly_audience)

        self.audiences = optly_typed_audiences

    def update_experiment(self, experiment, conditions, audiences_map):
        '''
            Gets an OptimizelyExperiment to update, conditions from
            the corresponding entities.Experiment and an audiences_map
            in the form of [id:name]

            Updates the OptimizelyExperiment.audiences with a string
            of conditions and audience names.
        '''
        audiences = self.replace_ids_with_names(conditions, audiences_map)
        experiment.audiences = audiences

    def replace_ids_with_names(self, conditions, audiences_map):
        '''
            Gets conditions and audiences_map [id:name]

            Returns:
                a string of conditions with id's swapped with names
                or None if no conditions found.

        '''
        if conditions is not None:
            return self.stringify_conditions(conditions, audiences_map)
        else:
            return None

    def lookup_name_from_id(self, audience_id, audiences_map):
        '''
            Gets and audience ID and audiences map

            Returns:
                The name corresponding to the ID
                or None if not found
        '''
        name = ""
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
        condition = ""
        conditions_str = ""
        length = len(conditions)

        if length == 0:
            return
        if length == 1:
            # Lookup ID and replace with name
            audience_name = self.lookup_name_from_id(conditions[0], audiences_map)

            return '"' + audience_name + '"'

        if length == 2:
            if conditions[0] in ARGS:
                condition = conditions[0]
                audience_name = self.lookup_name_from_id(conditions[1], audiences_map)
                return condition.upper() + ' "' + audience_name + '"'
            else:
                condition = 'OR'
                name1 = self.lookup_name_from_id(conditions[0], audiences_map)
                name2 = self.lookup_name_from_id(conditions[1], audiences_map)
                return ('"' + name1 + '" ' + condition.upper() + ' "' + name2 + '"')

        if length > 2:
            for i in range(length):
                if conditions[i] in ARGS:
                    condition = conditions[i].upper()
                else:
                    if condition == "":
                        condition = 'OR'
                    if type(conditions[i]) == list:
                        # If the next item is a list, recursively call function on list
                        if i + 1 < length:
                            conditions_str += '(' + self.stringify_conditions(conditions[i], audiences_map) + ') '
                            conditions_str += condition + ' '
                        else:
                            conditions_str += '(' + self.stringify_conditions(conditions[i], audiences_map) + ')'
                    else:
                        # Handle IDs here - Lookup name based on ID
                        audience_name = self.lookup_name_from_id(conditions[i], audiences_map)
                        if audience_name is not None:
                            if i + 1 < length:
                                conditions_str += '"' + audience_name + '" ' + condition + ' '
                            else:
                                conditions_str += '"' + audience_name + '"'

        return conditions_str + ""

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
            self.audiences,
            self._get_delivery_rules(self.rollouts)
        )

    def _create_lookup_maps(self):
        """ Creates lookup maps to avoid redundant iteration of config objects.  """

        self.exp_id_to_feature_map = {}
        self.feature_key_variable_key_to_variable_map = {}
        self.feature_key_variable_id_to_variable_map = {}

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

            self.feature_key_variable_key_to_variable_map[feature['key']] = variables_key_map
            self.feature_key_variable_id_to_variable_map[feature['key']] = variables_id_map

    def _get_variables_map(self, experiment, variation):
        """ Gets variables map for given experiment and variation.

        Args:
            experiment dict -- Experiment parsed from the datafile.
            variation dict -- Variation of the given experiment.

        Returns:
            dict - Map of variable key to OptimizelyVariable for the given variation.
        """
        feature_flag = self.exp_id_to_feature_map.get(experiment['id'], None)
        if feature_flag is None:
            return {}

        # set default variables for each variation
        variables_map = {}
        variables_map = copy.deepcopy(self.feature_key_variable_key_to_variable_map[feature_flag['key']])

        # set variation specific variable value if any
        if variation.get('featureEnabled'):
            for variable in variation.get('variables', []):
                feature_variable = self.feature_key_variable_id_to_variable_map[feature_flag['key']][variable['id']]
                variables_map[feature_variable.key].value = variable['value']

        return variables_map

    def _get_variations_map(self, experiment):
        """ Gets variation map for the given experiment.

        Args:
            experiment dict -- Experiment parsed from the datafile.

        Returns:
            dict -- Map of variation key to OptimizelyVariation.
        """
        variations_map = {}

        for variation in experiment.get('variations', []):
            variables_map = self._get_variables_map(experiment, variation)
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
            self.update_experiment(optly_exp, exp.get('audienceConditions', []), audiences_map)

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

        for feature in self.feature_flags:
            exp_map = {}
            for experiment_id in feature.get('experimentIds', []):
                optly_exp = experiments_id_map[experiment_id]
                exp_map[optly_exp.key] = optly_exp

            variables_map = self.feature_key_variable_key_to_variable_map[feature['key']]

            optly_feature = OptimizelyFeature(
                feature['id'], feature['key'], exp_map, variables_map
            )

            features_map[feature['key']] = optly_feature

        return features_map

    def _get_delivery_rules(self, rollouts):
        """ Gets an array of rollouts for the project config

        returns:
            an array of OptimizelyExperiments as delivery rules
        """
        # Return list for delivery rules
        delivery_rules = []
        # Audiences map to use for updating experiments with new audience conditions string
        audiences_map = {}

        # Build map from OptimizelyAudience array
        for optly_audience in self.audiences:
            audiences_map[optly_audience.id] = optly_audience.name

        for rollout in rollouts:
            experiments = rollout.get('experiments_map')
            if experiments:
                for experiment in experiments:
                    optly_exp = OptimizelyExperiment(
                        experiment['id'], experiment['key'], self._get_variations_map(experiment)
                    )
                    self.update_experiment(optly_exp, experiment.get('audienceConditions', []), audiences_map)
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
