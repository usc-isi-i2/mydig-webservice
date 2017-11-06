
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

default_configuration = {
    'digapp_full_url': 'http://localhost:8090',
    'digapp_sample_url': 'http://localhost:8090',
    'sandpaper_full_url': 'http://sandpaper:9876',
    'sandpaper_sample_url': 'http://sandpaper:9876'
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
        'glossaries': ['cities'],
        'case_sensitive': False
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
        'glossaries': ['states_usa_canada'],
        'case_sensitive': False
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
        'glossaries': ['states_usa_codes'],
        'case_sensitive': False
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
        'glossaries': ['countries'],
        'case_sensitive': False
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
        'rule_extractor_enabled': False,
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
