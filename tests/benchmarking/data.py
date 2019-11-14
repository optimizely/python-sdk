# Copyright 2016, 2019, Optimizely
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

from optimizely import optimizely


config_10_exp = {
    "experiments": [
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment4",
            "trafficAllocation": [
                {"entityId": "6373141147", "endOfRange": 5000},
                {"entityId": "6373141148", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6373141147", "key": "control"}, {"id": "6373141148", "key": "variation"}],
            "forcedVariations": {},
            "id": "6358043286",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment5",
            "trafficAllocation": [
                {"entityId": "6335242053", "endOfRange": 5000},
                {"entityId": "6335242054", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6335242053", "key": "control"}, {"id": "6335242054", "key": "variation"}],
            "forcedVariations": {},
            "id": "6364835526",
        },
        {
            "status": "Paused",
            "percentageIncluded": 10000,
            "key": "testExperimentNotRunning",
            "trafficAllocation": [
                {"entityId": "6377281127", "endOfRange": 5000},
                {"entityId": "6377281128", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6377281127", "key": "control"}, {"id": "6377281128", "key": "variation"}],
            "forcedVariations": {},
            "id": "6367444440",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment1",
            "trafficAllocation": [
                {"entityId": "6384330451", "endOfRange": 5000},
                {"entityId": "6384330452", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6384330451", "key": "control"}, {"id": "6384330452", "key": "variation"}],
            "forcedVariations": {"variation_user": "variation", "control_user": "control"},
            "id": "6367863211",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment3",
            "trafficAllocation": [
                {"entityId": "6376141758", "endOfRange": 5000},
                {"entityId": "6376141759", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6376141758", "key": "control"}, {"id": "6376141759", "key": "variation"}],
            "forcedVariations": {},
            "id": "6370392407",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment6",
            "trafficAllocation": [
                {"entityId": "6379060914", "endOfRange": 5000},
                {"entityId": "6379060915", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6379060914", "key": "control"}, {"id": "6379060915", "key": "variation"}],
            "forcedVariations": {"forced_variation_user": "variation"},
            "id": "6370821515",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment2",
            "trafficAllocation": [
                {"entityId": "6386700062", "endOfRange": 5000},
                {"entityId": "6386700063", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6386700062", "key": "control"}, {"id": "6386700063", "key": "variation"}],
            "forcedVariations": {"variation_user": "variation", "control_user": "control"},
            "id": "6376870125",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperimentWithFirefoxAudience",
            "trafficAllocation": [
                {"entityId": "6333082303", "endOfRange": 5000},
                {"entityId": "6333082304", "endOfRange": 10000},
            ],
            "audienceIds": ["6369992312"],
            "variations": [{"id": "6333082303", "key": "control"}, {"id": "6333082304", "key": "variation"}],
            "forcedVariations": {},
            "id": "6383811281",
        },
    ],
    "version": "1",
    "audiences": [
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"safari\"}]]]",
            "id": "6352892614",
            "name": "Safari users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"android\"}]]]",
            "id": "6355234780",
            "name": "Android users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"desktop\"}]]]",
            "id": "6360574256",
            "name": "Desktop users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"opera\"}]]]",
            "id": "6365864533",
            "name": "Opera users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"tablet\"}]]]",
            "id": "6369831151",
            "name": "Tablet users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"firefox\"}]]]",
            "id": "6369992312",
            "name": "Firefox users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"chrome\"}]]]",
            "id": "6373141157",
            "name": "Chrome users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"ie\"}]]]",
            "id": "6378191386",
            "name": "IE users",
        },
    ],
    "dimensions": [{"id": "6359881003", "key": "browser_type", "segmentId": "6380740826"}],
    "groups": [
        {"policy": "random", "trafficAllocation": [], "experiments": [], "id": "6367902163"},
        {"policy": "random", "trafficAllocation": [], "experiments": [], "id": "6393150032"},
        {
            "policy": "random",
            "trafficAllocation": [
                {"entityId": "6450630664", "endOfRange": 5000},
                {"entityId": "6447021179", "endOfRange": 10000},
            ],
            "experiments": [
                {
                    "status": "Running",
                    "percentageIncluded": 5000,
                    "key": "mutex_exp2",
                    "trafficAllocation": [
                        {"entityId": "6453410972", "endOfRange": 5000},
                        {"entityId": "6453410973", "endOfRange": 10000},
                    ],
                    "audienceIds": [],
                    "variations": [{"id": "6453410972", "key": "a"}, {"id": "6453410973", "key": "b"}],
                    "forcedVariations": {"user_b": "b", "user_a": "a"},
                    "id": "6447021179",
                },
                {
                    "status": "Running",
                    "percentageIncluded": 5000,
                    "key": "mutex_exp1",
                    "trafficAllocation": [
                        {"entityId": "6451680205", "endOfRange": 5000},
                        {"entityId": "6451680206", "endOfRange": 10000},
                    ],
                    "audienceIds": ["6373141157"],
                    "variations": [{"id": "6451680205", "key": "a"}, {"id": "6451680206", "key": "b"}],
                    "forcedVariations": {},
                    "id": "6450630664",
                },
            ],
            "id": "6436903041",
        },
    ],
    "projectId": "6377970066",
    "accountId": "6365361536",
    "events": [
        {
            "experimentIds": ["6450630664", "6447021179"],
            "id": "6370392432",
            "key": "testEventWithMultipleGroupedExperiments",
        },
        {"experimentIds": ["6367863211"], "id": "6372590948", "key": "testEvent"},
        {
            "experimentIds": [
                "6364835526",
                "6450630664",
                "6367863211",
                "6376870125",
                "6383811281",
                "6358043286",
                "6370392407",
                "6367444440",
                "6370821515",
                "6447021179",
            ],
            "id": "6372952486",
            "key": "testEventWithMultipleExperiments",
        },
        {"experimentIds": ["6367444440"], "id": "6380961307", "key": "testEventWithExperimentNotRunning"},
        {"experimentIds": ["6383811281"], "id": "6384781388", "key": "testEventWithAudiences"},
        {"experimentIds": [], "id": "6386521015", "key": "testEventWithoutExperiments"},
        {"experimentIds": ["6450630664", "6383811281", "6376870125"], "id": "6316734272", "key": "Total Revenue"},
    ],
    "revision": "83",
}

config_25_exp = {
    "experiments": [
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment12",
            "trafficAllocation": [
                {"entityId": "6387320950", "endOfRange": 5000},
                {"entityId": "6387320951", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6387320950", "key": "control"}, {"id": "6387320951", "key": "variation"}],
            "forcedVariations": {},
            "id": "6344617435",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment19",
            "trafficAllocation": [
                {"entityId": "6380932289", "endOfRange": 5000},
                {"entityId": "6380932290", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6380932289", "key": "control"}, {"id": "6380932290", "key": "variation"}],
            "forcedVariations": {},
            "id": "6349682899",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment21",
            "trafficAllocation": [
                {"entityId": "6356833706", "endOfRange": 5000},
                {"entityId": "6356833707", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6356833706", "key": "control"}, {"id": "6356833707", "key": "variation"}],
            "forcedVariations": {},
            "id": "6350472041",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment7",
            "trafficAllocation": [
                {"entityId": "6367863508", "endOfRange": 5000},
                {"entityId": "6367863509", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6367863508", "key": "control"}, {"id": "6367863509", "key": "variation"}],
            "forcedVariations": {},
            "id": "6352512126",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment15",
            "trafficAllocation": [
                {"entityId": "6379652128", "endOfRange": 5000},
                {"entityId": "6379652129", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6379652128", "key": "control"}, {"id": "6379652129", "key": "variation"}],
            "forcedVariations": {},
            "id": "6357622647",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment16",
            "trafficAllocation": [
                {"entityId": "6359551503", "endOfRange": 5000},
                {"entityId": "6359551504", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6359551503", "key": "control"}, {"id": "6359551504", "key": "variation"}],
            "forcedVariations": {},
            "id": "6361100609",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment8",
            "trafficAllocation": [
                {"entityId": "6378191496", "endOfRange": 5000},
                {"entityId": "6378191497", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6378191496", "key": "control"}, {"id": "6378191497", "key": "variation"}],
            "forcedVariations": {},
            "id": "6361743021",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperimentWithFirefoxAudience",
            "trafficAllocation": [
                {"entityId": "6380932291", "endOfRange": 5000},
                {"entityId": "6380932292", "endOfRange": 10000},
            ],
            "audienceIds": ["6317864099"],
            "variations": [{"id": "6380932291", "key": "control"}, {"id": "6380932292", "key": "variation"}],
            "forcedVariations": {},
            "id": "6361931183",
        },
        {
            "status": "Not started",
            "percentageIncluded": 10000,
            "key": "testExperimentNotRunning",
            "trafficAllocation": [
                {"entityId": "6377723538", "endOfRange": 5000},
                {"entityId": "6377723539", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6377723538", "key": "control"}, {"id": "6377723539", "key": "variation"}],
            "forcedVariations": {},
            "id": "6362042330",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment5",
            "trafficAllocation": [
                {"entityId": "6361100607", "endOfRange": 5000},
                {"entityId": "6361100608", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6361100607", "key": "control"}, {"id": "6361100608", "key": "variation"}],
            "forcedVariations": {},
            "id": "6365780767",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment0",
            "trafficAllocation": [
                {"entityId": "6379122883", "endOfRange": 5000},
                {"entityId": "6379122884", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6379122883", "key": "control"}, {"id": "6379122884", "key": "variation"}],
            "forcedVariations": {},
            "id": "6366023085",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment2",
            "trafficAllocation": [
                {"entityId": "6373980983", "endOfRange": 5000},
                {"entityId": "6373980984", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6373980983", "key": "control"}, {"id": "6373980984", "key": "variation"}],
            "forcedVariations": {"variation_user": "variation", "control_user": "control"},
            "id": "6367473060",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment13",
            "trafficAllocation": [
                {"entityId": "6361931181", "endOfRange": 5000},
                {"entityId": "6361931182", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6361931181", "key": "control"}, {"id": "6361931182", "key": "variation"}],
            "forcedVariations": {},
            "id": "6367842673",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment18",
            "trafficAllocation": [
                {"entityId": "6375121958", "endOfRange": 5000},
                {"entityId": "6375121959", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6375121958", "key": "control"}, {"id": "6375121959", "key": "variation"}],
            "forcedVariations": {},
            "id": "6367902537",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment17",
            "trafficAllocation": [
                {"entityId": "6353582033", "endOfRange": 5000},
                {"entityId": "6353582034", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6353582033", "key": "control"}, {"id": "6353582034", "key": "variation"}],
            "forcedVariations": {},
            "id": "6368671885",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment11",
            "trafficAllocation": [
                {"entityId": "6355235088", "endOfRange": 5000},
                {"entityId": "6355235089", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6355235088", "key": "control"}, {"id": "6355235089", "key": "variation"}],
            "forcedVariations": {},
            "id": "6369512098",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment3",
            "trafficAllocation": [
                {"entityId": "6355235086", "endOfRange": 5000},
                {"entityId": "6355235087", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6355235086", "key": "control"}, {"id": "6355235087", "key": "variation"}],
            "forcedVariations": {},
            "id": "6371041921",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment10",
            "trafficAllocation": [
                {"entityId": "6382231014", "endOfRange": 5000},
                {"entityId": "6382231015", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6382231014", "key": "control"}, {"id": "6382231015", "key": "variation"}],
            "forcedVariations": {},
            "id": "6375231186",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment20",
            "trafficAllocation": [
                {"entityId": "6362951972", "endOfRange": 5000},
                {"entityId": "6362951973", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6362951972", "key": "control"}, {"id": "6362951973", "key": "variation"}],
            "forcedVariations": {},
            "id": "6377131549",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment9",
            "trafficAllocation": [
                {"entityId": "6369462637", "endOfRange": 5000},
                {"entityId": "6369462638", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6369462637", "key": "control"}, {"id": "6369462638", "key": "variation"}],
            "forcedVariations": {},
            "id": "6382251626",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment14",
            "trafficAllocation": [
                {"entityId": "6388520034", "endOfRange": 5000},
                {"entityId": "6388520035", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6388520034", "key": "control"}, {"id": "6388520035", "key": "variation"}],
            "forcedVariations": {},
            "id": "6383770101",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment6",
            "trafficAllocation": [
                {"entityId": "6378802069", "endOfRange": 5000},
                {"entityId": "6378802070", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6378802069", "key": "control"}, {"id": "6378802070", "key": "variation"}],
            "forcedVariations": {},
            "id": "6386411740",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment4",
            "trafficAllocation": [
                {"entityId": "6350263010", "endOfRange": 5000},
                {"entityId": "6350263011", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6350263010", "key": "control"}, {"id": "6350263011", "key": "variation"}],
            "forcedVariations": {},
            "id": "6386460951",
        },
    ],
    "version": "1",
    "audiences": [
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"firefox\"}]]]",
            "id": "6317864099",
            "name": "Firefox users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"safari\"}]]]",
            "id": "6360592016",
            "name": "Safari users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"chrome\"}]]]",
            "id": "6361743063",
            "name": "Chrome users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"desktop\"}]]]",
            "id": "6372190788",
            "name": "Desktop users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"android\"}]]]",
            "id": "6376141951",
            "name": "Android users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"ie\"}]]]",
            "id": "6377605300",
            "name": "IE users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"tablet\"}]]]",
            "id": "6378191534",
            "name": "Tablet users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"opera\"}]]]",
            "id": "6386521201",
            "name": "Opera users",
        },
    ],
    "dimensions": [{"id": "6381732124", "key": "browser_type", "segmentId": "6388221232"}],
    "groups": [
        {
            "policy": "random",
            "trafficAllocation": [
                {"entityId": "6416416234", "endOfRange": 5000},
                {"entityId": "6451651052", "endOfRange": 10000},
            ],
            "experiments": [
                {
                    "status": "Running",
                    "percentageIncluded": 5000,
                    "key": "mutex_exp1",
                    "trafficAllocation": [
                        {"entityId": "6448110056", "endOfRange": 5000},
                        {"entityId": "6448110057", "endOfRange": 10000},
                    ],
                    "audienceIds": ["6361743063"],
                    "variations": [{"id": "6448110056", "key": "a"}, {"id": "6448110057", "key": "b"}],
                    "forcedVariations": {},
                    "id": "6416416234",
                },
                {
                    "status": "Running",
                    "percentageIncluded": 5000,
                    "key": "mutex_exp2",
                    "trafficAllocation": [
                        {"entityId": "6437485007", "endOfRange": 5000},
                        {"entityId": "6437485008", "endOfRange": 10000},
                    ],
                    "audienceIds": [],
                    "variations": [{"id": "6437485007", "key": "a"}, {"id": "6437485008", "key": "b"}],
                    "forcedVariations": {"user_b": "b", "user_a": "a"},
                    "id": "6451651052",
                },
            ],
            "id": "6441101079",
        }
    ],
    "projectId": "6379191198",
    "accountId": "6365361536",
    "events": [
        {"experimentIds": [], "id": "6360377431", "key": "testEventWithoutExperiments"},
        {"experimentIds": ["6366023085"], "id": "6373184839", "key": "testEvent"},
        {"experimentIds": ["6451651052"], "id": "6379061102", "key": "testEventWithMultipleGroupedExperiments"},
        {"experimentIds": ["6362042330"], "id": "6385201698", "key": "testEventWithExperimentNotRunning"},
        {"experimentIds": ["6361931183"], "id": "6385551103", "key": "testEventWithAudiences"},
        {
            "experimentIds": [
                "6371041921",
                "6382251626",
                "6368671885",
                "6361743021",
                "6386460951",
                "6377131549",
                "6365780767",
                "6369512098",
                "6367473060",
                "6366023085",
                "6361931183",
                "6361100609",
                "6367902537",
                "6375231186",
                "6349682899",
                "6362042330",
                "6344617435",
                "6386411740",
                "6350472041",
                "6416416234",
                "6451651052",
                "6367842673",
                "6383770101",
                "6357622647",
                "6352512126",
            ],
            "id": "6386470923",
            "key": "testEventWithMultipleExperiments",
        },
        {"experimentIds": ["6361931183", "6416416234", "6367473060"], "id": "6386460946", "key": "Total Revenue"},
    ],
    "revision": "92",
}

config_50_exp = {
    "experiments": [
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment31",
            "trafficAllocation": [
                {"entityId": "6383523065", "endOfRange": 5000},
                {"entityId": "6383523066", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6383523065", "key": "control"}, {"id": "6383523066", "key": "variation"}],
            "forcedVariations": {},
            "id": "6313973431",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment15",
            "trafficAllocation": [
                {"entityId": "6363413697", "endOfRange": 5000},
                {"entityId": "6363413698", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6363413697", "key": "control"}, {"id": "6363413698", "key": "variation"}],
            "forcedVariations": {},
            "id": "6332666164",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment33",
            "trafficAllocation": [
                {"entityId": "6330789404", "endOfRange": 5000},
                {"entityId": "6330789405", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6330789404", "key": "control"}, {"id": "6330789405", "key": "variation"}],
            "forcedVariations": {},
            "id": "6338678718",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment38",
            "trafficAllocation": [
                {"entityId": "6376706101", "endOfRange": 5000},
                {"entityId": "6376706102", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6376706101", "key": "control"}, {"id": "6376706102", "key": "variation"}],
            "forcedVariations": {},
            "id": "6338678719",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment44",
            "trafficAllocation": [
                {"entityId": "6316734590", "endOfRange": 5000},
                {"entityId": "6316734591", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6316734590", "key": "control"}, {"id": "6316734591", "key": "variation"}],
            "forcedVariations": {},
            "id": "6355784786",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperimentWithFirefoxAudience",
            "trafficAllocation": [
                {"entityId": "6362476365", "endOfRange": 5000},
                {"entityId": "6362476366", "endOfRange": 10000},
            ],
            "audienceIds": ["6373742627"],
            "variations": [{"id": "6362476365", "key": "control"}, {"id": "6362476366", "key": "variation"}],
            "forcedVariations": {},
            "id": "6359356006",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment14",
            "trafficAllocation": [
                {"entityId": "6327476066", "endOfRange": 5000},
                {"entityId": "6327476067", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6327476066", "key": "control"}, {"id": "6327476067", "key": "variation"}],
            "forcedVariations": {},
            "id": "6360796560",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment46",
            "trafficAllocation": [
                {"entityId": "6357247500", "endOfRange": 5000},
                {"entityId": "6357247501", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6357247500", "key": "control"}, {"id": "6357247501", "key": "variation"}],
            "forcedVariations": {},
            "id": "6361359596",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment16",
            "trafficAllocation": [
                {"entityId": "6378191544", "endOfRange": 5000},
                {"entityId": "6378191545", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6378191544", "key": "control"}, {"id": "6378191545", "key": "variation"}],
            "forcedVariations": {},
            "id": "6361743077",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment10",
            "trafficAllocation": [
                {"entityId": "6372300744", "endOfRange": 5000},
                {"entityId": "6372300745", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6372300744", "key": "control"}, {"id": "6372300745", "key": "variation"}],
            "forcedVariations": {},
            "id": "6362476358",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment11",
            "trafficAllocation": [
                {"entityId": "6357247497", "endOfRange": 5000},
                {"entityId": "6357247498", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6357247497", "key": "control"}, {"id": "6357247498", "key": "variation"}],
            "forcedVariations": {},
            "id": "6362476359",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment12",
            "trafficAllocation": [
                {"entityId": "6368497829", "endOfRange": 5000},
                {"entityId": "6368497830", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6368497829", "key": "control"}, {"id": "6368497830", "key": "variation"}],
            "forcedVariations": {},
            "id": "6363607946",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment7",
            "trafficAllocation": [
                {"entityId": "6386590519", "endOfRange": 5000},
                {"entityId": "6386590520", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6386590519", "key": "control"}, {"id": "6386590520", "key": "variation"}],
            "forcedVariations": {},
            "id": "6364882055",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment6",
            "trafficAllocation": [
                {"entityId": "6385481560", "endOfRange": 5000},
                {"entityId": "6385481561", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6385481560", "key": "control"}, {"id": "6385481561", "key": "variation"}],
            "forcedVariations": {},
            "id": "6366023126",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment23",
            "trafficAllocation": [
                {"entityId": "6375122007", "endOfRange": 5000},
                {"entityId": "6375122008", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6375122007", "key": "control"}, {"id": "6375122008", "key": "variation"}],
            "forcedVariations": {},
            "id": "6367902584",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment13",
            "trafficAllocation": [
                {"entityId": "6360762679", "endOfRange": 5000},
                {"entityId": "6360762680", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6360762679", "key": "control"}, {"id": "6360762680", "key": "variation"}],
            "forcedVariations": {},
            "id": "6367922509",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment39",
            "trafficAllocation": [
                {"entityId": "6341311988", "endOfRange": 5000},
                {"entityId": "6341311989", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6341311988", "key": "control"}, {"id": "6341311989", "key": "variation"}],
            "forcedVariations": {},
            "id": "6369992702",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment4",
            "trafficAllocation": [
                {"entityId": "6370014876", "endOfRange": 5000},
                {"entityId": "6370014877", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6370014876", "key": "control"}, {"id": "6370014877", "key": "variation"}],
            "forcedVariations": {},
            "id": "6370815084",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment17",
            "trafficAllocation": [
                {"entityId": "6384651930", "endOfRange": 5000},
                {"entityId": "6384651931", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6384651930", "key": "control"}, {"id": "6384651931", "key": "variation"}],
            "forcedVariations": {},
            "id": "6371742027",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment42",
            "trafficAllocation": [
                {"entityId": "6371581616", "endOfRange": 5000},
                {"entityId": "6371581617", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6371581616", "key": "control"}, {"id": "6371581617", "key": "variation"}],
            "forcedVariations": {},
            "id": "6374064265",
        },
        {
            "status": "Not started",
            "percentageIncluded": 10000,
            "key": "testExperimentNotRunning",
            "trafficAllocation": [
                {"entityId": "6380740985", "endOfRange": 5000},
                {"entityId": "6380740986", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6380740985", "key": "control"}, {"id": "6380740986", "key": "variation"}],
            "forcedVariations": {},
            "id": "6375231238",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment36",
            "trafficAllocation": [
                {"entityId": "6380164945", "endOfRange": 5000},
                {"entityId": "6380164946", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6380164945", "key": "control"}, {"id": "6380164946", "key": "variation"}],
            "forcedVariations": {},
            "id": "6375494974",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment45",
            "trafficAllocation": [
                {"entityId": "6374765096", "endOfRange": 5000},
                {"entityId": "6374765097", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6374765096", "key": "control"}, {"id": "6374765097", "key": "variation"}],
            "forcedVariations": {},
            "id": "6375595048",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment43",
            "trafficAllocation": [
                {"entityId": "6385191624", "endOfRange": 5000},
                {"entityId": "6385191625", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6385191624", "key": "control"}, {"id": "6385191625", "key": "variation"}],
            "forcedVariations": {},
            "id": "6376141968",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment25",
            "trafficAllocation": [
                {"entityId": "6368955066", "endOfRange": 5000},
                {"entityId": "6368955067", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6368955066", "key": "control"}, {"id": "6368955067", "key": "variation"}],
            "forcedVariations": {},
            "id": "6376658685",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment2",
            "trafficAllocation": [
                {"entityId": "6382040994", "endOfRange": 5000},
                {"entityId": "6382040995", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6382040994", "key": "control"}, {"id": "6382040995", "key": "variation"}],
            "forcedVariations": {"variation_user": "variation", "control_user": "control"},
            "id": "6377001018",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment18",
            "trafficAllocation": [
                {"entityId": "6370582521", "endOfRange": 5000},
                {"entityId": "6370582522", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6370582521", "key": "control"}, {"id": "6370582522", "key": "variation"}],
            "forcedVariations": {},
            "id": "6377202148",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment24",
            "trafficAllocation": [
                {"entityId": "6381612278", "endOfRange": 5000},
                {"entityId": "6381612279", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6381612278", "key": "control"}, {"id": "6381612279", "key": "variation"}],
            "forcedVariations": {},
            "id": "6377723605",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment19",
            "trafficAllocation": [
                {"entityId": "6362476361", "endOfRange": 5000},
                {"entityId": "6362476362", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6362476361", "key": "control"}, {"id": "6362476362", "key": "variation"}],
            "forcedVariations": {},
            "id": "6379205044",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment20",
            "trafficAllocation": [
                {"entityId": "6370537428", "endOfRange": 5000},
                {"entityId": "6370537429", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6370537428", "key": "control"}, {"id": "6370537429", "key": "variation"}],
            "forcedVariations": {},
            "id": "6379205045",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment28",
            "trafficAllocation": [
                {"entityId": "6387291313", "endOfRange": 5000},
                {"entityId": "6387291314", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6387291313", "key": "control"}, {"id": "6387291314", "key": "variation"}],
            "forcedVariations": {},
            "id": "6379841378",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment35",
            "trafficAllocation": [
                {"entityId": "6375332081", "endOfRange": 5000},
                {"entityId": "6375332082", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6375332081", "key": "control"}, {"id": "6375332082", "key": "variation"}],
            "forcedVariations": {},
            "id": "6379900650",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment1",
            "trafficAllocation": [
                {"entityId": "6355235181", "endOfRange": 5000},
                {"entityId": "6355235182", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6355235181", "key": "control"}, {"id": "6355235182", "key": "variation"}],
            "forcedVariations": {"variation_user": "variation", "control_user": "control"},
            "id": "6380251600",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment8",
            "trafficAllocation": [
                {"entityId": "6310506102", "endOfRange": 5000},
                {"entityId": "6310506103", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6310506102", "key": "control"}, {"id": "6310506103", "key": "variation"}],
            "forcedVariations": {},
            "id": "6380932373",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment3",
            "trafficAllocation": [
                {"entityId": "6373612240", "endOfRange": 5000},
                {"entityId": "6373612241", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6373612240", "key": "control"}, {"id": "6373612241", "key": "variation"}],
            "forcedVariations": {},
            "id": "6380971484",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment22",
            "trafficAllocation": [
                {"entityId": "6360796561", "endOfRange": 5000},
                {"entityId": "6360796562", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6360796561", "key": "control"}, {"id": "6360796562", "key": "variation"}],
            "forcedVariations": {},
            "id": "6381631585",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment37",
            "trafficAllocation": [
                {"entityId": "6356824684", "endOfRange": 5000},
                {"entityId": "6356824685", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6356824684", "key": "control"}, {"id": "6356824685", "key": "variation"}],
            "forcedVariations": {},
            "id": "6381732143",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment41",
            "trafficAllocation": [
                {"entityId": "6389170550", "endOfRange": 5000},
                {"entityId": "6389170551", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6389170550", "key": "control"}, {"id": "6389170551", "key": "variation"}],
            "forcedVariations": {},
            "id": "6381781177",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment27",
            "trafficAllocation": [
                {"entityId": "6372591085", "endOfRange": 5000},
                {"entityId": "6372591086", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6372591085", "key": "control"}, {"id": "6372591086", "key": "variation"}],
            "forcedVariations": {},
            "id": "6382300680",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment26",
            "trafficAllocation": [
                {"entityId": "6375602097", "endOfRange": 5000},
                {"entityId": "6375602098", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6375602097", "key": "control"}, {"id": "6375602098", "key": "variation"}],
            "forcedVariations": {},
            "id": "6382682166",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment9",
            "trafficAllocation": [
                {"entityId": "6376221556", "endOfRange": 5000},
                {"entityId": "6376221557", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6376221556", "key": "control"}, {"id": "6376221557", "key": "variation"}],
            "forcedVariations": {},
            "id": "6382950966",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment29",
            "trafficAllocation": [
                {"entityId": "6382070548", "endOfRange": 5000},
                {"entityId": "6382070549", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6382070548", "key": "control"}, {"id": "6382070549", "key": "variation"}],
            "forcedVariations": {},
            "id": "6383120500",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment32",
            "trafficAllocation": [
                {"entityId": "6391210101", "endOfRange": 5000},
                {"entityId": "6391210102", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6391210101", "key": "control"}, {"id": "6391210102", "key": "variation"}],
            "forcedVariations": {},
            "id": "6383430268",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment30",
            "trafficAllocation": [
                {"entityId": "6364835927", "endOfRange": 5000},
                {"entityId": "6364835928", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6364835927", "key": "control"}, {"id": "6364835928", "key": "variation"}],
            "forcedVariations": {},
            "id": "6384711622",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment34",
            "trafficAllocation": [
                {"entityId": "6390151025", "endOfRange": 5000},
                {"entityId": "6390151026", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6390151025", "key": "control"}, {"id": "6390151026", "key": "variation"}],
            "forcedVariations": {},
            "id": "6384861073",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment21",
            "trafficAllocation": [
                {"entityId": "6384881124", "endOfRange": 5000},
                {"entityId": "6384881125", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6384881124", "key": "control"}, {"id": "6384881125", "key": "variation"}],
            "forcedVariations": {},
            "id": "6385551136",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment40",
            "trafficAllocation": [
                {"entityId": "6387261935", "endOfRange": 5000},
                {"entityId": "6387261936", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6387261935", "key": "control"}, {"id": "6387261936", "key": "variation"}],
            "forcedVariations": {},
            "id": "6387252155",
        },
        {
            "status": "Running",
            "percentageIncluded": 10000,
            "key": "testExperiment5",
            "trafficAllocation": [
                {"entityId": "6312093242", "endOfRange": 5000},
                {"entityId": "6312093243", "endOfRange": 10000},
            ],
            "audienceIds": [],
            "variations": [{"id": "6312093242", "key": "control"}, {"id": "6312093243", "key": "variation"}],
            "forcedVariations": {},
            "id": "6388170688",
        },
    ],
    "version": "1",
    "audiences": [
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"android\"}]]]",
            "id": "6366023138",
            "name": "Android users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"firefox\"}]]]",
            "id": "6373742627",
            "name": "Firefox users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"ie\"}]]]",
            "id": "6376161539",
            "name": "IE users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"desktop\"}]]]",
            "id": "6376714797",
            "name": "Desktop users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"safari\"}]]]",
            "id": "6381732153",
            "name": "Safari users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"opera\"}]]]",
            "id": "6383110825",
            "name": "Opera users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"tablet\"}]]]",
            "id": "6387291324",
            "name": "Tablet users",
        },
        {
            "conditions": "[\"and\", [\"or\", [\"or\", {\"name\": \"browser_type\", "
            "\"type\": \"custom_dimension\", \"value\": \"chrome\"}]]]",
            "id": "6388221254",
            "name": "Chrome users",
        },
    ],
    "dimensions": [{"id": "6380961481", "key": "browser_type", "segmentId": "6384711633"}],
    "groups": [
        {
            "policy": "random",
            "trafficAllocation": [
                {"entityId": "6454500206", "endOfRange": 5000},
                {"entityId": "6456310069", "endOfRange": 10000},
            ],
            "experiments": [
                {
                    "status": "Running",
                    "percentageIncluded": 5000,
                    "key": "mutex_exp1",
                    "trafficAllocation": [
                        {"entityId": "6413061880", "endOfRange": 5000},
                        {"entityId": "6413061881", "endOfRange": 10000},
                    ],
                    "audienceIds": ["6388221254"],
                    "variations": [{"id": "6413061880", "key": "a"}, {"id": "6413061881", "key": "b"}],
                    "forcedVariations": {},
                    "id": "6454500206",
                },
                {
                    "status": "Running",
                    "percentageIncluded": 5000,
                    "key": "mutex_exp2",
                    "trafficAllocation": [
                        {"entityId": "6445960276", "endOfRange": 5000},
                        {"entityId": "6445960277", "endOfRange": 10000},
                    ],
                    "audienceIds": [],
                    "variations": [{"id": "6445960276", "key": "a"}, {"id": "6445960277", "key": "b"}],
                    "forcedVariations": {"user_b": "b", "user_a": "a"},
                    "id": "6456310069",
                },
            ],
            "id": "6455220163",
        }
    ],
    "projectId": "6372300739",
    "accountId": "6365361536",
    "events": [
        {"experimentIds": ["6359356006"], "id": "6357247504", "key": "testEventWithAudiences"},
        {"experimentIds": ["6456310069"], "id": "6357622693", "key": "testEventWithMultipleGroupedExperiments"},
        {"experimentIds": ["6375231238"], "id": "6367473109", "key": "testEventWithExperimentNotRunning"},
        {"experimentIds": ["6380251600"], "id": "6370537431", "key": "testEvent"},
        {"experimentIds": [], "id": "6377001020", "key": "testEventWithoutExperiments"},
        {
            "experimentIds": [
                "6375231238",
                "6364882055",
                "6382300680",
                "6374064265",
                "6363607946",
                "6370815084",
                "6360796560",
                "6384861073",
                "6380932373",
                "6385551136",
                "6376141968",
                "6375595048",
                "6384711622",
                "6381732143",
                "6332666164",
                "6379205045",
                "6382682166",
                "6313973431",
                "6381781177",
                "6377001018",
                "6387252155",
                "6375494974",
                "6338678719",
                "6388170688",
                "6456310069",
                "6362476358",
                "6362476359",
                "6379205044",
                "6382950966",
                "6371742027",
                "6367922509",
                "6380251600",
                "6355784786",
                "6377723605",
                "6366023126",
                "6380971484",
                "6381631585",
                "6379841378",
                "6377202148",
                "6361743077",
                "6359356006",
                "6379900650",
                "6361359596",
                "6454500206",
                "6383120500",
                "6367902584",
                "6338678718",
                "6383430268",
                "6376658685",
                "6369992702",
            ],
            "id": "6385432091",
            "key": "testEventWithMultipleExperiments",
        },
        {"experimentIds": ["6377001018", "6359356006", "6454500206"], "id": "6370815083", "key": "Total Revenue"},
    ],
    "revision": "58",
}

datafiles = {10: config_10_exp, 25: config_25_exp, 50: config_50_exp}


def create_optimizely_object(datafile):
    """ Helper method to create and return Optimizely object. """

    class NoOpEventDispatcher(object):
        @staticmethod
        def dispatch_event(url, params):
            """ No op event dispatcher.

      Args:
        url: URL to send impression/conversion event to.
        params: Params to be sent to the impression/conversion event.
      """

        pass

    return optimizely.Optimizely(datafile, event_dispatcher=NoOpEventDispatcher)


optimizely_obj_10_exp = create_optimizely_object(json.dumps(datafiles.get(10)))
optimizely_obj_25_exp = create_optimizely_object(json.dumps(datafiles.get(25)))
optimizely_obj_50_exp = create_optimizely_object(json.dumps(datafiles.get(50)))

test_data = {
    'create_object': {10: [datafiles.get(10)], 25: [datafiles.get(25)], 50: [datafiles.get(50)]},
    'create_object_schema_validation_off': {10: [datafiles.get(10)], 25: [datafiles.get(25)], 50: [datafiles.get(50)]},
    'activate_with_no_attributes': {
        10: [optimizely_obj_10_exp, 'test'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'activate_with_attributes': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'test'],
    },
    'activate_with_forced_variation': {
        10: [optimizely_obj_10_exp, 'variation_user'],
        25: [optimizely_obj_25_exp, 'variation_user'],
        50: [optimizely_obj_50_exp, 'variation_user'],
    },
    'activate_grouped_experiment_no_attributes': {
        10: [optimizely_obj_10_exp, 'no'],
        25: [optimizely_obj_25_exp, 'test'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'activate_grouped_experiment_with_attributes': {
        10: [optimizely_obj_10_exp, 'test'],
        25: [optimizely_obj_25_exp, 'yes'],
        50: [optimizely_obj_50_exp, 'test'],
    },
    'get_variation_with_no_attributes': {
        10: [optimizely_obj_10_exp, 'test'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'get_variation_with_attributes': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'test'],
    },
    'get_variation_with_forced_variation': {
        10: [optimizely_obj_10_exp, 'variation_user'],
        25: [optimizely_obj_25_exp, 'variation_user'],
        50: [optimizely_obj_50_exp, 'variation_user'],
    },
    'get_variation_grouped_experiment_no_attributes': {
        10: [optimizely_obj_10_exp, 'no'],
        25: [optimizely_obj_25_exp, 'test'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'get_variation_grouped_experiment_with_attributes': {
        10: [optimizely_obj_10_exp, 'test'],
        25: [optimizely_obj_25_exp, 'yes'],
        50: [optimizely_obj_50_exp, 'test'],
    },
    'track_with_attributes': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'track_with_revenue': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'track_with_attributes_and_revenue': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'track_no_attributes_no_revenue': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'track_grouped_experiment': {
        10: [optimizely_obj_10_exp, 'no'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'track_grouped_experiment_with_attributes': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'yes'],
        50: [optimizely_obj_50_exp, 'test'],
    },
    'track_grouped_experiment_with_revenue': {
        10: [optimizely_obj_10_exp, 'no'],
        25: [optimizely_obj_25_exp, 'optimizely_user'],
        50: [optimizely_obj_50_exp, 'optimizely_user'],
    },
    'track_grouped_experiment_with_attributes_and_revenue': {
        10: [optimizely_obj_10_exp, 'optimizely_user'],
        25: [optimizely_obj_25_exp, 'yes'],
        50: [optimizely_obj_50_exp, 'test'],
    },
}
