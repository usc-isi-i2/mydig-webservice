import logging

config = {
    'debug': True,
    'server': {
        'host': '0.0.0.0',
        'port': 9879,
    },
    'repo': {
        'local_path': '/user_data/mydig-projects',
        'git': {
            'enable_sync': False,
            'remote_url': 'https://user:password@github.com/xxx/mydig-project.git'
        }
    },
    'repo_landmark': {
        'local_path': '/user_data/mydig-projects-landmark-public',
        'git': {
            'enable_sync': False,
            'remote_url': 'https://user:password@github.com/xxx/mydig-projects-landmark-public.git'
        }
    },
    'logging': {
        'file_path': '/user_data/log.log',
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
        'number_of_processes': 8
    },
    'sandpaper': {
        'url': 'http://localhost:9878',
        'ws_url': 'http://memex:digdig@localhost:9879'
    },
    'frontend': {
        'host': '0.0.0.0',
        'port': 9880,
        'debug': True,
        'backend_url': 'http://0.0.0.0:9879/'
    },
    'users': {
        'admin': '123' # basic YWRtaW46MTIz
    },
    'default_source_credentials_path': '/user_data/default_source_credentials.json',
    'default_glossary_dicts_path': '/user_data/dig3-resources/builtin_resources',
    'default_glossaries_path': '/user_data/dig3-resources/glossaries',
    'default_spacy_rules_path': '/user_data/dig3-resources/custom_spacy_rules'
}