import logging

config = {
    'debug': True,
    'server': {
        'host': '0.0.0.0',
        'port': 9879,
    },
    'repo': {
        'local_path': '/shared_data/projects',
        'git': {
            'enable_sync': False,
            'remote_url': 'https://github.com/GreatYYX/mydig-project-test.git',
        }
    },
    'logging': {
        'file_path': 'log.log',
        'format': '%(asctime)s %(levelname)s %(message)s',
        'level': logging.INFO
    },
    'es': {
        # do not add / at the end
        'sample_url': 'http://localhost:9200',
        'full_url': 'http://localhost:9200'
    },
    'etk': {
        'path': '/app/etk',
        'conda_path': '/app/miniconda/bin/',
        'daemon': {
            'host': 'localhost',
            'port': 12121
        },
        # 'number_of_processes': 8
    },
    'etl': {
        'url': 'http://dig_etl_engine:9999',
        'number_of_workers': 1,
        'timeout': 5
    },
    'kafka': {
        'servers': ['kafka:9092']
    },
    'sandpaper': {
        'url': 'http://sandpaper:9878',
        'ws_url': 'http://admin:123@mydig_ws:9879'
    },
    'users': {
        'admin': '123' # basic YWRtaW46MTIz
    },
    'frontend': {
        'host': '0.0.0.0',
        'port': 9880,
        'debug': True,
        'backend_url': 'http://localhost:5000/' # change to ip of host machine
    },
    # 'default_source_credentials_path': './default_source_credentials.json',
    'default_glossary_dicts_path': '/shared_data/dig3-resources/builtin_resources',
    'default_glossaries_path': '/shared_data/dig3-resources/glossaries',
    'default_spacy_rules_path': '/shared_data/dig3-resources/custom_spacy_rules'
}