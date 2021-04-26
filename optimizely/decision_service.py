# Copyright 2017-2021, Optimizely
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
from .helpers import audience as audience_helper
from .helpers import enums
from .helpers import experiment as experiment_helper
from .helpers import validator
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
            variation_key = forced_variations.get(user_id)
            variation = project_config.get_variation_from_key(experiment.key, variation_key)
            if variation:
                message = 'User "%s" is forced in variation "%s".' % (user_id, variation_key)
                self.logger.info(message)
                decide_reasons.append(message)
            return variation, decide_reasons

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
                message = 'Found a stored decision. User "%s" is in variation "%s" of experiment "%s".'\
                          % (user_id, variation.key, experiment.key)
                self.logger.info(
                    message
                )
                return variation

        return None

    def get_variation(
        self, project_config, experiment, user_id, attributes, ignore_user_profile=False
    ):
        """ Top-level function to help determine variation user should be put in.

    First, check if experiment is running.
    Second, check if user is forced in a variation.
    Third, check if there is a stored decision for the user and return the corresponding variation.
    Fourth, figure out if user is in the experiment by evaluating audience conditions if any.
    Fifth, bucket the user and return the variation.

    Args:
      project_config: Instance of ProjectConfig.
      experiment: Experiment for which user variation needs to be determined.
      user_id: ID for user.
      attributes: Dict representing user attributes.
      ignore_user_profile: True to ignore the user profile lookup. Defaults to False.

    Returns:
      Variation user should see. None if user is not in experiment or experiment is not running
      And an array of log messages representing decision making.
    """
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

    def get_variation_for_rollout(self, project_config, rollout, user_id, attributes=None):
        """ Determine which experiment/variation the user is in for a given rollout.
            Returns the variation of the first experiment the user qualifies for.

    Args:
      project_config: Instance of ProjectConfig.
      rollout: Rollout for which we are getting the variation.
      user_id: ID for user.
      attributes: Dict representing user attributes.

    Returns:
      Decision namedtuple consisting of experiment and variation for the user and
      array of log messages representing decision making.
    """
        decide_reasons = []
        # Go through each experiment in order and try to get the variation for the user
        if rollout and len(rollout.experiments) > 0:
            for idx in range(len(rollout.experiments) - 1):
                logging_key = str(idx + 1)
                rollout_rule = project_config.get_experiment_from_key(rollout.experiments[idx].get('key'))

                # Check if user meets audience conditions for targeting rule
                audience_conditions = rollout_rule.get_audience_conditions_or_ids()
                user_meets_audience_conditions, reasons_received = audience_helper.does_user_meet_audience_conditions(
                    project_config,
                    audience_conditions,
                    enums.RolloutRuleAudienceEvaluationLogs,
                    logging_key,
                    attributes,
                    self.logger)
                decide_reasons += reasons_received
                if not user_meets_audience_conditions:
                    message = 'User "{}" does not meet conditions for targeting rule {}.'.format(user_id, logging_key)
                    self.logger.debug(
                        message
                    )
                    decide_reasons.append(message)
                    continue
                message = 'User "{}" meets audience conditions for targeting rule {}.'.format(user_id, idx + 1)
                self.logger.debug(message)
                decide_reasons.append(message)
                # Determine bucketing ID to be used
                bucketing_id, bucket_reasons = self._get_bucketing_id(user_id, attributes)
                decide_reasons += bucket_reasons
                variation, reasons = self.bucketer.bucket(project_config, rollout_rule, user_id, bucketing_id)
                decide_reasons += reasons
                if variation:
                    message = 'User "{}" is in the traffic group of targeting rule {}.'.format(user_id, logging_key)
                    self.logger.debug(
                        message
                    )
                    decide_reasons.append(message)
                    return Decision(rollout_rule, variation, enums.DecisionSources.ROLLOUT), decide_reasons
                else:
                    message = 'User "{}" is not in the traffic group for targeting rule {}. ' \
                              'Checking "Everyone Else" rule now.'.format(user_id, logging_key)
                    # Evaluate no further rules
                    self.logger.debug(
                        message
                    )
                    decide_reasons.append(message)
                    break

            # Evaluate last rule i.e. "Everyone Else" rule
            everyone_else_rule = project_config.get_experiment_from_key(rollout.experiments[-1].get('key'))
            audience_conditions = everyone_else_rule.get_audience_conditions_or_ids()
            audience_eval, audience_reasons = audience_helper.does_user_meet_audience_conditions(
                project_config,
                audience_conditions,
                enums.RolloutRuleAudienceEvaluationLogs,
                'Everyone Else',
                attributes,
                self.logger
            )
            decide_reasons += audience_reasons
            if audience_eval:
                # Determine bucketing ID to be used
                bucketing_id, bucket_id_reasons = self._get_bucketing_id(user_id, attributes)
                decide_reasons += bucket_id_reasons
                variation, bucket_reasons = self.bucketer.bucket(
                    project_config, everyone_else_rule, user_id, bucketing_id)
                decide_reasons += bucket_reasons
                if variation:
                    message = 'User "{}" meets conditions for targeting rule "Everyone Else".'.format(user_id)
                    self.logger.debug(message)
                    decide_reasons.append(message)
                    return Decision(everyone_else_rule, variation, enums.DecisionSources.ROLLOUT,), decide_reasons

        return Decision(None, None, enums.DecisionSources.ROLLOUT), decide_reasons

    def get_variation_for_feature(self, project_config, feature, user_id, attributes=None, ignore_user_profile=False):
        """ Returns the experiment/variation the user is bucketed in for the given feature.

    Args:
      project_config: Instance of ProjectConfig.
      feature: Feature for which we are determining if it is enabled or not for the given user.
      user_id: ID for user.
      attributes: Dict representing user attributes.
      ignore_user_profile: True if we should bypass the user profile service

    Returns:
      Decision namedtuple consisting of experiment and variation for the user.
    """
        decide_reasons = []
        bucketing_id, reasons = self._get_bucketing_id(user_id, attributes)
        decide_reasons += reasons

        # Check if the feature flag is under an experiment and the the user is bucketed into one of these experiments
        if feature.experimentIds:
            # Evaluate each experiment ID and return the first bucketed experiment variation
            for experiment in feature.experimentIds:
                experiment = project_config.get_experiment_from_id(experiment)
                if experiment:
                    variation, variation_reasons = self.get_variation(
                        project_config, experiment, user_id, attributes, ignore_user_profile)
                    decide_reasons += variation_reasons
                    if variation:
                        return Decision(experiment, variation, enums.DecisionSources.FEATURE_TEST), decide_reasons

        # Next check if user is part of a rollout
        if feature.rolloutId:
            rollout = project_config.get_rollout_from_id(feature.rolloutId)
            return self.get_variation_for_rollout(project_config, rollout, user_id, attributes)
        else:
            return Decision(None, None, enums.DecisionSources.ROLLOUT), decide_reasons
