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
  experiment_key = request.form.get('experiment_key')
  user_id = request.form.get('user_id')
  attributes = request.form.get('attributes')
  variation = opt_obj.activate(experiment_key, user_id, attributes=attributes)
  return json.dumps({'result': variation}), 200, {'content-type': 'application/json'}

@app.route('/get_variation', methods=['POST'])
def get_variation():
  experiment_key = request.form.get('experiment_key')
  user_id = request.form.get('user_id')
  attributes = request.form.get('attributes')
  variation = opt_obj.get_variation(experiment_key, user_id, attributes=attributes)
  return json.dumps({'result': variation}), 200, {'content-type': 'application/json'}

@app.route('/track', methods=['POST'])
def track():
  event_key = request.form.get('event_key')
  user_id = request.form.get('user_id')
  attributes = request.form.get('attributes')
  event_value = request.form.get('event_value')
  opt_obj.track(event_key, user_id, attributes=attributes, event_value=event_value)
  return json.dumps({'result': ''}), 200, {'content-type': 'application/json'}

if __name__ == '__main__':
  app.run()
