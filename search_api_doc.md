The mydig-webservice provides certain APIs to query the data from the knowledge graph.
The first API is the Conjuctive Query API -

A typical invocation looks like this:
```
http://<mydigurl>/mydig/projects/<project_name>/search/conjunctive?name=fred&city="los angeles"&date$less-equal-than=2017-12-15&country/key=france&_fields=name,email,phone&_format=jsonlines
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
- `_statistics`: specifies whether to return statistics about the query execution,returns time to execute, etc like in elastic search (this option is ignored if the format is other than JSON. Now there are three levels of verbosity `minimal` , `full` and `es`.
`minimal` - returns minified version of response with just values
`full` - returns the doc from the es without statistics
`es` - returns the complete response from es without alteration

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
http://<mydigurl>/mydig/projects/sage/search/conjunctive?website/value=acleddata.com&_size=1
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
http://<mydigurl>/mydig/projects/sage/search/conjunctive?website/value=acleddata.com&_size=5&event_date$greater-than=2012-01-01T00:00:00&_order-by=event_date$asc&_fields=event_date
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
      ...
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
http://<mydigurl>/mydig/projects/sage/search/conjunctive?website/value=acleddata.com&_size=5&event_date$greater-than=2012-01-01T00:00:00&_order-by=event_date$asc&_fields=event_date&_verbosity=minimal

```

```
[
  {
    "event_date": [
      "2012-06-08T00:00:00"
    ]
  },
 .
 .
 .
 .
 .
 .
  {
    "event_date": [
      "2013-01-26T00:00:00"
    ]
  }
]
```

Same query above with no statistics
```
http://<mydigurl>/mydig/projects/sage/search/conjunctive?website/value=acleddata.com&_size=5&event_date$greater-than=2012-01-01T00:00:00&_order-by=event_date$asc&_fields=event_date&_verbosity=minimal

```
```
Notice the time taken and docs are removed away from response if verbosity is not es.
[
  {
    "event_date": [
      "2012-06-08T00:00:00"
    ]
  },
  .
  .
  .
  .
  .
  .
  .
  .
  {
    "event_date": [
      "2013-01-26T00:00:00"
    ]
  }
]
```

Some advanced queries that can be performed on the dataset are dereferencing nested documents and also performing nested filters.
To run a query to dereference a nested field, lets consider a particular case. 
The below query can be run on the elicit_gtd dataset. 

In the query, we dereference a field called fatalities. This field has data that is stored in a separate document. The api will retrieve the documents and merge the responses together appropriately and return the response back.
Below is an example:
```
http://<mydigurl>/mydig/projects/elicit_gtd/search/conjunctive?country/value=nigeria&_size=5&_fields=fatalities&_dereference=fatalities&_verbosity=minimal
```
Also note in the below response how setting `_verbosity` to `minimal` recursively simplifies the Knowledge Graph of the nested document as well.
```
[
  {
    "fatalities": [
      {
        "website": [
          "umd.edu"
        ],
        "title": [
          "{\"doc_id\": \"26dc82eb5b18f029dd00e6f114c69f06594b899b\", \"size\": \"0\", \"title\": \"No Fatalities\", \"type\": [\"Consequence\", \"Group Of People\", \"Killed People\", \"Group Of Terrorists\", \"Empty Group\"]}"
        ],
        "type": [
          "Consequence"
        ],
        "size": [
          "0"
        ]
      }
    ]
  },
 .
 .
 .
 .
 .
 .
]
```

To perform some additional queries such as aggregations please read below:
Aggregations queries are supported in the current API. You can perform several type of queries like aggregation by date with varied intervals such as weekly,monthly etc. 
The accepted intervals are week,month,year,quarter,hour,minute,day,second
This can be specified as
```
http://<mydigurl>/mydig/projects/<project_name>/search/conjunctive?_group-by=date_field_here
```

You can also execute queries where the data is bucketed according to a string field/number field as well. In such scenarios a sub-aggregation is possible with sum,min,max,avg and count as the possibilities.

This can be specified as 
```
http://<mydigurl>/mydig/projects/<project_name>/search/conjunctive?_group-by=some_field&_aggregation-field=death_count
&_aggregation=avg
```
The above syntax can be used to execute aggregation queries using mydig.

Let us now consider some examples below

Example 1: Date histogram 
This query can be executed on the sage dataset with acled & pitf data loaded into it. Note how the earlier syntax of field/value=something is used to filter out the result and the aggregation is performed on the resultant subset.
```
http://<mydigurl>/mydig/projects/sage/search/conjunctive?_group-by=event_date&_interval=year&website/value=acleddata.com
```

```
{
  "hits": {
    "hits": [],
    "total": 100,
    "max_score": 0.0
  },
  "_shards": {
    "successful": 5,
    "failed": 0,
    "skipped": 0,
    "total": 5
  },
  "took": 2,
  "aggregations": {
    "event_date": {
      "buckets": [
        {
          "key_as_string": "1997-01-01T00:00:00.000Z",
          "key": 852076800000,
          "doc_count": 2
        },
        {
          "key_as_string": "1998-01-01T00:00:00.000Z",
          "key": 883612800000,
          "doc_count": 3
        },
        .
        .
        .
        .
        .

        {
          "key_as_string": "2017-01-01T00:00:00.000Z",
          "key": 1483228800000,
          "doc_count": 17
        }
      ]
    }
  },
  "timed_out": false
}
```

Example 2 : Performing bucket aggregation with a string field
```
http://<mydigurl>/mydig/projects/sage/search/conjunctive?_group-by=website
```

```
{
  "hits": {
    "hits": [],
    "total": 200,
    "max_score": 0.0
  },
  "_shards": {
    "successful": 5,
    "failed": 0,
    "skipped": 0,
    "total": 5
  },
  "took": 599,
  "aggregations": {
    "website": {
      "buckets": [
        {
          "key": "acleddata.com",
          "doc_count": 100
        },
        {
          "key": "parusanalytics.com",
          "doc_count": 100
        }
      ],
      "sum_other_doc_count": 0,
      "doc_count_error_upper_bound": 0
    }
  },
  "timed_out": false
}
```
Another example : 

```
http://<mydigurl>/mydig/projects/sage/search/conjunctive?_group-by=event_type
```

```
{
  "hits": {
    "hits": [],
    "total": 200,
    "max_score": 0.0
  },
  "_shards": {
    "successful": 5,
    "failed": 0,
    "skipped": 0,
    "total": 5
  },
  "took": 6,
  "aggregations": {
    "event_type": {
      "buckets": [
        {
          "key": "attack/massacre",
          "doc_count": 94
        },
        {
          "key": "incident",
          "doc_count": 64
        },
        {
          "key": "riots/protests",
          "doc_count": 45
        },
        {
          "key": "campaign",
          "doc_count": 36
        },
        {
          "key": "firearms",
          "doc_count": 32
        },
        {
          "key": "sole protester action",
          "doc_count": 32
        },
        {
          "key": "heavy weapons",
          "doc_count": 31
        },
        {
          "key": "battle-no change of territory",
          "doc_count": 23
        },
        {
          "key": "violence against civilians",
          "doc_count": 23
        },
        {
          "key": "unclear/other",
          "doc_count": 20
        }
      ],
      "sum_other_doc_count": 99,
      "doc_count_error_upper_bound": 2
    }
  },
  "timed_out": false
}

```
