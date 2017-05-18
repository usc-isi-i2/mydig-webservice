import copy


def get(name):
    return copy.deepcopy(eval(name))

project = {
    'master_config': {}, # master_config
    'entities': {} # 'kg-id': entity
}

master_config = {
  'root_name': 'Ad',
  'sources': [],
  'fields': {},
  'glossaries': {}
}

entity = {
    'kg_id': '',
    'tags': []
}