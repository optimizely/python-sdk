import json
from flask import Flask
from flask import request
from optimizely import optimizely
from optimizely import logger

app = Flask(__name__)

datafile = open('datafile.json', 'r')
datafile_content = datafile.read()
datafile.close()

opt_obj = optimizely.Optimizely(datafile_content, logger=logger.SimpleLogger())


@app.route('/activate', methods=['POST'])
def activate():
  payload = request.get_json()
  experiment_key = payload.get('experiment_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  variation = opt_obj.activate(experiment_key, user_id, attributes=attributes)
  return json.dumps({'result': variation}), 200, {'content-type': 'application/json'}

@app.route('/get_variation', methods=['POST'])
def get_variation():
  payload = request.get_json()
  experiment_key = payload.get('experiment_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  variation = opt_obj.get_variation(experiment_key, user_id, attributes=attributes)
  return json.dumps({'result': variation}), 200, {'content-type': 'application/json'}

@app.route('/track', methods=['POST'])
def track():
  payload = request.get_json()
  event_key = payload.get('event_key')
  user_id = payload.get('user_id')
  attributes = payload.get('attributes')
  event_value = payload.get('event_value')
  result = opt_obj.track(event_key, user_id, attributes=attributes, event_value=event_value)
  return json.dumps({'result': result}), 200, {'content-type': 'application/json'}

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=3000)
