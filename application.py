import json
from flask import Flask
from flask import request
from optimizely import logger
from optimizely import notification_center
from optimizely import optimizely
from optimizely.helpers import enums
from optimizely import entities
from optimizely import event_builder

import user_profile_service

app = Flask(__name__)

datafile = open('datafile.json', 'r')
datafile_content = datafile.read()
datafile.close()

optimizely_instance = None
user_profile_service_instance = None


@app.before_request
def before_request():
  global user_profile_service_instance
  global optimizely_instance

  user_profile_service_instance = None
  optimizely_instance = None

  request.payload = request.get_json()
  user_profile_service_instance = request.payload.get('user_profile_service')
  if user_profile_service_instance:
    ups_class = getattr(user_profile_service, request.payload.get('user_profile_service'))
    user_profile_service_instance = ups_class(request.payload.get('user_profiles'))

  optimizely_instance = optimizely.Optimizely(datafile_content, logger=logger.SimpleLogger(), user_profile_service=user_profile_service_instance)


@app.route('/activate', methods=['POST'])
def activate():
  payload = request.get_json()
  experiment_key = payload.get('experiment_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  listener_called = [False]

  if attributes and attributes.get('$add_listener') == 'true':
    def on_activate(experiment, user_id, attributes, variation, event):
      testPass = isinstance(experiment, entities.Experiment) and isinstance(user_id, basestring)
      if attributes is not None:
        testPass = testPass and isinstance(attributes, dict)
      testPass = testPass and isinstance(variation, entities.Variation) and isinstance(event, event_builder.Event)

      print("Here for experiment {0}".format(experiment.key))
      listener_called[0] = testPass

    notification_id = optimizely_instance.notification_center.add_notification_listener(enums.NotificationTypes.ACTIVATE,
                                                                           on_activate)

  variation = optimizely_instance.activate(experiment_key, user_id, attributes=attributes)
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  if listener_called[0]:
    return json.dumps({'result': variation, 'user_profiles': user_profiles, 'listenerCalled': 'true'}), 200, {'content-type': 'application/json'}
  return json.dumps({'result': variation, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}


@app.route('/get_variation', methods=['POST'])
def get_variation():
  payload = request.get_json()
  experiment_key = payload.get('experiment_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  variation = optimizely_instance.get_variation(experiment_key, user_id, attributes=attributes)
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  return json.dumps({'result': variation, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}


@app.route('/track', methods=['POST'])
def track():
  payload = request.get_json()
  event_key = payload.get('event_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  event_tags = payload.get('event_tags')
  listener_called = [False]

  if attributes and attributes.get('$add_listener') == 'true':
    def on_track(event_key, user_id, attributes, event_tags, event):
      print("Here for experiment {0}".format(event_key))
      testPass = isinstance(event_key, basestring) and \
         isinstance(user_id, basestring)
      if attributes is not None:
        testPass = testPass and isinstance(attributes, dict)
      if event_tags is not None:
        testPass = testPass and isinstance(attributes, dict)
      testPass = testPass and isinstance(event, event_builder.Event)
      listener_called[0] = testPass

    notification_id = optimizely_instance.notification_center.add_notification_listener(enums.NotificationTypes.TRACK,
                                                                           on_track)

  result = optimizely_instance.track(event_key, user_id, attributes, event_tags)
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  if listener_called[0]:
    return json.dumps({'result': result, 'user_profiles': user_profiles, 'listenerCalled': 'true'}), 200, {'content-type': 'application/json'}

  return json.dumps({'result': result, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/is_feature_enabled', methods=['POST'])
def is_feature_enabled():
  payload = request.get_json()
  feature_flag_key = payload.get('feature_flag_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')

  feature_enabled = optimizely_instance.is_feature_enabled(feature_flag_key, user_id, attributes)
  result = 'true' if feature_enabled else 'false'
  user_profiles =user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  return json.dumps({'result': result, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}


@app.route('/get_feature_variable_boolean', methods=['POST'])
def get_feature_variable_boolean():
  payload = request.get_json()
  variable_key = payload.get('feature_flag_key')
  feature_flag_key = payload.get('variable_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')

  boolean_value = optimizely_instance.get_feature_variable_boolean(feature_flag_key,
                                                                   variable_key,
                                                                   user_id,
                                                                   attributes)
  result = 'true' if boolean_value else 'false'

  user_profiles =user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  return json.dumps({'result': result,
                     'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/get_feature_variable_double', methods=['POST'])
def get_feature_variable_double():
  payload = request.get_json()
  variable_key = payload.get('feature_flag_key')
  feature_flag_key = payload.get('variable_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')

  double_value = optimizely_instance.get_feature_variable_integer(feature_flag_key,
                                                                  variable_key,
                                                                  user_id,
                                                                  attributes)

  user_profiles =user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  return json.dumps({'result': str(double_value),
                     'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/get_feature_variable_integer', methods=['POST'])
def get_feature_variable_integer():
  payload = request.get_json()
  variable_key = payload.get('feature_flag_key')
  feature_flag_key = payload.get('variable_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')

  integer_value = optimizely_instance.get_feature_variable_integer(feature_flag_key,
                                                                   variable_key,
                                                                   user_id,
                                                                   attributes)

  user_profiles =user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  return json.dumps({'result': str(integer_value),
                     'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/get_feature_variable_string', methods=['POST'])
def get_feature_variable_string():
  payload = request.get_json()
  variable_key = payload.get('feature_flag_key')
  feature_flag_key = payload.get('variable_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')

  string_value = optimizely_instance.get_feature_variable_integer(feature_flag_key,
                                                                  variable_key,
                                                                  user_id,
                                                                  attributes)

  user_profiles =user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  return json.dumps({'result': string_value, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/forced_variation', methods=['POST'])
def forced_variation():
  payload = request.get_json()
  user_id = payload.get('user_id')
  experiment_key = payload.get('experiment_key')
  forced_variation_key = payload.get('forced_variation_key')
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  result = optimizely_instance.set_forced_variation(experiment_key, user_id, forced_variation_key)
  if result is False:
    return json.dumps({'result': None, 'user_profiles': user_profiles}), 400, {'content-type': 'application/json'}
  variation = optimizely_instance.get_forced_variation(experiment_key, user_id)
  return json.dumps({'result': variation, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/forced_variation_multiple_sets', methods=['POST'])
def forced_variation_multiple_sets():
  payload = request.get_json()
  user_id_1 = payload.get('user_id_1')
  user_id_2 = payload.get('user_id_2')
  experiment_key_1 = payload.get('experiment_key_1')
  experiment_key_2 = payload.get('experiment_key_2')
  forced_variation_key_1 = payload.get('forced_variation_key_1')
  forced_variation_key_2 = payload.get('forced_variation_key_2')
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  result = optimizely_instance.set_forced_variation(experiment_key_1, user_id_1, forced_variation_key_1)
  if result is False:
    return json.dumps({'result': None, 'user_profiles': user_profiles}), 400, {'content-type': 'application/json'}
  result = optimizely_instance.set_forced_variation(experiment_key_2, user_id_1, forced_variation_key_2)
  if result is False:
    return json.dumps({'result': None, 'user_profiles': user_profiles}), 400, {'content-type': 'application/json'}
  result = optimizely_instance.set_forced_variation(experiment_key_1, user_id_2, forced_variation_key_1)
  if result is False:
    return json.dumps({'result': None, 'user_profiles': user_profiles}), 400, {'content-type': 'application/json'}
  result = optimizely_instance.set_forced_variation(experiment_key_2, user_id_2, forced_variation_key_2)
  if result is False:
    return json.dumps({'result': None, 'user_profiles': user_profiles}), 400, {'content-type': 'application/json'}
  variation_1 = optimizely_instance.get_forced_variation(experiment_key_1, user_id_1)
  variation_2 = optimizely_instance.get_forced_variation(experiment_key_2, user_id_1)
  variation_3 = optimizely_instance.get_forced_variation(experiment_key_1, user_id_2)
  variation_4 = optimizely_instance.get_forced_variation(experiment_key_2, user_id_2)
  return json.dumps({'result_1': variation_1,
                     'result_2': variation_2,
                     'result_3': variation_3,
                     'result_4': variation_4,
                     'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/forced_variation_get_variation', methods=['POST'])
def forced_variation_get_variation():
  payload = request.get_json()
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  experiment_key = payload.get('experiment_key')
  forced_variation_key = payload.get('forced_variation_key')
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  result = optimizely_instance.set_forced_variation(experiment_key, user_id, forced_variation_key)
  if result is False:
    return json.dumps({'result': None, 'user_profiles': user_profiles}), 400, {'content-type': 'application/json'}
  variation = optimizely_instance.get_variation(experiment_key, user_id, attributes=attributes)
  return json.dumps({'result': variation, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

@app.route('/forced_variation_activate', methods=['POST'])
def forced_variation_activate():
  payload = request.get_json()
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  experiment_key = payload.get('experiment_key')
  forced_variation_key = payload.get('forced_variation_key')
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  result = optimizely_instance.set_forced_variation(experiment_key, user_id, forced_variation_key)
  if result is False:
    return json.dumps({'result': None, 'user_profiles': user_profiles}), 400, {'content-type': 'application/json'}
  variation = optimizely_instance.activate(experiment_key, user_id, attributes=attributes)
  return json.dumps({'result': variation, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=3000)
