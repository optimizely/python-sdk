# Copyright 2019 Optimizely
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


class Visitor(object):
  def __init__(self, snapshots, attributes, visitor_id):
    self.snapshots = snapshots
    self.attributes = attributes
    self.visitor_id = visitor_id

  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
