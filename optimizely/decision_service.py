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

from collections import namedtuple

from six import string_types

from . import bucketer
from .decision.optimizely_decide_option import OptimizelyDecideOption
from .helpers import audience as audience_helper
from .helpers import enums
from .helpers import experiment as experiment_helper
from .helpers import validator
from .optimizely_user_context import OptimizelyUserContext
from .user_profile import UserProfile

Decision = namedtuple('Decision', 'experiment variation source')


class DecisionService(object):
    """ Class encapsulating all decision related capabilities. """

    def __init__(self, logger, user_profile_service):
        self.bucketer = bucketer.Bucketer()
        self.logger = logger
        self.user_profile_service = user_profile_service

        # Map of user IDs to another map of experiments to variations.
        # This contains all the forced variations set by the user
        # by calling set_forced_variation (it is not the same as the
        # whitelisting forcedVariations data structure).
        self.forced_variation_map = {}

    def _get_bucketing_id(self, user_id, attributes):
        """ Helper method to determine bucketing ID for the user.

        Args:
          user_id: ID for user.
          attributes: Dict representing user attributes. May consist of bucketing ID to be used.

        Returns:
          String representing bucketing ID if it is a String type in attributes else return user ID
          array of log messages representing decision making.
        """
        decide_reasons = []
        attributes = attributes or {}
        bucketing_id = attributes.get(enums.ControlAttributes.BUCKETING_ID)

        if bucketing_id is not None:
            if isinstance(bucketing_id, string_types):
                return bucketing_id, decide_reasons
            message = 'Bucketing ID attribute is not a string. Defaulted to user_id.'
            self.logger.warning(message)
            decide_reasons.append(message)

        return user_id, decide_reasons

    def set_forced_variation(self, project_config, experiment_key, user_id, variation_key):
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
                experiment_to_variation_map = self.forced_variation_map.get(user_id)
                if experiment_id in experiment_to_variation_map:
                    del self.forced_variation_map[user_id][experiment_id]
                    self.logger.debug(
                        'Variation mapped to experiment "%s" has been removed for user "%s".'
                        % (experiment_key, user_id)
                    )
                else:
                    self.logger.debug(
                        'Nothing to remove. Variation mapped to experiment "%s" for user "%s" does not exist.'
                        % (experiment_key, user_id)
                    )
            else:
                self.logger.debug('Nothing to remove. User "%s" does not exist in the forced variation map.' % user_id)
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
            'Set variation "%s" for experiment "%s" and user "%s" in the forced variation map.'
            % (variation_id, experiment_id, user_id)
        )
        return True

    def get_forced_variation(self, project_config, experiment_key, user_id):
        """ Gets the forced variation key for the given user and experiment.

          Args:
            project_config: Instance of ProjectConfig.
            experiment_key: Key for experiment.
            user_id: The user ID.

          Returns:
            The variation which the given user and experiment should be forced into and
             array of log messages representing decision making.
        """
        decide_reasons = []
        if user_id not in self.forced_variation_map:
            message = 'User "%s" is not in the forced variation map.' % user_id
            self.logger.debug(message)
            return None, decide_reasons

        experiment = project_config.get_experiment_from_key(experiment_key)
        if not experiment:
            # The invalid experiment key will be logged inside this call.
            return None, decide_reasons

        experiment_to_variation_map = self.forced_variation_map.get(user_id)

        if not experiment_to_variation_map:
            message = 'No experiment "%s" mapped to user "%s" in the forced variation map.' % (experiment_key, user_id)
            self.logger.debug(
                message
            )
            return None, decide_reasons

        variation_id = experiment_to_variation_map.get(experiment.id)
        if variation_id is None:
            message = 'No variation mapped to experiment "%s" in the forced variation map.' % experiment_key
            self.logger.debug(message)
            return None, decide_reasons

        variation = project_config.get_variation_from_id(experiment_key, variation_id)
        message = 'Variation "%s" is mapped to experiment "%s" and user "%s" in the forced variation map' \
                  % (variation.key, experiment_key, user_id)
        self.logger.debug(
            message
        )
        decide_reasons.append(message)
        return variation, decide_reasons

    def get_whitelisted_variation(self, project_config, experiment, user_id):
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
            forced_variation_key = forced_variations.get(user_id)
            forced_variation = project_config.get_variation_from_key(experiment.key, forced_variation_key)

            if forced_variation:
                message = 'User "%s" is forced in variation "%s".' % (user_id, forced_variation_key)
                self.logger.info(message)
                decide_reasons.append(message)

            return forced_variation, decide_reasons

        return None, decide_reasons

    def get_stored_variation(self, project_config, experiment, user_profile):
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
                message = 'Found a stored decision. User "%s" is in variation "%s" of experiment "%s".' \
                          % (user_id, variation.key, experiment.key)
                self.logger.info(
                    message
                )
                return variation

        return None

    def get_variation(self, project_config, experiment, user_context, options=None):
        """ Top-level function to help determine variation user should be put in.

        First, check if experiment is running.
        Second, check if user is forced in a variation.
        Third, check if there is a stored decision for the user and return the corresponding variation.
        Fourth, figure out if user is in the experiment by evaluating audience conditions if any.
        Fifth, bucket the user and return the variation.

        Args:
          project_config: Instance of ProjectConfig.
          experiment: Experiment for which user variation needs to be determined.
          user_context: contains user id and attributes
          options: Decide options.

        Returns:
          Variation user should see. None if user is not in experiment or experiment is not running
          And an array of log messages representing decision making.
        """
        user_id = user_context.user_id
        attributes = user_context.get_user_attributes()

        if options:
            ignore_user_profile = OptimizelyDecideOption.IGNORE_USER_PROFILE_SERVICE in options
        else:
            ignore_user_profile = False

        decide_reasons = []
        # Check if experiment is running
        if not experiment_helper.is_experiment_running(experiment):
            message = 'Experiment "%s" is not running.' % experiment.key
            self.logger.info(message)
            decide_reasons.append(message)
            return None, decide_reasons

        # Check if the user is forced into a variation
        variation, reasons_received = self.get_forced_variation(project_config, experiment.key, user_id)
        decide_reasons += reasons_received
        if variation:
            return variation, decide_reasons

        # Check to see if user is white-listed for a certain variation
        variation, reasons_received = self.get_whitelisted_variation(project_config, experiment, user_id)
        decide_reasons += reasons_received
        if variation:
            return variation, decide_reasons

        # Check to see if user has a decision available for the given experiment
        user_profile = UserProfile(user_id)
        if not ignore_user_profile and self.user_profile_service:
            try:
                retrieved_profile = self.user_profile_service.lookup(user_id)
            except:
                self.logger.exception('Unable to retrieve user profile for user "{}" as lookup failed.'.format(user_id))
                retrieved_profile = None

            if validator.is_user_profile_valid(retrieved_profile):
                user_profile = UserProfile(**retrieved_profile)
                variation = self.get_stored_variation(project_config, experiment, user_profile)
                if variation:
                    message = 'Returning previously activated variation ID "{}" of experiment ' \
                              '"{}" for user "{}" from user profile.'.format(variation, experiment, user_id)
                    self.logger.info(message)
                    decide_reasons.append(message)
                    return variation, decide_reasons
            else:
                self.logger.warning('User profile has invalid format.')

        # Bucket user and store the new decision
        audience_conditions = experiment.get_audience_conditions_or_ids()
        user_meets_audience_conditions, reasons_received = audience_helper.does_user_meet_audience_conditions(
            project_config, audience_conditions,
            enums.ExperimentAudienceEvaluationLogs,
            experiment.key,
            attributes, self.logger)
        decide_reasons += reasons_received
        if not user_meets_audience_conditions:
            message = 'User "{}" does not meet conditions to be in experiment "{}".'.format(user_id, experiment.key)
            self.logger.info(
                message
            )
            decide_reasons.append(message)
            return None, decide_reasons

        # Determine bucketing ID to be used
        bucketing_id, bucketing_id_reasons = self._get_bucketing_id(user_id, attributes)
        decide_reasons += bucketing_id_reasons
        variation, bucket_reasons = self.bucketer.bucket(project_config, experiment, user_id, bucketing_id)
        decide_reasons += bucket_reasons
        if variation:
            message = 'User "%s" is in variation "%s" of experiment %s.' % (user_id, variation.key, experiment.key)
            self.logger.info(
                message
            )
            decide_reasons.append(message)
            # Store this new decision and return the variation for the user
            if not ignore_user_profile and self.user_profile_service:
                try:
                    user_profile.save_variation_for_experiment(experiment.id, variation.id)
                    self.user_profile_service.save(user_profile.__dict__)
                except:
                    self.logger.exception('Unable to save user profile for user "{}".'.format(user_id))
            return variation, decide_reasons
        message = 'User "%s" is in no variation.' % user_id
        self.logger.info(message)
        decide_reasons.append(message)
        return None, decide_reasons

    def get_variation_for_rollout(self, project_config, feature, user):
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
        decide_reasons = []
        user_id = user.user_id
        attributes = user.get_user_attributes()

        if not feature or not feature.rolloutId:
            return Decision(None, None, enums.DecisionSources.ROLLOUT), decide_reasons

        rollout = project_config.get_rollout_from_id(feature.rolloutId)

        if not rollout:
            message = 'There is no rollout of feature {}.'.format(feature.key)
            self.logger.debug(message)
            decide_reasons.append(message)
            return Decision(None, None, enums.DecisionSources.ROLLOUT), decide_reasons

        rollout_rules = project_config.get_rollout_experiments(rollout)

        if not rollout_rules:
            message = 'Rollout {} has no experiments.'.format(rollout.id)
            self.logger.debug(message)
            decide_reasons.append(message)
            return Decision(None, None, enums.DecisionSources.ROLLOUT), decide_reasons

        index = 0
        while index < len(rollout_rules):
            skip_to_everyone_else = False

            # check forced decision first
            rule = rollout_rules[index]
            optimizely_decision_context = OptimizelyUserContext.OptimizelyDecisionContext(feature.key, rule.key)
            forced_decision_variation, reasons_received = self.validated_forced_decision(
                project_config, optimizely_decision_context, user)
            decide_reasons += reasons_received

            if forced_decision_variation:
                return Decision(experiment=rule, variation=forced_decision_variation,
                                source=enums.DecisionSources.ROLLOUT), decide_reasons

            bucketing_id, bucket_reasons = self._get_bucketing_id(user_id, attributes)
            decide_reasons += bucket_reasons

            everyone_else = (index == len(rollout_rules) - 1)
            logging_key = "Everyone Else" if everyone_else else str(index + 1)

            rollout_rule = project_config.get_experiment_from_id(rule.id)
            audience_conditions = rollout_rule.get_audience_conditions_or_ids()

            audience_decision_response, reasons_received_audience = audience_helper.does_user_meet_audience_conditions(
                project_config, audience_conditions, enums.RolloutRuleAudienceEvaluationLogs,
                logging_key, attributes, self.logger)

            decide_reasons += reasons_received_audience

            if audience_decision_response:
                message = 'User "{}" meets audience conditions for targeting rule {}.'.format(user_id, logging_key)
                self.logger.debug(message)
                decide_reasons.append(message)

                bucketed_variation, bucket_reasons = self.bucketer.bucket(project_config, rollout_rule, user_id,
                                                                          bucketing_id)
                decide_reasons.extend(bucket_reasons)

                if bucketed_variation:
                    message = 'User "{}" bucketed into a targeting rule {}.'.format(user_id, logging_key)
                    self.logger.debug(message)
                    decide_reasons.append(message)
                    return Decision(experiment=rule, variation=bucketed_variation,
                                    source=enums.DecisionSources.ROLLOUT), decide_reasons

                elif not everyone_else:
                    # skip this logging for EveryoneElse since this has a message not for everyone_else
                    message = 'User "{}" not bucketed into a targeting rule {}. ' \
                              'Checking "Everyone Else" rule now.'.format(user_id, logging_key)
                    self.logger.debug(message)
                    decide_reasons.append(message)

                    # skip the rest of rollout rules to the everyone-else rule if audience matches but not bucketed.
                    skip_to_everyone_else = True

            else:
                message = 'User "{}" does not meet audience conditions for targeting rule {}.'.format(
                    user_id, logging_key)
                self.logger.debug(message)
                decide_reasons.append(message)

            # the last rule is special for "Everyone Else"
            index = len(rollout_rules) - 1 if skip_to_everyone_else else index + 1

        return Decision(None, None, enums.DecisionSources.ROLLOUT), decide_reasons

    def get_variation_for_feature(self, project_config, feature, user_context, options=None):
        """ Returns the experiment/variation the user is bucketed in for the given feature.

        Args:
          project_config: Instance of ProjectConfig.
          feature: Feature for which we are determining if it is enabled or not for the given user.
          user: user context for user.
          attributes: Dict representing user attributes.
          options: Decide options.

        Returns:
          Decision namedtuple consisting of experiment and variation for the user.
    """
        decide_reasons = []

        # Check if the feature flag is under an experiment and the the user is bucketed into one of these experiments
        if feature.experimentIds:
            # Evaluate each experiment ID and return the first bucketed experiment variation
            for experiment in feature.experimentIds:
                experiment = project_config.get_experiment_from_id(experiment)
                decision_variation = None

                if experiment:
                    optimizely_decision_context = OptimizelyUserContext.OptimizelyDecisionContext(feature.key,
                                                                                                  experiment.key)

                    forced_decision_variation, reasons_received = self.validated_forced_decision(
                        project_config, optimizely_decision_context, user_context)
                    decide_reasons += reasons_received

                    if forced_decision_variation:
                        decision_variation = forced_decision_variation
                    else:
                        decision_variation, variation_reasons = self.get_variation(project_config,
                                                                                   experiment, user_context, options)
                        decide_reasons += variation_reasons

                    if decision_variation:
                        message = 'User "{}" bucketed into a experiment "{}" of feature "{}".'.format(
                            user_context.user_id, experiment.key, feature.key)
                        self.logger.debug(message)
                        return Decision(experiment, decision_variation,
                                        enums.DecisionSources.FEATURE_TEST), decide_reasons

        message = 'User "{}" is not bucketed into any of the experiments on the feature "{}".'.format(
            user_context.user_id, feature.key)
        self.logger.debug(message)
        variation, rollout_variation_reasons = self.get_variation_for_rollout(project_config, feature, user_context)
        if rollout_variation_reasons:
            decide_reasons += rollout_variation_reasons
        return variation, decide_reasons

    def validated_forced_decision(self, project_config, decision_context, user_context):
        """
        Gets forced decisions based on flag key, rule key and variation.

        Args:
            project_config: a project config
            decision context: a decision context
            user_context context: a user context

        Returns:
            Variation of the forced decision.
        """
        reasons = []

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
