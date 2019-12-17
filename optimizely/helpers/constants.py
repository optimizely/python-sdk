# Copyright 2016-2017, Optimizely
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

JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "projectId": {"type": "string"},
        "accountId": {"type": "string"},
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "policy": {"type": "string"},
                    "trafficAllocation": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"entityId": {"type": "string"}, "endOfRange": {"type": "integer"}},
                            "required": ["entityId", "endOfRange"],
                        },
                    },
                    "experiments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "layerId": {"type": "string"},
                                "key": {"type": "string"},
                                "status": {"type": "string"},
                                "variations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {"id": {"type": "string"}, "key": {"type": "string"}},
                                        "required": ["id", "key"],
                                    },
                                },
                                "trafficAllocation": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "entityId": {"type": "string"},
                                            "endOfRange": {"type": "integer"},
                                        },
                                        "required": ["entityId", "endOfRange"],
                                    },
                                },
                                "audienceIds": {"type": "array", "items": {"type": "string"}},
                                "forcedVariations": {"type": "object"},
                            },
                            "required": [
                                "id",
                                "layerId",
                                "key",
                                "status",
                                "variations",
                                "trafficAllocation",
                                "audienceIds",
                                "forcedVariations",
                            ],
                        },
                    },
                },
                "required": ["id", "policy", "trafficAllocation", "experiments"],
            },
        },
        "experiments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "layerId": {"type": "string"},
                    "key": {"type": "string"},
                    "status": {"type": "string"},
                    "variations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"id": {"type": "string"}, "key": {"type": "string"}},
                            "required": ["id", "key"],
                        },
                    },
                    "trafficAllocation": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"entityId": {"type": "string"}, "endOfRange": {"type": "integer"}},
                            "required": ["entityId", "endOfRange"],
                        },
                    },
                    "audienceIds": {"type": "array", "items": {"type": "string"}},
                    "forcedVariations": {"type": "object"},
                },
                "required": [
                    "id",
                    "layerId",
                    "key",
                    "status",
                    "variations",
                    "trafficAllocation",
                    "audienceIds",
                    "forcedVariations",
                ],
            },
        },
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "experimentIds": {"type": "array", "items": {"type": "string"}},
                    "id": {"type": "string"},
                },
                "required": ["key", "experimentIds", "id"],
            },
        },
        "audiences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "name": {"type": "string"}, "conditions": {"type": "string"}},
                "required": ["id", "name", "conditions"],
            },
        },
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "key": {"type": "string"}},
                "required": ["id", "key"],
            },
        },
        "version": {"type": "string"},
        "revision": {"type": "string"},
    },
    "required": [
        "projectId",
        "accountId",
        "groups",
        "experiments",
        "events",
        "audiences",
        "attributes",
        "version",
        "revision",
    ],
}
