import logging

config = {
    'debug': True,
    'server': {
        'host': '127.0.0.1',
        'port': 5000,
    },
    'repo': {
        'local_path': '../../mydig-projects-test',
    },
    'logging': {
        'file_path': 'log.log',
        'format': '%(asctime)s %(levelname)s %(message)s',
        'level': logging.INFO
    }
}