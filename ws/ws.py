import os
import shutil
import logging
import json
import yaml
import types
import threading
import werkzeug
import codecs
import csv

from flask import Flask, render_template, Response
from flask import request, abort, redirect, url_for
from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api, reqparse

from config import config
from elastic_manager.elastic_manager import ES
import templates
import rest
from basic_auth import requires_auth, requires_auth_html

# logger
logger = logging.getLogger('mydig-webservice.log')
log_file = logging.FileHandler(config['logging']['file_path'])
logger.addHandler(log_file)
log_file.setFormatter(logging.Formatter(config['logging']['format']))
logger.setLevel(config['logging']['level'])

# flask app
app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls

    return wrapper


api.route = types.MethodType(api_route, api)

# in-memory data
data = {}


def write_to_file(content, file_path):
    o = codecs.open(file_path, 'w')
    o.write(content)
    o.close()

# set to list
# def json_encode(obj):
#     if isinstance(obj, set):
#         return list(obj)
#     raise TypeError


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
            del self._lock[name]  # remove lock name first, then release
            l.release()
        except:
            pass


project_lock = ProjectLock()


def _get_project_dir_path(project_name):
    return os.path.join(config['repo']['local_path'], project_name)

@app.route('/spec')
def spec():
    return render_template('swagger_index.html', title='MyDIG web service API reference', spec_path='/spec.yaml')


@app.route('/spec.yaml')
def spec_file_path():
    with open('spec.yaml', 'r') as f:
        c = yaml.load(f)
        c['host'] = request.host
    return Response(yaml.dump(c), mimetype='text/x-yaml')


@app.route('/')
def home():
    return 'MyDIG Web Service'


@api.route('/debug')
class Debug(Resource):
    @requires_auth
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
    @requires_auth
    def post(self):
        input = request.get_json(force=True)
        project_name = input.get('project_name', '')
        if len(project_name) == 0 or len(project_name) >= 256:
            return rest.bad_request('Invalid project name.')
        if project_name in data:
            return rest.exists('Project name already exists.')
        project_sources = input.get('sources', [])
        if len(project_sources) == 0:
            return rest.bad_request('Invalid sources.')

        # create project data structure, folders & files
        project_dir_path = _get_project_dir_path(project_name)
        try:
            project_lock.acquire(project_name)
            if not os.path.exists(project_dir_path):
                os.makedirs(project_dir_path)
            data[project_name] = templates.get('project')
            data[project_name]['master_config'] = templates.get('master_config')
            data[project_name]['master_config']['sources'] = project_sources
            with open(os.path.join(project_dir_path, 'master_config.json'), 'w') as f:
                f.write(json.dumps(data[project_name]['master_config'], indent=4))

            os.makedirs(os.path.join(project_dir_path, 'field_annotations'))
            write_to_file(json.dumps({}), os.path.join(project_dir_path, 'field_annotations/field_annotations.json'))
            os.makedirs(os.path.join(project_dir_path, 'entity_annotations'))
            write_to_file(json.dumps({}), os.path.join(project_dir_path, 'entity_annotations/entity_annotations.json'))
            os.makedirs(os.path.join(project_dir_path, 'glossaries'))
            logger.info('project %s created.' % project_name)
            return rest.created()
        except Exception as e:
            logger.error('creating project %s: %s' % (project_name, e.message))
        finally:
            project_lock.release(project_name)

    @requires_auth
    def get(self):
        return data.keys()

    @requires_auth
    def delete(self):
        for project_name in data.keys():  # not iterkeys(), need to do del in iteration
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
    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found()
        input = request.get_json(force=True)
        project_sources = input.get('sources', [])
        if len(project_sources) == 0:
            return rest.bad_request('Invalid sources.')
        try:
            project_lock.acquire(project_name)
            data[project_name]['master_config']['sources'] = project_sources
            # write to file
            file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
            write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
            return rest.created()
        except Exception as e:
            logger.error('Updating project %s: %s' % (project_name, e.message))
            return rest.internal_error('Updating project %s error, halted.' % project_name)
        finally:
            project_lock.release(project_name)

    @requires_auth
    def put(self, project_name):
        return self.post(project_name)

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found()
        return data[project_name]

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found()
        try:
            project_lock.acquire(project_name)
            del data[project_name]
            shutil.rmtree(os.path.join(_get_project_dir_path(project_name)))
            return rest.deleted()
        except Exception as e:
            logger.error('deleting project %s: %s' % (project_name, e.message))
            return rest.internal_error('deleting project %s error, halted.' % project_name)
        finally:
            project_lock.remove(project_name)


@api.route('/projects/<project_name>/tags')
class ProjectTags(Resource):
    @requires_auth
    def get(self, project_name):
        # return all the tags created for this project
        if project_name not in data:
            return rest.not_found("Project \'{}\' not found".format(project_name))
        return data[project_name]['master_config']['tags']

    @requires_auth
    def delete(self, project_name):
        # delete all the tags for this project
        if project_name not in data:
            return rest.not_found("Project \'{}\' not found".format(project_name))
        data[project_name]['master_config']['tags'] = dict()
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.deleted()

    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found("Project \'{}\' not found".format(project_name))

        input = request.get_json(force=True)
        tag_name = input.get('tag_name', '')
        if len(tag_name) == 0:
            return rest.bad_request('Invalid tag name')
        if tag_name in data[project_name]['master_config']['tags']:
            return rest.exists('Tag name already exists')
        tag_object = input.get('tag_object', {})
        if 'name' not in tag_object or tag_object['name'] != tag_name:
            return rest.bad_request('Name of tag is not correct')
        data[project_name]['master_config']['tags'][tag_name] = tag_object
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.created()


@api.route('/projects/<project_name>/tags/<tag_name>')
class Tag(Resource):
    @requires_auth
    def get(self, project_name, tag_name):
        if project_name not in data:
            return rest.not_found("Project {} not found".format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found("Tag {} not found".format(tag_name))
        return data[project_name]['master_config']['tags'][tag_name]

    @requires_auth
    def post(self, project_name, tag_name):
        # user is not allowed to update tag_name
        if project_name not in data:
            return rest.not_found("Project {} not found".format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found("Tag {} not found".format(tag_name))
        input = request.get_json(force=True)
        tag_object = input.get('tag_object', {})
        if 'name' not in tag_object or tag_object['name'] != tag_name:
            return rest.bad_request('Name of tag is not correct')
        data[project_name]['master_config']['tags'][tag_name] = tag_object
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.created()

    @requires_auth
    def put(self, project_name, tag_name):
        return self.post(project_name, tag_name)

    @requires_auth
    def delete(self, project_name, tag_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        del data[project_name]['master_config']['tags'][tag_name]
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.deleted()


@api.route('/projects/<project_name>/fields')
class ProjectFields(Resource):
    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found()
        input = request.get_json(force=True)
        field_name = input.get('field_name', '')
        if len(field_name) == 0:
            return rest.bad_request('Invalid field name')
        if field_name in data[project_name]['master_config']['fields']:
            return rest.exists('Field name already exists')
        field_object = input.get('field_object', {})

        data[project_name]['master_config']['fields'][field_name] = field_object
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.created()

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found()
        return data[project_name]['master_config']['fields']

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found()

        data[project_name]['master_config']['fields'] = dict()
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.deleted()


@api.route('/projects/<project_name>/fields/<field_name>')
class Field(Resource):
    @requires_auth
    def get(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found()
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found()
        return data[project_name]['master_config']['fields'][field_name]

    @requires_auth
    def post(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found()
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found()
        input = request.get_json(force=True)
        field_object = input.get('field_object', {})
        if 'name' not in field_object or field_object['name'] != field_name:
            return rest.bad_request('Name of tag is not correct')
        data[project_name]['master_config']['fields'][field_name] = field_object
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.created()

    @requires_auth
    def put(self, project_name, field_name):
        return self.post(project_name, field_name)

    @requires_auth
    def delete(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found()
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found()
        del data[project_name]['master_config']['fields'][field_name]
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)
        return rest.deleted()


@api.route('/projects/<project_name>/glossaries')
class ProjectGlossaries(Resource):
    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        parse = reqparse.RequestParser()
        parse.add_argument('glossary_file', type=werkzeug.FileStorage, location='files')
        parse.add_argument('glossary_name')

        args = parse.parse_args()

        # http://werkzeug.pocoo.org/docs/0.12/datastructures/#werkzeug.datastructures.FileStorage
        name = args['glossary_name']
        file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.txt')
        if os.path.exists(file_path):
            return rest.exists('Glossary name {} exists'.format(name))
        file = args['glossary_file']
        # write_to_file(content, file_path)
        file.save(file_path)

        data[project_name]['glossaries'].append(name)

        return rest.created()

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        return data[project_name]['glossaries']

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        dir_path = os.path.join(_get_project_dir_path(project_name), 'glossaries')
        shutil.rmtree(dir_path)
        os.mkdir(dir_path) # recreate folder
        data[project_name]['glossaries'] = []
        return rest.deleted()


@api.route('/projects/<project_name>/glossaries/<glossary_name>')
class Glossary(Resource):
    @requires_auth
    def post(self, project_name, glossary_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        if glossary_name not in data[project_name]['glossaries']:
            return rest.not_found('Glossary {} not found'.format(glossary_name))

        # parse = reqparse.RequestParser()
        # parse.add_argument('glossary_file', type=werkzeug.FileStorage, location='files')
        #
        # args = parse.parse_args()
        #
        # # http://werkzeug.pocoo.org/docs/0.12/datastructures/#werkzeug.datastructures.FileStorage
        # name = args['glossary_name']
        # file = args['glossary_file']
        # file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.txt')
        # # write_to_file(content, file_path)
        # file.save(file_path)
        # return rest.created()

    # def get(self, project_name):
    #     if project_name not in data:
    #         return rest.not_found('Project {} not found'.format(project_name))
    #
    #     dir_path = os.path.join(_get_project_dir_path(project_name), 'glossaries')
    #     ret = []
    #     for file_name in os.listdir(dir_path):
    #         name, ext = os.path.splitext(file_name)
    #         if ext == '.txt':
    #             ret.append(name)
    #     return ret
    #
    # def delete(self, project_name):
    #     if project_name not in data:
    #         return rest.not_found('Project {} not found'.format(project_name))
    #
    #     dir_path = os.path.join(_get_project_dir_path(project_name), 'glossaries')
    #     shutil.rmtree(dir_path)
    #     os.mkdir(dir_path) # recreate folder
    #     return rest.deleted()


@api.route('/projects/<project_name>/entities/<kg_id>/tags')
class EntityTags(Resource):
    @requires_auth
    def get(self, project_name, kg_id):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        entity_name = 'Ad'
        if entity_name not in data[project_name]['entities']:
            data[project_name]['entities'][entity_name] = dict()
        if kg_id not in data[project_name]['entities'][entity_name]:
            return rest.not_found('kg_id {} not found'.format(kg_id))

        return data[project_name]['entities'][entity_name][kg_id]

    @requires_auth
    def post(self, project_name, kg_id):
        if project_name not in data:
            return rest.not_found()

        input = request.get_json(force=True)
        tags = input.get('tags', [])
        if len(tags) == 0:
            return rest.bad_request('No tags given')
        # tag should be exist
        for tag_name in tags:
            if tag_name not in data[project_name]['master_config']['tags']:
                return rest.bad_request('Tag {} is not exist'.format(tag_name))
        # add tags to entity
        entity_name = 'Ad'
        for tag_name in tags:
            if entity_name not in data[project_name]['entities']:
                data[project_name]['entities'][entity_name] = dict()
            if kg_id not in data[project_name]['entities'][entity_name]:
                data[project_name]['entities'][entity_name][kg_id] = dict()
            if tag_name not in data[project_name]['entities'][entity_name][kg_id]:
                data[project_name]['entities'][entity_name][kg_id][tag_name] = dict()

        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/entity_annotations.json')
        write_to_file(json.dumps(data[project_name]['entities'], indent=4), file_path)
        return rest.created()


@api.route('/projects/<project_name>/entities/<kg_id>/fields/<field_name>/annotations')
class FieldAnnotations(Resource):
    @requires_auth
    def get(self, project_name, kg_id, field_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if kg_id not in data[project_name]['field_annotations']:
            return rest.not_found('kg_id {} not found'.format(kg_id))
        if field_name not in data[project_name]['field_annotations'][kg_id]:
            return rest.not_found('Field name {} not found'.format(field_name))
        return data[project_name]['field_annotations'][kg_id][field_name]

    @requires_auth
    def delete(self, project_name, kg_id, field_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if kg_id not in data[project_name]['field_annotations']:
            return rest.not_found('kg_id {} not found'.format(kg_id))
        if field_name not in data[project_name]['field_annotations'][kg_id]:
            return rest.not_found('Field name {} not found'.format(field_name))
        data[project_name]['field_annotations'][kg_id][field_name] = dict()
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'field_annotations/field_annotations.json')
        write_to_file(json.dumps(data[project_name]['field_annotations'], indent=4), file_path)
        # load into ES
        self.remove_field_annotation('full', project_name, kg_id, field_name)
        self.remove_field_annotation('sample', project_name, kg_id, field_name)

        return rest.deleted()

    @requires_auth
    def post(self, project_name, kg_id, field_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))

        # field should be in master_config
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.bad_request('Field {} is not exist'.format(field_name))

        input = request.get_json(force=True)
        key = input.get('key', '')
        if key.strip() == '':
            return rest.bad_request('invalid key')
        human_annotation = input.get('human_annotation', -1)
        if not isinstance(human_annotation, int) or human_annotation == -1:
            return rest.bad_request('invalid human_annotation')

        if kg_id not in data[project_name]['field_annotations']:
            data[project_name]['field_annotations'][kg_id] = dict()

        if field_name not in data[project_name]['field_annotations'][kg_id]:
            data[project_name]['field_annotations'][kg_id][field_name] = dict()

        if key not in data[project_name]['field_annotations'][kg_id][field_name]:
            data[project_name]['field_annotations'][kg_id][field_name][key] = dict()

        data[project_name]['field_annotations'][kg_id][field_name][key]['human_annotation'] = human_annotation
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'field_annotations/field_annotations.json')
        write_to_file(json.dumps(data[project_name]['field_annotations'], indent=4), file_path)
        # load into ES
        self.update_field_annotation('full', project_name, kg_id, field_name, key, human_annotation)
        self.update_field_annotation('sample', project_name, kg_id, field_name, key, human_annotation)

        return rest.created()

    @requires_auth
    def put(self, project_name, kg_id, field_name):
        return rest.post(project_name, kg_id, field_name)


    @staticmethod
    def update_field_annotation(index_version, project_name, kg_id, field_name, key, human_annotation):
        try:
            es = ES(config['es']['url'])
            index = data[project_name]['master_config']['index'][index_version]
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                doc = hits['hits']['hits'][0]['_source']
                if 'knowledge_graph' not in doc:
                    doc['knowledge_graph'] = dict()
                if field_name not in doc['knowledge_graph']:
                    doc['knowledge_graph'][field_name] = dict()
                for field_instance in doc['knowledge_graph'][field_name]:
                    if field_instance['key'] == key:
                        field_instance['human_annotation'] = human_annotation
                        break

                res = es.load_data(index, type, doc, doc['doc_id'])
                if not res:
                    logger.info('Fail to load data to {}: project {}, kg_id {}, field {}, key {}'.format(
                        index_version, project_name, kg_id, field_name, key
                    ))
                    return

            logger.info('Fail to retrieve from {}: project {}, kg_id {}, field {}, key {}'.format(
                index_version, project_name, kg_id, field_name, key
            ))
            return
        except Exception as e:
            print e
            logger.warning('Fail to update annotation to {}: project {}, kg_id {}, field {}, key {}'.format(
                index_version, project_name, kg_id, field_name, key
            ))

    @staticmethod
    def remove_field_annotation(index_version, project_name, kg_id, field_name, key=None):
        try:
            es = ES(config['es']['url'])
            index = data[project_name]['master_config']['index'][index_version]
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                doc = hits['hits']['hits'][0]['_source']
                if 'knowledge_graph' not in doc:
                    return
                if field_name not in doc['knowledge_graph']:
                    return
                for field_instance in doc['knowledge_graph'][field_name]:
                    if key is None: # delete all annotations
                        if 'human_annotation' in field_instance:
                            del field_instance['human_annotation']
                    else: # delete annotation of a specific key
                        if field_instance['key'] == key:
                            del field_instance['human_annotation']
                            break
                res = es.load_data(index, type, doc, doc['doc_id'])
                if not res:
                    return True

            return False
        except Exception as e:
            print e
            logger.warning('Fail to remove annotation from {}: project {}, kg_id {}, field {}, key {}'.format(
                index_version, project_name, kg_id, field_name, key
            ))


@api.route('/projects/<project_name>/entities/<kg_id>/fields/<field_name>/annotations/<key>')
class FieldInstanceAnnotations(Resource):
    @requires_auth
    def get(self, project_name, kg_id, field_name, key):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if kg_id not in data[project_name]['field_annotations']:
            return rest.not_found(
                'Field annotations not found, kg_id: {}'.format(kg_id))
        if field_name not in data[project_name]['field_annotations'][kg_id]:
            return rest.not_found(
                'Field annotations not found, kg_id: {}, field: {}'.format(kg_id, field_name))
        if key not in data[project_name]['field_annotations'][kg_id][field_name]:
            return rest.not_found(
                'Field annotations not found, kg_id: {}, field: {}, key: {}'.format(kg_id, field_name, key))

        return data[project_name]['field_annotations'][kg_id][field_name][key]

    @requires_auth
    def delete(self, project_name, kg_id, field_name, key):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if kg_id not in data[project_name]['field_annotations']:
            return rest.not_found(
                'Field annotations not found, kg_id: {}'.format(kg_id))
        if field_name not in data[project_name]['field_annotations'][kg_id]:
            return rest.not_found(
                'Field annotations not found, kg_id: {}, field: {}'.format(kg_id, field_name))
        if key not in data[project_name]['field_annotations'][kg_id][field_name]:
            return rest.not_found(
                'Field annotations not found, kg_id: {}, field: {}, key: {}'.format(kg_id, field_name, key))

        del data[project_name]['field_annotations'][kg_id][field_name][key]
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'field_annotations/field_annotations.json')
        write_to_file(json.dumps(data[project_name]['field_annotations'], indent=4), file_path)
        # load into ES
        FieldAnnotations.remove_field_annotation('full', project_name, kg_id, field_name, key)
        FieldAnnotations.remove_field_annotation('sample', project_name, kg_id, field_name, key)
        return rest.deleted()


@api.route('/projects/<project_name>/tags/<tag_name>/annotations/<entity_name>/annotations')
class TagAnnotationsForEntityType(Resource):
    @requires_auth
    def delete(self, project_name, tag_name, entity_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        if entity_name not in data[project_name]['entities']:
            return rest.not_found('Entity {} not found'.format(entity_name))

        for kg_id, kg_item in data[project_name]['entities'][entity_name].items():
            # if tag_name in kg_item.iterkeys():
            #     if 'human_annotation' in kg_item[tag_name]:
            #         del kg_item[tag_name]['human_annotation']

            # hard code
            if tag_name in kg_item:
                del kg_item[tag_name]
                # remove from ES
                self.remove_tag_annotation('full', project_name, kg_id, tag_name)
                self.remove_tag_annotation('sample', project_name, kg_id, tag_name)
            if len(kg_item) == 0:
                del data[project_name]['entities'][entity_name][kg_id]

        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/entity_annotations.json')
        write_to_file(json.dumps(data[project_name]['entities'], indent=4), file_path)

        return rest.deleted()

    @requires_auth
    def get(self, project_name, tag_name, entity_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))

        result = dict()
        if entity_name in data[project_name]['entities']:
            for kg_id, kg_item in data[project_name]['entities'][entity_name].iteritems():
                for tag_name_, annotation in kg_item.iteritems():
                    if tag_name == tag_name_:
                        result[kg_id] = annotation
        return result

    @requires_auth
    def post(self, project_name, tag_name, entity_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        if entity_name not in data[project_name]['entities']:
            return rest.not_found('Entity {} not found'.format(entity_name))

        input = request.get_json(force=True)
        kg_id = input.get('kg_id', '')
        if len(kg_id) == 0:
            return rest.bad_request('Invalid kg_id')
        human_annotation = input.get('human_annotation', -1)
        if not isinstance(human_annotation, int) or human_annotation == -1:
            return rest.bad_request('Invalid human annotation')

        # if kg_id not in data[project_name]['entities'][entity_name]:
        #     return rest.not_found('kg_id {} not found'.format(kg_id))
        #
        # if tag_name not in data[project_name]['entities'][entity_name][kg_id]:
        #     return rest.not_found('Tag {} not found'.format(tag_name))

        if kg_id not in data[project_name]['entities'][entity_name]:
            data[project_name]['entities'][entity_name][kg_id] = dict()

        data[project_name]['entities'][entity_name][kg_id][tag_name] = dict()

        data[project_name]['entities'][entity_name][kg_id][tag_name]['human_annotation'] = human_annotation
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/entity_annotations.json')
        write_to_file(json.dumps(data[project_name]['entities'], indent=4), file_path)
        # self.write_to_tag_file(project_name, tag_name)
        # load to ES
        self.update_tag_annotation('full', project_name, kg_id, tag_name, human_annotation)
        self.update_tag_annotation('sample', project_name, kg_id, tag_name, human_annotation)

        return rest.created()

    @requires_auth
    def put(self, project_name, tag_name, entity_name):
        return self.post(project_name, tag_name, entity_name)


    @staticmethod
    def update_tag_annotation(index_version, project_name, kg_id, tag_name, human_annotation):
        try:
            es = ES(config['es']['url'])
            index = data[project_name]['master_config']['index'][index_version]
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                # should retrieve one doc
                # print json.dumps(hits['hits']['hits'][0]['_source'], indent=2)
                doc = hits['hits']['hits'][0]['_source']
                if 'knowledge_graph' not in doc:
                    doc['knowledge_graph'] = dict()
                if '_tags' not in doc['knowledge_graph']:
                    doc['knowledge_graph']['_tags'] = dict()
                if tag_name not in doc['knowledge_graph']['_tags']:
                    doc['knowledge_graph']['_tags'][tag_name] = dict()
                doc['knowledge_graph']['_tags'][tag_name]['human_annotation'] = human_annotation
                res = es.load_data(index, type, doc, doc['doc_id'])
                if not res:
                    logger.info('Fail to retrieve or load data to {}: project {}, kg_id {}, tag{}, index {}, type {}'
                   .format(index_version, project_name, kg_id, tag_name, index, type))
                    return

            logger.info('Fail to retrieve or load data to {}: project {}, kg_id {}, tag{}, index {}, type {}'
                .format(index_version, project_name, kg_id, tag_name, index, type))
            return
        except Exception as e:
            print e
            logger.warning('Fail to update annotation to {}: project {}, kg_id {}, tag {}'
                .format(index_version, project_name, kg_id, tag_name))

    @staticmethod
    def remove_tag_annotation(index_version, project_name, kg_id, tag_name):
        try:
            es = ES(config['es']['url'])
            index = data[project_name]['master_config']['index'][index_version]
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                doc = hits['hits']['hits'][0]['_source']
                if 'knowledge_graph' not in doc:
                    return
                if '_tags' not in doc['knowledge_graph']:
                    return
                if tag_name not in doc['knowledge_graph']['_tags']:
                    return
                if 'human_annotation' not in doc['knowledge_graph']['_tags'][tag_name]:
                    return
                # here, I only removed 'human_annotation' instead of the whole tag
                # for tag should be deleted in another api
                del doc['knowledge_graph']['_tags'][tag_name]['human_annotation']
                res = es.load_data(index, type, doc, doc['doc_id'])
                if not res:
                    logger.info('Fail to retrieve or load data to {}: project {}, kg_id {}, tag{}, index {}, type {}'
                        .format(index_version, project_name, kg_id, tag_name, index, type))
                    return

            logger.info('Fail to retrieve or load data to {}: project {}, kg_id {}, tag{}, index {}, type {}'
                .format(index_version, project_name, kg_id, tag_name, index, type))
            return
        except Exception as e:
            print e
            logger.warning('Fail to remove annotation from {}: project {}, kg_id {}, tag {}'.format(
                index_version, project_name, kg_id, tag_name
            ))

    @staticmethod
    def write_to_tag_file(project_name, tag_name):
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/' + tag_name + '.csv')
        tag_obj = data[project_name]['entities']
        with open(file_path, 'w') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=['tag_name', 'entity_name', 'kg_id', 'human_annotation'],
                delimiter=' ', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for entity_name_, entity in tag_obj.iteritems():
                for kg_id_, kg in entity.iteritems():
                    for tag_name_, tag in kg.iteritems():
                        if tag_name_ == tag_name and 'human_annotation' in tag:
                            writer.writerow(
                                {'tag_name': tag_name_, 'entity_name': entity_name_,
                                 'kg_id': kg_id_, 'human_annotation': tag['human_annotation']})

    @staticmethod
    def read_from_tag_file(project_name, tag_name):
        pass


@api.route('/projects/<project_name>/tags/<tag_name>/annotations/<entity_name>/annotations/<kg_id>')
class TagAnnotationsForEntity(Resource):
    @requires_auth
    def delete(self, project_name, tag_name, entity_name, kg_id):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        if entity_name not in data[project_name]['entities']:
            return rest.not_found('Entity {} not found'.format(entity_name))
        if kg_id not in data[project_name]['entities'][entity_name]:
            return rest.not_found('kg_id {} not found'.format(kg_id))

        if tag_name not in data[project_name]['entities'][entity_name][kg_id]:
            return rest.not_found('kg_id {} not found'.format(kg_id))
        if 'human_annotation' in data[project_name]['entities'][entity_name][kg_id][tag_name]:
            del data[project_name]['entities'][entity_name][kg_id][tag_name]['human_annotation']

        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/entity_annotations.json')
        write_to_file(json.dumps(data[project_name]['entities'], indent=4), file_path)
        # remove from ES
        TagAnnotationsForEntityType.remove_tag_annotation('full', project_name, kg_id, tag_name)
        TagAnnotationsForEntityType.remove_tag_annotation('sample', project_name, kg_id, tag_name)

        return rest.deleted()

    @requires_auth
    def get(self, project_name, tag_name, entity_name, kg_id):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        if entity_name not in data[project_name]['entities']:
            return rest.not_found('Entity {} not found'.format(entity_name))
        if kg_id not in data[project_name]['entities'][entity_name]:
            return rest.not_found('kg_id {} not found'.format(kg_id))

        if tag_name not in data[project_name]['entities'][entity_name][kg_id]:
            return rest.not_found('kg_id {} not found'.format(kg_id))
        # if 'human_annotation' not in data[project_name]['entities'][entity_name][kg_id][tag_name]:
        #     return rest.not_found('No human_annotation')

        ret = data[project_name]['entities'][entity_name][kg_id][tag_name]
        # return knowledge graph
        parser = reqparse.RequestParser()
        parser.add_argument('kg', required=False, type=bool, help='knowledge graph')
        args = parser.parse_args()

        if args['kg']:
            ret['knowledge_graph'] = self.get_kg(project_name, kg_id, tag_name)

        return ret

    @staticmethod
    def get_kg(project_name, kg_id, tag_name):
        try:
            es = ES(config['es']['url'])
            index = data[project_name]['master_config']['index']['full']
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                doc = hits['hits']['hits'][0]['_source']
                if 'knowledge_graph' not in doc:
                    return None
                return doc['knowledge_graph']

            return None
        except Exception as e:
            print e
            logger.warning('Fail to update annotation to: project {}, kg_id {}, tag {}'.format(
                project_name, kg_id, tag_name
            ))


if __name__ == '__main__':
    try:

        # init
        for project_name in os.listdir(config['repo']['local_path']):
            project_dir_path = _get_project_dir_path(project_name)
            if os.path.isdir(project_dir_path) and not project_name.startswith('.'):
                data[project_name] = templates.get('project')

                master_config_file_path = os.path.join(project_dir_path, 'master_config.json')
                if not os.path.exists(master_config_file_path):
                    logger.error('Missing master_config.json file for ' + project_name)
                with open(master_config_file_path, 'r') as f:
                    data[project_name]['master_config'] = json.loads(f.read())
                    # if 'index' not in data[project_name]['master_config'] or \
                    #         any(k not in data[project_name]['master_config']['index'] for k in ('sample', 'full')):
                    #     raise Exception('Missing index in project {}'.format(project_name))
                    # sys.exit()

                entity_annotations_path = os.path.join(project_dir_path, 'entity_annotations/entity_annotations.json')
                with open(entity_annotations_path, 'r') as f:
                    data[project_name]['entities'] = json.loads(f.read())

                field_annotations_path = os.path.join(project_dir_path, 'field_annotations/field_annotations.json')
                with open(field_annotations_path, 'r') as f:
                    data[project_name]['field_annotations'] = json.loads(f.read())

                dir_path = os.path.join(project_dir_path, 'glossaries')
                for file_name in os.listdir(dir_path):
                    name, ext = os.path.splitext(file_name)
                    if ext == '.txt':
                        data[project_name]['glossaries'].append(name)

        # print json.dumps(data, indent=4)
        # run app
        app.run(debug=config['debug'], host=config['server']['host'], port=config['server']['port'])

    except Exception as e:
        print e
        logger.error(e.message)
