def fields_for_attributes_for_model(model_class):
    """

    :param model_class:
    :return:
    """
    return (model_class._meta.pk,)


def attribute_key_for_field(field):
    return '{field.model._meta.label}__{field.name}'.format(field=field)


def model_instance_id_and_attributes(model_instance, attribute_overrides=None):
    """
    Helper for forming id + attributes that get passed in.

    :param model_instance:          Django model instance
    :param attribute_overrides      dict
    :return:                        (str, dict)
                                    str will be of the form 'app_label.ModelClass:{model_instance.pk}'
                                    dict will be a generated dict of field names and values based on a list
                                    of attributes provided in settings.:
                                        {'users.User:id': 12345,
                                         'users.User:first_name': 'Michael',
                                         'users.User:last_name': 'Bluth',
                                         'users.User:email': 'michael@thebluthcompany.com'}
    """
    formatted_user_id = '{instance._meta.label}:{instance.pk}'.format(instance=model_instance)
    attributes = {}
    for field in fields_for_attributes_for_model(model_instance):
        attribute_key = attribute_key_for_field(field)
        attributes[attribute_key] = getattr(model_instance, field.attname)
    if attribute_overrides:
        attributes.update(attribute_overrides)
    return formatted_user_id, attributes
