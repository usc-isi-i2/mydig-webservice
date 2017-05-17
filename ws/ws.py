import os
import shutil
import logging
import json
import types
import threading

from flask import Flask
from flask import request, abort, redirect, url_for
from flask_restful import Resource, Api

from config import config
import templates
import rest

# logger
logger = logging.getLogger('mydig-webservice.log')
log_file = logging.FileHandler(config['logging']['file_path'])
logger.addHandler(log_file)
log_file.setFormatter(logging.Formatter(config['logging']['format']))
logger.setLevel(config['logging']['level'])

# flask app
app = Flask(__name__)
api = Api(app)
def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper
api.route = types.MethodType(api_route, api)

# in-memory data
data = {}

# lock for each project
# treat it as a singleton
# all file operation should be in lock region
class ProjectLock(object):
    _lock = {}

    def acquire(self, name):
        # create lock if it is not there
        if name not in self._lock:
            self._lock[name] = threading.Lock()
        # acquire lock
        self._lock[name].acquire()

    def release(self, name):
        # lock hasn't been created
        if name not in self._lock:
            return
        try:
            self._lock[name].release()
        except:
            pass

    def remove(self, name):
        # acquire lock first!!!
        if name not in self._lock:
            return
        try:
            l = self._lock[name]
            del self._lock[name] # remove lock name first, then release
            l.release()
        except:
            pass

project_lock = ProjectLock()


def _get_project_dir_path(project_name):
    return os.path.join(config['repo']['local_path'], project_name)


@api.route('/debug')
class Debug(Resource):
    def get(self):
        if not config['debug']:
            return abort(404)
        debug_info = {
            'lock': {k: v.locked() for k, v in project_lock._lock.iteritems()},
            'data': data
        }
        return debug_info


@api.route('/projects')
class AllProjects(Resource):
    def post(self):
        global data

        if 'project_name' not in request.form:
            return rest.bad_request('Missing project name.')
        project_name = request.form['project_name']
        if len(project_name) >= 256:
            return rest.bad_request('Invalid project name.')
        if request.form['project_name'] in data:
            return rest.exists('Project name already exists.')

        # create project data structure, folders & files
        project_dir_path = _get_project_dir_path(project_name)
        try:
            project_lock.acquire(project_name)
            if not os.path.exists(project_dir_path):
                os.makedirs(project_dir_path)
            data[project_name] = templates.get('master_config')
            with open(os.path.join(project_dir_path, 'master_config.json'), 'w') as f:
                f.write(json.dumps(data[project_name]))
            logger.info('project %s created.' % project_name)
            return rest.created()
        except Exception as e:
            logger.error('creating project %s: %s' % (project_name, e.message))
        finally:
            project_lock.release(project_name)

    def get(self):
        global data
        return data.keys()

    def delete(self):
        global data
        for project_name in data.keys(): # not iterkeys(), need to do del in iteration
            try:
                project_lock.acquire(project_name)
                del data[project_name]
                shutil.rmtree(os.path.join(_get_project_dir_path(project_name)))
            except Exception as e:
                logger.error('deleting project %s: %s' % (project_name, e.message))
                return rest.internal_error('deleting project %s error, halted.' % project_name)
            finally:
                project_lock.remove(project_name)

        return rest.deleted()


@api.route('/projects/<project_name>')
class Project(Resource):
    def post(self, project_name):
        global data
        pass

    def put(self, project_name):
        return self.post(project_name)

    def get(self, project_name):
        global data
        if project_name not in data:
            return rest.not_found()
        return data[project_name]

    def delete(self, project_name):
        global data
        try:
            project_lock.acquire(project_name)
            del data[project_name]
            shutil.rmtree(os.path.join(_get_project_dir_path(project_name)))
        except Exception as e:
            logger.error('deleting project %s: %s' % (project_name, e.message))
            return rest.internal_error('deleting project %s error, halted.' % project_name)
        finally:
            project_lock.remove(project_name)


if __name__ == '__main__':
    try:
        # sync data
        # pull
        # if not os.path.exists(config['local_repo_path']):
        #     logging.info('create')
        #     os.exit()


        # init
        for project_name in os.listdir(config['repo']['local_path']):
            project_dir_path = _get_project_dir_path(project_name)
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