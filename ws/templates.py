import copy


def get(name):
    return copy.deepcopy(eval(name))

project = {
    'master_config': {}, # master_config
    'entities': {}, # 'kg-id': entity
    'field_annotations': {},
    # 'glossaries': {}
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

default_tags = {
    'movement': {
        'name': 'movement',
        'scree_label': 'movement',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'risky service': {
        'name': 'risky service',
        'scree_label': 'risky service',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'France': {
        'name': 'France',
        'scree_label': 'France',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'Australia': {
        'name': 'Australia',
        'scree_label': 'Australia',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'United States': {
        'name': 'United States',
        'scree_label': 'United States',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
}
default_fields = {
    'city': {
        'name': 'city',
        'screen_label': 'City',
        'description': 'city',
        'type': 'location',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'location',
        'search_importance': 1,
        'use_in_network_search': True,
        'combined_field': 'location'
    },
    'title': {
        'name': 'title',
        'screen_label': 'Title',
        'description': 'title',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'normal',
        'search_importance': 1,
        'use_in_network_search': True
    },
    'description': {
        'name': 'description',
        'screen_label': 'Description',
        'description': 'description',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'normal',
        'search_importance': 1,
        'use_in_network_search': True
    },
    'phone': {
        'name': 'phone',
        'screen_label': 'Phone',
        'description': 'phone',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'phone',
        'search_importance': 1,
        'use_in_network_search': True,
    },
    'state': {
        'name': 'state',
        'screen_label': 'State',
        'description': 'state',
        'type': 'location',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'location',
        'search_importance': 1,
        'use_in_network_search': True,
        'combined_field': 'location'
    },
    'country': {
        'name': 'country',
        'screen_label': 'Country',
        'description': 'country',
        'type': 'location',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'location',
        'search_importance': 1,
        'use_in_network_search': True,
        'combined_field': 'location'
    },
    'address': {
        'name': 'address',
        'screen_label': 'Address',
        'description': 'address',
        'type': 'location',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'location',
        'search_importance': 1,
        'use_in_network_search': True,
        'combined_field': 'location'
    },
    'posting_date': {
        'name': 'posting_date',
        'screen_label': 'Posting Date',
        'description': 'posting date',
        'type': 'date',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'normal',
        'search_importance': 1,
        'use_in_network_search': True
    },
    'email': {
        'name': 'email',
        'screen_label': 'Email',
        'description': 'email',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'email',
        'search_importance': 1,
        'use_in_network_search': True
    },
    'name': {
        'name': 'name',
        'screen_label': 'Name',
        'description': 'name',
        'type': 'string',
        'show_in_search': True,
        'show_in_facets': True,
        'show_as_link': 'text',
        'show_in_result': 'header',
        'color': 'grey',
        'icon': 'default',
        'format': 'normal',
        'search_importance': 1,
        'use_in_network_search': True
    }
}

master_config = {
    'root_name': 'Ad',
    'sources': [],
    'fields': copy.deepcopy(default_fields),
    'tags': copy.deepcopy(default_tags),
    'index': {
        'sample': '',
        'full': 'dig-ht-gt'
    }
}

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
#     'show_in_result': 'enum(header | detail | no)',
#     'color': 'enum(...)',
#     'icon': 'enum(...)',
#     'search_importance': 1, # (integer range in [1, 10])
#     'use_in_network_search': True
#     'group_name': string optional,
#     'combine_fields': boolean, optional
#     'glossaries': [], optional
# }

# fields = {
#     fields: [{                      # Defines the extraction fields used throughout the application.
#         field: 'phone',               # The elasticsearch field.  Assume data structure '_source.knowledge_graph.<input>'.
#         name: 'Telephone Number',     # Pretty name to show in the UI.
#         type: 'string',               # Either 'string', 'location', 'image', or 'date'.
#         search: True,                 # Whether to show this extraction in the search terms popup.
#         facets: True,                 # Whether to show this extraction in the facets.
#         link: 'entity',               # Whether to show this extraction as a link.  Either 'text' (uses raw text as link), 'entity' (uses entity page link),
#                   #     'custom' (uses custom link property), or 'none'.
#         showInResult: 'header',       # Whether to show this extraction in the search results.  Either 'header', 'detail', or 'no'.
#         color: 'purple',              # The extraction icon (we will provide a list of available colors).
#         icon: 'communication:phone',  # The extraction icon (we will just use polymer/fontawesome but provide a list of available icons).
#         format: 'phone'               # Formatting function to transform extractions.  We will provide a list of available functions.  EX:  'phone' (add hypens),
#               #     'email' (decode emails), 'location' (transform city:state:country:lat:lon strings).
#     }],
#     entities: [{
#         field: 'phone',               # Defines the type of entity page.  Corresponds to a 'field' in the 'fields' array above.
#         config: {},                   # Any page-specific config.
#         left: [{                      # Defines the sections in the left column of the page.
#             type: 'map',                # Defines the type of visualization.  EX:  'aggregation', 'date-histogram', 'event-drops', 'images', 'list', 'map'.
#             field: 'city',              # The field of the data shown in the visualization.  Corresponds to a 'field' in the 'fields' array above.
#             filter: True,               # Whether to let users filter on this data.
#             config: {}                  # Any visualization-specific config.
#         },
#         {
#             type: 'aggregation',
#             field: 'phone',
#             filter: True
#         },
#         {
#             type: 'aggregation',
#             field: 'email',
#             filter: True
#         }],
#         right: [{                       # Defines the sections in the right column of the page.
#
#         }]
#     }]
# }