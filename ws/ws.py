import os
import shutil
import logging
import json
import yaml
import types
import threading


from flask import Flask, render_template, Response
from flask import request, abort, redirect, url_for
from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api

from config import config
from elastic_manager.elastic_manager import ES
import templates
import rest
import codecs

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


@app.route('/spec')
def spec():
    return render_template('swagger_index.html', title='MyDIG web service API reference', spec_path='/spec.yaml')


@app.route('/spec.yaml')
def spec_file_path():
    with open('spec.yaml', 'r') as f:
        c = yaml.load(f)
        c['host'] = '{}:{}'.format(config['server']['host'], config['server']['port'])
    return Response(yaml.dump(c), mimetype='text/x-yaml')


@api.route('/')
class Home(Resource):
    def get(self):
        return 'Welcome'


@api.route('/projects')
class AllProjects(Resource):
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
            logger.info('project %s created.' % project_name)
            return rest.created()
        except Exception as e:
            logger.error('creating project %s: %s' % (project_name, e.message))
        finally:
            project_lock.release(project_name)

    def get(self):
        return data.keys()

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
            write_to_file(json.dumps(data[project_name], indent=4), file_path)
            return rest.created()
        except Exception as e:
            logger.error('Updating project %s: %s' % (project_name, e.message))
            return rest.internal_error('Updating project %s error, halted.' % project_name)
        finally:
            project_lock.release(project_name)

    def put(self, project_name):
        return self.post(project_name)

    def get(self, project_name):
        if project_name not in data:
            return rest.not_found()
        return data[project_name]

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
    def get(self, project_name):
        # return all the tags created for this project
        if project_name not in data:
            return rest.not_found("Project \'{}\' not found".format(project_name))
        return data[project_name]['master_config']['tags']

    def delete(self, project_name):
        # delete all the tags for this project
        if project_name not in data:
            return rest.not_found("Project \'{}\' not found".format(project_name))
        data[project_name]['master_config']['tags'] = dict()
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.deleted()

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
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.created()


@api.route('/projects/<project_name>/tags/<tag_name>')
class Tag(Resource):
    def get(self, project_name, tag_name):
        if project_name not in data:
            return rest.not_found("Project {} not found".format(project_name))
        print data[project_name].keys()
        print data[project_name]['master_config']
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found("Tag {} not found".format(tag_name))
        return data[project_name]['master_config']['tags'][tag_name]

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
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.created()

    def put(self, project_name, tag_name):
        return self.post(project_name, tag_name)

    def delete(self, project_name, tag_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        del data[project_name]['master_config']['tags'][tag_name]
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.deleted()


@api.route('/projects/<project_name>/fields')
class ProjectFields(Resource):
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
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.created()

    def get(self, project_name):
        if project_name not in data:
            return rest.not_found()
        return data[project_name]['master_config']['fields']

    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found()

        data[project_name]['master_config']['fields'] = dict()
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.deleted()


@api.route('/projects/<project_name>/fields/<field_name>')
class Field(Resource):
    def get(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found()
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found()
        return data[project_name]['master_config']['fields'][field_name]

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
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.created()

    def put(self, project_name, field_name):
        return self.post(project_name, field_name)

    def delete(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found()
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found()
        del data[project_name]['master_config']['fields'][field_name]
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
        write_to_file(json.dumps(data[project_name], indent=4), file_path)
        return rest.deleted()


@api.route('/projects/<project_name>/entities/<entity_name>/<kg_id>/tags')
class EntityTags(Resource):
    def get(self, project_name, entity_name, kg_id):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if entity_name not in data[project_name]['entities']:
            return rest.not_found('Entity {} not found'.format(entity_name))
        if kg_id not in data[project_name]['entities'][entity_name]:
            return rest.not_found('kg_id {} not found'.format(kg_id))

        return data[project_name]['entities'][entity_name][kg_id]

    def post(self, project_name, entity_name, kg_id):
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


    # def post(self, project_name, kg_id):
    #     if project_name not in data:
    #         return rest.not_found()
    #     input = request.get_json(force=True)
    #     if len(kg_id) == 0:
    #         return rest.bad_request()
    #     tag = input.get('tags', '')
    #     if not tag or tag.strip() == '':
    #         return rest.bad_request('input is not a valid tag')
    #
    #     human_annotation = str(input.get('human_annotation', ''))
    #
    #     if not human_annotation or human_annotation.strip() == '' or (
    #                     human_annotation != '1' and human_annotation != '0'):
    #         return rest.bad_request('invalid human annotation, value can be either 1(true) or 0(false)')
    #
    #     if tag not in data[project_name]['entities']:
    #         data[project_name]['entities'][tag] = dict()
    #
    #     if kg_id not in data[project_name]['entities'][tag]:
    #         data[project_name]['entities'][tag][kg_id] = dict()
    #     data[project_name]['entities'][tag][kg_id]['human_annotation'] = human_annotation
    #
    #     # write all annotations for this tag to file
    #     tag_annotation = data[project_name]['entities'][tag]
    #     file_content = ''
    #     for id in tag_annotation.keys():
    #         file_content += id + '\t' + tag_annotation[id]['human_annotation'] + '\n'
    #     file_name = os.path.join(_get_project_dir_path(project_name), "/entity_annotations/" + tag + ".json")
    #     write_to_file(file_content, file_name)
    #     # load the results into doc in ES
    #     self.add_tag_kg_id(kg_id, tag, human_annotation)
    #     return rest.created()
    #
    # @staticmethod
    # def add_tag_kg_id(kg_id, tag_name, human_annotation):
    #     es = ES(config['write_es']['es_url'])
    #     hits = es.retrieve_doc(config['write_es']['index'], config['write_es']['doc_type'], kg_id)
    #     if hits:
    #         # should retrieve one doc
    #         # print json.dumps(hits['hits']['hits'][0]['_source'], indent=2)
    #         doc = hits['hits']['hits'][0]['_source']
    #
    #         if 'knowledge_graph' not in doc:
    #             doc['knowledge_graph'] = dict()
    #         doc['knowledge_graph'] = EntityTags.add_tag_to_kg(doc['knowledge_graph'], tag_name, human_annotation)
    #         res = es.load_data(config['write_es']['index'], config['write_es']['doc_type'], doc, doc['doc_id'])
    #         if res:
    #             return rest.ok('Tag \'{}\' added to doc: \'{}\''.format(tag_name, kg_id))
    #
    #     else:
    #         return rest.not_found('doc: \'{}\' not found in elasticsearch'.format(kg_id))
    #
    # @staticmethod
    # def add_tag_to_kg(kg, tag_name, human_annotation):
    #     if '_tags' not in kg:
    #         kg['_tags'] = dict()
    #     if tag_name not in kg['_tags']:
    #         kg['_tags'][tag_name] = dict()
    #     kg['_tags'][tag_name]['human_annotation'] = human_annotation
    #     return kg


@api.route('/projects/<project_name>/entities/<kg_id>/fields/<field_name>/annotations')
class FieldAnnotations(Resource):
    def get(self, project_name, kg_id, field_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if kg_id not in data[project_name]['field_annotations']:
            return rest.not_found('kg_id {} not found'.format(kg_id))
        if field_name not in data[project_name]['field_annotations'][kg_id]:
            return rest.not_found('Field name {} not found'.format(field_name))
        return data[project_name]['field_annotations'][kg_id][field_name]

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
        # TODO
        return rest.deleted()

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
        # TODO
        return rest.created()


@api.route('/projects/<project_name>/entities/<kg_id>/fields/<field_name>/annotations/<key>')
class FieldInstanceAnnotations(Resource):
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
        # TODO
        return rest.deleted()

    def post(self, project_name, kg_id, field_name, key):
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

        input = request.get_json(force=True)
        human_annotation = input.get('human_annotation', None)
        if not isinstance(human_annotation, int) or human_annotation == -1:
            return rest.bad_request('invalid human_annotation')
        data[project_name]['field_annotations'][kg_id][field_name][key]['human_annotation'] = human_annotation
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'field_annotations/field_annotations.json')
        write_to_file(json.dumps(data[project_name]['field_annotations'], indent=4), file_path)
        # load into ES
        # TODO
        return rest.created()

    def put(self, project_name, kg_id, field_name, key):
        return self.post(project_name, kg_id, field_name, key)


@api.route('/projects/<project_name>/tags/<tag_name>/annotations/<entity_name>/annotations')
class TagAnnotationsForEntity(Resource):
    def delete(self, project_name, tag_name, entity_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        if entity_name not in data[project_name]['entities']:
            return rest.not_found('Entity {} not found'.format(entity_name))

        for kg_item in data[project_name]['entities'][entity_name].values():
            if tag_name in kg_item.iterkeys():
                if 'human_annotation' in kg_item[tag_name]:
                    del kg_item[tag_name]['human_annotation']

        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/entity_annotations.json')
        write_to_file(json.dumps(data[project_name]['entities'], indent=4), file_path)
        return rest.deleted()

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

        if kg_id not in data[project_name]['entities'][entity_name]:
            return rest.not_found('kg_id {} not found'.format(kg_id))

        if tag_name not in data[project_name]['entities'][entity_name][kg_id]:
            return rest.not_found('Tag {} not found'.format(tag_name))

        data[project_name]['entities'][entity_name][kg_id][tag_name]['human_annotation'] = human_annotation
        # write to file
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/entity_annotations.json')
        write_to_file(json.dumps(data[project_name]['entities'], indent=4), file_path)
        return rest.created()


    def put(self, project_name, tag_name, entity_name):
        return self.post(project_name, tag_name, entity_name)


@api.route('/projects/<project_name>/tags/<tag_name>/annotations/<entity_name>/annotations/<kg_id>')
class TagAnnotationsForInstanceOfEntity(Resource):
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
        return rest.deleted()

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

        return data[project_name]['entities'][entity_name][kg_id][tag_name]

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

                entity_annotations_path = os.path.join(project_dir_path, 'entity_annotations/entity_annotations.json')
                with open(entity_annotations_path, 'r') as f:
                    data[project_name]['entities'] = json.loads(f.read())

                field_annotations_path = os.path.join(project_dir_path, 'field_annotations/field_annotations.json')
                with open(field_annotations_path, 'r') as f:
                    data[project_name]['field_annotations'] = json.loads(f.read())

        # run app
        app.run(debug=config['debug'], host=config['server']['host'], port=config['server']['port'])

    except Exception as e:
        print e
        logger.error(e.message)
