import copy


def get(name):
    return copy.deepcopy(eval(name))

project = {
    'master_config': {}, # master_config
    'entities': {}, # 'kg-id': entity
    'field_annotations': {},
    'glossaries': [], # no need to dump to file
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
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'risky service': {
        'name': 'risky service',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'France': {
        'name': 'France',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'Australia': {
        'name': 'Australia',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
    'United States': {
        'name': 'United States',
        'description': '',
        'include_in_menu': False,
        'positive_class_precision': 0.0,
        'negative_class_precision': 0.0
    },
}
default_fields = {
    'city': {'name': 'city', 'description': ''},
    'weight': {'name': 'weight', 'description': ''},
    'review_id': {'name': 'review_id', 'description': ''},
    'service': {'name': 'service', 'description': ''},
    'gender': {'name': 'gender', 'description': ''},
    'age': {'name': 'age', 'description': ''},
    'eye_color': {'name': 'eye_color', 'description': ''},
    'hair_color': {'name': 'hair_color', 'description': ''},
    'height': {'name': 'height', 'description': ''},
    'price': {'name': 'price', 'description': ''},
    'phone': {'name': 'phone', 'description': ''},
    'state': {'name': 'state', 'description': ''},
    'address': {'name': 'address', 'description': ''},
    'posting_date': {'name': 'posting_date', 'description': ''},
    'email': {'name': 'email', 'description': ''},
    'ethnicity': {'name': 'ethnicity', 'description': ''},
    'name': {'name': 'name', 'description': ''}
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
#     'include_in_menu': False,
#     'positive_class_precision': 0.0,
#     'negative_class_precision': 0.0
# }