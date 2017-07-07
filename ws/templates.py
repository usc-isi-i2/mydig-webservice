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
    # 'cities': {
    #     'path': 'cities.json.gz',
    #     'entry_count': 13156,
    #     'ngram_distribution': {
    #         '1': 11333,
    #         '2': 1485,
    #         '3': 229,
    #         '4': 93,
    #         '5': 15
    #     }
    # },
    # 'countries': {
    #     'path': 'countries.json.gz',
    #     'entry_count': 257,
    #     'ngram_distribution': {
    #         '1': 185,
    #         '2': 46,
    #         '3': 13,
    #         '4': 7,
    #         '5': 5
    #     }
    # },
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
    # 'states_usa_canada': {
    #     'path': 'states_usa_canada.json.gz',
    #     'entry_count': 63,
    #     'ngram_distribution': {
    #         '1': 47,
    #         '2': 14,
    #         '3': 2
    #     }
    # }
}

default_configurations = {
    'digapp_full_url': 'http://52.36.12.77:8090',
    'digapp_sample_url': 'http://52.36.12.77:8090',
    'sandpaper_full_url': 'http://172.31.1.187:9876',
    'sandpaper_sample_url': 'http://172.31.1.187:9877'
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
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
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
        'color': '--paper-amber-500',
        'icon': 'default',
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
        'description': 'phone',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': '--paper-blue-600',
        'icon': 'icons:settings-phone',
        'search_importance': 1,
        'use_in_network_search': True,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'phone'
    },
    'city': {
        'name': 'city',
        'screen_label': 'City',
        'screen_label_plural': 'Cities',
        'description': 'cities mentioned in the page',
        'type': 'location',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'entity',
        'show_in_result': 'header',
        'color': '--paper-amber-500',
        'icon': 'default',
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
        'description': 'city names mentioned in the page',
        'type': 'location',
        'show_in_search': False,
        'show_in_facets': False,
        'show_as_link': 'text',
        'show_in_result': 'no',
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
        'use_in_network_search': False,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none'
    },
    'state': {
        'name': 'state',
        'screen_label': 'State',
        'screen_label_plural': 'States',
        'description': 'state',
        'type': 'location',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
        'use_in_network_search': True,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none'
    },
    'address': {
        'name': 'address',
        'screen_label': 'Address',
        'screen_label_plural': 'Addresses',
        'description': 'address',
        'type': 'string',
        'show_in_search': False,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'detail',
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
        'use_in_network_search': True,
        'combined_field': 'location',
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'address'
    },
    'posting_date': {
        'name': 'posting_date',
        'screen_label': 'Posting Date',
        'screen_label_plural': 'Posting Dates',
        'description': 'posting date',
        'type': 'date',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
        'use_in_network_search': True,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'posting_date'
    },
    'email': {
        'name': 'email',
        'screen_label': 'Email',
        'screen_label_plural': 'Emails',
        'description': 'email',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
        'use_in_network_search': True,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'email'
    },
    'name': {
        'name': 'name',
        'screen_label': 'Name',
        'screen_label_plural': 'Names',
        'description': 'name',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
        'use_in_network_search': True,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'none'
    },
    'website': {
        'name': 'website',
        'screen_label': 'TLD',
        'screen_label_plural': 'TLDs',
        'description': 'The field that contains the TLD of a page',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': '--paper-amber-500',
        'icon': 'default',
        'search_importance': 1,
        'use_in_network_search': True,
        'rule_extractor_enabled': False,
        'number_of_rules': 0,
        'predefined_extractor': 'TLD',
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
    }
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