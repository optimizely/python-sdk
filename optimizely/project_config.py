# Copyright 2016-2019, Optimizely
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

import json

from .helpers import condition as condition_helper
from .helpers import enums
from . import entities
from . import exceptions

SUPPORTED_VERSIONS = [
    enums.DatafileVersions.V2,
    enums.DatafileVersions.V3,
    enums.DatafileVersions.V4,
]

RESERVED_ATTRIBUTE_PREFIX = '$opt_'


class ProjectConfig(object):
    """ Representation of the Optimizely project config. """

    def __init__(self, datafile, logger, error_handler):
        """ ProjectConfig init method to load and set project config data.

        Args:
            datafile: JSON string representing the project.
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
        """

        config = json.loads(datafile)
        self._datafile = u'{}'.format(datafile)
        self.logger = logger
        self.error_handler = error_handler
        self.version = config.get('version')
        if self.version not in SUPPORTED_VERSIONS:
            raise exceptions.UnsupportedDatafileVersionException(
                enums.Errors.UNSUPPORTED_DATAFILE_VERSION.format(self.version)
            )

        self.account_id = config.get('accountId')
        self.project_id = config.get('projectId')
        self.revision = config.get('revision')
        self.groups = config.get('groups', [])
        self.experiments = config.get('experiments', [])
        self.events = config.get('events', [])
        self.attributes = config.get('attributes', [])
        self.audiences = config.get('audiences', [])
        self.typed_audiences = config.get('typedAudiences', [])
        self.feature_flags = config.get('featureFlags', [])
        self.rollouts = config.get('rollouts', [])
        self.anonymize_ip = config.get('anonymizeIP', False)
        self.send_flag_decisions = config.get('sendFlagDecisions', False)
        self.bot_filtering = config.get('botFiltering', None)

        # Utility maps for quick lookup
        self.group_id_map = self._generate_key_map(self.groups, 'id', entities.Group)
        self.experiment_key_map = self._generate_key_map(self.experiments, 'key', entities.Experiment)
        self.event_key_map = self._generate_key_map(self.events, 'key', entities.Event)
        self.attribute_key_map = self._generate_key_map(self.attributes, 'key', entities.Attribute)

        self.audience_id_map = self._generate_key_map(self.audiences, 'id', entities.Audience)

        # Conditions of audiences in typedAudiences are not expected
        # to be string-encoded as they are in audiences.
        for typed_audience in self.typed_audiences:
            typed_audience['conditions'] = json.dumps(typed_audience['conditions'])
        typed_audience_id_map = self._generate_key_map(self.typed_audiences, 'id', entities.Audience)
        self.audience_id_map.update(typed_audience_id_map)

        self.rollout_id_map = self._generate_key_map(self.rollouts, 'id', entities.Layer)
        for layer in self.rollout_id_map.values():
            for experiment in layer.experiments:
                self.experiment_key_map[experiment['key']] = entities.Experiment(**experiment)

        self.audience_id_map = self._deserialize_audience(self.audience_id_map)
        for group in self.group_id_map.values():
            experiments_in_group_key_map = self._generate_key_map(group.experiments, 'key', entities.Experiment)
            for experiment in experiments_in_group_key_map.values():
                experiment.__dict__.update({'groupId': group.id, 'groupPolicy': group.policy})
            self.experiment_key_map.update(experiments_in_group_key_map)

        self.experiment_id_map = {}
        self.variation_key_map = {}
        self.variation_id_map = {}
        self.variation_variable_usage_map = {}
        for experiment in self.experiment_key_map.values():
            self.experiment_id_map[experiment.id] = experiment
            self.variation_key_map[experiment.key] = self._generate_key_map(
                experiment.variations, 'key', entities.Variation
            )
            self.variation_id_map[experiment.key] = {}
            for variation in self.variation_key_map.get(experiment.key).values():
                self.variation_id_map[experiment.key][variation.id] = variation
                self.variation_variable_usage_map[variation.id] = self._generate_key_map(
                    variation.variables, 'id', entities.Variation.VariableUsage
                )

        self.feature_key_map = self._generate_key_map(self.feature_flags, 'key', entities.FeatureFlag)

        # As we cannot create json variables in datafile directly, here we convert
        # the variables of string type and json subType to json type
        # This is needed to fully support json variables
        for feature in self.feature_key_map:
            for variable in self.feature_key_map[feature].variables:
                sub_type = variable.get('subType', '')
                if variable['type'] == entities.Variable.Type.STRING and sub_type == entities.Variable.Type.JSON:
                    variable['type'] = entities.Variable.Type.JSON

        # Dict containing map of experiment ID to feature ID.
        # for checking that experiment is a feature experiment or not.
        self.experiment_feature_map = {}
        for feature in self.feature_key_map.values():
            feature.variables = self._generate_key_map(feature.variables, 'key', entities.Variable)

            for exp_id in feature.experimentIds:
                # Add this experiment in experiment-feature map.
                self.experiment_feature_map[exp_id] = [feature.id]

                experiment_in_feature = self.experiment_id_map[exp_id]
                # Check if any of the experiments are in a group and add the group id for faster bucketing later on
                if experiment_in_feature.groupId:
                    feature.groupId = experiment_in_feature.groupId
                    # Experiments in feature can only belong to one mutex group
                    break

    @staticmethod
    def _generate_key_map(entity_list, key, entity_class):
        """ Helper method to generate map from key to entity object for given list of dicts.

        Args:
            entity_list: List consisting of dict.
            key: Key in each dict which will be key in the map.
            entity_class: Class representing the entity.

        Returns:
            Map mapping key to entity object.
        """

        key_map = {}
        for obj in entity_list:
            key_map[obj[key]] = entity_class(**obj)

        return key_map

    @staticmethod
    def _deserialize_audience(audience_map):
        """ Helper method to de-serialize and populate audience map with the condition list and structure.

        Args:
            audience_map: Dict mapping audience ID to audience object.

        Returns:
            Dict additionally consisting of condition list and structure on every audience object.
        """

        for audience in audience_map.values():
            condition_structure, condition_list = condition_helper.loads(audience.conditions)
            audience.__dict__.update({'conditionStructure': condition_structure, 'conditionList': condition_list})

        return audience_map

    def get_typecast_value(self, value, type):
        """ Helper method to determine actual value based on type of feature variable.

        Args:
            value: Value in string form as it was parsed from datafile.
            type: Type denoting the feature flag type.

        Returns:
            Value type-casted based on type of feature variable.
        """

        if type == entities.Variable.Type.BOOLEAN:
            return value == 'true'
        elif type == entities.Variable.Type.INTEGER:
            return int(value)
        elif type == entities.Variable.Type.DOUBLE:
            return float(value)
        elif type == entities.Variable.Type.JSON:
            return json.loads(value)
        else:
            return value

    def to_datafile(self):
        """ Get the datafile corresponding to ProjectConfig.

        Returns:
            A JSON string representation of the project datafile.
        """

        return self._datafile

    def get_version(self):
        """ Get version of the datafile.

        Returns:
            Version of the datafile.
        """

        return self.version

    def get_revision(self):
        """ Get revision of the datafile.

        Returns:
            Revision of the datafile.
        """

        return self.revision

    def get_account_id(self):
        """ Get account ID from the config.

        Returns:
            Account ID information from the config.
        """

        return self.account_id

    def get_project_id(self):
        """ Get project ID from the config.

        Returns:
            Project ID information from the config.
        """

        return self.project_id

    def get_experiment_from_key(self, experiment_key):
        """ Get experiment for the provided experiment key.

        Args:
            experiment_key: Experiment key for which experiment is to be determined.

        Returns:
            Experiment corresponding to the provided experiment key.
        """

        experiment = self.experiment_key_map.get(experiment_key)

        if experiment:
            return experiment

        self.logger.error('Experiment key "%s" is not in datafile.' % experiment_key)
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_experiment_from_id(self, experiment_id):
        """ Get experiment for the provided experiment ID.

        Args:
            experiment_id: Experiment ID for which experiment is to be determined.

        Returns:
            Experiment corresponding to the provided experiment ID.
        """

        experiment = self.experiment_id_map.get(experiment_id)

        if experiment:
            return experiment

        self.logger.error('Experiment ID "%s" is not in datafile.' % experiment_id)
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_group(self, group_id):
        """ Get group for the provided group ID.

        Args:
            group_id: Group ID for which group is to be determined.

        Returns:
            Group corresponding to the provided group ID.
        """

        group = self.group_id_map.get(group_id)

        if group:
            return group

        self.logger.error('Group ID "%s" is not in datafile.' % group_id)
        self.error_handler.handle_error(exceptions.InvalidGroupException(enums.Errors.INVALID_GROUP_ID))
        return None

    def get_audience(self, audience_id):
        """ Get audience object for the provided audience ID.

        Args:
            audience_id: ID of the audience.

        Returns:
            Dict representing the audience.
        """

        audience = self.audience_id_map.get(audience_id)
        if audience:
            return audience

        self.logger.error('Audience ID "%s" is not in datafile.' % audience_id)
        self.error_handler.handle_error(exceptions.InvalidAudienceException((enums.Errors.INVALID_AUDIENCE)))

    def get_variation_from_key(self, experiment_key, variation_key):
        """ Get variation given experiment and variation key.

        Args:
            experiment: Key representing parent experiment of variation.
            variation_key: Key representing the variation.

        Returns
            Object representing the variation.
        """

        variation_map = self.variation_key_map.get(experiment_key)

        if variation_map:
            variation = variation_map.get(variation_key)
            if variation:
                return variation
            else:
                self.logger.error('Variation key "%s" is not in datafile.' % variation_key)
                self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION))
                return None

        self.logger.error('Experiment key "%s" is not in datafile.' % experiment_key)
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_variation_from_id(self, experiment_key, variation_id):
        """ Get variation given experiment and variation ID.

        Args:
            experiment: Key representing parent experiment of variation.
            variation_id: ID representing the variation.

        Returns
            Object representing the variation.
        """

        variation_map = self.variation_id_map.get(experiment_key)

        if variation_map:
            variation = variation_map.get(variation_id)
            if variation:
                return variation
            else:
                self.logger.error('Variation ID "%s" is not in datafile.' % variation_id)
                self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION))
                return None

        self.logger.error('Experiment key "%s" is not in datafile.' % experiment_key)
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_event(self, event_key):
        """ Get event for the provided event key.

        Args:
            event_key: Event key for which event is to be determined.

        Returns:
            Event corresponding to the provided event key.
        """

        event = self.event_key_map.get(event_key)

        if event:
            return event

        self.logger.error('Event "%s" is not in datafile.' % event_key)
        self.error_handler.handle_error(exceptions.InvalidEventException(enums.Errors.INVALID_EVENT_KEY))
        return None

    def get_attribute_id(self, attribute_key):
        """ Get attribute ID for the provided attribute key.

        Args:
            attribute_key: Attribute key for which attribute is to be fetched.

        Returns:
            Attribute ID corresponding to the provided attribute key.
        """

        attribute = self.attribute_key_map.get(attribute_key)
        has_reserved_prefix = attribute_key.startswith(RESERVED_ATTRIBUTE_PREFIX)

        if attribute:
            if has_reserved_prefix:
                self.logger.warning(
                    (
                        'Attribute %s unexpectedly has reserved prefix %s; using attribute ID '
                        'instead of reserved attribute name.' % (attribute_key, RESERVED_ATTRIBUTE_PREFIX)
                    )
                )

            return attribute.id

        if has_reserved_prefix:
            return attribute_key

        self.logger.error('Attribute "%s" is not in datafile.' % attribute_key)
        self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE))
        return None

    def get_feature_from_key(self, feature_key):
        """ Get feature for the provided feature key.

        Args:
            feature_key: Feature key for which feature is to be fetched.

        Returns:
            Feature corresponding to the provided feature key.
        """

        feature = self.feature_key_map.get(feature_key)

        if feature:
            return feature

        self.logger.error('Feature "%s" is not in datafile.' % feature_key)
        return None

    def get_rollout_from_id(self, rollout_id):
        """ Get rollout for the provided ID.

        Args:
            rollout_id: ID of the rollout to be fetched.

        Returns:
            Rollout corresponding to the provided ID.
        """

        layer = self.rollout_id_map.get(rollout_id)

        if layer:
            return layer

        self.logger.error('Rollout with ID "%s" is not in datafile.' % rollout_id)
        return None

    def get_variable_value_for_variation(self, variable, variation):
        """ Get the variable value for the given variation.

        Args:
            variable: The Variable for which we are getting the value.
            variation: The Variation for which we are getting the variable value.

        Returns:
            The variable value or None if any of the inputs are invalid.
        """

        if not variable or not variation:
            return None

        if variation.id not in self.variation_variable_usage_map:
            self.logger.error('Variation with ID "%s" is not in the datafile.' % variation.id)
            return None

        # Get all variable usages for the given variation
        variable_usages = self.variation_variable_usage_map[variation.id]

        # Find usage in given variation
        variable_usage = None
        if variable_usages:
            variable_usage = variable_usages.get(variable.id)

        if variable_usage:
            variable_value = variable_usage.value

        else:
            variable_value = variable.defaultValue

        return variable_value

    def get_variable_for_feature(self, feature_key, variable_key):
        """ Get the variable with the given variable key for the given feature.

        Args:
            feature_key: The key of the feature for which we are getting the variable.
            variable_key: The key of the variable we are getting.

        Returns:
            Variable with the given key in the given variation.
        """

        feature = self.feature_key_map.get(feature_key)
        if not feature:
            self.logger.error('Feature with key "%s" not found in the datafile.' % feature_key)
            return None

        if variable_key not in feature.variables:
            self.logger.error('Variable with key "%s" not found in the datafile.' % variable_key)
            return None

        return feature.variables.get(variable_key)

    def get_anonymize_ip_value(self):
        """ Gets the anonymize IP value.

        Returns:
            A boolean value that indicates if the IP should be anonymized.
        """

        return self.anonymize_ip

    def get_send_flag_decisions_value(self):
        """ Gets the Send Flag Decisions value.

        Returns:
            A boolean value that indicates if we should send flag decisions.
        """

        return self.send_flag_decisions

    def get_bot_filtering_value(self):
        """ Gets the bot filtering value.

        Returns:
            A boolean value that indicates if bot filtering should be enabled.
        """

        return self.bot_filtering

    def is_feature_experiment(self, experiment_id):
        """ Determines if given experiment is a feature test.

        Args:
            experiment_id: Experiment ID for which feature test is to be determined.

        Returns:
            A boolean value that indicates if given experiment is a feature test.
        """

        return experiment_id in self.experiment_feature_map
