import copy


def get(name):
    return copy.deepcopy(eval(name))


master_config = {
  'root_name': 'Ad',
  'sources': [],
  'fields': [],
  'glossaries': {}
}
