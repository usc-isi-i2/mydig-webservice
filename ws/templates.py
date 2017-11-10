import copy
import threading
import default_resources


def get(name):
    return copy.deepcopy(eval(name))

status = {
    'desired_docs': {
        # number of docs to run set by user
        # tld:num
    },
    'added_docs': {
        # number of marked docs (increment only)
        # tld:num
    },
    'total_docs': {
        # will be modified if there's an update in catalog
        # tld:num
    }
}

project = {
    'master_config': {}, # master_config
    'entities': {}, # 'kg-id': entity
    'field_annotations': {},
    'data': {}, # tlds -> meta data, protected by catalog lock
    'status': copy.deepcopy(status),
    'locks': {
        'data': None, # for data[project_name]['data']
        'status': None, # for data[project_name]['status']
        'catalog_log': None,
        'status_file_write_lock': None,
        'data_file_write_lock': None
    },
    'data_pushing_worker': None # daemon to periodically check if data needs to push to kafka
}

master_config = {
    'configuration': copy.deepcopy(default_resources.default_configuration) \
        if hasattr(default_resources, 'default_configuration') else {},
    'table_attributes': {},
    'glossaries': copy.deepcopy(default_resources.default_glossaries) \
        if hasattr(default_resources, 'default_glossaries') else {},
    'glossary_dicts': copy.deepcopy(default_resources.default_glossary_dicts) \
        if hasattr(default_resources, 'default_glossary_dicts') else {},
    'root_name': 'ads',
    'sources': [],
    'fields': copy.deepcopy(default_resources.default_fields) \
        if hasattr(default_resources, 'default_fields') else {},
    'tags': copy.deepcopy(default_resources.default_tags) \
        if hasattr(default_resources, 'default_tags') else {},
    'index': {
        'sample': '',
        'full': '',
        'version': 0
    },
    'image_prefix': ''
}

# data = {
#     'tld1': {
#         'doc_id1': {'path': 'raw_content_path_1', 'add_to_queue': bool},
#         'doc_id2': ...,
#     },
#     'tld2': {
#
#     }
# }

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
#     'rule_extraction_target': enum('title_only', 'description_only', 'title_and_description'),
#     'case_sensitive': boolean
# }