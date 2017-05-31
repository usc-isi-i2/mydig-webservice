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

master_config = {
    'root_name': 'Ad',
    'sources': [],
    'fields': {},
    'tags': set(), # will be converted to list when dumps
    'glossaries': {}
}

entity = {
}