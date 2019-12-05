# Copyright 2019, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class OptimizelyConfig(object):
    def __init__(self, project_config):
        self.revision = None
        self.experiments_map = None
        self.features_map = None

class OptimizelyConfigExperiment(object):
    def __init__(self, id, key, variations_map):
        self.id = id
        self.key = key
        self.variations_map = variations_map

class OptimizelyConfigFeature(object):
    def __init__(self, id, key, experiments_map):
        self.id = id
        self.key = key
        self.experiments_map = experiments_map

class OptimizelyConfigVariation(object):
    def __init__(self, id, key, variables_map):
        self.id = id
        self.key = key
        self.variables_map = 

class OptimizelyConfigVariable(object):
    def __init__(self, id, key, type, value):
        self.id = id
        self.key = key
        self.type = type
        self.value = value

class OptimizelyConfigBuilder(object):

    @staticmethod
    def get_config():
    pass

    @staticmethod
    def _get_features_map():
        pass

    @staticmethod
    def _get_merged_variables_map():
        pass

    @staticmethod
    def _get_experiments_map()
        pass


