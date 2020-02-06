from django.core.management.base import BaseCommand, CommandError
import requests

from ...settings import optimizely_settings
from ... import utils


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run',
                            action='store_true', dest='dry_run', default=False,
                            help='Output a list of model attributes without syncing with Optimizely')
        parser.add_argument('--all-fields',
                            action='store_true', dest='all_fields', default=False,
                            help='Run with ALL fields and not just those that have already been synced.')

    def handle(self, *args, **options):
        is_dry_run = options['dry_run']
        report_all_fields = options['all_fields']
        auth_headers = {'Authorization': 'Bearer {}'.format(optimizely_settings.PERSONAL_ACCESS_TOKEN)}

        # Determine what fields need to be synced.
        if report_all_fields:
            keys = set()
        else:
            resp = requests.get('https://api.optimizely.com/v2/attributes',
                                headers=auth_headers,
                                params={'project_id': optimizely_settings.PROJECT_ID,
                                        'per_page': 100})
            # TODO: account for multiple pages of this in the future
            keys = {attribute['key'] for attribute in resp.json()}

        # Gather all fields/attributes for posting to the Optimizely API
        for feature_flag_model, model_config in optimizely_settings.FEATURE_FLAG_MODELS.items():
            model_name = model_config.get('MODEL_NAME', feature_flag_model._meta.verbose_name.title())
            fields = utils.fields_for_attributes_for_model(feature_flag_model)
            names_and_keys = []

            for field in fields:
                attribute_key = utils.attribute_key_for_field(field)
                if attribute_key not in keys:
                    attribute_name = utils.attribute_name_for_field(field)
                    names_and_keys.append({'name': attribute_name,
                                           'key': attribute_key})
            for additional_attribute in model_config.get('ADDITIONAL_ATTRIBUTES', []):
                attribute_key = utils.attribute_key_for_model(additional_attribute['key'], feature_flag_model)
                if attribute_key not in keys:
                    attribute_name = utils.attribute_name_for_additional_attribute(additional_attribute,
                                                                                   feature_flag_model)
                    names_and_keys.append({'name': attribute_name, 'key': attribute_key})

            for name_and_key in names_and_keys:
                data = {'project_id': int(optimizely_settings.PROJECT_ID),
                        'archived': False}
                data.update(name_and_key)
                if not is_dry_run:
                    resp = requests.post('https://api.optimizely.com/v2/attributes',
                                         headers=auth_headers,
                                         json=data)
                    resp.raise_for_status()
                else:
                    print(data)
