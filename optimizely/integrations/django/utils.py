import six
from .settings import optimizely_settings


def fields_for_attributes_for_model(model_class):
    """

    :param model_class:
    :return:
    """
    fields = optimizely_settings.FEATURE_FLAG_MODELS[model_class].get('FIELDS')
    if fields is None:
        return (model_class._meta.pk,)
    return [model_class._meta.get_field(field) if isinstance(field, six.string_types) else field for field in fields]


def attribute_key_for_field(field):
    return attribute_key_for_model(field.name, field.model)


def attribute_key_for_model(key, model_class):
    return '{model_class._meta.label}__{key}'.format(key=key, model_class=model_class)


def model_instance_id_and_attributes(model_instance, attribute_overrides=None):
    """
    Helper for forming id + attributes that get passed in.

    :param model_instance:          Django model instance
    :param attribute_overrides      dict
    :return:                        (str, dict)
                                    str will be of the form 'app_label.ModelClass:{model_instance.pk}'
                                    dict will be a generated dict of field names and values based on a list
                                    of attributes provided in settings.:
                                        {'users.User__id': 12345,
                                         'users.User__first_name': 'Michael',
                                         'users.User__last_name': 'Bluth',
                                         'users.User__email': 'michael@thebluthcompany.com'}
    """
    formatted_user_id = '{instance._meta.label}:{instance.pk}'.format(instance=model_instance)
    attributes = {}
    model_class = type(model_instance)
    for field in fields_for_attributes_for_model(model_class):
        attribute_key = attribute_key_for_field(field)
        attributes[attribute_key] = getattr(model_instance, field.attname)

    for additional_attribute in optimizely_settings.FEATURE_FLAG_MODELS[model_class].get('ADDITIONAL_ATTRIBUTES', []):
        attribute_key = attribute_key_for_model(additional_attribute['key'], model_class)
        attributes[attribute_key] = additional_attribute['value'](model_instance)

    if attribute_overrides:
        attributes.update(attribute_overrides)
    return formatted_user_id, attributes
