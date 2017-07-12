import copy


def get(name):
    return copy.deepcopy(eval(name))

project = {
    'master_config': {}, # master_config
    'entities': {}, # 'kg-id': entity
    'field_annotations': {}
}

# field_annotations = {
#     kg_id: {
#         field_name: {
#             key: {
#                 'human_annotation': 0/1
#             }
#         }
#     },
# }


# entities = {
#     entity_name: {
#         kg_id: {
#             tag_name: {
#                 'human_annotation': 0/1
#             }
#         }
#     }
# }

default_glossary_dicts = {
    'state_to_country': {
        'path': 'state_country_dict.json'
    },
    'country_code': {
        'path': 'country_codes_dict.json'
    },
    'state_to_codes_lower': {
        'path': 'states_to_codes_lower.json'
    },
    'geonames': {
        'path': 'city_dict_alt_15000.json'
    },
    'populated_cities': {
        'path': 'populated_cities.json'
    },
    'cities': {
        'path': 'cities.json.gz'
    },
    'countries': {
        'path': 'countries.json.gz'
    },
    'states_usa_canada': {
        'path': 'states_usa_canada.json.gz'
    }
}

default_glossaries = {
    'adult_services': {
        'path': 'adult_services.json.gz',
        'entry_count': 151,
        'ngram_distribution': {
            '1': 119,
            '2': 28,
            '3': 4
        }
    },
    'cities': {
        'path': 'cities.json.gz',
        'entry_count': 13156,
        'ngram_distribution': {
            '1': 11333,
            '2': 1485,
            '3': 229,
            '4': 93,
            '5': 15
        }
    },
    'countries': {
        'path': 'countries.json.gz',
        'entry_count': 256,
        'ngram_distribution': {
            '1': 184,
            '2': 46,
            '3': 13,
            '4': 7,
            '5': 5
        }
    },
    'ethnicities': {
        'path': 'ethnicities.json.gz',
        'entry_count': 291,
        'ngram_distribution': {
            '1': 262,
            '2': 27,
            '3': 2
        }
    },
    'eyecolors': {
        'path': 'eyecolors.json.gz',
        'entry_count': 28,
        'ngram_distribution': {
            '1': 28
        }
    },
    'haircolors': {
        'path': 'haircolors.json.gz',
        'entry_count': 60,
        'ngram_distribution': {
            '1': 60
        }
    },
    'states_usa_codes': {
        'path': 'states_usa_codes.json.gz',
        'entry_count': 59,
        'ngram_distribution': {
            '1': 59
        }
    },
    'states_usa_canada': {
        'path': 'states_usa_canada.json.gz',
        'entry_count': 63,
        'ngram_distribution': {
            '1': 47,
            '2': 14,
            '3': 2
        }
    }
}

default_configurations = {
    'digapp_full_url': 'http://52.36.12.77:8090',
    'digapp_sample_url': 'http://52.36.12.77:8090',
    # 'sandpaper_full_url': 'http://172.31.1.187:9876',
    # 'sandpaper_sample_url': 'http://172.31.1.187:9877'
    'sandpaper_full_url': 'http://172.31.30.159:9876',
    'sandpaper_sample_url': 'http://172.31.30.159:9877'
}

default_tags = {
    'movement': {
        'name': 'movement',
        'screen_label': 'movement',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'risky service': {
        'name': 'risky service',
        'screen_label': 'risky service',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'France': {
        'name': 'France',
        'screen_label': 'France',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'Australia': {
        'name': 'Australia',
        'screen_label': 'Australia',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'United States': {
        'name': 'United States',
        'screen_label': 'United States',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
}

default_fields = {
    'title': {
        'name': 'title',
        'screen_label': 'Title',
        'screen_label_plural': 'Titles',
        'description': 'The title of a page',
        'type': 'string',
        'group_name': 'page',
        'show_in_search': True,
        'show_in_facets': False,
        'show_as_link': 'text',
        'show_in_result': 'title',
        'color': 'amber',
        'icon': 'icons:view-stream',
        'search_importance': 3,
        'use_in_network_search': False,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none'
    },
    'description': {
        'name': 'description',
        'screen_label': 'Description',
        'screen_label_plural': 'Descriptions',
        'description': 'The main content of a page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': False,
        'show_as_link': 'text',
        'show_in_result': 'description',
        'color': 'cyan',
        'icon': 'editor:format-align-left',
        'search_importance': 1,
        'use_in_network_search': False,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none'
    },
    'phone': {
        'name': 'phone',
        'screen_label': 'Phone',
        'screen_label_plural': 'Phones',
        'description': 'Phone numbers mentioned in the page',
        'type': 'phone',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'entity',
        'show_in_result': 'header',
        'color': 'amber',
        'icon': 'communication:call',
        'search_importance': 10,
        'use_in_network_search': True,
        'rule_extractor_enabled': True,
        'number_of_rules': 49,
        'predefined_extractor': 'none'
    },
    'city': {
        'name': 'city',
        'screen_label': 'City',
        'screen_label_plural': 'Cities',
        'description': 'Cities mentioned in the page',
        'type': 'location',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'entity',
        'show_in_result': 'header',
        'color': 'pink',
        'icon': 'maps:place',
        'search_importance': 10,
        'use_in_network_search': False,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none'
    },
    'city_name': {
        'name': 'city_name',
        'screen_label': 'City Name',
        'screen_label_plural': 'City Names',
        'description': 'City names mentioned in the page',
        'type': 'string',
        'show_in_search': False,
        'show_in_facets': False,
        'show_as_link': 'text',
        'show_in_result': 'no',
        'color': 'brown',
        'icon': 'maps:place',
        'search_importance': 1,
        'use_in_network_search': False,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none',
        'glossaries': ['cities']
    },
    'state': {
        'name': 'state',
        'screen_label': 'State',
        'screen_label_plural': 'States',
        'description': 'USA and Canada states mentioned in the page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'detail',
        'color': 'teal',
        'icon': 'icons:language',
        'search_importance': 4,
        'use_in_network_search': False,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none',
        'glossaries': ['states_usa_canada']
    },
    'states_usa_codes': {
        'name': 'states_usa_codes',
        'screen_label': 'USA state code',
        'screen_label_plural': 'USA state codes',
        'description': 'USA state codes mentioned in the page',
        'type': 'string',
        'show_in_search': False,
        'show_in_facets': False,
        'show_as_link': 'text',
        'show_in_result': 'no',
        'color': 'teal',
        'icon': 'icons:language',
        'search_importance': 3,
        'use_in_network_search': False,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none',
        'glossaries': ['states_usa_codes']
    },
    'country': {
        'name': 'country',
        'screen_label': 'Country',
        'screen_label_plural': 'Countries',
        'description': 'Countries mentioned in the page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'detail',
        'color': 'indigo',
        'icon': 'icons:language',
        'search_importance': 5,
        'use_in_network_search': False,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none',
        'glossaries': ['countries']
    },
    'address': {
        'name': 'address',
        'screen_label': 'Address',
        'screen_label_plural': 'Addresses',
        'description': 'Addresses mentioned in the page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'detail',
        'color': 'indigo',
        'icon': 'icons:account-balance',
        'search_importance': 1,
        'use_in_network_search': True,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'address'
    },
    'posting_date': {
        'name': 'posting_date',
        'screen_label': 'Date',
        'screen_label_plural': 'Dates',
        'description': 'Dates mentioned in the page',
        'type': 'date',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'green',
        'icon': 'icons:today',
        'search_importance': 5,
        'use_in_network_search': True,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'posting_date'
    },
    'email': {
        'name': 'email',
        'screen_label': 'Email',
        'screen_label_plural': 'Emails',
        'description': 'Email addresses mentioned in the page',
        'type': 'email',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'entity',
        'show_in_result': 'header',
        'color': 'blue',
        'icon': 'communication:mail-outline',
        'search_importance': 10,
        'use_in_network_search': True,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'email'
    },
    'name': {
        'name': 'name',
        'screen_label': 'Name',
        'screen_label_plural': 'Names',
        'description': 'Names mentioned in the page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'blue',
        'icon': 'communication:contacts',
        'search_importance': 5,
        'use_in_network_search': False,
        'rule_extractor_enabled': True,
        'number_of_rules': 15,
        'predefined_extractor': 'none'
    },
    'website': {
        'name': 'website',
        'screen_label': 'TLD',
        'screen_label_plural': 'TLDs',
        'description': 'The TLD of a page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'light-green',
        'icon': 'communication:rss-feed',
        'search_importance': 2,
        'use_in_network_search': False,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'TLD',
        'rule_extraction_target': 'title_and_description'
    },
    'stock_ticker': {
        'name': 'stock_ticker',
        'screen_label': 'Stock',
        'screen_label_plural': 'Stocks',
        'description': 'Stock tickers mentioned in the page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'entity',
        'show_in_result': 'header',
        'color': 'red',
        'icon': 'icons:timeline',
        'search_importance': 9,
        'use_in_network_search': True,
        'rule_extractor_enabled': True,
        'number_of_rules': 42,
        'predefined_extractor': 'none',
        'rule_extraction_target': 'title_and_description'
    }
}

master_config = {
    'configuration': {
        'digapp_full_url': '',
        'digapp_sample_url': '',
        'sandpaper_full_url': '',
        'sandpaper_sample_url': ''
    },
    'table_attributes': {},
    'glossaries': copy.deepcopy(default_glossaries),
    'glossary_dicts': copy.deepcopy(default_glossary_dicts),
    'root_name': 'ads',
    'sources': [],
    'fields': copy.deepcopy(default_fields),
    'tags': copy.deepcopy(default_tags),
    'index': {
        'sample': '',
        'full': '',
        'version': 0
    },
    'image_prefix': ''
}

# table_attribute = {
#     'name': 'attribute_name_1',
#     'field_name': '',
#     'value': [],
#     'info': {}
# }

# entity = {
# }
#
# tag = {
#     'name': 'name',
#     'description': '',
#     'screen_label': 'show on the screen',
#     'include_in_menu': False,
#     'positive_class_precision': 0.0,
#     'negative_class_precision': 0.0
# }

# field = {
#     'name': 'same as the key',
#     'screen_label': 'show on the screen',
#     'screen_label_plural': 'screen label plural',
#     'description': 'whatever',
#     'type': 'enum(string | location | username | date | email | hyphenated | phone | image)',
#     'show_in_search': True,
#     'show_in_facets': True,
#     'show_as_link': 'enum(text | entity)',
#     'show_in_result': 'enum(header | detail | no | title | description)',
#     'color': 'enum(...)',
#     'icon': 'enum(...)',
#     'search_importance': 1, # (integer range in [1, 10])
#     'use_in_network_search': True
#     'group_name': string optional,
#     'combine_fields': boolean, optional
#     'glossaries': [], optional,
#     'rule_extractor_enabled': boolean,
#     'number_of_rules': integer,
#     'predefined_extractor': 'enum (social_media | review_id | city | posting_date | phone | email | address |
#      country | TLD | none)',
#     'rule_extraction_target': enum('title_only', 'description_only', 'title_and_description')
# }