import json
from flask import Flask
from flask import request
from optimizely import optimizely
from optimizely import logger
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
  variation = optimizely_instance.activate(experiment_key, user_id, attributes=attributes)
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
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
  result = optimizely_instance.track(event_key, user_id, attributes, event_tags)
  user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
  return json.dumps({'result': result, 'user_profiles': user_profiles}), 200, {'content-type': 'application/json'}

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=3000)
