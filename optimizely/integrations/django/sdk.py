from django.db import models

from ...optimizely import Optimizely

from . import utils


class DjangoOptimizely(Optimizely):
    """
    Wrapper for the SDK to be able to pass in Django models that automatically get translated into an id and
    attributes dict.  This will be an opinionated approach for how attributes are named in Optimizely.

    While the attributes kwarg is optional, it will override anything that is automatically inferred through
    the model instance that's passed in for user_id.

    For security reasons, by default we will ONLY include the pk of the model instance so that passwords and PII fields
    don't accidentally get unnecessarily shared. Additional fields can be added in settings.
    """

    def activate(self, experiment_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).activate(experiment_key, user_id, attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).activate(experiment_key, formatted_user_id,
                                                      attributes=formatted_attributes)

    def track(self, event_key, user_id, attributes=None, event_tags=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).track(event_key, user_id, attributes=attributes, event_tags=event_tags)

        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).track(event_key, formatted_user_id,
                                                   attributes=formatted_attributes, event_tags=event_tags)

    def is_feature_enabled(self, feature_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).is_feature_enabled(feature_key, user_id, attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).is_feature_enabled(feature_key, formatted_user_id,
                                                                attributes=formatted_attributes)

    def get_variation(self, experiment_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_variation(experiment_key, user_id, attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).get_variation(experiment_key, formatted_user_id,
                                                           attributes=formatted_attributes)

    def get_enabled_features(self, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_enabled_features(user_id, attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).get_enabled_features(formatted_user_id, attributes=formatted_attributes)

    def get_feature_variable(self, feature_key, variable_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_feature_variable(feature_key, variable_key, user_id,
                                                                      attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).get_feature_variable(feature_key, variable_key,
                                                                  formatted_user_id, attributes=formatted_attributes)

    def get_feature_variable_boolean(self, feature_key, variable_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_feature_variable_boolean(feature_key, variable_key, user_id,
                                                                              attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).get_feature_variable_boolean(feature_key, variable_key,
                                                                          formatted_user_id,
                                                                          attributes=formatted_attributes)

    def get_feature_variable_double(self, feature_key, variable_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_feature_variable_double(feature_key, variable_key, user_id,
                                                                             attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).get_feature_variable_double(feature_key, variable_key,
                                                                         formatted_user_id,
                                                                         attributes=formatted_attributes)

    def get_feature_variable_integer(self, feature_key, variable_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_feature_variable_integer(feature_key, variable_key, user_id,
                                                                              attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).get_feature_variable_integer(feature_key, variable_key,
                                                                          formatted_user_id,
                                                                          attributes=formatted_attributes)

    def get_feature_variable_string(self, feature_key, variable_key, user_id, attributes=None):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_feature_variable_string(feature_key, variable_key, user_id,
                                                                             attributes=attributes)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id, attributes)
        return super(DjangoOptimizely, self).get_feature_variable_string(feature_key, variable_key,
                                                                         formatted_user_id,
                                                                         attributes=formatted_attributes)

    def get_forced_variation(self, experiment_key, user_id):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).get_forced_variation(experiment_key, user_id)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id)
        return super(DjangoOptimizely, self).get_forced_variation(experiment_key, formatted_user_id)

    def set_forced_variation(self, experiment_key, user_id, variation_key):
        if not isinstance(user_id, models.Model):
            return super(DjangoOptimizely, self).set_forced_variation(experiment_key, user_id, variation_key)
        formatted_user_id, formatted_attributes = utils.model_instance_id_and_attributes(user_id)
        return super(DjangoOptimizely, self).set_forced_variation(experiment_key, formatted_user_id, variation_key)
