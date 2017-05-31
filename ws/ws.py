import os
import shutil
import logging
import json
import types
import threading
import copy


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

def json_encode(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


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


def read_entity_annotations_from_disk(dir_path):
    entities = dict()
    for tag_file in os.listdir(dir_path):
        tag_name = tag_file[0:len(tag_file) - 5]
        tag_file_path = os.path.join(dir_path, tag_file)
        f = codecs.open(tag_file_path, 'r')
        entities[tag_name] = dict()
        for line in f:
            line = line.replace('\n', '')
            vals = line.split('\t')
            kg_id = vals[0]
            human_annotation = vals[1]
            entities[tag_name][kg_id] = dict()
            entities[tag_name][kg_id]['human_annotation'] = human_annotation
    return entities


def read_field_annotations_from_disk(file_path):
    if os.path.exists(file_path):
        field_annotations = dict()
        f = codecs.open(file_path, 'r')
        for line in f:
            line = line.replace('\n', '')
            vals = line.split('\t')
            kg_id = vals[0]
            field_name = vals[1]
            key = vals[2]
            human_annotation = vals[3]
            if kg_id not in field_annotations:
                field_annotations[kg_id] = dict()
            if field_name not in field_annotations[kg_id]:
                field_annotations[kg_id][field_name] = dict()
            if key not in field_annotations[kg_id][field_name]:
                field_annotations[kg_id][field_name][key] = dict()
            field_annotations[kg_id][field_name][key]['human_annotation'] = human_annotation
        return field_annotations
    return {}


@api.route('/debug')
class Debug(Resource):

    def get(self):
        if not config['debug']:
            return abort(404)
        debug_info = {
            'lock': {k: v.locked() for k, v in project_lock._lock.iteritems()},
            'data': json.loads(json.dumps(data, default=json_encode))
        }
        return debug_info


@app.route('/spec')
def spec():
    return render_template('swagger_index.html', title='MyDIG web service API reference', spec_path='/spec.yaml')


@app.route('/spec.yaml')
def spec_file_path():
    with open('spec.yaml', 'r') as f:
        content = f.read()
    return Response(content, mimetype='text/x-yaml')


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
                f.write(json.dumps(data[project_name]['master_config'], indent=4, default=json_encode))

            os.makedirs(os.path.join(project_dir_path, 'field_annotations'))
            write_to_file('', os.path.join(project_dir_path, 'field_annotations/field_annotations.json'))
            os.makedirs(os.path.join(project_dir_path, 'entity_annotations'))
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


@api.route('/')
class Home(Resource):
    def get(self):
        return 'Welcome'


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
            data[project_name]['master_config'] = project_sources
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
            # shutil.rmtree(os.path.join(_get_project_dir_path(project_name)))
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
        return list(data[project_name]['master_config']['tags'])

    def delete(self, project_name):
        # delete all the tags for this project
        if project_name not in data:
            return rest.not_found("Project \'{}\' not found".format(project_name))
        data[project_name]['master_config']['tags'] = set()
        return rest.deleted()

    def post(self, project_name):
        if project_name not in data:
            return rest.not_found("Project \'{}\' not found".format(project_name))
        # create a tag for this project
        if 'tags' not in data[project_name]:
            data[project_name]['master_config']['tags'] = set()
        tag = request.get_json(force=True).get('tag_name', '')
        data[project_name]['master_config']['tags'].add(tag)
        return rest.created()


@api.route('/projects/<project_name>/tags/<tag_name>')
class Tag(Resource):
    def delete(self, project_name, tag_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))
        data[project_name]['master_config']['tags'].remove(tag_name)
        return rest.deleted()


@api.route('/projects/<project_name>/fields/<field_name>/annotations')
class EntityAnnotations(Resource):
    def get(self, project_name, field_name):
        pass
        # if project_name not in data:
        #     return rest.not_found('Project: {} not found'.format(project_name))
        # if field_name not in data[project_name]:
        #     return rest.not_found('Field name not found')
        # return data[project_name][field_name]

    def delete(self):
        # do something
        pass

    def post(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if 'field_annotations' not in data[project_name]:
            data[project_name]['field_annotations'] = dict()
        post_data = request.get_json(force=True)
        kg_id = post_data.get('kg_id', '')
        if kg_id.strip() == '':
            return rest.bad_request('invalid kg_id')
        human_annotation = post_data.get('human_annotation', '')
        if human_annotation.strip() == '':
            return rest.bad_request('invalid human_annotation')
        key = post_data.get('key', '')
        if key.strip() == '':
            return rest.bad_request('invalid key')

        if kg_id not in data[project_name]['field_annotations']:
            data[project_name]['field_annotations'][kg_id] = dict()

        if field_name not in data[project_name]['field_annotations'][kg_id]:
            data[project_name]['field_annotations'][kg_id][field_name] = dict()

        if key not in data[project_name]['field_annotations'][kg_id][field_name]:
            data[project_name]['field_annotations'][kg_id][field_name][key] = dict()

        data[project_name]['field_annotations'][kg_id][field_name][key]['human_annotation'] = human_annotation
        # write to file
        file_content = ''
        field_annotations = data[project_name]['field_annotations']
        for kg_id in field_annotations.keys():
            field_names = field_annotations[kg_id]
            for field_name in field_names.keys():
                field_keys = field_names[field_name]
                for key in field_keys.keys():
                    human_annotation = field_keys[key]['human_annotation']
                    file_content += kg_id + '\t' + field_name + '\t' + key + '\t' + human_annotation + "\n"
        file_name = config['repo']['local_path'] + "/" + project_name + "/field_annotations/field_annotations.json"
        write_to_file(file_content, file_name)
        # load into ES
        # TODO TO DO
        return rest.created()


@api.route('/projects/<project_name>/entities/<kg_id>/fields/<field_name>/annotations/<key>')
class FieldAnnotationsForEntity(Resource):
    def get(self, project_name, kg_id, field_name, key):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if 'field_annotations' not in data[project_name]:
            data[project_name]['field_annotations'] = dict()
            # nothing can be found now, as we are creating the field_annotations right now
            return rest.not_found('Field annotations not found for project: {} '.format(project_name))
        if kg_id not in data[project_name]['field_annotations']:
            return rest.not_found('Field annotations not found for project: {}, kg_id: {}'.format(project_name, kg_id))
        if field_name not in data[project_name]['field_annotations'][kg_id]:
            return rest.not_found(
                'Field annotations not found for project: {}, kg_id: {}, field: {}'.format(project_name, kg_id,
                                                                                           field_name))
        if key not in data[project_name]['field_annotations'][kg_id][field_name]:
            return rest.not_found(
                'Field annotations not found for project: {}, kg_id: {}, field: {}, key: {}'.format(project_name, kg_id,
                                                                                                    field_name, key))

        return data[project_name]['field_annotations'][kg_id][field_name][key]

    def delete(self):
        # do something
        pass

    def put(self):
        # do something
        pass


@api.route('/projects/<project_name>/entities/<kg_id>/tags')
class EntityTags(Resource):
    def get(self, project_name, kg_id):
        if project_name not in data:
            return rest.not_found()
        if kg_id not in data[project_name]['entities']:
            return rest.not_found()

        return data[project_name]['entities'][kg_id]['tags']

    def post(self, project_name, kg_id):
        if project_name not in data:
            return rest.not_found()
        input = request.get_json(force=True)
        if len(kg_id) == 0:
            return rest.bad_request()
        tag = input.get('tags', '')
        if not tag or tag.strip() == '':
            return rest.bad_request('input is not a valid tag')

        human_annotation = str(input.get('human_annotation', ''))

        if not human_annotation or human_annotation.strip() == '' or (
                        human_annotation != '1' and human_annotation != '0'):
            return rest.bad_request('invalid human annotation, value can be either 1(true) or 0(false)')
        try:
            project_lock.acquire(project_name)

            if tag not in data[project_name]['entities']:
                data[project_name]['entities'][tag] = dict()

            if kg_id not in data[project_name]['entities'][tag]:
                data[project_name]['entities'][tag][kg_id] = dict()
            data[project_name]['entities'][tag][kg_id]['human_annotation'] = human_annotation

            # write all annotations for this tag to file
            tag_annotation = data[project_name]['entities'][tag]
            file_content = ''
            for id in tag_annotation.keys():
                file_content += id + '\t' + tag_annotation[id]['human_annotation'] + '\n'
            file_name = config['repo']['local_path'] + "/" + project_name + "/entity_annotations/" + tag + ".json"
            write_to_file(file_content, file_name)
            # load the results into doc in ES
            self.add_tag_kg_id(kg_id, tag, human_annotation)
            return rest.created()
        except Exception as e:
            print e
            logger.error('deleting project %s: %s' % (project_name, e.message))
            return rest.internal_error('deleting project %s error, halted.' % project_name)
        finally:
            project_lock.release(project_name)

    @staticmethod
    def add_tag_kg_id(kg_id, tag_name, human_annotation):
        es = ES(config['write_es']['es_url'])
        hits = es.retrieve_doc(config['write_es']['index'], config['write_es']['doc_type'], kg_id)
        if hits:
            # should retrieve one doc
            # print json.dumps(hits['hits']['hits'][0]['_source'], indent=2)
            doc = hits['hits']['hits'][0]['_source']

            if 'knowledge_graph' not in doc:
                doc['knowledge_graph'] = dict()
            doc['knowledge_graph'] = EntityTags.add_tag_to_kg(doc['knowledge_graph'], tag_name, human_annotation)
            res = es.load_data(config['write_es']['index'], config['write_es']['doc_type'], doc, doc['doc_id'])
            if res:
                return rest.ok('Tag \'{}\' added to doc: \'{}\''.format(tag_name, kg_id))

        else:
            return rest.not_found('doc: \'{}\' not found in elasticsearch'.format(kg_id))

    @staticmethod
    def add_tag_to_kg(kg, tag_name, human_annotation):
        if '_tags' not in kg:
            kg['_tags'] = dict()
        if tag_name not in kg['_tags']:
            kg['_tags'][tag_name] = dict()
        kg['_tags'][tag_name]['human_annotation'] = human_annotation
        return kg


@api.route('/projects/<project_name>/fields')
class AllFields(Resource):
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found()
        input = request.get_json(force=True)
        field_name = input.get('field_name', '')
        if len(field_name) == 0:
            return rest.bad_request()
        if field_name in data[project_name]['master_config']['fields']:
            return rest.exists()
        field_object = input.get('field_object', {})

        try:
            project_lock.acquire(project_name)
            data[project_name]['master_config']['fields'][field_name] = field_object
            return rest.created()
        except Exception as e:
            logger.error('creating field %s in project: %s' % (field_name, project_name, e.message))
            return rest.internal_error('creating field %s in project %s error, halted.' % field_name, project_name)
        finally:
            project_lock.release(project_name)

    def get(self, project_name):
        if project_name not in data:
            return rest.not_found()
        return data[project_name]['master_config']['fields']

    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found()

        try:
            project_lock.acquire(project_name)
            data[project_name]['master_config']['fields'] = {}
            return rest.deleted()
        except Exception as e:
            logger.error('deleting all fields in project %s: %s' % (project_name, e.message))
            return rest.internal_error('deleting all fields in project %s error, halted.' % project_name)
        finally:
            project_lock.remove(project_name)


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
        field = input.get('field', {})
        if len(field) == 0:
            return rest.bad_request('Invalid field.')
        try:
            project_lock.acquire(project_name)
            data[project_name]['master_config']['fields'][field_name] = field
            return rest.created()
        except Exception as e:
            logger.error('updating field %s in project %s: %s' % (field_name, project_name, e.message))
            return rest.internal_error('updating field %s in project %s error, halted.' % (field_name, project_name))
        finally:
            project_lock.release(project_name)

    def put(self, project_name, field_name):
        return self.post(project_name, field_name)

    def delete(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found()
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found()
        try:
            project_lock.acquire(project_name)
            del data[project_name]['master_config']['fields'][field_name]
            return rest.deleted()
        except Exception as e:
            logger.error('deleting field %s in project %s: %s' % (field_name, project_name, e.message))
            return rest.internal_error('deleting field %s in project %s error, halted.' % (field_name, project_name))
        finally:
            project_lock.release(project_name)


if __name__ == '__main__':
    try:

        # init
        for project_name in os.listdir(config['repo']['local_path']):
            project_dir_path = _get_project_dir_path(project_name)

            if os.path.isdir(project_dir_path) and not project_name.startswith('.'):
                data[project_name] = templates.get('project')
                # master_config
                master_config_file_path = os.path.join(project_dir_path, 'master_config.json')
                if not os.path.exists(master_config_file_path):
                    logger.error('Missing master_config.json file for ' + project_name)
                with open(master_config_file_path, 'r') as f:
                    data[project_name]['master_config'] = json.loads(f.read())
                    data[project_name]['master_config']['tags'] = set(data[project_name]['master_config']['tags'])

                entity_annotations_path = os.path.join(project_dir_path, 'entity_annotations')
                data[project_name]['entities'] = read_entity_annotations_from_disk(entity_annotations_path)

                field_annotations_path = os.path.join(project_dir_path, 'field_annotations/field_annotations.json')
                data[project_name]['field_annotations'] = read_field_annotations_from_disk(field_annotations_path)

        # run app
        app.run(debug=config['debug'], host=config['server']['host'], port=config['server']['port'])

    except Exception as e:
        print e
        logger.error(e.message)
