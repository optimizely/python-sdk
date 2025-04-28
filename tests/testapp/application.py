# Copyright 2016-2018, Optimizely
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

import json
import logging
import types
from os import environ

import user_profile_service
from flask import Flask, request
from flask_wtf.csrf import CSRFProtect

from optimizely import logger, optimizely
from optimizely.helpers import enums

app = Flask(__name__)
# Initialize CSRF protection
csrf = CSRFProtect(app)

datafile = open('datafile.json', 'r')
datafile_content = datafile.read()
datafile.close()

optimizely_instance = None
user_profile_service_instance = None
listener_return_maps = None


def copy_func(f, name=None):
    return types.FunctionType(f.func_code, f.func_globals, name or f.func_name, f.func_defaults, f.func_closure,)


def on_activate(experiment, _user_id, _attributes, variation, event):
    # listener callback for activate.
    global listener_return_maps

    listener_return_map = {
        'experiment_key': experiment.key,
        'user_id': _user_id,
        'attributes': _attributes or {},
        'variation_key': variation.key,
    }

    if listener_return_maps is None:
        listener_return_maps = [listener_return_map]
    else:
        listener_return_maps.append(listener_return_map)


def on_track(_event_key, _user_id, _attributes, _event_tags, event):
    # listener callback for track
    global listener_return_maps

    listener_return_map = {
        'event_key': _event_key,
        "user_id": _user_id,
        'attributes': _attributes or {},
        'event_tags': _event_tags or {},
    }
    if listener_return_maps is None:
        listener_return_maps = [listener_return_map]
    else:
        listener_return_maps.append(listener_return_map)


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

    with_listener = request.payload.get('with_listener')

    log_level = environ.get('OPTIMIZELY_SDK_LOG_LEVEL', 'DEBUG')
    min_level = getattr(logging, log_level)
    optimizely_instance = optimizely.Optimizely(
        datafile_content,
        logger=logger.SimpleLogger(min_level=min_level),
        user_profile_service=user_profile_service_instance,
    )

    if with_listener is not None:
        for listener_add in with_listener:
            if listener_add['type'] == 'Activate':
                count = int(listener_add['count'])
                for i in range(count):
                    # make a value copy so that we can add multiple callbacks.
                    a_cb = copy_func(on_activate)
                    optimizely_instance.notification_center.add_notification_listener(
                        enums.NotificationTypes.ACTIVATE, a_cb
                    )
            if listener_add['type'] == 'Track':
                count = int(listener_add['count'])
                for i in range(count):
                    # make a value copy so that we can add multiple callbacks.
                    t_cb = copy_func(on_track)
                    optimizely_instance.notification_center.add_notification_listener(
                        enums.NotificationTypes.TRACK, t_cb
                    )


@app.after_request
def after_request(response):
    global optimizely_instance  # noqa: F824
    global listener_return_maps

    optimizely_instance.notification_center.clear_all_notifications()
    listener_return_maps = None
    return response


@app.route('/activate', methods=['POST'])
def activate():
    payload = request.get_json()
    experiment_key = payload.get('experiment_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')

    variation = optimizely_instance.activate(experiment_key, user_id, attributes=attributes)
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else []

    payload = {
        'result': variation,
        'user_profiles': user_profiles,
        'listener_called': listener_return_maps,
    }
    return json.dumps(payload), 200, {'content-type': 'application/json'}


@app.route('/get_variation', methods=['POST'])
def get_variation():
    payload = request.get_json()
    experiment_key = payload.get('experiment_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')
    variation = optimizely_instance.get_variation(experiment_key, user_id, attributes=attributes)
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else []
    return (
        json.dumps({'result': variation, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/track', methods=['POST'])
def track():
    payload = request.get_json()
    event_key = payload.get('event_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')
    event_tags = payload.get('event_tags')

    result = optimizely_instance.track(event_key, user_id, attributes, event_tags)

    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else []

    payload = {
        'result': result,
        'user_profiles': user_profiles,
        'listener_called': listener_return_maps,
    }
    return json.dumps(payload), 200, {'content-type': 'application/json'}


@app.route('/is_feature_enabled', methods=['POST'])
def is_feature_enabled():
    payload = request.get_json()
    feature_flag_key = payload.get('feature_flag_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')

    feature_enabled = optimizely_instance.is_feature_enabled(feature_flag_key, user_id, attributes)
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}

    result = feature_enabled if feature_enabled is None else 'true' if feature_enabled is True else 'false'
    return (
        json.dumps({'result': result, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/get_enabled_features', methods=['POST'])
def get_enabled_features():
    payload = request.get_json()
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')

    enabled_features = optimizely_instance.get_enabled_features(user_id, attributes)
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}

    payload = {
        'result': enabled_features,
        'user_profiles': user_profiles,
        'listener_called': listener_return_maps,
    }
    return json.dumps(payload), 200, {'content-type': 'application/json'}


@app.route('/get_feature_variable_boolean', methods=['POST'])
def get_feature_variable_boolean():
    payload = request.get_json()
    feature_flag_key = payload.get('feature_flag_key')
    variable_key = payload.get('variable_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')

    boolean_value = optimizely_instance.get_feature_variable_boolean(
        feature_flag_key, variable_key, user_id, attributes
    )
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
    return (
        json.dumps({'result': boolean_value, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/get_feature_variable_double', methods=['POST'])
def get_feature_variable_double():
    payload = request.get_json()
    feature_flag_key = payload.get('feature_flag_key')
    variable_key = payload.get('variable_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')

    double_value = optimizely_instance.get_feature_variable_double(feature_flag_key, variable_key, user_id, attributes)

    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
    return (
        json.dumps({'result': double_value, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/get_feature_variable_integer', methods=['POST'])
def get_feature_variable_integer():
    payload = request.get_json()
    feature_flag_key = payload.get('feature_flag_key')
    variable_key = payload.get('variable_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')

    integer_value = optimizely_instance.get_feature_variable_integer(
        feature_flag_key, variable_key, user_id, attributes
    )

    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
    return (
        json.dumps({'result': integer_value, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/get_feature_variable_string', methods=['POST'])
def get_feature_variable_string():
    payload = request.get_json()
    feature_flag_key = payload.get('feature_flag_key')
    variable_key = payload.get('variable_key')
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')

    string_value = optimizely_instance.get_feature_variable_string(feature_flag_key, variable_key, user_id, attributes)

    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else {}
    return (
        json.dumps({'result': string_value, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/forced_variation', methods=['POST'])
def forced_variation():
    payload = request.get_json()
    user_id = payload.get('user_id')
    experiment_key = payload.get('experiment_key')
    forced_variation_key = payload.get('forced_variation_key')
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else []
    result = optimizely_instance.set_forced_variation(experiment_key, user_id, forced_variation_key)
    if result is False:
        return (
            json.dumps({'result': None, 'user_profiles': user_profiles}),
            400,
            {'content-type': 'application/json'},
        )
    variation = optimizely_instance.get_forced_variation(experiment_key, user_id)
    return (
        json.dumps({'result': variation, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/forced_variation_multiple_sets', methods=['POST'])
def forced_variation_multiple_sets():
    payload = request.get_json()
    user_id_1 = payload.get('user_id_1')
    user_id_2 = payload.get('user_id_2')
    experiment_key_1 = payload.get('experiment_key_1')
    experiment_key_2 = payload.get('experiment_key_2')
    forced_variation_key_1 = payload.get('forced_variation_key_1')
    forced_variation_key_2 = payload.get('forced_variation_key_2')
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else []
    result = optimizely_instance.set_forced_variation(experiment_key_1, user_id_1, forced_variation_key_1)
    if result is False:
        return (
            json.dumps({'result': None, 'user_profiles': user_profiles}),
            400,
            {'content-type': 'application/json'},
        )
    result = optimizely_instance.set_forced_variation(experiment_key_2, user_id_1, forced_variation_key_2)
    if result is False:
        return (
            json.dumps({'result': None, 'user_profiles': user_profiles}),
            400,
            {'content-type': 'application/json'},
        )
    result = optimizely_instance.set_forced_variation(experiment_key_1, user_id_2, forced_variation_key_1)
    if result is False:
        return (
            json.dumps({'result': None, 'user_profiles': user_profiles}),
            400,
            {'content-type': 'application/json'},
        )
    result = optimizely_instance.set_forced_variation(experiment_key_2, user_id_2, forced_variation_key_2)
    if result is False:
        return (
            json.dumps({'result': None, 'user_profiles': user_profiles}),
            400,
            {'content-type': 'application/json'},
        )
    variation_1 = optimizely_instance.get_forced_variation(experiment_key_1, user_id_1)
    variation_2 = optimizely_instance.get_forced_variation(experiment_key_2, user_id_1)
    variation_3 = optimizely_instance.get_forced_variation(experiment_key_1, user_id_2)
    variation_4 = optimizely_instance.get_forced_variation(experiment_key_2, user_id_2)
    return (
        json.dumps(
            {
                'result_1': variation_1,
                'result_2': variation_2,
                'result_3': variation_3,
                'result_4': variation_4,
                'user_profiles': user_profiles,
            }
        ),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/forced_variation_get_variation', methods=['POST'])
def forced_variation_get_variation():
    payload = request.get_json()
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')
    experiment_key = payload.get('experiment_key')
    forced_variation_key = payload.get('forced_variation_key')
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else []
    result = optimizely_instance.set_forced_variation(experiment_key, user_id, forced_variation_key)
    if result is False:
        return (
            json.dumps({'result': None, 'user_profiles': user_profiles}),
            400,
            {'content-type': 'application/json'},
        )
    variation = optimizely_instance.get_variation(experiment_key, user_id, attributes=attributes)
    return (
        json.dumps({'result': variation, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


@app.route('/forced_variation_activate', methods=['POST'])
def forced_variation_activate():
    payload = request.get_json()
    user_id = payload.get('user_id')
    attributes = payload.get('attributes')
    experiment_key = payload.get('experiment_key')
    forced_variation_key = payload.get('forced_variation_key')
    user_profiles = user_profile_service_instance.user_profiles.values() if user_profile_service_instance else []
    result = optimizely_instance.set_forced_variation(experiment_key, user_id, forced_variation_key)
    if result is False:
        return (
            json.dumps({'result': None, 'user_profiles': user_profiles}),
            400,
            {'content-type': 'application/json'},
        )
    variation = optimizely_instance.activate(experiment_key, user_id, attributes=attributes)
    return (
        json.dumps({'result': variation, 'user_profiles': user_profiles}),
        200,
        {'content-type': 'application/json'},
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
