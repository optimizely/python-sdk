# Copyright 2016-2019, 2021-2022, Optimizely
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
from __future__ import annotations
import json
from typing import TYPE_CHECKING, Optional, Type, TypeVar, cast, Any, Iterable, List
from sys import version_info

from . import entities
from . import exceptions
from .helpers import condition as condition_helper
from .helpers import enums
from .helpers import types

if version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final  # type: ignore

if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from .logger import Logger


SUPPORTED_VERSIONS = [
    enums.DatafileVersions.V2,
    enums.DatafileVersions.V3,
    enums.DatafileVersions.V4,
]

RESERVED_ATTRIBUTE_PREFIX: Final = '$opt_'

EntityClass = TypeVar('EntityClass')


class ProjectConfig:
    """ Representation of the Optimizely project config. """

    def __init__(self, datafile: str | bytes, logger: Logger, error_handler: Any):
        """ ProjectConfig init method to load and set project config data.

        Args:
            datafile: JSON string representing the project.
            logger: Provides a logger instance.
            error_handler: Provides a handle_error method to handle exceptions.
        """

        config = json.loads(datafile)
        self._datafile = datafile.decode('utf-8') if isinstance(datafile, bytes) else datafile
        self.logger = logger
        self.error_handler = error_handler
        self.version: str = config.get('version')
        if self.version not in SUPPORTED_VERSIONS:
            raise exceptions.UnsupportedDatafileVersionException(
                enums.Errors.UNSUPPORTED_DATAFILE_VERSION.format(self.version)
            )

        self.account_id: str = config.get('accountId')
        self.project_id: str = config.get('projectId')
        self.revision: str = config.get('revision')
        self.sdk_key: Optional[str] = config.get('sdkKey', None)
        self.environment_key: Optional[str] = config.get('environmentKey', None)
        self.groups: list[types.GroupDict] = config.get('groups', [])
        self.experiments: list[types.ExperimentDict] = config.get('experiments', [])
        self.events: list[types.EventDict] = config.get('events', [])
        self.attributes: list[types.AttributeDict] = config.get('attributes', [])
        self.audiences: list[types.AudienceDict] = config.get('audiences', [])
        self.typed_audiences: list[types.AudienceDict] = config.get('typedAudiences', [])
        self.feature_flags: list[types.FeatureFlagDict] = config.get('featureFlags', [])
        self.rollouts: list[types.RolloutDict] = config.get('rollouts', [])
        self.integrations: list[types.IntegrationDict] = config.get('integrations', [])
        self.anonymize_ip: bool = config.get('anonymizeIP', False)
        self.send_flag_decisions: bool = config.get('sendFlagDecisions', False)
        self.bot_filtering: Optional[bool] = config.get('botFiltering', None)
        self.public_key_for_odp: Optional[str] = None
        self.host_for_odp: Optional[str] = None
        self.all_segments: list[str] = []

        # Utility maps for quick lookup
        self.group_id_map: dict[str, entities.Group] = self._generate_key_map(self.groups, 'id', entities.Group)
        self.experiment_id_map: dict[str, entities.Experiment] = self._generate_key_map(
            self.experiments, 'id', entities.Experiment
        )
        self.event_key_map: dict[str, entities.Event] = self._generate_key_map(self.events, 'key', entities.Event)
        self.attribute_key_map: dict[str, entities.Attribute] = self._generate_key_map(
            self.attributes, 'key', entities.Attribute
        )

        self.audience_id_map: dict[str, entities.Audience] = self._generate_key_map(
            self.audiences, 'id', entities.Audience
        )

        # Conditions of audiences in typedAudiences are not expected
        # to be string-encoded as they are in audiences.
        for typed_audience in self.typed_audiences:
            typed_audience['conditions'] = json.dumps(typed_audience['conditions'])
        typed_audience_id_map = self._generate_key_map(self.typed_audiences, 'id', entities.Audience)
        self.audience_id_map.update(typed_audience_id_map)

        self.rollout_id_map = self._generate_key_map(self.rollouts, 'id', entities.Layer)
        for layer in self.rollout_id_map.values():
            for experiment_dict in layer.experiments:
                self.experiment_id_map[experiment_dict['id']] = entities.Experiment(**experiment_dict)

        if self.integrations:
            self.integration_key_map = self._generate_key_map(
                self.integrations, 'key', entities.Integration, first_value=True
            )
            odp_integration = self.integration_key_map.get('odp')
            if odp_integration:
                self.public_key_for_odp = odp_integration.publicKey
                self.host_for_odp = odp_integration.host

        self.audience_id_map = self._deserialize_audience(self.audience_id_map)
        for group in self.group_id_map.values():
            experiments_in_group_id_map = self._generate_key_map(group.experiments, 'id', entities.Experiment)
            for experiment in experiments_in_group_id_map.values():
                experiment.__dict__.update({'groupId': group.id, 'groupPolicy': group.policy})
            self.experiment_id_map.update(experiments_in_group_id_map)

        for audience in self.audience_id_map.values():
            self.all_segments += audience.get_segments()

        self.experiment_key_map: dict[str, entities.Experiment] = {}
        self.variation_key_map: dict[str, dict[str, entities.Variation]] = {}
        self.variation_id_map: dict[str, dict[str, entities.Variation]] = {}
        self.variation_variable_usage_map: dict[str, dict[str, entities.Variation.VariableUsage]] = {}
        self.variation_id_map_by_experiment_id: dict[str, dict[str, entities.Variation]] = {}
        self.variation_key_map_by_experiment_id: dict[str, dict[str, entities.Variation]] = {}
        self.flag_variations_map: dict[str, list[entities.Variation]] = {}

        for experiment in self.experiment_id_map.values():
            self.experiment_key_map[experiment.key] = experiment
            self.variation_key_map[experiment.key] = self._generate_key_map(
                experiment.variations, 'key', entities.Variation
            )

            self.variation_id_map[experiment.key] = {}
            self.variation_id_map_by_experiment_id[experiment.id] = {}
            self.variation_key_map_by_experiment_id[experiment.id] = {}

            for variation in self.variation_key_map[experiment.key].values():
                self.variation_id_map[experiment.key][variation.id] = variation
                self.variation_id_map_by_experiment_id[experiment.id][variation.id] = variation
                self.variation_key_map_by_experiment_id[experiment.id][variation.key] = variation
                self.variation_variable_usage_map[variation.id] = self._generate_key_map(
                    variation.variables, 'id', entities.Variation.VariableUsage
                )

        self.feature_key_map = self._generate_key_map(self.feature_flags, 'key', entities.FeatureFlag)

        # Dictionary containing dictionary of experiment ID to feature ID.
        # for checking that experiment is a feature experiment or not.
        self.experiment_feature_map: dict[str, list[str]] = {}
        for feature in self.feature_key_map.values():
            # As we cannot create json variables in datafile directly, here we convert
            # the variables of string type and json subType to json type
            # This is needed to fully support json variables
            for variable in cast(List[types.VariableDict], self.feature_key_map[feature.key].variables):
                sub_type = variable.get('subType', '')
                if variable['type'] == entities.Variable.Type.STRING and sub_type == entities.Variable.Type.JSON:
                    variable['type'] = entities.Variable.Type.JSON

            feature.variables = self._generate_key_map(feature.variables, 'key', entities.Variable)

            rules: list[entities.Experiment] = []
            variations: list[entities.Variation] = []
            for exp_id in feature.experimentIds:
                # Add this experiment in experiment-feature map.
                self.experiment_feature_map[exp_id] = [feature.id]
                rules.append(self.experiment_id_map[exp_id])
            rollout = None if len(feature.rolloutId) == 0 else self.rollout_id_map[feature.rolloutId]
            if rollout:
                for exp in rollout.experiments:
                    rules.append(self.experiment_id_map[exp['id']])

            for rule in rules:
                # variation_id_map_by_experiment_id gives variation entity object while
                # experiment_id_map will give us dictionary
                for rule_variation in self.variation_id_map_by_experiment_id[rule.id].values():
                    if len(list(filter(lambda variation: variation.id == rule_variation.id, variations))) == 0:
                        variations.append(rule_variation)
            self.flag_variations_map[feature.key] = variations

    @staticmethod
    def _generate_key_map(
        entity_list: Iterable[Any], key: str, entity_class: Type[EntityClass], first_value: bool = False
    ) -> dict[str, EntityClass]:
        """ Helper method to generate map from key to entity object for given list of dicts.

        Args:
            entity_list: List consisting of dict.
            key: Key in each dict which will be key in the map.
            entity_class: Class representing the entity.
            first_value: If True, only save the first value found for each key.

        Returns:
            Map mapping key to entity object.
        """

        key_map: dict[str, EntityClass] = {}
        for obj in entity_list:
            if first_value and key_map.get(obj[key]):
                continue
            key_map[obj[key]] = entity_class(**obj)

        return key_map

    @staticmethod
    def _deserialize_audience(audience_map: dict[str, entities.Audience]) -> dict[str, entities.Audience]:
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

    def get_rollout_experiments(self, rollout: entities.Layer) -> list[entities.Experiment]:
        """ Helper method to get rollout experiments.

        Args:
            rollout: rollout

        Returns:
            Mapped rollout experiments.
        """

        rollout_experiments_id_map = self._generate_key_map(rollout.experiments, 'id', entities.Experiment)
        rollout_experiments = [experiment for experiment in rollout_experiments_id_map.values()]

        return rollout_experiments

    def get_typecast_value(self, value: str, type: str) -> Any:
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

    def to_datafile(self) -> str:
        """ Get the datafile corresponding to ProjectConfig.

        Returns:
            A JSON string representation of the project datafile.
        """

        return self._datafile

    def get_version(self) -> str:
        """ Get version of the datafile.

        Returns:
            Version of the datafile.
        """

        return self.version

    def get_revision(self) -> str:
        """ Get revision of the datafile.

        Returns:
            Revision of the datafile.
        """

        return self.revision

    def get_sdk_key(self) -> Optional[str]:
        """ Get sdk key from the datafile.

        Returns:
            Revision of the sdk key.
        """

        return self.sdk_key

    def get_environment_key(self) -> Optional[str]:
        """ Get environment key from the datafile.

        Returns:
            Revision of the environment key.
        """

        return self.environment_key

    def get_account_id(self) -> str:
        """ Get account ID from the config.

        Returns:
            Account ID information from the config.
        """

        return self.account_id

    def get_project_id(self) -> str:
        """ Get project ID from the config.

        Returns:
            Project ID information from the config.
        """

        return self.project_id

    def get_experiment_from_key(self, experiment_key: str) -> Optional[entities.Experiment]:
        """ Get experiment for the provided experiment key.

        Args:
            experiment_key: Experiment key for which experiment is to be determined.

        Returns:
            Experiment corresponding to the provided experiment key.
        """

        experiment = self.experiment_key_map.get(experiment_key)

        if experiment:
            return experiment

        self.logger.error(f'Experiment key "{experiment_key}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_experiment_from_id(self, experiment_id: str) -> Optional[entities.Experiment]:
        """ Get experiment for the provided experiment ID.

        Args:
            experiment_id: Experiment ID for which experiment is to be determined.

        Returns:
            Experiment corresponding to the provided experiment ID.
        """

        experiment = self.experiment_id_map.get(experiment_id)

        if experiment:
            return experiment

        self.logger.error(f'Experiment ID "{experiment_id}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_group(self, group_id: Optional[str]) -> Optional[entities.Group]:
        """ Get group for the provided group ID.

        Args:
            group_id: Group ID for which group is to be determined.

        Returns:
            Group corresponding to the provided group ID.
        """

        group = self.group_id_map.get(group_id)  # type: ignore[arg-type]

        if group:
            return group

        self.logger.error(f'Group ID "{group_id}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidGroupException(enums.Errors.INVALID_GROUP_ID))
        return None

    def get_audience(self, audience_id: str) -> Optional[entities.Audience]:
        """ Get audience object for the provided audience ID.

        Args:
            audience_id: ID of the audience.

        Returns:
            Dict representing the audience.
        """

        audience = self.audience_id_map.get(audience_id)
        if audience:
            return audience

        self.logger.error(f'Audience ID "{audience_id}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidAudienceException((enums.Errors.INVALID_AUDIENCE)))
        return None

    def get_variation_from_key(self, experiment_key: str, variation_key: str) -> Optional[entities.Variation]:
        """ Get variation given experiment and variation key.

        Args:
            experiment: Key representing parent experiment of variation.
            variation_key: Key representing the variation.
            Variation is of type variation object or None.

        Returns
            Object representing the variation.
        """

        variation_map = self.variation_key_map.get(experiment_key)

        if variation_map:
            variation = variation_map.get(variation_key)
            if variation:
                return variation
            else:
                self.logger.error(f'Variation key "{variation_key}" is not in datafile.')
                self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION))
                return None

        self.logger.error(f'Experiment key "{experiment_key}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_variation_from_id(self, experiment_key: str, variation_id: str) -> Optional[entities.Variation]:
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
                self.logger.error(f'Variation ID "{variation_id}" is not in datafile.')
                self.error_handler.handle_error(exceptions.InvalidVariationException(enums.Errors.INVALID_VARIATION))
                return None

        self.logger.error(f'Experiment key "{experiment_key}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidExperimentException(enums.Errors.INVALID_EXPERIMENT_KEY))
        return None

    def get_event(self, event_key: str) -> Optional[entities.Event]:
        """ Get event for the provided event key.

        Args:
            event_key: Event key for which event is to be determined.

        Returns:
            Event corresponding to the provided event key.
        """

        event = self.event_key_map.get(event_key)

        if event:
            return event

        self.logger.error(f'Event "{event_key}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidEventException(enums.Errors.INVALID_EVENT_KEY))
        return None

    def get_attribute_id(self, attribute_key: str) -> Optional[str]:
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
                        f'Attribute {attribute_key} unexpectedly has reserved prefix {RESERVED_ATTRIBUTE_PREFIX};'
                        f' using attribute ID instead of reserved attribute name.'
                    )
                )

            return attribute.id

        if has_reserved_prefix:
            return attribute_key

        self.logger.error(f'Attribute "{attribute_key}" is not in datafile.')
        self.error_handler.handle_error(exceptions.InvalidAttributeException(enums.Errors.INVALID_ATTRIBUTE))
        return None

    def get_feature_from_key(self, feature_key: str) -> Optional[entities.FeatureFlag]:
        """ Get feature for the provided feature key.

        Args:
            feature_key: Feature key for which feature is to be fetched.

        Returns:
            Feature corresponding to the provided feature key.
        """

        feature = self.feature_key_map.get(feature_key)

        if feature:
            return feature

        self.logger.error(f'Feature "{feature_key}" is not in datafile.')
        return None

    def get_rollout_from_id(self, rollout_id: str) -> Optional[entities.Layer]:
        """ Get rollout for the provided ID.

        Args:
            rollout_id: ID of the rollout to be fetched.

        Returns:
            Rollout corresponding to the provided ID.
        """

        layer = self.rollout_id_map.get(rollout_id)

        if layer:
            return layer

        self.logger.error(f'Rollout with ID "{rollout_id}" is not in datafile.')
        return None

    def get_variable_value_for_variation(
        self, variable: Optional[entities.Variable], variation: Optional[entities.Variation]
    ) -> Optional[str]:
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
            self.logger.error(f'Variation with ID "{variation.id}" is not in the datafile.')
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

    def get_variable_for_feature(self, feature_key: str, variable_key: str) -> Optional[entities.Variable]:
        """ Get the variable with the given variable key for the given feature.

        Args:
            feature_key: The key of the feature for which we are getting the variable.
            variable_key: The key of the variable we are getting.

        Returns:
            Variable with the given key in the given variation.
        """

        feature = self.feature_key_map.get(feature_key)
        if not feature:
            self.logger.error(f'Feature with key "{feature_key}" not found in the datafile.')
            return None

        if variable_key not in feature.variables:
            self.logger.error(f'Variable with key "{variable_key}" not found in the datafile.')
            return None

        return feature.variables.get(variable_key)

    def get_anonymize_ip_value(self) -> bool:
        """ Gets the anonymize IP value.

        Returns:
            A boolean value that indicates if the IP should be anonymized.
        """

        return self.anonymize_ip

    def get_send_flag_decisions_value(self) -> bool:
        """ Gets the Send Flag Decisions value.

        Returns:
            A boolean value that indicates if we should send flag decisions.
        """

        return self.send_flag_decisions

    def get_bot_filtering_value(self) -> Optional[bool]:
        """ Gets the bot filtering value.

        Returns:
            A boolean value that indicates if bot filtering should be enabled.
        """

        return self.bot_filtering

    def is_feature_experiment(self, experiment_id: str) -> bool:
        """ Determines if given experiment is a feature test.

        Args:
            experiment_id: Experiment ID for which feature test is to be determined.

        Returns:
            A boolean value that indicates if given experiment is a feature test.
        """

        return experiment_id in self.experiment_feature_map

    def get_variation_from_id_by_experiment_id(
        self, experiment_id: str, variation_id: str
    ) -> Optional[entities.Variation]:
        """ Gets variation from variation id and specific experiment id

            Returns:
                The variation for the experiment id and variation id
                or None if not found
        """
        if (experiment_id in self.variation_id_map_by_experiment_id and
                variation_id in self.variation_id_map_by_experiment_id[experiment_id]):
            return self.variation_id_map_by_experiment_id[experiment_id][variation_id]

        self.logger.error(
            f'Variation with id "{variation_id}" not defined in the datafile for experiment "{experiment_id}".'
        )

        return None

    def get_variation_from_key_by_experiment_id(
        self, experiment_id: str, variation_key: str
    ) -> Optional[entities.Variation]:
        """ Gets variation from variation key and specific experiment id

            Returns:
                The variation for the experiment id and variation key
                or None if not found
        """
        if (experiment_id in self.variation_key_map_by_experiment_id and
                variation_key in self.variation_key_map_by_experiment_id[experiment_id]):
            return self.variation_key_map_by_experiment_id[experiment_id][variation_key]

        self.logger.error(
            f'Variation with key "{variation_key}" not defined in the datafile for experiment "{experiment_id}".'
        )

        return None

    def get_flag_variation(
        self, flag_key: str, variation_attribute: str, target_value: str
    ) -> Optional[entities.Variation]:
        """
        Gets variation by specified variation attribute.
        For example if variation_attribute is id, the function gets variation by using variation_id.
        If variation_attribute is key, the function gets variation by using variation_key.

        We used to have two separate functions:
        get_flag_variation_by_id()
        get_flag_variation_by_key()

        This function consolidates both functions into one.

        Important to always relate variation_attribute to the target value.
        Should never enter for example variation_attribute=key and target_value=variation_id.
        Correct is object_attribute=key and target_value=variation_key.

        Args:
            flag_key: flag key
            variation_attribute: (string) id or key for example. The part after the dot notation (id in variation.id)
            target_value: target value we want to get for example variation_id or variation_key

        Returns:
            Variation as a map.
        """
        if not flag_key:
            return None

        variations = self.flag_variations_map.get(flag_key)
        if variations:
            for variation in variations:
                if getattr(variation, variation_attribute) == target_value:
                    return variation

        return None
