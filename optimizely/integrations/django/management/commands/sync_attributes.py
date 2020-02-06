from django.core.management.base import BaseCommand, CommandError
import requests

from ...settings import optimizely_settings
from ... import utils

class Command(BaseCommand):
    def handle(self, *args, **options):
        auth_headers = {'Authorization': 'Bearer {}'.format(optimizely_settings.PERSONAL_ACCESS_TOKEN)}
        resp = requests.get('https://api.optimizely.com/v2/attributes',
                            headers=auth_headers,
                            params={'project_id': optimizely_settings.PROJECT_ID,
                                    'per_page': 100})
        # TODO: account for multiple pages of this in the future
        keys = {attribute['key'] for attribute in resp.json()}
        for feature_flag_model in optimizely_settings.FEATURE_FLAG_MODELS.keys():
            fields = utils.fields_for_attributes_for_model(feature_flag_model)
            for field in fields:
                attribute_key = utils.attribute_key_for_field(field)
                if attribute_key not in keys:
                    data = {'project_id': int(optimizely_settings.PROJECT_ID),
                            'key': attribute_key,
                            'archived': False,
                            'name': '{}: {}'.format(feature_flag_model._meta.verbose_name.capitalize(),
                                                    field.verbose_name.capitalize())}
                    resp = requests.post('https://api.optimizely.com/v2/attributes',
                                         headers=auth_headers,
                                         json=data)
                    resp.raise_for_status()
