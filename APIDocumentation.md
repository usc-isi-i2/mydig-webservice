The mydig-webservice provides certain APIs to query the data from the knowledge graph.
The first API is the Conjuctive Query API -

A typical invocation looks like this:
```
<digurl>/search?name=fred&city="los angeles"&date$less-equal-than=2017-12-15&country/key=france&_fields=name,email,phone&_format=jsonlines
```

There are two types of query parameters:

- fields: names of fields defined in the myDIG specification
- underscore parameters: modify the search

The `dot` modifier to fields specify where to match the value:

- `field/key`: searches on the key attribute of the field
- `field/value`: searches on the value attribute of the field
- `field`: searches on the value, so the default is to search the value if no modifier is provided

The `$` modifier is used to specify additional constraints:

- `field$less-than`, `field$less-equal-than`, `field$greater-than`, `field$greater-equal-than`: used to produce range constrains

The underscore parameters specify modifiers to the query:

- `_fields`: specifies which fields to return, if not given, all fields are returned, the value is a comma-separated list of fields
- `_size`: specifies how many records to return. If not specified, return 20
- `_order-by`: a set of fields specifies fields to use as sort criteria, with modifiers such as `name$desc` or `name$asc`
- `_format`: specifies how to format the query results, the possible values are `json` to produce an array of JSON objects, `jsonlines` to produce a sequence of JSON lines, one object per line
- `_verbosity`: specifies how much data for each KG object to return, the possible values are `minimal` to return a compact representation, stripping provenance and returning the `value` attribute, `full` to return the original format of the KN object
- `_statistics`: specifies whether to return statistics about the query execution, like in elastic search, possible values are `no` to return no statistics so that the payload contains only the KG objects, `yes` returns time to execute, etc like in elastic search (this option is ignored if the format is other than JSON.

The query also would do a nested filter which would be of the format - 
`field_name.nested_field`: searches on the nested_field attribute of the field_name in the KG.
This is to query directly on certain nested fields which will be flattened to the form field_name_ _ nested_field in the KG. 
For example : size field. 
fatalities.size will be flattened as fatalities _ _ size in the KG. and this nested query can be performed by specifying fatalities.size=value in the input query
```
Ex: search?country/value=nigeria&fatalities.size=10
```

The API returns the following codes:

- 200 for success
- 401 for authorization problems
- 400 if the query cannot be parsed, e.g., invalid underscore arguments, unmatched quotes, uses a field name node defined in myDIG 
- 500 for other internal errors.

Some examples: 
Let's consider the ACLED dataset to show some simple queries. The following queries are possible once the ACLED data is loaded 
into the knowledge Graph.

Let's try a simple query to fetch all acled documents.

```
http://<mydigurl>/mydig/search/sage?website/value=acleddata.com&_size=1
```
Sample response looks like: 
```
   {
  "hits": {
    "hits": [
      {
        "_score": 0.00012595252,
        "_type": "ads",
        "_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0",
        "_source": {
          "event_type": [
            "Riots/Protests",
            "MILITARY VERSUS RIOTERS"
          ],
          "event_death_count": 0,
          "event_title": "A police constable on duty was allegedly assaulted...",
          "@timestamp": "2018-01-11T09:32:44.439Z",
          "content_extraction": {
            "url": {
              "text": "www.acleddata.com",
              "simple_tokens": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ],
              "simple_tokens_original_case": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ]
            },
            "event_date": [
              {
                "text": "2017-03-29T00:00:00",
                "simple_tokens": [
                  "2017",
                  "-",
                  "03",
                  "-",
                  "29t00",
                  ":",
                  "00",
                  ":",
                  "00"
                ],
                "simple_tokens_original_case": [
                  "2017",
                  "-",
                  "03",
                  "-",
                  "29T00",
                  ":",
                  "00",
                  ":",
                  "00"
                ]
              }
            ],
            "content_strict": {
              "text": ".",
              "simple_tokens": [
                "."
              ],
              "simple_tokens_original_case": [
                "."
              ]
            },
            "event_type": [
              {
                "text": "Riots/Protests",
                "simple_tokens": [
                  "riots",
                  "/",
                  "protests"
                ],
                "simple_tokens_original_case": [
                  "Riots",
                  "/",
                  "Protests"
                ]
              },
              {
                "text": "MILITARY VERSUS RIOTERS",
                "simple_tokens": [
                  "military",
                  "versus",
                  "rioters"
                ],
                "simple_tokens_original_case": [
                  "MILITARY",
                  "VERSUS",
                  "RIOTERS"
                ]
              }
            ],
            "title": {
              "text": "",
              "simple_tokens": [],
              "simple_tokens_original_case": []
            }
          },
          "event_location": {
            "key": "Amritsar:x:India:74.8728:31.6344",
            "value": "Amritsar,India"
          },
          "event_description": "A police constable on duty was allegedly assaulted by several persons, include former sarpanch of Fatehgarh Shukar Chak village, who were armed with hockey sticks and baseball bats. The victim reached near Mahraja Garden on the Majitha-Verka bypass road in Amritsar when a speeding SUV hit him following which he fell down. Without any provocation, the accused came out of the vehicle and started thrashing him",
          "event_actors": [
            {
              "title": "Rioters (India)",
              "description": "Rioters",
              "id": "indiariotersrioters"
            },
            {
              "title": "Police Forces of India",
              "description": "Government or mutinous force",
              "id": "forceforcesgovernmentindiamutinousoforpolice"
            }
          ],
          "knowledge_graph": {
            "website": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "url",
                      "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_website_domain",
                    "extracted_value": "acleddata.com"
                  }
                ],
                "key": "acleddata.com",
                "value": "acleddata.com"
              }
            ],
            "url": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.url.[0]",
                      "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "www.acleddata.com"
                  },
                  {
                    "source": {
                      "segment": "content_extraction.url.[0]",
                      "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "www.acleddata.com"
                  }
                ],
                "key": "www.acleddata.com",
                "value": "www.acleddata.com"
              }
            ],
            "description": [
              {
                "confidence": 1,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_strict",
                      "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "method": "rearrange_description"
                  }
                ],
                "key": "description",
                "value": "."
              }
            ],
            "event_date": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_date.[0]",
                      "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "2017-03-29T00:00:00"
                  }
                ],
                "key": "2017-03-29t00:00:00",
                "value": "2017-03-29T00:00:00"
              }
            ],
            "event_type": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_type.[0]",
                      "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "Riots/Protests"
                  }
                ],
                "key": "riots/protests",
                "value": "Riots/Protests"
              },
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_type.[1]",
                      "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "MILITARY VERSUS RIOTERS"
                  }
                ],
                "key": "military versus rioters",
                "value": "MILITARY VERSUS RIOTERS"
              }
            ]
          },
          "document_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0",
          "indexed": {
            "website": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "acleddata.com",
                    "value": "acleddata.com"
                  }
                ]
              }
            },
            "url": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "www.acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "www.acleddata.com",
                    "value": "www.acleddata.com"
                  }
                ]
              }
            },
            "description": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "description"
              ],
              "key_count": 1,
              "other_method": {
                "content_strict": [
                  {
                    "key": "description",
                    "value": "."
                  }
                ]
              }
            },
            "event_date": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "2017-03-29t00:00:00"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "2017-03-29t00:00:00",
                    "value": "2017-03-29T00:00:00"
                  }
                ]
              }
            },
            "event_type": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "military versus rioters",
                "riots/protests"
              ],
              "key_count": 2,
              "other_method": {
                "other_segment": [
                  {
                    "key": "riots/protests",
                    "value": "Riots/Protests"
                  },
                  {
                    "key": "military versus rioters",
                    "value": "MILITARY VERSUS RIOTERS"
                  }
                ]
              }
            }
          },
          "event_date": "2017-03-29T00:00:00",
          "type": "sage_complete",
          "timestamp_crawl": "2018-01-11T09:28:46.595157",
          "event_references": [
            "The Tribune"
          ],
          "@execution_profile": {
            "@doc_processed_time": 0.010957002639770508,
            "@run_core_time": 0.010820865631103516,
            "@doc_arrived_time": "2018-01-11T09:32:38.605061",
            "@worker_id": 0,
            "@doc_length": 1274,
            "@doc_sent_time": "2018-01-11T09:32:38.616018",
            "@doc_wait_time": 0.7657411098480225,
            "@etk_start_time": "2018-01-11T09:32:38.605198",
            "@etk_end_time": "2018-01-11T09:32:38.615945",
            "@etk_process_time": 0.010747194290161133
          },
          "url": "www.acleddata.com",
          "doc_id": "39c420b6-c67c-11e7-a6cc-cc2f7122e7f0",
          "raw_content": ".",
          "prefilter_filter_outcome": "no_action",
          "tld": "acleddata.com",
          "@version": "1"
        },
        "_index": "sage_complete"
      }
    ],
    "total": 20000,
    "max_score": 0.00012595252
  },
  "_shards": {
    "successful": 5,
    "failed": 0,
    "skipped": 0,
    "total": 5
  },
  "took": 2,
  "timed_out": false
}
```
A sample query with sorting according to the `event_date` in ACLED data:
```
http://<mydigurl>/mydig/search/sage?website/value=acleddata.com&_size=5&event_date$greater-than=2012-01-01T00:00:00&_order-by=event_date$asc&_fields=event_date
```
The response is given below:
```
{
  "hits": {
    "hits": [
      {
        "sort": [
          1325462400000
        ],
        "_type": "ads",
        "_source": {
          "event_type": [
            "Riots/Protests",
            "SOLE PROTESTER ACTION"
          ],
          "event_death_count": 0,
          "event_title": "Residents protest enters its third day...",
          "@timestamp": "2018-01-11T09:49:34.419Z",
          "content_extraction": {
            "url": {
              "text": "www.acleddata.com",
              "simple_tokens": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ],
              "simple_tokens_original_case": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ]
            },
            "event_date": [
              {
                "text": "2012-01-02T00:00:00",
                "simple_tokens": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "02t00",
                  ":",
                  "00",
                  ":",
                  "00"
                ],
                "simple_tokens_original_case": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "02T00",
                  ":",
                  "00",
                  ":",
                  "00"
                ]
              }
            ],
            "content_strict": {
              "text": ".",
              "simple_tokens": [
                "."
              ],
              "simple_tokens_original_case": [
                "."
              ]
            },
            "event_type": [
              {
                "text": "Riots/Protests",
                "simple_tokens": [
                  "riots",
                  "/",
                  "protests"
                ],
                "simple_tokens_original_case": [
                  "Riots",
                  "/",
                  "Protests"
                ]
              },
              {
                "text": "SOLE PROTESTER ACTION",
                "simple_tokens": [
                  "sole",
                  "protester",
                  "action"
                ],
                "simple_tokens_original_case": [
                  "SOLE",
                  "PROTESTER",
                  "ACTION"
                ]
              }
            ],
            "title": {
              "text": "",
              "simple_tokens": [],
              "simple_tokens_original_case": []
            }
          },
          "event_location": {
            "key": "Douala:x:Cameroon:9.70840:4.04690",
            "value": "Douala,Cameroon"
          },
          "event_description": "Residents protest enters its third day",
          "event_actors": [
            {
              "title": "Protesters (Cameroon)",
              "description": "Protesters",
              "id": "cameroonprotestersprotesters"
            },
            {
              "title": "",
              "description": "",
              "id": ""
            }
          ],
          "knowledge_graph": {
            "event_date": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_date.[0]",
                      "document_id": "3e680d13-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "2012-01-02T00:00:00"
                  }
                ],
                "key": "2012-01-02t00:00:00",
                "value": "2012-01-02T00:00:00"
              }
            ]
          },
          "document_id": "3e680d13-c67c-11e7-a6cc-cc2f7122e7f0",
          "indexed": {
            "website": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "acleddata.com",
                    "value": "acleddata.com"
                  }
                ]
              }
            },
            "url": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "www.acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "www.acleddata.com",
                    "value": "www.acleddata.com"
                  }
                ]
              }
            },
            "description": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "description"
              ],
              "key_count": 1,
              "other_method": {
                "content_strict": [
                  {
                    "key": "description",
                    "value": "."
                  }
                ]
              }
            },
            "event_date": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "2012-01-02t00:00:00"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "2012-01-02t00:00:00",
                    "value": "2012-01-02T00:00:00"
                  }
                ]
              }
            },
            "event_type": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "riots/protests",
                "sole protester action"
              ],
              "key_count": 2,
              "other_method": {
                "other_segment": [
                  {
                    "key": "riots/protests",
                    "value": "Riots/Protests"
                  },
                  {
                    "key": "sole protester action",
                    "value": "SOLE PROTESTER ACTION"
                  }
                ]
              }
            }
          },
          "event_date": "2012-01-02T00:00:00",
          "type": "sage_complete",
          "timestamp_crawl": "2018-01-11T09:29:07.020280",
          "event_references": [
            "CNN Wire"
          ],
          "@execution_profile": {
            "@doc_processed_time": 0.006161928176879883,
            "@run_core_time": 0.006073951721191406,
            "@doc_arrived_time": "2018-01-11T09:49:34.410284",
            "@worker_id": 0,
            "@doc_length": 814,
            "@doc_sent_time": "2018-01-11T09:49:34.416446",
            "@doc_wait_time": 0.0037610530853271484,
            "@etk_start_time": "2018-01-11T09:49:34.410373",
            "@etk_end_time": "2018-01-11T09:49:34.416383",
            "@etk_process_time": 0.0060100555419921875
          },
          "url": "www.acleddata.com",
          "doc_id": "3e680d13-c67c-11e7-a6cc-cc2f7122e7f0",
          "raw_content": ".",
          "prefilter_filter_outcome": "no_action",
          "tld": "acleddata.com",
          "@version": "1"
        },
        "_score": null,
        "_index": "sage_complete",
        "_id": "3e680d13-c67c-11e7-a6cc-cc2f7122e7f0"
      },
      {
        "sort": [
          1325462400000
        ],
        "_type": "ads",
        "_source": {
          "event_type": [
            "Strategic development",
            "SOLE POLITICAL MILITIA ACTION"
          ],
          "event_death_count": 0,
          "event_title": "Cache of weaponry discovered in several Ugandan villages...",
          "@timestamp": "2018-01-11T10:19:19.751Z",
          "content_extraction": {
            "url": {
              "text": "www.acleddata.com",
              "simple_tokens": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ],
              "simple_tokens_original_case": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ]
            },
            "event_date": [
              {
                "text": "2012-01-02T00:00:00",
                "simple_tokens": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "02t00",
                  ":",
                  "00",
                  ":",
                  "00"
                ],
                "simple_tokens_original_case": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "02T00",
                  ":",
                  "00",
                  ":",
                  "00"
                ]
              }
            ],
            "content_strict": {
              "text": ".",
              "simple_tokens": [
                "."
              ],
              "simple_tokens_original_case": [
                "."
              ]
            },
            "event_type": [
              {
                "text": "Strategic development",
                "simple_tokens": [
                  "strategic",
                  "development"
                ],
                "simple_tokens_original_case": [
                  "Strategic",
                  "development"
                ]
              },
              {
                "text": "SOLE POLITICAL MILITIA ACTION",
                "simple_tokens": [
                  "sole",
                  "political",
                  "militia",
                  "action"
                ],
                "simple_tokens_original_case": [
                  "SOLE",
                  "POLITICAL",
                  "MILITIA",
                  "ACTION"
                ]
              }
            ],
            "title": {
              "text": "",
              "simple_tokens": [],
              "simple_tokens_original_case": []
            }
          },
          "event_location": {
            "key": "Kucwiny:x:Uganda:31.23968:2.55246",
            "value": "Kucwiny,Uganda"
          },
          "event_description": "Cache of weaponry discovered in several Ugandan villages",
          "event_actors": [
            {
              "title": "Unidentified Armed Group (Uganda)",
              "description": "Political militia",
              "id": "armedgroupmilitiapoliticalugandaunidentified"
            },
            {
              "title": "",
              "description": "",
              "id": ""
            }
          ],
          "knowledge_graph": {
            "event_date": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_date.[0]",
                      "document_id": "4da13c09-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "2012-01-02T00:00:00"
                  }
                ],
                "key": "2012-01-02t00:00:00",
                "value": "2012-01-02T00:00:00"
              }
            ]
          },
          "document_id": "4da13c09-c67c-11e7-a6cc-cc2f7122e7f0",
          "indexed": {
            "website": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "acleddata.com",
                    "value": "acleddata.com"
                  }
                ]
              }
            },
            "url": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "www.acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "www.acleddata.com",
                    "value": "www.acleddata.com"
                  }
                ]
              }
            },
            "description": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "description"
              ],
              "key_count": 1,
              "other_method": {
                "content_strict": [
                  {
                    "key": "description",
                    "value": "."
                  }
                ]
              }
            },
            "event_date": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "2012-01-02t00:00:00"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "2012-01-02t00:00:00",
                    "value": "2012-01-02T00:00:00"
                  }
                ]
              }
            },
            "event_type": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "strategic development",
                "sole political militia action"
              ],
              "key_count": 2,
              "other_method": {
                "other_segment": [
                  {
                    "key": "strategic development",
                    "value": "Strategic development"
                  },
                  {
                    "key": "sole political militia action",
                    "value": "SOLE POLITICAL MILITIA ACTION"
                  }
                ]
              }
            }
          },
          "event_date": "2012-01-02T00:00:00",
          "type": "sage_complete",
          "timestamp_crawl": "2018-01-11T09:31:10.288586",
          "event_references": [
            "All Africa"
          ],
          "@execution_profile": {
            "@doc_processed_time": 0.007862091064453125,
            "@run_core_time": 0.007745981216430664,
            "@doc_arrived_time": "2018-01-11T10:19:18.633524",
            "@worker_id": 0,
            "@doc_length": 898,
            "@doc_sent_time": "2018-01-11T10:19:18.641386",
            "@doc_wait_time": 0.4749898910522461,
            "@etk_start_time": "2018-01-11T10:19:18.633640",
            "@etk_end_time": "2018-01-11T10:19:18.641288",
            "@etk_process_time": 0.007647991180419922
          },
          "url": "www.acleddata.com",
          "doc_id": "4da13c09-c67c-11e7-a6cc-cc2f7122e7f0",
          "raw_content": ".",
          "prefilter_filter_outcome": "no_action",
          "tld": "acleddata.com",
          "@version": "1"
        },
        "_score": null,
        "_index": "sage_complete",
        "_id": "4da13c09-c67c-11e7-a6cc-cc2f7122e7f0"
      },
      {
        "sort": [
          1325548800000
        ],
        "_type": "ads",
        "_source": {
          "event_type": [
            "Riots/Protests",
            "SOLE PROTESTER ACTION"
          ],
          "event_death_count": 0,
          "event_title": "Protesters gather to denounce the end of an...",
          "@timestamp": "2018-01-11T10:14:07.323Z",
          "content_extraction": {
            "url": {
              "text": "www.acleddata.com",
              "simple_tokens": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ],
              "simple_tokens_original_case": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ]
            },
            "event_date": [
              {
                "text": "2012-01-03T00:00:00",
                "simple_tokens": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "03t00",
                  ":",
                  "00",
                  ":",
                  "00"
                ],
                "simple_tokens_original_case": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "03T00",
                  ":",
                  "00",
                  ":",
                  "00"
                ]
              }
            ],
            "content_strict": {
              "text": ".",
              "simple_tokens": [
                "."
              ],
              "simple_tokens_original_case": [
                "."
              ]
            },
            "event_type": [
              {
                "text": "Riots/Protests",
                "simple_tokens": [
                  "riots",
                  "/",
                  "protests"
                ],
                "simple_tokens_original_case": [
                  "Riots",
                  "/",
                  "Protests"
                ]
              },
              {
                "text": "SOLE PROTESTER ACTION",
                "simple_tokens": [
                  "sole",
                  "protester",
                  "action"
                ],
                "simple_tokens_original_case": [
                  "SOLE",
                  "PROTESTER",
                  "ACTION"
                ]
              }
            ],
            "title": {
              "text": "",
              "simple_tokens": [],
              "simple_tokens_original_case": []
            }
          },
          "event_location": {
            "key": "Makurdi:x:Nigeria:8.51210:7.74110",
            "value": "Makurdi,Nigeria"
          },
          "event_description": "Protesters gather to denounce the end of an oil subsidy",
          "event_actors": [
            {
              "title": "Protesters (Nigeria)",
              "description": "Protesters",
              "id": "nigeriaprotestersprotesters"
            },
            {
              "title": "",
              "description": "",
              "id": ""
            }
          ],
          "knowledge_graph": {
            "event_date": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_date.[0]",
                      "document_id": "4510b7bf-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "2012-01-03T00:00:00"
                  }
                ],
                "key": "2012-01-03t00:00:00",
                "value": "2012-01-03T00:00:00"
              }
            ]
          },
          "document_id": "4510b7bf-c67c-11e7-a6cc-cc2f7122e7f0",
          "indexed": {
            "website": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "acleddata.com",
                    "value": "acleddata.com"
                  }
                ]
              }
            },
            "url": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "www.acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "www.acleddata.com",
                    "value": "www.acleddata.com"
                  }
                ]
              }
            },
            "description": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "description"
              ],
              "key_count": 1,
              "other_method": {
                "content_strict": [
                  {
                    "key": "description",
                    "value": "."
                  }
                ]
              }
            },
            "event_date": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "2012-01-03t00:00:00"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "2012-01-03t00:00:00",
                    "value": "2012-01-03T00:00:00"
                  }
                ]
              }
            },
            "event_type": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "riots/protests",
                "sole protester action"
              ],
              "key_count": 2,
              "other_method": {
                "other_segment": [
                  {
                    "key": "riots/protests",
                    "value": "Riots/Protests"
                  },
                  {
                    "key": "sole protester action",
                    "value": "SOLE PROTESTER ACTION"
                  }
                ]
              }
            }
          },
          "event_date": "2012-01-03T00:00:00",
          "type": "sage_complete",
          "timestamp_crawl": "2018-01-11T09:29:42.886300",
          "event_references": [
            "All Africa"
          ],
          "@execution_profile": {
            "@doc_processed_time": 0.006997108459472656,
            "@run_core_time": 0.0069141387939453125,
            "@doc_arrived_time": "2018-01-11T10:14:07.313346",
            "@worker_id": 0,
            "@doc_length": 835,
            "@doc_sent_time": "2018-01-11T10:14:07.320343",
            "@doc_wait_time": 0.004736900329589844,
            "@etk_start_time": "2018-01-11T10:14:07.313429",
            "@etk_end_time": "2018-01-11T10:14:07.320245",
            "@etk_process_time": 0.006815910339355469
          },
          "url": "www.acleddata.com",
          "doc_id": "4510b7bf-c67c-11e7-a6cc-cc2f7122e7f0",
          "raw_content": ".",
          "prefilter_filter_outcome": "no_action",
          "tld": "acleddata.com",
          "@version": "1"
        },
        "_score": null,
        "_index": "sage_complete",
        "_id": "4510b7bf-c67c-11e7-a6cc-cc2f7122e7f0"
      },
      {
        "sort": [
          1325548800000
        ],
        "_type": "ads",
        "_source": {
          "event_type": [
            "Riots/Protests",
            "SOLE PROTESTER ACTION"
          ],
          "event_death_count": 0,
          "event_title": "Protests took place in Okapi following the death...",
          "@timestamp": "2018-01-11T10:16:29.500Z",
          "content_extraction": {
            "url": {
              "text": "www.acleddata.com",
              "simple_tokens": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ],
              "simple_tokens_original_case": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ]
            },
            "event_date": [
              {
                "text": "2012-01-03T00:00:00",
                "simple_tokens": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "03t00",
                  ":",
                  "00",
                  ":",
                  "00"
                ],
                "simple_tokens_original_case": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "03T00",
                  ":",
                  "00",
                  ":",
                  "00"
                ]
              }
            ],
            "content_strict": {
              "text": ".",
              "simple_tokens": [
                "."
              ],
              "simple_tokens_original_case": [
                "."
              ]
            },
            "event_type": [
              {
                "text": "Riots/Protests",
                "simple_tokens": [
                  "riots",
                  "/",
                  "protests"
                ],
                "simple_tokens_original_case": [
                  "Riots",
                  "/",
                  "Protests"
                ]
              },
              {
                "text": "SOLE PROTESTER ACTION",
                "simple_tokens": [
                  "sole",
                  "protester",
                  "action"
                ],
                "simple_tokens_original_case": [
                  "SOLE",
                  "PROTESTER",
                  "ACTION"
                ]
              }
            ],
            "title": {
              "text": "",
              "simple_tokens": [],
              "simple_tokens_original_case": []
            }
          },
          "event_location": {
            "key": "Mambasa:x:Democratic Republic of Congo:29.03535:1.36010",
            "value": "Mambasa,Democratic Republic of Congo"
          },
          "event_description": "Protests took place in Okapi following the death of a secondary student who was beaten by police",
          "event_actors": [
            {
              "title": "Protesters (Democratic Republic of Congo)",
              "description": "Protesters",
              "id": "congodemocraticofprotestersprotestersrepublic"
            },
            {
              "title": "",
              "description": "",
              "id": ""
            }
          ],
          "knowledge_graph": {
            "event_date": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_date.[0]",
                      "document_id": "3ff54760-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "2012-01-03T00:00:00"
                  }
                ],
                "key": "2012-01-03t00:00:00",
                "value": "2012-01-03T00:00:00"
              }
            ]
          },
          "document_id": "3ff54760-c67c-11e7-a6cc-cc2f7122e7f0",
          "indexed": {
            "website": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "acleddata.com",
                    "value": "acleddata.com"
                  }
                ]
              }
            },
            "url": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "www.acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "www.acleddata.com",
                    "value": "www.acleddata.com"
                  }
                ]
              }
            },
            "description": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "description"
              ],
              "key_count": 1,
              "other_method": {
                "content_strict": [
                  {
                    "key": "description",
                    "value": "."
                  }
                ]
              }
            },
            "event_date": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "2012-01-03t00:00:00"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "2012-01-03t00:00:00",
                    "value": "2012-01-03T00:00:00"
                  }
                ]
              }
            },
            "event_type": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "riots/protests",
                "sole protester action"
              ],
              "key_count": 2,
              "other_method": {
                "other_segment": [
                  {
                    "key": "riots/protests",
                    "value": "Riots/Protests"
                  },
                  {
                    "key": "sole protester action",
                    "value": "SOLE PROTESTER ACTION"
                  }
                ]
              }
            }
          },
          "event_date": "2012-01-03T00:00:00",
          "type": "sage_complete",
          "timestamp_crawl": "2018-01-11T09:29:12.828938",
          "event_references": [
            "Radio Okapi"
          ],
          "@execution_profile": {
            "@doc_processed_time": 0.010419845581054688,
            "@run_core_time": 0.010250091552734375,
            "@doc_arrived_time": "2018-01-11T10:16:29.285164",
            "@worker_id": 0,
            "@doc_length": 962,
            "@doc_sent_time": "2018-01-11T10:16:29.295584",
            "@doc_wait_time": 0.6288840770721436,
            "@etk_start_time": "2018-01-11T10:16:29.285337",
            "@etk_end_time": "2018-01-11T10:16:29.295491",
            "@etk_process_time": 0.010154008865356445
          },
          "url": "www.acleddata.com",
          "doc_id": "3ff54760-c67c-11e7-a6cc-cc2f7122e7f0",
          "raw_content": ".",
          "prefilter_filter_outcome": "no_action",
          "tld": "acleddata.com",
          "@version": "1"
        },
        "_score": null,
        "_index": "sage_complete",
        "_id": "3ff54760-c67c-11e7-a6cc-cc2f7122e7f0"
      },
      {
        "sort": [
          1325635200000
        ],
        "_type": "ads",
        "_source": {
          "event_type": [
            "Battle-No change of territory",
            "COMMUNAL MILITIA VERSUS COMMUNAL MILITIA"
          ],
          "event_death_count": 6,
          "event_title": "At six people, including three children, were killed...",
          "@timestamp": "2018-01-11T10:15:53.346Z",
          "content_extraction": {
            "url": {
              "text": "www.acleddata.com",
              "simple_tokens": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ],
              "simple_tokens_original_case": [
                "www",
                ".",
                "acleddata",
                ".",
                "com"
              ]
            },
            "event_date": [
              {
                "text": "2012-01-04T00:00:00",
                "simple_tokens": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "04t00",
                  ":",
                  "00",
                  ":",
                  "00"
                ],
                "simple_tokens_original_case": [
                  "2012",
                  "-",
                  "01",
                  "-",
                  "04T00",
                  ":",
                  "00",
                  ":",
                  "00"
                ]
              }
            ],
            "content_strict": {
              "text": ".",
              "simple_tokens": [
                "."
              ],
              "simple_tokens_original_case": [
                "."
              ]
            },
            "event_type": [
              {
                "text": "Battle-No change of territory",
                "simple_tokens": [
                  "battle",
                  "-",
                  "no",
                  "change",
                  "of",
                  "territory"
                ],
                "simple_tokens_original_case": [
                  "Battle",
                  "-",
                  "No",
                  "change",
                  "of",
                  "territory"
                ]
              },
              {
                "text": "COMMUNAL MILITIA VERSUS COMMUNAL MILITIA",
                "simple_tokens": [
                  "communal",
                  "militia",
                  "versus",
                  "communal",
                  "militia"
                ],
                "simple_tokens_original_case": [
                  "COMMUNAL",
                  "MILITIA",
                  "VERSUS",
                  "COMMUNAL",
                  "MILITIA"
                ]
              }
            ],
            "title": {
              "text": "",
              "simple_tokens": [],
              "simple_tokens_original_case": []
            }
          },
          "event_location": {
            "key": "Moyale:x:Kenya:39.05276:3.50937",
            "value": "Moyale,Kenya"
          },
          "event_description": "At six people, including three children, were killed in a tribal clash over grazing land and other resources in northeast Kenya near the Ethiopian border",
          "event_actors": [
            {
              "title": "Borana Ethnic Militia (Kenya)",
              "description": "Ethnic militia",
              "id": "boranaethnicethnickenyamilitiamilitia"
            },
            {
              "title": "Garba Ethnic Militia (Kenya)",
              "description": "Ethnic militia",
              "id": "ethnicethnicgarbakenyamilitiamilitia"
            }
          ],
          "knowledge_graph": {
            "event_date": [
              {
                "confidence": 1.0,
                "provenance": [
                  {
                    "source": {
                      "segment": "content_extraction.event_date.[0]",
                      "document_id": "42c9426b-c67c-11e7-a6cc-cc2f7122e7f0"
                    },
                    "confidence": {
                      "extraction": 1.0
                    },
                    "method": "extract_as_is",
                    "extracted_value": "2012-01-04T00:00:00"
                  }
                ],
                "key": "2012-01-04t00:00:00",
                "value": "2012-01-04T00:00:00"
              }
            ]
          },
          "document_id": "42c9426b-c67c-11e7-a6cc-cc2f7122e7f0",
          "indexed": {
            "website": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "acleddata.com",
                    "value": "acleddata.com"
                  }
                ]
              }
            },
            "url": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "www.acleddata.com"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "www.acleddata.com",
                    "value": "www.acleddata.com"
                  }
                ]
              }
            },
            "description": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "description"
              ],
              "key_count": 1,
              "other_method": {
                "content_strict": [
                  {
                    "key": "description",
                    "value": "."
                  }
                ]
              }
            },
            "event_date": {
              "provenance_count": 1,
              "high_confidence_keys": [
                "2012-01-04t00:00:00"
              ],
              "key_count": 1,
              "other_method": {
                "other_segment": [
                  {
                    "key": "2012-01-04t00:00:00",
                    "value": "2012-01-04T00:00:00"
                  }
                ]
              }
            },
            "event_type": {
              "provenance_count": 2,
              "high_confidence_keys": [
                "communal militia versus communal militia",
                "battle-no change of territory"
              ],
              "key_count": 2,
              "other_method": {
                "other_segment": [
                  {
                    "key": "battle-no change of territory",
                    "value": "Battle-No change of territory"
                  },
                  {
                    "key": "communal militia versus communal militia",
                    "value": "COMMUNAL MILITIA VERSUS COMMUNAL MILITIA"
                  }
                ]
              }
            }
          },
          "event_date": "2012-01-04T00:00:00",
          "type": "sage_complete",
          "timestamp_crawl": "2018-01-11T09:29:28.274958",
          "event_references": [
            "Agence France Presse"
          ],
          "@execution_profile": {
            "@doc_processed_time": 0.011421918869018555,
            "@run_core_time": 0.011255025863647461,
            "@doc_arrived_time": "2018-01-11T10:15:53.329415",
            "@worker_id": 0,
            "@doc_length": 1081,
            "@doc_sent_time": "2018-01-11T10:15:53.340837",
            "@doc_wait_time": 0.24850010871887207,
            "@etk_start_time": "2018-01-11T10:15:53.329641",
            "@etk_end_time": "2018-01-11T10:15:53.340752",
            "@etk_process_time": 0.011110782623291016
          },
          "url": "www.acleddata.com",
          "doc_id": "42c9426b-c67c-11e7-a6cc-cc2f7122e7f0",
          "raw_content": ".",
          "prefilter_filter_outcome": "no_action",
          "tld": "acleddata.com",
          "@version": "1"
        },
        "_score": null,
        "_index": "sage_complete",
        "_id": "42c9426b-c67c-11e7-a6cc-cc2f7122e7f0"
      }
    ],
    "total": 13374,
    "max_score": null
  },
  "_shards": {
    "successful": 5,
    "failed": 0,
    "skipped": 0,
    "total": 5
  },
  "took": 6,
  "timed_out": false
}
```
Applying verbosity to minimize the response size
```
http://<mydigurl>/mydig/search/sage?website/value=acleddata.com&_size=5&event_date$greater-than=2012-01-01T00:00:00&_order-by=event_date$asc&_fields=event_date&_verbosity=minimal

```

```
{
  "execution_time": 5,
  "hits": {
    "hits": [
      {
        "event_date": [
          {
            "value": "2012-01-02T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-02T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-03T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-03T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-04T00:00:00"
          }
        ]
      }
    ]
  },
  "hit_count": 13374
}
```

Same query above with no statistics
```
http://<mydigurl>/mydig/search/sage?website/value=acleddata.com&_size=5&event_date$greater-than=2012-01-01T00:00:00&_order-by=event_date$asc&_fields=event_date&_verbosity=minimal&_statistics=no

```
```
Notice the time taken and docs are removed away from response if statistics is a no

{
  "hits": {
    "hits": [
      {
        "event_date": [
          {
            "value": "2012-01-02T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-02T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-03T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-03T00:00:00"
          }
        ]
      },
      {
        "event_date": [
          {
            "value": "2012-01-04T00:00:00"
          }
        ]
      }
    ]
  }
}
```

Some advanced queries that can be performed on the dataset are dereferencing nested documents and also performing nested filters.
To run a query to dereference a nested field, lets consider a particular case. 
The below query can be run on the elicit_gtd dataset. 

In the query, we dereference a field called fatalities. This field has data that is stored in a separate document. The api will retrieve the documents and merge the responses together appropriately and return the response back.
Below is an example:
```
http://<mydigurl>/mydig/search/elicit_gtd?country/value=nigeria&_size=5&_fields=fatalities&_dereference=fatalities&_verbosity=minimal
```
Also note in the below response how setting `_verbosity` to `minimal` recursively simplifies the Knowledge Graph of the nested document as well.
```
{
  "execution_time": 7863,
  "hits": {
    "hits": [
      {
        "fatalities": [
          {
            "knowledge_graph": {
              "website": [
                {
                  "value": "umd.edu"
                }
              ],
              "title": [
                {
                  "value": "{\"doc_id\": \"26dc82eb5b18f029dd00e6f114c69f06594b899b\", \"size\": \"0\", \"title\": \"No Fatalities\", \"type\": [\"Consequence\", \"Group Of People\", \"Killed People\", \"Group Of Terrorists\", \"Empty Group\"]}"
                }
              ],
              "type": [
                {
                  "value": "Consequence"
                }
              ],
              "size": [
                {
                  "value": "0"
                }
              ]
            },
            "value": "26dc82eb5b18f029dd00e6f114c69f06594b899b"
          }
        ]
      },
      {
        "fatalities": [
          {
            "knowledge_graph": {
              "website": [
                {
                  "value": "umd.edu"
                }
              ],
              "title": [
                {
                  "value": "{\"doc_id\": \"26dc82eb5b18f029dd00e6f114c69f06594b899b\", \"size\": \"0\", \"title\": \"No Fatalities\", \"type\": [\"Consequence\", \"Group Of People\", \"Killed People\", \"Group Of Terrorists\", \"Empty Group\"]}"
                }
              ],
              "type": [
                {
                  "value": "Consequence"
                }
              ],
              "size": [
                {
                  "value": "0"
                }
              ]
            },
            "value": "26dc82eb5b18f029dd00e6f114c69f06594b899b"
          }
        ]
      },
      {
        "fatalities": [
          {
            "knowledge_graph": {
              "website": [
                {
                  "value": "umd.edu"
                }
              ],
              "title": [
                {
                  "value": "{\"doc_id\": \"26dc82eb5b18f029dd00e6f114c69f06594b899b\", \"size\": \"0\", \"title\": \"No Fatalities\", \"type\": [\"Consequence\", \"Group Of People\", \"Killed People\", \"Group Of Terrorists\", \"Empty Group\"]}"
                }
              ],
              "type": [
                {
                  "value": "Consequence"
                }
              ],
              "size": [
                {
                  "value": "0"
                }
              ]
            },
            "value": "26dc82eb5b18f029dd00e6f114c69f06594b899b"
          }
        ]
      },
      {
        "fatalities": [
          {
            "knowledge_graph": {
              "website": [
                {
                  "value": "umd.edu"
                }
              ],
              "title": [
                {
                  "value": "{\"doc_id\": \"26dc82eb5b18f029dd00e6f114c69f06594b899b\", \"size\": \"0\", \"title\": \"No Fatalities\", \"type\": [\"Consequence\", \"Group Of People\", \"Killed People\", \"Group Of Terrorists\", \"Empty Group\"]}"
                }
              ],
              "type": [
                {
                  "value": "Consequence"
                }
              ],
              "size": [
                {
                  "value": "0"
                }
              ]
            },
            "value": "26dc82eb5b18f029dd00e6f114c69f06594b899b"
          }
        ]
      },
      {
        "fatalities": [
          {
            "knowledge_graph": {
              "website": [
                {
                  "value": "umd.edu"
                }
              ],
              "title": [
                {
                  "value": "{\"doc_id\": \"26dc82eb5b18f029dd00e6f114c69f06594b899b\", \"size\": \"0\", \"title\": \"No Fatalities\", \"type\": [\"Consequence\", \"Group Of People\", \"Killed People\", \"Group Of Terrorists\", \"Empty Group\"]}"
                }
              ],
              "type": [
                {
                  "value": "Consequence"
                }
              ],
              "size": [
                {
                  "value": "0"
                }
              ]
            },
            "value": "26dc82eb5b18f029dd00e6f114c69f06594b899b"
          }
        ]
      }
    ]
  },
  "hit_count": 3418
}
```
