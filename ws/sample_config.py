import logging

config = {
    'debug': True,
    'server': {
        'host': '0.0.0.0',
        'port': 9876,
    },
    # add a mydig-admin user to the below to repos,
    # and set up user.name and user.email in git config
    'repo': {
        'local_path': '../../mydig-projects-test',
        'git': {
            'enable_sync': True,
            'remote_url': '<remote url>',
            # generate & deploy ssh key
            # https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/
            # 'ssh_key_file_path': '<file path>'
        }
    },
    'repo_landmark': {
        'local_path': '../../mydig-projects-landmark',
        'git': {
            'enable_sync': True,
            'remote_url': '<remote url>',
            # 'ssh_key_file_path': '<file path>'
        }
    },
    'logging': {
        'file_path': 'log.log',
        'format': '%(asctime)s %(levelname)s %(message)s',
        'level': logging.INFO
    },
    'es': {
        # do not add / at the end
        'url': 'http://localhost:9200'
    },
    'etk': {
        'path': '...',
        'conda_path': '...',
        'daemon': {
            'host': 'localhost',
            'port': 12121
        },
        'number_of_processes': 8
    },
    'sandpaper': {
        'url': 'http://localhost:9878',
        'ws_url': 'http://admin:123@localhost:9879'
    },
    'users': {
        'admin': '123' # basic
    },
    'default_source_credentials_path': './default_source_credentials.json',
    'default_glossary_dicts_path': '/jpl/dig3-resources/builtin_resources',
    'default_glossaries_path': '/jpl/dig3-resources/glossaries',
    'default_spacy_rules_path': '/jpl/dig3-resources/custom_spacy_rules'
}