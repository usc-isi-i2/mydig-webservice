import logging

config = {
    'debug': True,
    'server': {
        'host': '127.0.0.1',
        'port': 9875,
    },
    'repo': {
        'local_path': '/Users/amandeep/Github/mydig-projects',
    },
    'logging': {
        'file_path': 'log.log',
        'format': '%(asctime)s %(levelname)s %(message)s',
        'level': logging.INFO
    },
    'write_es': {
        'index': 'dig-etk-gt',
        'es_url': 'http://10.1.94.103:9201',
        'doc_type': 'ads'
    }
}