import copy


def get(name):
    return copy.deepcopy(eval(name))


master_config = {
  'root_name': 'Ad',
  'sources': [
    {
      'type': 'cdr',
      'url': 'http://...',
      'index_name': 'name of the index',
      'elastic_search_doctype': 'the type in elastic search',
      'elastic_search_query': {},
      'start_date': 'date-in-iso-format-at-any-resolution',
      'end_date': 'date-in-iso-format-at-any-resolution'
    }
  ],
  'fields': [],
  'glossaries': {}
}
