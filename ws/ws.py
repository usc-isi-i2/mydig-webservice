import os
import logging
import json

from flask import Flask
from flask import request, abort, redirect, url_for
from config import config

# logger
logger = logging.getLogger('mydig-webservice.log')
log_file = logging.FileHandler(config['logging']['file_path'])
logger.addHandler(log_file)
log_file.setFormatter(logging.Formatter(config['logging']['format']))
logger.setLevel(config['logging']['level'])

# flask app
app = Flask(__name__)

# in-memory data
data = {}


@app.route('/debug/data', methods=['GET'])
def debug_get_all_data():
    if not config['debug']:
        return abort(404)
    return json.dumps(data)

@app.route('/projects', methods=['POST', 'GET', 'DELETE'])
def hello():
    if request.method == 'POST':
        pass
    return 'hello'

if __name__ == '__main__':
    try:
        # sync data
        # pull
        # if not os.path.exists(config['local_repo_path']):
        #     logging.info('create')
        #     os.exit()

        # init
        for project_name in os.listdir(config['repo']['local_path']):
            project_dir_path = os.path.join(config['repo']['local_path'], project_name)
            if not os.path.isdir(project_dir_path) or project_name == '.git':
                continue

            # master_config
            master_config_file_path = os.path.join(project_dir_path, 'master_config.json')
            if not os.path.exists(master_config_file_path):
                logger.error('Missing master_config.json file for ' + project_name)
            with open(master_config_file_path, 'r') as f:
                data[project_name] = json.loads(f.read())

        # run app
        app.run(debug=config['debug'], host=config['server']['host'], port=config['server']['port'])

    except Exception as e:
        logger.error(e.message)