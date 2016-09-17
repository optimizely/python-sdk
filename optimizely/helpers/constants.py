JSON_SCHEMA_V1 = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "projectId": {
      "type": "string"
    },
    "accountId": {
      "type": "string"
    },
    "groups": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "policy": {
            "type": "string"
          },
          "trafficAllocation": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "entityId": {
                  "type": "string"
                },
                "endOfRange": {
                  "type": "integer"
                }
              },
              "required": [
                "entityId",
                "endOfRange"
              ]
            }
          },
          "experiments": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "string"
                },
                "key": {
                  "type": "string"
                },
                "status": {
                  "type": "string"
                },
                "variations": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "string"
                      },
                      "key": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "id",
                      "key"
                    ]
                  }
                },
                "trafficAllocation": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "entityId": {
                        "type": "string"
                      },
                      "endOfRange": {
                        "type": "integer"
                      }
                    },
                    "required": [
                      "entityId",
                      "endOfRange"
                    ]
                  }
                },
                "audienceIds": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "forcedVariations": {
                  "type": "object"
                }
              },
              "required": [
                "id",
                "key",
                "status",
                "variations",
                "trafficAllocation",
                "audienceIds",
                "forcedVariations"
              ]
            }
          }
        },
        "required": [
          "id",
          "policy",
          "trafficAllocation",
          "experiments"
        ]
      },
    },
    "experiments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "key": {
            "type": "string"
          },
          "status": {
            "type": "string"
          },
          "variations": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "string"
                },
                "key": {
                  "type": "string"
                }
              },
              "required": [
                "id",
                "key"
              ]
            }
          },
          "trafficAllocation": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "entityId": {
                  "type": "string"
                },
                "endOfRange": {
                  "type": "integer"
                }
              },
              "required": [
                "entityId",
                "endOfRange"
              ]
            }
          },
          "audienceIds": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "forcedVariations": {
            "type": "object"
          }
        },
        "required": [
          "id",
          "key",
          "status",
          "variations",
          "trafficAllocation",
          "audienceIds",
          "forcedVariations"
        ]
      }
    },
    "events": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "key": {
            "type": "string"
          },
          "experimentIds": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "id": {
            "type": "string"
          }
        },
        "required": [
          "key",
          "experimentIds",
          "id"
        ]
      }
    },
    "audiences": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "conditions": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "conditions"
        ]
      }
    },
    "dimensions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "key": {
            "type": "string"
          },
          "segmentId": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "key",
          "segmentId",
        ]
      }
    },
    "version": {
      "type": "string"
    },
    "revision": {
      "type": "string"
    },
  },
  "required": [
    "projectId",
    "accountId",
    "groups",
    "experiments",
    "events",
    "audiences",
    "dimensions",
    "version",
    "revision",
  ]
}

JSON_SCHEMA_V2 = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "projectId": {
      "type": "string"
    },
    "accountId": {
      "type": "string"
    },
    "groups": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "policy": {
            "type": "string"
          },
          "trafficAllocation": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "entityId": {
                  "type": "string"
                },
                "endOfRange": {
                  "type": "integer"
                }
              },
              "required": [
                "entityId",
                "endOfRange"
              ]
            }
          },
          "experiments": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "string"
                },
                "layerId": {
                  "type": "string"
                },
                "key": {
                  "type": "string"
                },
                "status": {
                  "type": "string"
                },
                "variations": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "string"
                      },
                      "key": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "id",
                      "key"
                    ]
                  }
                },
                "trafficAllocation": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "entityId": {
                        "type": "string"
                      },
                      "endOfRange": {
                        "type": "integer"
                      }
                    },
                    "required": [
                      "entityId",
                      "endOfRange"
                    ]
                  }
                },
                "audienceIds": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "forcedVariations": {
                  "type": "object"
                }
              },
              "required": [
                "id",
                "layerId",
                "key",
                "status",
                "variations",
                "trafficAllocation",
                "audienceIds",
                "forcedVariations"
              ]
            }
          }
        },
        "required": [
          "id",
          "policy",
          "trafficAllocation",
          "experiments"
        ]
      },
    },
    "experiments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "layerId": {
            "type": "string"
          },
          "key": {
            "type": "string"
          },
          "status": {
            "type": "string"
          },
          "variations": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "string"
                },
                "key": {
                  "type": "string"
                }
              },
              "required": [
                "id",
                "key"
              ]
            }
          },
          "trafficAllocation": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "entityId": {
                  "type": "string"
                },
                "endOfRange": {
                  "type": "integer"
                }
              },
              "required": [
                "entityId",
                "endOfRange"
              ]
            }
          },
          "audienceIds": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "forcedVariations": {
            "type": "object"
          }
        },
        "required": [
          "id",
          "layerId",
          "key",
          "status",
          "variations",
          "trafficAllocation",
          "audienceIds",
          "forcedVariations"
        ]
      }
    },
    "events": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "key": {
            "type": "string"
          },
          "experimentIds": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "id": {
            "type": "string"
          }
        },
        "required": [
          "key",
          "experimentIds",
          "id"
        ]
      }
    },
    "audiences": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "conditions": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "conditions"
        ]
      }
    },
    "attributes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "key": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "key",
        ]
      }
    },
    "version": {
      "type": "string"
    },
    "revision": {
      "type": "string"
    },
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
  ]
}
