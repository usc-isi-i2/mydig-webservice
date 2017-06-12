import logging

config = {
    'debug': True,
    'server': {
        'host': '127.0.0.1',
        'port': 5000,
    },
    'repo': {
        'local_path': '../../mydig-projects-test',
        # make sure remote alias had been created
        # https://help.github.com/articles/changing-a-remote-s-url/
        # git remote set-url origin https://github.com/{owner}/{repo}.git
        # and also generate & deploy ssh key
        # https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/
        'github': {
            'ssh_key_file_path': '<file path>',
            # 'username': 'usc-isi-i2',
            # 'access_token': '<Access Token>'
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
    'users': {
        'admin': '123' # basic YWRtaW46MTIz
    }
}