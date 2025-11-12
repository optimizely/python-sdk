# Copyright 2017-2022, Optimizely
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
from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence, List, TypedDict, Union

from optimizely.helpers.types import HoldoutDict, VariationDict

from . import bucketer
from . import entities
from .decision.optimizely_decide_option import OptimizelyDecideOption
from .helpers import audience as audience_helper
from .helpers import enums
from .helpers import experiment as experiment_helper
from .helpers import validator
from .optimizely_user_context import OptimizelyUserContext, UserAttributes
from .user_profile import UserProfile, UserProfileService, UserProfileTracker
from .cmab.cmab_service import DefaultCmabService, CmabDecision
from optimizely.helpers.enums import Errors

if TYPE_CHECKING:
    # prevent circular dependenacy by skipping import at runtime
    from .project_config import ProjectConfig
    from .logger import Logger


class CmabDecisionResult(TypedDict):
    """
    TypedDict representing the result of a CMAB (Contextual Multi-Armed Bandit) decision.

    Attributes:
        error (bool): Indicates whether an error occurred during the decision process.
        result (Optional[CmabDecision]): Resulting CmabDecision object if the decision was successful, otherwise None.
        reasons (List[str]): A list of reasons or messages explaining the outcome or any errors encountered.
    """
    error: bool
    result: Optional[CmabDecision]
    reasons: List[str]


class VariationResult(TypedDict):
    """
    TypedDict representing the result of a variation decision process.

    Attributes:
        cmab_uuid (Optional[str]): The unique identifier for the CMAB experiment, if applicable.
        error (bool): Indicates whether an error occurred during the decision process.
        reasons (List[str]): A list of reasons explaining the outcome or any errors encountered.
        variation (Optional[entities.Variation]): The selected variation entity, or None if no variation was assigned.
    """
    cmab_uuid: Optional[str]
    error: bool
    reasons: List[str]
    variation: Optional[Union[entities.Variation, VariationDict]]


class DecisionResult(TypedDict):
    """
    A TypedDict representing the result of a decision process.

    Attributes:
        decision (Decision): The decision object containing the outcome of the evaluation.
        error (bool): Indicates whether an error occurred during the decision process.
        reasons (List[str]): A list of reasons explaining the decision or any errors encountered.
    """
    decision: Decision
    error: bool
    reasons: List[str]


class Decision(NamedTuple):
    """Named tuple containing selected experiment, variation, source and cmab_uuid.
    None if no experiment/variation was selected."""
    experiment: Optional[entities.Experiment]
    variation: Optional[Union[entities.Variation, VariationDict]]
    source: Optional[str]
    cmab_uuid: Optional[str]


class DecisionService:
    """ Class encapsulating all decision related capabilities. """

    def __init__(self,
                 logger: Logger,
                 user_profile_service: Optional[UserProfileService],
                 cmab_service: DefaultCmabService):
        self.bucketer = bucketer.Bucketer()
        self.logger = logger
        self.user_profile_service = user_profile_service
        self.cmab_service = cmab_service
        self.cmab_uuid = None

        # Map of user IDs to another map of experiments to variations.
        # This contains all the forced variations set by the user
        # by calling set_forced_variation (it is not the same as the
        # whitelisting forcedVariations data structure).
        self.forced_variation_map: dict[str, dict[str, str]] = {}

    def _get_bucketing_id(self, user_id: str, attributes: Optional[UserAttributes]) -> tuple[str, list[str]]:
        """ Helper method to determine bucketing ID for the user.

        Args:
          user_id: ID for user.
          attributes: Dict representing user attributes. May consist of bucketing ID to be used.

        Returns:
          String representing bucketing ID if it is a String type in attributes else return user ID
          array of log messages representing decision making.
        """
        decide_reasons: list[str] = []
        attributes = attributes or UserAttributes({})
        bucketing_id = attributes.get(enums.ControlAttributes.BUCKETING_ID)

        if bucketing_id is not None:
            if isinstance(bucketing_id, str):
                return bucketing_id, decide_reasons
            message = 'Bucketing ID attribute is not a string. Defaulted to user_id.'
            self.logger.warning(message)
            decide_reasons.append(message)

        return user_id, decide_reasons

    def _get_decision_for_cmab_experiment(
        self,
        project_config: ProjectConfig,
        experiment: entities.Experiment,
        user_context: OptimizelyUserContext,
        bucketing_id: str,
        options: Optional[Sequence[str]] = None
    ) -> CmabDecisionResult:
        """
        Retrieves a decision for a contextual multi-armed bandit (CMAB) experiment.

        Args:
            project_config: Instance of ProjectConfig.
            experiment: The experiment object for which the decision is to be made.
            user_context: The user context containing user id and attributes.
            bucketing_id: The bucketing ID to use for traffic allocation.
            options: Optional sequence of decide options.

        Returns:
            A dictionary containing:
            - "error": Boolean indicating if there was an error.
            - "result": The CmabDecision result or None if error.
            - "reasons": List of strings with reasons or error messages.
        """
        decide_reasons: list[str] = []
        user_id = user_context.user_id

        # Check if user is in CMAB traffic allocation
        bucketed_entity_id, bucket_reasons = self.bucketer.bucket_to_entity_id(
            project_config, experiment, user_id, bucketing_id
        )
        decide_reasons.extend(bucket_reasons)

        if not bucketed_entity_id:
            message = f'User "{user_context.user_id}" not in CMAB experiment ' \
                      f'"{experiment.key}" due to traffic allocation.'
            self.logger.info(message)
            decide_reasons.append(message)
            return {
                "error": False,
                "result": None,
                "reasons": decide_reasons,
            }

        # User is in CMAB allocation, proceed to CMAB decision
        try:
            options_list = list(options) if options is not None else []
            cmab_decision, cmab_reasons = self.cmab_service.get_decision(
                project_config, user_context, experiment.id, options_list
            )
            decide_reasons.extend(cmab_reasons)
            return {
                "error": False,
                "result": cmab_decision,
                "reasons": decide_reasons,
            }
        except Exception as e:
            error_message = Errors.CMAB_FETCH_FAILED_DETAILED.format(
                experiment.key
            )
            decide_reasons.append(error_message)
            if self.logger:
                self.logger.error(f'{error_message} {str(e)}')
            return {
                "error": True,
                "result": None,
                "reasons": decide_reasons,
            }

    def set_forced_variation(
        self, project_config: ProjectConfig, experiment_key: str,
        user_id: str, variation_key: Optional[str]
    ) -> bool:
        """ Sets users to a map of experiments to forced variations.

          Args:
            project_config: Instance of ProjectConfig.
            experiment_key: Key for experiment.
            user_id: The user ID.
            variation_key: Key for variation. If None, then clear the existing experiment-to-variation mapping.

          Returns:
            A boolean value that indicates if the set completed successfully.
        """
        experiment = project_config.get_experiment_from_key(experiment_key)
        if not experiment:
            # The invalid experiment key will be logged inside this call.
            return False

        experiment_id = experiment.id
        if variation_key is None:
            if user_id in self.forced_variation_map:
                experiment_to_variation_map = self.forced_variation_map[user_id]
                if experiment_id in experiment_to_variation_map:
                    del self.forced_variation_map[user_id][experiment_id]
                    self.logger.debug(
                        f'Variation mapped to experiment "{experiment_key}" has been removed for user "{user_id}".'
                    )
                else:
                    self.logger.debug(
                        f'Nothing to remove. Variation mapped to experiment "{experiment_key}" for '
                        f'user "{user_id}" does not exist.'
                    )
            else:
                self.logger.debug(f'Nothing to remove. User "{user_id}" does not exist in the forced variation map.')
            return True

        if not validator.is_non_empty_string(variation_key):
            self.logger.debug('Variation key is invalid.')
            return False

        forced_variation = project_config.get_variation_from_key(experiment_key, variation_key)
        if not forced_variation:
            # The invalid variation key will be logged inside this call.
            return False

        variation_id = forced_variation.id

        if user_id not in self.forced_variation_map:
            self.forced_variation_map[user_id] = {experiment_id: variation_id}
        else:
            self.forced_variation_map[user_id][experiment_id] = variation_id

        self.logger.debug(
            f'Set variation "{variation_id}" for experiment "{experiment_id}" and '
            f'user "{user_id}" in the forced variation map.'
        )
        return True

    def get_forced_variation(
        self, project_config: ProjectConfig, experiment_key: str, user_id: str
    ) -> tuple[Optional[entities.Variation], list[str]]:
        """ Gets the forced variation key for the given user and experiment.

          Args:
            project_config: Instance of ProjectConfig.
            experiment_key: Key for experiment.
            user_id: The user ID.

          Returns:
            The variation which the given user and experiment should be forced into and
             array of log messages representing decision making.
        """
        decide_reasons: list[str] = []
        if user_id not in self.forced_variation_map:
            message = f'User "{user_id}" is not in the forced variation map.'
            self.logger.debug(message)
            return None, decide_reasons

        experiment = project_config.get_experiment_from_key(experiment_key)
        if not experiment:
            # The invalid experiment key will be logged inside this call.
            return None, decide_reasons

        experiment_to_variation_map = self.forced_variation_map.get(user_id)

        if not experiment_to_variation_map:
            message = f'No experiment "{experiment_key}" mapped to user "{user_id}" in the forced variation map.'
            self.logger.debug(message)
            return None, decide_reasons

        variation_id = experiment_to_variation_map.get(experiment.id)
        if variation_id is None:
            message = f'No variation mapped to experiment "{experiment_key}" in the forced variation map.'
            self.logger.debug(message)
            return None, decide_reasons

        variation = project_config.get_variation_from_id(experiment_key, variation_id)
        # this case is logged in get_variation_from_id
        if variation is None:
            return None, decide_reasons

        message = f'Variation "{variation.key}" is mapped to experiment "{experiment_key}" and ' \
                  f'user "{user_id}" in the forced variation map'
        self.logger.debug(message)
        decide_reasons.append(message)
        return variation, decide_reasons

    def get_whitelisted_variation(
        self, project_config: ProjectConfig, experiment: entities.Experiment, user_id: str
    ) -> tuple[Optional[entities.Variation], list[str]]:
        """ Determine if a user is forced into a variation (through whitelisting)
        for the given experiment and return that variation.

        Args:
          project_config: Instance of ProjectConfig.
          experiment: Object representing the experiment for which user is to be bucketed.
          user_id: ID for the user.

        Returns:
          Variation in which the user with ID user_id is forced into. None if no variation and
           array of log messages representing decision making.
        """
        decide_reasons = []
        forced_variations = experiment.forcedVariations

        if forced_variations and user_id in forced_variations:
            forced_variation_key = forced_variations[user_id]
            forced_variation = project_config.get_variation_from_key(experiment.key, forced_variation_key)

            if forced_variation:
                message = f'User "{user_id}" is forced in variation "{forced_variation_key}".'
                self.logger.info(message)
                decide_reasons.append(message)

            return forced_variation, decide_reasons

        return None, decide_reasons

    def get_stored_variation(
        self, project_config: ProjectConfig, experiment: entities.Experiment, user_profile: UserProfile
    ) -> Optional[entities.Variation]:
        """ Determine if the user has a stored variation available for the given experiment and return that.

        Args:
          project_config: Instance of ProjectConfig.
          experiment: Object representing the experiment for which user is to be bucketed.
          user_profile: UserProfile object representing the user's profile.

        Returns:
          Variation if available. None otherwise.
        """
        user_id = user_profile.user_id
        variation_id = user_profile.get_variation_for_experiment(experiment.id)

        if variation_id:
            variation = project_config.get_variation_from_id(experiment.key, variation_id)
            if variation:
                message = f'Found a stored decision. User "{user_id}" is in ' \
                          f'variation "{variation.key}" of experiment "{experiment.key}".'
                self.logger.info(message)
                return variation

        return None

    def get_variation(
        self,
        project_config: ProjectConfig,
        experiment: entities.Experiment,
        user_context: OptimizelyUserContext,
        user_profile_tracker: Optional[UserProfileTracker],
        reasons: list[str] = [],
        options: Optional[Sequence[str]] = None
    ) -> VariationResult:
        """
        Determines the variation a user should be assigned to for a given experiment.

        The decision process is as follows:
        1. Check if the experiment is running.
        2. Check if the user is forced into a variation via the forced variation map.
        3. Check if the user is whitelisted into a variation for the experiment.
        4. If user profile tracking is enabled and not ignored, check for a stored variation.
        5. Evaluate audience conditions to determine if the user qualifies for the experiment.
        6. For CMAB experiments:
            a. Check if the user is in the CMAB traffic allocation.
            b. If so, fetch the CMAB decision and assign the corresponding variation and cmab_uuid.
        7. For non-CMAB experiments, bucket the user into a variation.
        8. If a variation is assigned, optionally update the user profile.

        Args:
            project_config: Instance of ProjectConfig.
            experiment: Experiment for which the user's variation needs to be determined.
            user_context: Contains user id and attributes.
            user_profile_tracker: Tracker for reading and updating the user's profile.
            reasons: List of decision reasons.
            options: Decide options.

        Returns:
            A VariationResult dictionary with:
                - 'variation': The assigned Variation (or None if not assigned).
                - 'reasons': A list of log messages representing decision making.
                - 'cmab_uuid': The cmab_uuid if the experiment is a CMAB experiment, otherwise None.
                - 'error': Boolean indicating if an error occurred during the decision process.
        """
        user_id = user_context.user_id
        if options:
            ignore_user_profile = OptimizelyDecideOption.IGNORE_USER_PROFILE_SERVICE in options
        else:
            ignore_user_profile = False

        decide_reasons = []
        if reasons is not None:
            decide_reasons += reasons
        # Check if experiment is running
        if not experiment_helper.is_experiment_running(experiment):
            message = f'Experiment "{experiment.key}" is not running.'
            self.logger.info(message)
            decide_reasons.append(message)
            return {
                'cmab_uuid': None,
                'error': False,
                'reasons': decide_reasons,
                'variation': None
            }

        # Check if the user is forced into a variation
        variation: Optional[entities.Variation]
        variation, reasons_received = self.get_forced_variation(project_config, experiment.key, user_id)
        decide_reasons += reasons_received
        if variation:
            return {
                'cmab_uuid': None,
                'error': False,
                'reasons': decide_reasons,
                'variation': variation
            }

        # Check to see if user is white-listed for a certain variation
        variation, reasons_received = self.get_whitelisted_variation(project_config, experiment, user_id)
        decide_reasons += reasons_received
        if variation:
            return {
                'cmab_uuid': None,
                'error': False,
                'reasons': decide_reasons,
                'variation': variation
            }

        # Check to see if user has a decision available for the given experiment
        if user_profile_tracker is not None and not ignore_user_profile:
            variation = self.get_stored_variation(project_config, experiment, user_profile_tracker.get_user_profile())
            if variation:
                message = f'Returning previously activated variation ID "{variation}" of experiment ' \
                          f'"{experiment}" for user "{user_id}" from user profile.'
                self.logger.info(message)
                decide_reasons.append(message)
                return {
                    'cmab_uuid': None,
                    'error': False,
                    'reasons': decide_reasons,
                    'variation': variation
                }
            else:
                self.logger.warning('User profile has invalid format.')

        # Check audience conditions
        audience_conditions = experiment.get_audience_conditions_or_ids()
        user_meets_audience_conditions, reasons_received = audience_helper.does_user_meet_audience_conditions(
            project_config, audience_conditions,
            enums.ExperimentAudienceEvaluationLogs,
            experiment.key,
            user_context, self.logger)
        decide_reasons += reasons_received
        if not user_meets_audience_conditions:
            message = f'User "{user_id}" does not meet conditions to be in experiment "{experiment.key}".'
            self.logger.info(message)
            decide_reasons.append(message)
            return {
                'cmab_uuid': None,
                'error': False,
                'reasons': decide_reasons,
                'variation': None
            }

        # Determine bucketing ID to be used
        bucketing_id, bucketing_id_reasons = self._get_bucketing_id(user_id, user_context.get_user_attributes())
        decide_reasons += bucketing_id_reasons
        cmab_uuid = None

        # Check if this is a CMAB experiment
        # If so, handle CMAB-specific traffic allocation and decision logic.
        # Otherwise, proceed with standard bucketing logic for non-CMAB experiments.
        if experiment.cmab:
            cmab_decision_result = self._get_decision_for_cmab_experiment(project_config,
                                                                          experiment,
                                                                          user_context,
                                                                          bucketing_id,
                                                                          options)
            decide_reasons += cmab_decision_result.get('reasons', [])
            cmab_decision = cmab_decision_result.get('result')
            if cmab_decision_result['error']:
                return {
                    'cmab_uuid': None,
                    'error': True,
                    'reasons': decide_reasons,
                    'variation': None
                }
            variation_id = cmab_decision['variation_id'] if cmab_decision else None
            cmab_uuid = cmab_decision['cmab_uuid'] if cmab_decision else None
            variation = project_config.get_variation_from_id(experiment_key=experiment.key,
                                                             variation_id=variation_id) if variation_id else None
        else:
            # Bucket the user
            variation, bucket_reasons = self.bucketer.bucket(project_config, experiment, user_id, bucketing_id)
            decide_reasons += bucket_reasons

        if isinstance(variation, entities.Variation):
            message = f'User "{user_id}" is in variation "{variation.key}" of experiment {experiment.key}.'
            self.logger.info(message)
            decide_reasons.append(message)
            # Store this new decision and return the variation for the user
            if user_profile_tracker is not None and not ignore_user_profile:
                try:
                    user_profile_tracker.update_user_profile(experiment, variation)
                except:
                    self.logger.exception(f'Unable to save user profile for user "{user_id}".')
            return {
                'cmab_uuid': cmab_uuid,
                'error': False,
                'reasons': decide_reasons,
                'variation': variation
            }
        message = f'User "{user_id}" is in no variation.'
        self.logger.info(message)
        decide_reasons.append(message)
        return {
            'cmab_uuid': None,
            'error': False,
            'reasons': decide_reasons,
            'variation': None
        }

    def get_variation_for_rollout(
        self, project_config: ProjectConfig, feature: entities.FeatureFlag, user_context: OptimizelyUserContext
    ) -> tuple[Decision, list[str]]:
        """ Determine which experiment/variation the user is in for a given rollout.
            Returns the variation of the first experiment the user qualifies for.

        Args:
          project_config: Instance of ProjectConfig.
          flagKey: Feature key.
          rollout: Rollout for which we are getting the variation.
          user: ID and attributes for user.
          options: Decide options.

        Returns:
          Decision namedtuple consisting of experiment and variation for the user and
          array of log messages representing decision making.
        """
        decide_reasons: list[str] = []
        user_id = user_context.user_id
        attributes = user_context.get_user_attributes()

        if not feature or not feature.rolloutId:
            return Decision(None, None, enums.DecisionSources.ROLLOUT, None), decide_reasons

        rollout = project_config.get_rollout_from_id(feature.rolloutId)

        if not rollout:
            message = f'There is no rollout of feature {feature.key}.'
            self.logger.debug(message)
            decide_reasons.append(message)
            return Decision(None, None, enums.DecisionSources.ROLLOUT, None), decide_reasons

        rollout_rules = project_config.get_rollout_experiments(rollout)

        if not rollout_rules:
            message = f'Rollout {rollout.id} has no experiments.'
            self.logger.debug(message)
            decide_reasons.append(message)
            return Decision(None, None, enums.DecisionSources.ROLLOUT, None), decide_reasons

        index = 0
        while index < len(rollout_rules):
            skip_to_everyone_else = False

            # check forced decision first
            rule = rollout_rules[index]
            optimizely_decision_context = OptimizelyUserContext.OptimizelyDecisionContext(feature.key, rule.key)
            forced_decision_variation, reasons_received = self.validated_forced_decision(
                project_config, optimizely_decision_context, user_context)
            decide_reasons += reasons_received

            if forced_decision_variation:
                return Decision(experiment=rule, variation=forced_decision_variation,
                                source=enums.DecisionSources.ROLLOUT, cmab_uuid=None), decide_reasons

            bucketing_id, bucket_reasons = self._get_bucketing_id(user_id, attributes)
            decide_reasons += bucket_reasons

            everyone_else = (index == len(rollout_rules) - 1)
            logging_key = "Everyone Else" if everyone_else else str(index + 1)

            rollout_rule = project_config.get_experiment_from_id(rule.id)
            # error is logged in get_experiment_from_id
            if rollout_rule is None:
                continue
            audience_conditions = rollout_rule.get_audience_conditions_or_ids()

            audience_decision_response, reasons_received_audience = audience_helper.does_user_meet_audience_conditions(
                project_config, audience_conditions, enums.RolloutRuleAudienceEvaluationLogs,
                logging_key, user_context, self.logger)

            decide_reasons += reasons_received_audience

            if audience_decision_response:
                message = f'User "{user_id}" meets audience conditions for targeting rule {logging_key}.'
                self.logger.debug(message)
                decide_reasons.append(message)

                bucketed_variation, bucket_reasons = self.bucketer.bucket(project_config, rollout_rule, user_id,
                                                                          bucketing_id)
                decide_reasons.extend(bucket_reasons)

                if bucketed_variation:
                    message = f'User "{user_id}" bucketed into a targeting rule {logging_key}.'
                    self.logger.debug(message)
                    decide_reasons.append(message)
                    return Decision(experiment=rule, variation=bucketed_variation,
                                    source=enums.DecisionSources.ROLLOUT, cmab_uuid=None), decide_reasons

                elif not everyone_else:
                    # skip this logging for EveryoneElse since this has a message not for everyone_else
                    message = f'User "{user_id}" not bucketed into a targeting rule {logging_key}. ' \
                              'Checking "Everyone Else" rule now.'
                    self.logger.debug(message)
                    decide_reasons.append(message)

                    # skip the rest of rollout rules to the everyone-else rule if audience matches but not bucketed.
                    skip_to_everyone_else = True

            else:
                message = f'User "{user_id}" does not meet audience conditions for targeting rule {logging_key}.'
                self.logger.debug(message)
                decide_reasons.append(message)

            # the last rule is special for "Everyone Else"
            index = len(rollout_rules) - 1 if skip_to_everyone_else else index + 1

        return Decision(None, None, enums.DecisionSources.ROLLOUT, None), decide_reasons

    def get_variation_for_feature(
        self,
        project_config: ProjectConfig,
        feature: entities.FeatureFlag,
        user_context: OptimizelyUserContext,
        options: Optional[list[str]] = None
    ) -> DecisionResult:
        """ Returns the experiment/variation the user is bucketed in for the given feature.

        Args:
          project_config: Instance of ProjectConfig.
          feature: Feature for which we are determining if it is enabled or not for the given user.
          user_context: user context for user.
          options: Decide options.

        Returns:
          A DecisionResult dictionary containing:
            - 'decision': Decision namedtuple with experiment, variation, source, and cmab_uuid.
            - 'error': Boolean indicating if an error occurred during the decision process.
            - 'reasons': List of log messages representing decision making for the feature.
        """
        holdouts = project_config.get_holdouts_for_flag(feature.key)

        if holdouts:
            # Has holdouts - use get_decision_for_flag which checks holdouts first
            return self.get_decision_for_flag(feature, user_context, project_config, options)
        else:
            return self.get_variations_for_feature_list(project_config, [feature], user_context, options)[0]

    def get_decision_for_flag(
        self,
        feature_flag: entities.FeatureFlag,
        user_context: OptimizelyUserContext,
        project_config: ProjectConfig,
        decide_options: Optional[Sequence[str]] = None,
        user_profile_tracker: Optional[UserProfileTracker] = None,
        decide_reasons: Optional[list[str]] = None
    ) -> DecisionResult:
        """
        Get the decision for a single feature flag.
        Processes holdouts, experiments, and rollouts in that order.

        Args:
            feature_flag: The feature flag to get a decision for.
            user_context: The user context.
            project_config: The project config.
            decide_options: Sequence of decide options.
            user_profile_tracker: The user profile tracker.
            decide_reasons: List of decision reasons to merge.

        Returns:
            A DecisionResult for the feature flag.
        """
        reasons = decide_reasons.copy() if decide_reasons else []
        user_id = user_context.user_id

        # Check holdouts
        holdouts = project_config.get_holdouts_for_flag(feature_flag.key)
        for holdout in holdouts:
            holdout_decision = self.get_variation_for_holdout(holdout, user_context, project_config)
            reasons.extend(holdout_decision['reasons'])

            decision = holdout_decision['decision']
            # Check if user was bucketed into holdout (has a variation)
            if decision.variation is None:
                continue

            message = (
                f"The user '{user_id}' is bucketed into holdout '{holdout['key']}' "
                f"for feature flag '{feature_flag.key}'."
            )
            self.logger.info(message)
            reasons.append(message)
            return {
                'decision': holdout_decision['decision'],
                'error': False,
                'reasons': reasons
            }

        # If no holdout decision, fall back to existing experiment/rollout logic
        # Use get_variations_for_feature_list which handles experiments and rollouts
        fallback_result = self.get_variations_for_feature_list(
            project_config, [feature_flag], user_context, decide_options
        )[0]

        # Merge reasons
        if fallback_result.get('reasons'):
            reasons.extend(fallback_result['reasons'])

        return {
            'decision': fallback_result['decision'],
            'error': fallback_result.get('error', False),
            'reasons': reasons
        }

    def get_variation_for_holdout(
        self,
        holdout: HoldoutDict,
        user_context: OptimizelyUserContext,
        project_config: ProjectConfig
    ) -> DecisionResult:
        """
        Get the variation for holdout.

        Args:
            holdout: The holdout configuration (HoldoutDict).
            user_context: The user context.
            project_config: The project config.

        Returns:
            A DecisionResult for the holdout.
        """
        from optimizely.helpers.enums import ExperimentAudienceEvaluationLogs

        decide_reasons: list[str] = []
        user_id = user_context.user_id
        attributes = user_context.get_user_attributes()

        if not holdout or not holdout.get('status') or holdout.get('status') != 'Running':
            key = holdout.get('key') if holdout else 'unknown'
            message = f"Holdout '{key}' is not running."
            self.logger.info(message)
            decide_reasons.append(message)
            return {
                'decision': Decision(None, None, enums.DecisionSources.HOLDOUT, None),
                'error': False,
                'reasons': decide_reasons
            }

        bucketing_id, bucketing_id_reasons = self._get_bucketing_id(user_id, attributes)
        decide_reasons.extend(bucketing_id_reasons)

        # Check audience conditions
        audience_conditions = holdout.get('audienceIds')
        user_meets_audience_conditions, reasons_received = audience_helper.does_user_meet_audience_conditions(
            project_config,
            audience_conditions,
            ExperimentAudienceEvaluationLogs,
            holdout.get('key', 'unknown'),
            user_context,
            self.logger
        )
        decide_reasons.extend(reasons_received)

        if not user_meets_audience_conditions:
            message = (
                f"User '{user_id}' does not meet the conditions for holdout "
                f"'{holdout['key']}'."
            )
            self.logger.debug(message)
            decide_reasons.append(message)
            return {
                'decision': Decision(None, None, enums.DecisionSources.HOLDOUT, None),
                'error': False,
                'reasons': decide_reasons
            }

        # Bucket user into holdout variation
        variation, bucket_reasons = self.bucketer.bucket(
            project_config, holdout, user_id, bucketing_id  # type: ignore[arg-type]
        )
        decide_reasons.extend(bucket_reasons)

        if variation:
            # For holdouts, variation is a dict, not a Variation entity
            variation_key = variation['key'] if isinstance(variation, dict) else variation.key
            message = (
                f"The user '{user_id}' is bucketed into variation '{variation_key}' "
                f"of holdout '{holdout['key']}'."
            )
            self.logger.info(message)
            decide_reasons.append(message)

            # Create Decision for holdout - experiment is None, source is HOLDOUT
            holdout_decision: Decision = Decision(
                experiment=None,
                variation=variation,
                source=enums.DecisionSources.HOLDOUT,
                cmab_uuid=None
            )
            return {
                'decision': holdout_decision,
                'error': False,
                'reasons': decide_reasons
            }

        message = f"User '{user_id}' is not bucketed into any variation for holdout '{holdout['key']}'."
        self.logger.info(message)
        decide_reasons.append(message)
        return {
            'decision': Decision(None, None, enums.DecisionSources.HOLDOUT, None),
            'error': False,
            'reasons': decide_reasons
        }

    def validated_forced_decision(
        self,
        project_config: ProjectConfig,
        decision_context: OptimizelyUserContext.OptimizelyDecisionContext,
        user_context: OptimizelyUserContext
    ) -> tuple[Optional[entities.Variation], list[str]]:
        """
        Gets forced decisions based on flag key, rule key and variation.

        Args:
            project_config: a project config
            decision context: a decision context
            user_context context: a user context

        Returns:
            Variation of the forced decision.
        """
        reasons: list[str] = []

        forced_decision = user_context.get_forced_decision(decision_context)

        flag_key = decision_context.flag_key
        rule_key = decision_context.rule_key

        if forced_decision:
            if not project_config:
                return None, reasons
            variation = project_config.get_flag_variation(flag_key, 'key', forced_decision.variation_key)
            if variation:
                if rule_key:
                    user_has_forced_decision = enums.ForcedDecisionLogs \
                        .USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED.format(forced_decision.variation_key,
                                                                             flag_key,
                                                                             rule_key,
                                                                             user_context.user_id)

                else:
                    user_has_forced_decision = enums.ForcedDecisionLogs \
                        .USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED.format(forced_decision.variation_key,
                                                                                flag_key,
                                                                                user_context.user_id)

                reasons.append(user_has_forced_decision)
                user_context.logger.info(user_has_forced_decision)

                return variation, reasons

            else:
                if rule_key:
                    user_has_forced_decision_but_invalid = enums.ForcedDecisionLogs \
                        .USER_HAS_FORCED_DECISION_WITH_RULE_SPECIFIED_BUT_INVALID.format(flag_key,
                                                                                         rule_key,
                                                                                         user_context.user_id)
                else:
                    user_has_forced_decision_but_invalid = enums.ForcedDecisionLogs \
                        .USER_HAS_FORCED_DECISION_WITHOUT_RULE_SPECIFIED_BUT_INVALID.format(flag_key,
                                                                                            user_context.user_id)

                reasons.append(user_has_forced_decision_but_invalid)
                user_context.logger.info(user_has_forced_decision_but_invalid)

        return None, reasons

    def get_variations_for_feature_list(
        self,
        project_config: ProjectConfig,
        features: list[entities.FeatureFlag],
        user_context: OptimizelyUserContext,
        options: Optional[Sequence[str]] = None
    ) -> list[DecisionResult]:
        """
        Returns the list of experiment/variation the user is bucketed in for the given list of features.

        Args:
            project_config: Instance of ProjectConfig.
            features: List of features for which we are determining if it is enabled or not for the given user.
            user_context: user context for user.
            options: Decide options.

        Returns:
            A list of DecisionResult dictionaries, each containing:
                - 'decision': Decision namedtuple with experiment, variation, source, and cmab_uuid.
                - 'error': Boolean indicating if an error occurred during the decision process.
                - 'reasons': List of log messages representing decision making for each feature.
        """
        decide_reasons: list[str] = []

        if options:
            ignore_ups = OptimizelyDecideOption.IGNORE_USER_PROFILE_SERVICE in options
        else:
            ignore_ups = False

        user_profile_tracker: Optional[UserProfileTracker] = None
        if self.user_profile_service is not None and not ignore_ups:
            user_profile_tracker = UserProfileTracker(user_context.user_id, self.user_profile_service, self.logger)
            user_profile_tracker.load_user_profile(decide_reasons, None)

        decisions = []

        for feature in features:
            feature_reasons = decide_reasons.copy()
            experiment_decision_found = False  # Track if an experiment decision was made for the feature

            # Check if the feature flag is under an experiment
            if feature.experimentIds:
                for experiment_id in feature.experimentIds:
                    experiment = project_config.get_experiment_from_id(experiment_id)
                    decision_variation: Optional[Union[entities.Variation, VariationDict]] = None

                    if experiment:
                        optimizely_decision_context = OptimizelyUserContext.OptimizelyDecisionContext(
                            feature.key, experiment.key)
                        forced_decision_variation, reasons_received = self.validated_forced_decision(
                            project_config, optimizely_decision_context, user_context)
                        feature_reasons.extend(reasons_received)

                        if forced_decision_variation:
                            decision_variation = forced_decision_variation
                            cmab_uuid = None
                            error = False
                        else:
                            variation_result = self.get_variation(
                                project_config, experiment, user_context, user_profile_tracker, feature_reasons, options
                            )
                            cmab_uuid = variation_result['cmab_uuid']
                            variation_reasons = variation_result['reasons']
                            decision_variation = variation_result['variation']
                            error = variation_result['error']
                            feature_reasons.extend(variation_reasons)

                        if error:
                            decision = Decision(experiment, None, enums.DecisionSources.FEATURE_TEST, cmab_uuid)
                            decision_result: DecisionResult = {
                                'decision': decision,
                                'error': True,
                                'reasons': feature_reasons
                            }
                            decisions.append(decision_result)
                            experiment_decision_found = True
                            break

                        if decision_variation:
                            self.logger.debug(
                                f'User "{user_context.user_id}" '
                                f'bucketed into experiment "{experiment.key}" of feature "{feature.key}".'
                            )
                            decision = Decision(experiment, decision_variation,
                                                enums.DecisionSources.FEATURE_TEST, cmab_uuid)
                            decision_result = {
                                'decision': decision,
                                'error': False,
                                'reasons': feature_reasons
                            }
                            decisions.append(decision_result)
                            experiment_decision_found = True  # Mark that a decision was found
                            break  # Stop after the first successful experiment decision

            # Only process rollout if no experiment decision was found and no error
            if not experiment_decision_found:
                rollout_decision, rollout_reasons = self.get_variation_for_rollout(project_config,
                                                                                   feature,
                                                                                   user_context)
                if rollout_reasons:
                    feature_reasons.extend(rollout_reasons)
                if rollout_decision:
                    self.logger.debug(f'User "{user_context.user_id}" '
                                      f'bucketed into rollout for feature "{feature.key}".')
                else:
                    self.logger.debug(f'User "{user_context.user_id}" '
                                      f'not bucketed into any rollout for feature "{feature.key}".')

                decision_result = {
                    'decision': rollout_decision,
                    'error': False,
                    'reasons': feature_reasons
                }
                decisions.append(decision_result)

        if self.user_profile_service is not None and user_profile_tracker is not None and ignore_ups is False:
            user_profile_tracker.save_user_profile()

        return decisions
