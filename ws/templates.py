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
    'master_config': {},  # master_config
    'entities': {},  # 'kg-id': entity
    'field_annotations': {},
    'data': {},  # tlds -> meta data, protected by catalog lock
    'status': copy.deepcopy(status),
    'locks': {
        'data': None,  # for data[project_name]['data']
        'status': None,  # for data[project_name]['status']
        'catalog_log': None,
    },
    'data_pushing_worker': None,  # daemon to periodically check if data needs to push to kafka,
    'status_memory_dump_worker': None,
    'catalog_memory_dump_worker': None,
    'threads': []  # all threads exclude above workers
}

master_config = {
    'configuration': copy.deepcopy(default_resources.default_configuration) \
        if hasattr(default_resources, 'default_configuration') else {},
    'table_attributes': {},
    'glossaries': {},
    'glossary_dicts': {},
    'root_name': 'ads',
    'sources': [],
    'fields': {},
    'tags': {},
    'index': {
        'sample': '',
        'full': '',
        'version': 0
    },
    'image_prefix': '',
    'metadata': {}
}
