import os
import sys
import shutil
import distutils.dir_util
import logging
import json
import yaml
import types
import werkzeug
import codecs
import csv
import multiprocessing
import subprocess
import thread
import threading
import requests
import gzip
import tarfile
import re
import hashlib
import traceback
import time
import datetime
import random
import signal
import base64
from flask import Flask, render_template, Response, make_response
from flask import request, abort, redirect, url_for, send_file
from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api, reqparse

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
from tldextract import tldextract
import dateparser

from config import config
from search.elastic_manager import ES
import templates
import rest
from basic_auth import requires_auth, requires_auth_html
import git_helper
import etk_helper
import data_persistence
from search.conjunctive_query import ConjunctiveQueryProcessor
from search.event_query import EventQueryProcessor
import requests.packages.urllib3

sys.path.append(os.path.join(config['etk']['path'],
                             'etk/structured_extractors/digTokenizerExtractor/digCrfTokenizer'))
from crf_tokenizer import CrfTokenizer

requests.packages.urllib3.disable_warnings()

# logger
logger = logging.getLogger(config['logging']['name'])
log_formatter = logging.Formatter(config['logging']['format'])
if config['logging'].get('file_path') and config['logging']['file_path'] != '':
    log_file = logging.FileHandler(config['logging']['file_path'])
    log_file.setFormatter(log_formatter)
    logger.addHandler(log_file)
else:
    log_stdout = logging.StreamHandler(sys.stdout)
    log_stdout.setFormatter(log_formatter)
    logger.addHandler(log_stdout)
logger.setLevel(config['logging']['level'])
logging.getLogger('werkzeug').setLevel(config['logging']['werkzeug'])
# print logging.Logger.manager.loggerDict.get('werkzeug')

# flask app
app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=1024 * 1024 * 1024 * 10)
cors = CORS(app, resources={r"*": {"origins": "*"}}, supports_credentials=True)
api = Api(app)


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls

    return wrapper


api.route = types.MethodType(api_route, api)

# in-memory data
data = {}

# regex precompile
re_project_name = re.compile(r'^[a-z0-9]{1}[a-z0-9_-]{0,254}$')
re_url = re.compile(r'[^0-9a-z-_]+')
re_doc_id = re.compile(r'^[a-zA-Z0-9_-]{1,255}$')
os_reserved_file_names = ('CON', 'PRN', 'AUX', 'NUL',
                          'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                          'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9')

# kafka
kafka_producer = None


def write_to_file(content, file_path):
    with codecs.open(file_path, 'w') as f:
        f.write(content)


def update_master_config_file(project_name):
    file_path = os.path.join(_get_project_dir_path(project_name), 'master_config.json')
    write_to_file(json.dumps(data[project_name]['master_config'], indent=4), file_path)


def set_status_dirty(project_name):
    data[project_name]['status_memory_dump_worker'].memory_timestamp = time.time()


def update_status_file(project_name):
    status_file_path = os.path.join(_get_project_dir_path(project_name), 'working_dir/status.json')
    data_persistence.dump_data(json.dumps(data[project_name]['status'], indent=4), status_file_path)


def set_catalog_dirty(project_name):
    data[project_name]['catalog_memory_dump_worker'].memory_timestamp = time.time()


def update_catalog_file(project_name):
    data_db_path = os.path.join(_get_project_dir_path(project_name), 'data/_db.json')
    data_persistence.dump_data(json.dumps(data[project_name]['data']), data_db_path)


def _get_project_dir_path(project_name):
    return os.path.join(config['repo']['local_path'], project_name)


def _add_keys_to_dict(obj, keys):  # dict, list
    curr_obj = obj
    for key in keys:
        if key not in curr_obj:
            curr_obj[key] = dict()
        curr_obj = curr_obj[key]
    return obj


def tail_file(f, lines=1, _buffer=4098):
    # https://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        # Removed this line because it was redundant the while will catch
        # it, I left it for history
        # if len(lines_found) > lines:
        #    break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]


@app.route('/spec')
def spec():
    return render_template('swagger_index.html', title='MyDIG web service API reference', spec_path='spec.yaml')


@app.route('/spec.yaml')
def spec_file_path():
    with codecs.open('spec.yaml', 'r') as f:
        c = yaml.load(f)
        c['host'] = request.host
    return Response(yaml.dump(c), mimetype='text/x-yaml')


@app.route('/')
def home():
    return 'MyDIG Web Service\n'


@api.route('/authentication')
class Authentication(Resource):
    @requires_auth
    def get(self):
        # no need to do anything here
        # if user can pass the basic auth, it will return ok here
        # or it will be blocked by auth verification
        return rest.ok()


@api.route('/projects/<project_name>/debug/<mode>')
class ProjectDebug(Resource):
    @requires_auth
    def get(self, project_name, mode):
        if mode == 'threads':
            ret = {
                'threads': dict(),
                'data_pushing_worker': data[project_name]['data_pushing_worker'].get_status(),
                'status_memory_dump_worker': data[project_name]['status_memory_dump_worker'].get_status(),
                'catalog_memory_dump_worker': data[project_name]['catalog_memory_dump_worker'].get_status()
            }
            for t in data[project_name]['threads']:
                ret['threads'][t.ident] = {
                    'is_alive': t.is_alive(),
                    'name': t.name
                }
            return ret

        elif mode == 'etk_stdout':
            size = request.args.get('size', '20')
            worker_id = request.args.get('worker_id', '*')
            cmd = 'tail -n {size} {dir_path}/etk_stdout_{worker_id}.txt'.format(
                    size=size,
                    dir_path=os.path.join(_get_project_dir_path(project_name),'working_dir'),
                    worker_id=worker_id)
            logger.debug('getting etk_stdout: %s', cmd)
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            return Response(proc.stdout.read(), mimetype='text/plain')

        return dict()


@api.route('/projects/<project_name>/search/<type>')
class Search(Resource):
    @requires_auth
    def get(self, project_name, type):
        if project_name not in data:
            return rest.not_found()
        logger.error('API Request received for %s' % (project_name))

        es = ES(config['es']['sample_url'])
        if type == 'conjunctive':
            query = ConjunctiveQueryProcessor(request, project_name,
                                          data[project_name]['master_config']['fields'],
                                          data[project_name]['master_config']['root_name'], es)
            return query.process()
        elif type == 'event':
            query = EventQueryProcessor(request, project_name,
                                        data[project_name]['master_config']['fields'],
                                        data[project_name]['master_config']['root_name'], es)
            return query.process_event_query()
        elif type == 'time_series':

            query = EventQueryProcessor(request, project_name,
                                        data[project_name]['master_config']['fields'],
                                        data[project_name]['master_config']['root_name'], es)
            return query.process_ts_query()
        else:
            return rest.not_found('invalid search type')


@api.route('/projects')
class AllProjects(Resource):
    @requires_auth
    def post(self):
        input = request.get_json(force=True)
        project_name = input.get('project_name', '')
        project_name = project_name.lower()  # convert to lower (sandpaper index needs to be lower)
        if not re_project_name.match(project_name) or project_name in config['project_name_blacklist']:
            return rest.bad_request('Invalid project name.')
        if project_name in data:
            return rest.exists('Project name already exists.')

        # only use default settings when creating project
        # is_valid, message = self.validate(input)
        # if not is_valid:
        #     return rest.bad_request(message)

        # create topics in etl engine
        url = config['etl']['url'] + '/create_project'
        payload = {
            'project_name': project_name
        }
        resp = requests.post(url, json.dumps(payload), timeout=config['etl']['timeout'])
        if resp.status_code // 100 != 2:
            return rest.internal_error('Error in ETL Engine when creating project {}'.format(project_name))

        # create project data structure, folders & files
        project_dir_path = _get_project_dir_path(project_name)

        if not os.path.exists(project_dir_path):
            os.makedirs(project_dir_path)

        # create global gitignore file
        write_to_file('', os.path.join(project_dir_path, '.gitignore'))

        # initialize data structure
        data[project_name] = templates.get('project')
        data[project_name]['master_config'] = templates.get('master_config')
        data[project_name]['master_config']['index'] = {
            'sample': project_name,
            'full': project_name + '_deployed',
            'version': 0
        }
        # data[project_name]['master_config']['configuration'] = project_config
        data[project_name]['master_config']['image_prefix'] = input.get('image_prefix', '')
        data[project_name]['master_config']['default_desired_num'] = input.get('default_desired_num', 0)
        data[project_name]['master_config']['show_images_in_facets'] = input.get('show_images_in_facets', False)
        data[project_name]['master_config']['show_images_in_search_form'] = \
            input.get('show_images_in_search_form', False)
        data[project_name]['master_config']['hide_timelines'] = input.get('hide_timelines', False)
        data[project_name]['master_config']['new_linetype'] = input.get('new_linetype', 'break')
        data[project_name]['master_config']['show_original_search'] = input.get('show_original_search', 'V2')
        update_master_config_file(project_name)

        # create other dirs and files
        # .gitignore file should be created for empty folder will not be show in commit
        os.makedirs(os.path.join(project_dir_path, 'field_annotations'))
        write_to_file('', os.path.join(project_dir_path, 'field_annotations/.gitignore'))
        os.makedirs(os.path.join(project_dir_path, 'entity_annotations'))
        write_to_file('', os.path.join(project_dir_path, 'entity_annotations/.gitignore'))
        os.makedirs(os.path.join(project_dir_path, 'glossaries'))
        write_to_file('', os.path.join(project_dir_path, 'glossaries/.gitignore'))
        dst_dir = os.path.join(_get_project_dir_path(project_name), 'glossaries')
        src_dir = config['default_glossaries_path']
        for file_name in os.listdir(src_dir):
            full_file_name = os.path.join(src_dir, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, dst_dir)
        os.makedirs(os.path.join(project_dir_path, 'spacy_rules'))
        write_to_file('', os.path.join(project_dir_path, 'spacy_rules/.gitignore'))
        dst_dir = os.path.join(project_dir_path, 'spacy_rules')
        src_dir = config['default_spacy_rules_path']
        for file_name in os.listdir(src_dir):
            full_file_name = os.path.join(src_dir, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, dst_dir)
        write_to_file('', os.path.join(project_dir_path, 'spacy_rules/.gitignore'))
        os.makedirs(os.path.join(project_dir_path, 'data'))
        write_to_file('*\n', os.path.join(project_dir_path, 'data/.gitignore'))
        os.makedirs(os.path.join(project_dir_path, 'working_dir'))
        write_to_file('*\n', os.path.join(project_dir_path, 'working_dir/.gitignore'))
        os.makedirs(os.path.join(project_dir_path, 'landmark_rules'))
        write_to_file('*\n', os.path.join(project_dir_path, 'landmark_rules/.gitignore'))

        update_status_file(project_name)  # create status file after creating the working_dir

        start_threads_and_locks(project_name)

        # git_helper.commit(files=[project_name + '/*'], message='create project {}'.format(project_name))
        logger.info('project %s created.' % project_name)
        return rest.created()

    @requires_auth
    def get(self):
        return data.keys()

    # don't allow to delete all projects at one time
    # @requires_auth
    # def delete(self):
    #     for project_name in data.keys():  # not iterkeys(), need to do del in iteration
    #         try:
    #             # project_lock.acquire(project_name)
    #             del data[project_name]
    #             shutil.rmtree(os.path.join(_get_project_dir_path(project_name)))
    #         except Exception as e:
    #             logger.error('deleting project %s: %s' % (project_name, e.message))
    #             return rest.internal_error('deleting project %s error, halted.' % project_name)
    #             # finally:
    #             #     project_lock.remove(project_name)
    #
    #     git_helper.commit(message='delete all projects')
    #     return rest.deleted()


    @staticmethod
    def validate(pro_obj):
        """
        :return: bool, message
        """
        if 'image_prefix' not in pro_obj or not isinstance(pro_obj['image_prefix'], basestring):
            return False, 'invalid image_prefix'
        if 'default_desired_num' not in pro_obj or (999999999 < pro_obj['default_desired_num'] < 0):
            return False, 'invalid default_desired_num'
        if 'show_images_in_facets' not in pro_obj or not isinstance(pro_obj['show_images_in_facets'], bool):
            return False, 'invalid show_images_in_facets'
        if 'show_images_in_search_form' not in pro_obj or not isinstance(pro_obj['show_images_in_search_form'], bool):
            return False, 'invalid show_images_in_search_form'
        if 'hide_timelines' not in pro_obj or not isinstance(pro_obj['hide_timelines'], bool):
            return False, 'invalid hide_timelines'
        if 'new_linetype' not in pro_obj or pro_obj['new_linetype'] not in ('break', 'newline'):
            return False, 'invalid new_linetype'
        if 'show_original_search' not in pro_obj:
            pro_obj['show_original_search'] = 'V2'
        if pro_obj['show_original_search'] not in ('V2','V1'):
            return False, 'invalid show_original_search'

        return True, None


@api.route('/projects/<project_name>')
class Project(Resource):
    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found()
        input = request.get_json(force=True)


        is_valid, message = AllProjects.validate(input)
        if not is_valid:
            return rest.bad_request(message)

        # data[project_name]['master_config']['configuration'] = project_config
        data[project_name]['master_config']['image_prefix'] = input.get('image_prefix')
        data[project_name]['master_config']['default_desired_num'] = input.get('default_desired_num')
        data[project_name]['master_config']['show_images_in_facets'] = input.get('show_images_in_facets')
        data[project_name]['master_config']['show_images_in_search_form'] = input.get('show_images_in_search_form')
        data[project_name]['master_config']['hide_timelines'] = input.get('hide_timelines')
        data[project_name]['master_config']['new_linetype'] = input.get('new_linetype')
        data[project_name]['master_config']['show_original_search'] = input.get('show_original_search')
        # data[project_name]['master_config']['index'] = es_index

        # write to file
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='update project {}'.format(project_name))
        return rest.created()

    @requires_auth
    def put(self, project_name):
        return self.post(project_name)

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found()
        return data[project_name]['master_config']

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found()

        # 1. stop etk (and clean up previous queue)
        data[project_name]['data_pushing_worker'].stop_adding_data = True
        if not Actions._etk_stop(project_name, clean_up_queue=True):
            return rest.internal_error('failed to kill_etk in ETL')

        # 2. delete logstash config
        # since queue is empty, leave it here is not a problem
        # but for perfect solution, it needs to be deleted

        # 3. clean up es data
        url = '{}/{}'.format(
            config['es']['sample_url'],
            project_name
        )
        try:
            resp = requests.delete(url, timeout=10)
        except:
            pass  # ignore no index error

        # 4. release resource
        stop_threads_and_locks(project_name)

        # 5. delete all files
        try:
            del data[project_name]
            shutil.rmtree(os.path.join(_get_project_dir_path(project_name)))
        except Exception as e:
            logger.error('delete project error: %s', e)
            return rest.internal_error('delete project error')

        return rest.deleted()


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
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='delete all tags: project {}'.format(project_name))
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
        is_valid, message = self.validate(tag_object)
        if not is_valid:
            return rest.bad_request(message)
        if 'name' not in tag_object or tag_object['name'] != tag_name:
            return rest.bad_request('Name of tag is not correct')
        data[project_name]['master_config']['tags'][tag_name] = tag_object
        # write to file
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='create a tag: project {}, tag {}'.format(project_name, tag_name))
        return rest.created()

    @staticmethod
    def validate(tag_obj):
        """
        :return: bool, message
        """
        if 'name' not in tag_obj or len(tag_obj['name'].strip()) == 0:
            return False, 'Invalid tag attribute: name'
        if 'description' not in tag_obj:
            tag_obj['description'] = ''
        if 'screen_label' not in tag_obj or \
                        len(tag_obj['screen_label'].strip()) == 0:
            tag_obj['screen_label'] = tag_obj['name']
        if 'include_in_menu' not in tag_obj or \
                not isinstance(tag_obj['include_in_menu'], bool):
            return False, 'Invalid tag attribute: include_in_menu'
        if 'positive_class_precision' not in tag_obj or \
                        tag_obj['positive_class_precision'] > 1 or tag_obj['positive_class_precision'] < 0:
            return False, 'Invalid tag attribute: positive_class_precision'
        if 'negative_class_precision' not in tag_obj or \
                        tag_obj['negative_class_precision'] > 1 or tag_obj['negative_class_precision'] < 0:
            return False, 'Invalid tag attribute: negative_class_precision'
        return True, None


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
        is_valid, message = ProjectTags.validate(tag_object)
        if not is_valid:
            return rest.bad_request(message)
        if 'name' not in tag_object or tag_object['name'] != tag_name:
            return rest.bad_request('Name of tag is not correct')
        data[project_name]['master_config']['tags'][tag_name] = tag_object
        # write to file
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='update a tag: project {}, tag {}'.format(project_name, tag_name))
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
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='delete a tag: project {}, tag {}'.format(project_name, tag_name))
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
        is_valid, message = self.validate(field_object)
        if not is_valid:
            return rest.bad_request(message)

        data[project_name]['master_config']['fields'][field_name] = field_object
        # write to file
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='create a field: project {}, field {}'.format(project_name, field_name))
        return rest.created()

    @requires_auth
    def get(self, project_name):
        project_name = project_name.lower()  # patches for inferlink
        if project_name not in data:
            return rest.not_found()
        return data[project_name]['master_config']['fields']

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found()

        data[project_name]['master_config']['fields'] = dict()
        # remove all the fields associate with table attributes
        for k, v in data[project_name]['master_config']['table_attributes'].items():
            v['field_name'] = ''

        # write to file
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='delete all fields: project {}'.format(project_name))
        return rest.deleted()

    @staticmethod
    def validate(field_obj):
        """
        :return: bool, message (str)
        """
        if 'name' not in field_obj or \
                        len(field_obj['name'].strip()) == 0:
            return False, 'Invalid field attribute: name'
        if 'screen_label' not in field_obj or \
                        len(field_obj['screen_label'].strip()) == 0:
            field_obj['screen_label'] = field_obj['name']
        if 'screen_label_plural' not in field_obj or \
                        len(field_obj['screen_label_plural'].strip()) == 0:
            field_obj['screen_label_plural'] = field_obj['screen_label']
        if 'description' not in field_obj:
            field_obj['description'] = ''
        if 'type' not in field_obj or field_obj['type'] not in \
                ('string', 'location', 'username', 'date', 'email', 'hyphenated', 'phone', 'image', 'kg_id', 'number', 'text'):
            return False, 'Invalid field attribute: type'
        if 'show_in_search' not in field_obj or \
                not isinstance(field_obj['show_in_search'], bool):
            return False, 'Invalid field attribute: show_in_search'
        if 'show_in_facets' not in field_obj or \
                not isinstance(field_obj['show_in_facets'], bool):
            return False, 'Invalid field attribute: show_in_facets'
        if 'show_as_link' not in field_obj or \
                        field_obj['show_as_link'] not in ('text', 'entity'):
            return False, 'Invalid field attribute: show_as_link'
        if 'show_in_result' not in field_obj or \
                        field_obj['show_in_result'] not in ('header', 'detail', 'no', 'title', 'description', 'nested'):
            return False, 'Invalid field attribute: show_in_result'
        if 'color' not in field_obj:
            return False, 'Invalid field attribute: color'
        if 'icon' not in field_obj:
            return False, 'Invalid field attribute: icon'
        if 'search_importance' not in field_obj or \
                        field_obj['search_importance'] not in range(1, 11):
            return False, 'Invalid field attribute: search_importance'
        if 'use_in_network_search' not in field_obj or \
                not isinstance(field_obj['use_in_network_search'], bool):
            return False, 'Invalid field attribute: use_in_network_search'
        if 'group_name' not in field_obj:
            return False, 'Invalid field attribute: group_name'
        if 'combine_fields' not in field_obj:
            field_obj['combine_fields'] = False
        if 'glossaries' not in field_obj or \
                not isinstance(field_obj['glossaries'], list):
            return False, 'Invalid field attribute: glossaries'
        if 'rule_extractor_enabled' not in field_obj:
            field_obj['rule_extractor_enabled'] = False
        if 'number_of_rules' not in field_obj:
            field_obj['number_of_rules'] = 0
        if 'predefined_extractor' not in field_obj or field_obj['predefined_extractor'] not in \
                ('social_media', 'review_id', 'posting_date', 'phone', 'email', 'address', 'TLD', 'none'):
            field_obj['predefined_extractor'] = 'none'
        if 'rule_extraction_target' not in field_obj or \
                        field_obj['rule_extraction_target'] not in (
                'title_only', 'description_only', 'title_and_description'):
            field_obj['rule_extraction_target'] = 'title_and_description'
        if 'case_sensitive' not in field_obj or \
                not isinstance(field_obj['case_sensitive'], bool) or \
                        len(field_obj['glossaries']) == 0:
            field_obj['case_sensitive'] = False
        if 'blacklists' not in field_obj or \
                not isinstance(field_obj['blacklists'], list):
            field_obj['blacklists'] = list()
        if 'field_order' in field_obj:
            if not isinstance(field_obj['field_order'], int):
                del field_obj['field_order']
        if 'group_order' in field_obj:
            if not isinstance(field_obj['group_order'], int):
                del field_obj['group_order']
        if 'free_text_search' not in field_obj \
                or not isinstance(field_obj['free_text_search'], bool):
                field_obj['free_text_search'] = False
        if 'scoring_coefficient' not in field_obj:
                field_obj['scoring_coefficient'] = float(1.0)
        if 'enable_scoring_coefficient' not in field_obj:
                field_obj['enable_scoring_coefficient'] = False
        if 'enable_scoring_coefficient' in field_obj and not isinstance(field_obj['enable_scoring_coefficient'],bool):
                return False, 'Invalid field attribute: enable_scoring_coefficient'
        if 'scoring_coefficient' in field_obj and not (isinstance(field_obj['scoring_coefficient'],float) or isinstance(field_obj['scoring_coefficient'],int)):
                return False, 'Invalid field attribute: scoring_coefficient'
        # if 'scoring_coefficient' not isinstance(field_obj['scoring_coefficient'], float):
        #         return False, 'Invalid field attribute: scoring_coefficient'
        return True, None


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
        is_valid, message = ProjectFields.validate(field_object)
        if not is_valid:
            return rest.bad_request(message)
        if 'name' not in field_object or field_object['name'] != field_name:
            return rest.bad_request('Name of tag is not correct')
        # replace number_of_rules with previous value
        if 'number_of_rules' in data[project_name]['master_config']['fields'][field_name]:
            num_of_rules = data[project_name]['master_config']['fields'][field_name]['number_of_rules']
            field_object['number_of_rules'] = num_of_rules
        data[project_name]['master_config']['fields'][field_name] = field_object
        # write to file
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='update a field: project {}, field {}'.format(project_name, field_name))
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
        # remove associated table attribute
        for k, v in data[project_name]['master_config']['table_attributes'].items():
            if v['field_name'] == field_name:
                v['field_name'] = ''

        # write to file
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='delete a field: project {}, field {}'.format(project_name, field_name))
        return rest.deleted()


@api.route('/projects/<project_name>/fields/<field_name>/spacy_rules')
class SpacyRulesOfAField(Resource):
    @requires_auth
    def post(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found('Field {} not found'.format(field_name))

        input = request.get_json(force=True)
        obj = input
        obj['rules'] = input.get('rules', [])
        obj['test_text'] = input.get('test_text', '')
        obj['field_name'] = field_name
        # obj = {
        #     'rules': rules,
        #     'test_text': test_text,
        #     'field_name': field_name
        # }

        url = 'http://{}:{}/test_spacy_rules'.format(
            config['etk']['daemon']['host'], config['etk']['daemon']['port'])
        resp = requests.post(url, data=json.dumps(obj), timeout=10)
        if resp.status_code // 100 != 2:
            if resp.status_code // 100 == 4:
                j = json.loads(resp.content)
                return rest.bad_request('Format exception: {}'.format(j['message']))
            return rest.internal_error('failed to call daemon process')

        obj = json.loads(resp.content)

        path = os.path.join(_get_project_dir_path(project_name), 'spacy_rules/' + field_name + '.json')
        data[project_name]['master_config']['fields'][field_name]['number_of_rules'] = len(obj['rules'])
        # data[project_name]['master_config']['spacy_field_rules'] = {field_name: path}
        update_master_config_file(project_name)
        write_to_file(json.dumps(obj, indent=2), path)
        # git_helper.commit(files=[path, project_name + '/master_config.json'],
        #                   message='create / update spacy rules: project {}, field {}'.format(project_name, field_name))

        with codecs.open(path, 'r') as f:
            obj = json.loads(f.read())
        return rest.created(obj)

    @requires_auth
    def put(self, project_name, field_name):
        return self.post(project_name, field_name)

    @requires_auth
    def get(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found('Field {} not found'.format(field_name))

        path = os.path.join(_get_project_dir_path(project_name), 'spacy_rules/' + field_name + '.json')
        if not os.path.exists(path):
            return rest.not_found('no spacy rules')

        obj = dict()
        with codecs.open(path, 'r') as f:
            obj = json.loads(f.read())

        type = request.args.get('type', '')
        if type == 'rules':
            return {'rules': obj['rules']}
        elif type == 'tokens':
            return {'test_tokens': obj['test_tokens']}
        elif type == 'results':
            return {'results': obj['results']}
        else:
            return obj

    @requires_auth
    def delete(self, project_name, field_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if field_name not in data[project_name]['master_config']['fields']:
            return rest.not_found('Field {} not found'.format(field_name))

        path = os.path.join(_get_project_dir_path(project_name), 'spacy_rules/' + field_name + '.json')
        if not os.path.exists(path):
            return rest.not_found('no spacy rules')
        os.remove(path)
        data[project_name]['master_config']['fields'][field_name]['number_of_rules'] = 0
        # del data[project_name]['master_config']['spacy_field_rules'][field_name]
        update_master_config_file(project_name)
        # git_helper.commit(files=[path, project_name + '/master_config.json'],
        #                   message='delete spacy rules: project {}, field {}'.format(project_name, field_name))
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
        if args['glossary_name'] is None or args['glossary_file'] is None:
            return rest.bad_request('Invalid glossary_name or glossary_file')
        name = args['glossary_name'].strip()
        if len(name) == 0:
            return rest.bad_request('Invalid glossary_name')
        if name in data[project_name]['master_config']['glossaries']:
            return rest.exists('Glossary {} exists'.format(name))
        file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.txt')
        gzip_file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.txt.gz')
        json_file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.json.gz')

        content = args['glossary_file'].stream.read()
        with gzip.open(gzip_file_path, 'w') as f:
            f.write(content)
        with gzip.open(json_file_path, 'w') as f:
            f.write(ProjectGlossaries.convert_glossary_to_json(content))
        write_to_file(content, file_path)
        # file.save(file_path)

        self.compute_statistics(project_name, name, json_file_path)
        # git_helper.commit(files=[project_name + '/master_config.json', project_name + '/glossaries/*'],
        #                   message='create a glossary: project {}, glossary {}'.format(project_name, name))

        return rest.created()

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        return data[project_name]['master_config']['glossaries'].keys()

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        dir_path = os.path.join(_get_project_dir_path(project_name), 'glossaries')
        shutil.rmtree(dir_path)
        os.mkdir(dir_path)  # recreate folder
        data[project_name]['master_config']['glossaries'] = dict()
        # remove all glossary names from all fields
        for k, v in data[project_name]['master_config']['fields'].items():
            if 'glossaries' in v and v['glossaries']:
                v['glossaries'] = []
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json', project_name + '/glossaries/*'],
        #                   message='delete all glossaries: project {}'.format(project_name))
        return rest.deleted()

    @staticmethod
    def compute_statistics(project_name, glossary_name, json_file_path):
        THRESHOLD = 5
        ngram = {}
        with gzip.open(json_file_path, 'r') as f:
            obj = json.loads(f.read())
            for item in obj:
                t = len(item.split(' '))
                if t > THRESHOLD:
                    continue
                ngram[t] = ngram.get(t, 0) + 1
            data[project_name]['master_config']['glossaries'][glossary_name] = {
                'ngram_distribution': ngram,
                'entry_count': len(obj),
                'path': glossary_name + '.json.gz'
            }
            update_master_config_file(project_name)

    @staticmethod
    def convert_glossary_to_json(lines):
        glossary = list()
        lines = lines.replace('\r', '\n')  # convert
        lines = lines.split('\n')

        t = CrfTokenizer()
        t.setRecognizeHtmlEntities(True)
        t.setRecognizeHtmlTags(True)
        t.setSkipHtmlTags(True)

        for line in lines:
            line = line.strip()
            if len(line) == 0:  # trim empty line
                continue
            line = ' '.join(t.tokenize(line))
            glossary.append(line)
        return json.dumps(glossary)


@api.route('/projects/<project_name>/glossaries/<glossary_name>')
class Glossary(Resource):
    @requires_auth
    def post(self, project_name, glossary_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        if glossary_name not in data[project_name]['master_config']['glossaries']:
            return rest.not_found('Glossary {} not found'.format(glossary_name))

        parse = reqparse.RequestParser()
        parse.add_argument('glossary_file', type=werkzeug.FileStorage, location='files')

        args = parse.parse_args()

        # http://werkzeug.pocoo.org/docs/0.12/datastructures/#werkzeug.datastructures.FileStorage
        if args['glossary_file'] is None:
            return rest.bad_request('Invalid glossary_file')

        name = glossary_name

        file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.txt')
        gzip_file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.txt.gz')
        json_file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + name + '.json.gz')

        # file = args['glossary_file']
        # file.save(file_path)

        content = args['glossary_file'].stream.read()
        with gzip.open(gzip_file_path, 'w') as f:
            f.write(content)
        with gzip.open(json_file_path, 'w') as f:
            f.write(ProjectGlossaries.convert_glossary_to_json(content))
        write_to_file(content, file_path)

        ProjectGlossaries.compute_statistics(project_name, glossary_name, json_file_path)
        # git_helper.commit(files=[project_name + '/master_config.json', project_name + '/glossaries/*'],
        #                   message='update a glossary: project {}, glossary {}'.format(project_name, name))
        return rest.created()

    @requires_auth
    def put(self, project_name, glossary_name):
        return self.post(project_name, glossary_name)

    @requires_auth
    def get(self, project_name, glossary_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        if glossary_name not in data[project_name]['master_config']['glossaries']:
            return rest.not_found('Glossary {} not found'.format(glossary_name))

        file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.txt.gz')
        ret = send_file(file_path, mimetype='application/gzip',
                        as_attachment=True, attachment_filename=glossary_name + '.txt.gz')
        ret.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return ret

    @requires_auth
    def delete(self, project_name, glossary_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        if glossary_name not in data[project_name]['master_config']['glossaries']:
            return rest.not_found('Glossary {} not found'.format(glossary_name))

        file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.txt')
        gzip_file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.txt.gz')
        json_file_path = os.path.join(_get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.json.gz')
        os.remove(file_path)
        os.remove(gzip_file_path)
        os.remove(json_file_path)
        del data[project_name]['master_config']['glossaries'][glossary_name]
        # remove glossary_name from field which contains it
        for k, v in data[project_name]['master_config']['fields'].items():
            if 'glossaries' in v and glossary_name in v['glossaries']:
                v['glossaries'].remove(glossary_name)
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json', project_name + '/glossaries/*'],
        #                   message='delete a glossary: project {}, glossary {}'.format(project_name, glossary_name))
        return rest.deleted()


@api.route('/projects/<project_name>/table_attributes')
class ProjectTableAttributes(Resource):
    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        input = request.get_json(force=True)

        is_valid, message = ProjectTableAttributes.validator(input)
        if not is_valid:
            return rest.bad_request(message)
        attribute_name = input['name']
        if attribute_name in data[project_name]['master_config']['table_attributes']:
            return rest.exists()

        if input['field_name'] != '' and \
                        input['field_name'] not in data[project_name]['master_config']['fields']:
            return rest.bad_request('No such field')

        data[project_name]['master_config']['table_attributes'][attribute_name] = input
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='create / update table attributes: project {}, attribute {}'
        #                   .format(project_name, attribute_name))
        return rest.created()

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if 'table_attributes' not in data[project_name]['master_config']:
            return rest.ok()
        return data[project_name]['master_config']['table_attributes']

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if 'table_attributes' not in data[project_name]['master_config']:
            return rest.deleted()
        data[project_name]['master_config']['table_attributes'] = input
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='delete table attributes: project {}'.format(project_name))
        return rest.deleted()

    @staticmethod
    def validator(obj):
        if 'name' not in obj or len(obj['name'].strip()) == 0:
            return False, 'Invalid attribute: name'
        if 'field_name' not in obj:
            obj['field_name'] = ''
        if 'value' not in obj or not isinstance(obj['value'], list):
            return False, 'Invalid attribute: value'
        if 'info' not in obj:
            return False, 'Invalid attribute: info'
        return True, None


@api.route('/projects/<project_name>/table_attributes/<attribute_name>')
class TableAttribute(Resource):
    @requires_auth
    def post(self, project_name, attribute_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if attribute_name not in data[project_name]['master_config']['table_attributes']:
            return rest.not_found('attribute name not found')

        input = request.get_json(force=True)
        is_valid, message = ProjectTableAttributes.validator(input)
        if not is_valid:
            return rest.bad_request(message)
        if attribute_name != input['name']:
            return rest.bad_request('Invalid table attribute name')
        if input['field_name'] != '' and \
                        input['field_name'] not in data[project_name]['master_config']['fields']:
            return rest.bad_request('No such field')
        data[project_name]['master_config']['table_attributes'][attribute_name] = input
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='create / update table attributes: project {}, attribute {}'
        #                   .format(project_name, attribute_name))
        return rest.created()

    @requires_auth
    def put(self, project_name, attribute_name):
        return self.post(project_name, attribute_name)

    @requires_auth
    def get(self, project_name, attribute_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if attribute_name not in data[project_name]['master_config']['table_attributes']:
            return rest.not_found('attribute name not found')

        return data[project_name]['master_config']['table_attributes'][attribute_name]

    @requires_auth
    def delete(self, project_name, attribute_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))
        if attribute_name not in data[project_name]['master_config']['table_attributes']:
            return rest.not_found('attribute name not found')

        del data[project_name]['master_config']['table_attributes'][attribute_name]
        update_master_config_file(project_name)
        # git_helper.commit(files=[project_name + '/master_config.json'],
        #                   message='delete table attributes: project {}, attribute {}'
        #                   .format(project_name, attribute_name))
        return rest.deleted()


# @api.route('/projects/<project_name>/entities/<kg_id>/tags')
# class EntityTags(Resource):
#     @requires_auth
#     def get(self, project_name, kg_id):
#         if project_name not in data:
#             return rest.not_found('Project {} not found'.format(project_name))
#         entity_name = 'Ad'
#         if entity_name not in data[project_name]['entities']:
#             data[project_name]['entities'][entity_name] = dict()
#         if kg_id not in data[project_name]['entities'][entity_name]:
#             return rest.not_found('kg_id {} not found'.format(kg_id))
#
#         return data[project_name]['entities'][entity_name][kg_id]
#
#     @requires_auth
#     def post(self, project_name, kg_id):
#         if project_name not in data:
#             return rest.not_found()
#
#         input = request.get_json(force=True)
#         tags = input.get('tags', [])
#         if len(tags) == 0:
#             return rest.bad_request('No tags given')
#         # tag should be exist
#         for tag_name in tags:
#             if tag_name not in data[project_name]['master_config']['tags']:
#                 return rest.bad_request('Tag {} is not exist'.format(tag_name))
#         # add tags to entity
#         entity_name = 'Ad'
#         for tag_name in tags:
#             if entity_name not in data[project_name]['entities']:
#                 data[project_name]['entities'][entity_name] = dict()
#             if kg_id not in data[project_name]['entities'][entity_name]:
#                 data[project_name]['entities'][entity_name][kg_id] = dict()
#             if tag_name not in data[project_name]['entities'][entity_name][kg_id]:
#                 data[project_name]['entities'][entity_name][kg_id][tag_name] = dict()
#
#         # write to file
#         file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/entity_annotations.json')
#         write_to_file(json.dumps(data[project_name]['entities'], indent=4), file_path)
#         return rest.created()


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
        self.write_to_field_file(project_name, field_name)
        # load into ES
        self.es_remove_field_annotation('full', project_name, kg_id, field_name)
        self.es_remove_field_annotation('sample', project_name, kg_id, field_name)
        # commit to git
        # git_helper.commit(files=[project_name + '/field_annotations/' + field_name + '.csv'],
        #                   message='delete all field annotations: project {}, field {}, kg_id {}'
        #                   .format(project_name, field_name, kg_id))
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

        _add_keys_to_dict(data[project_name]['field_annotations'], [kg_id, field_name, key])
        data[project_name]['field_annotations'][kg_id][field_name][key]['human_annotation'] = human_annotation
        # write to file
        self.write_to_field_file(project_name, field_name)
        # load into ES
        self.es_update_field_annotation('full', project_name, kg_id, field_name, key, human_annotation)
        self.es_update_field_annotation('sample', project_name, kg_id, field_name, key, human_annotation)
        # commit to git
        # git_helper.commit(files=[project_name + '/field_annotations/' + field_name + '.csv'],
        #                   message='create / update a field annotation: project {}, field {}, kg_id {}'
        #                   .format(project_name, field_name, kg_id))
        return rest.created()

    @requires_auth
    def put(self, project_name, kg_id, field_name):
        return rest.post(project_name, kg_id, field_name)

    @staticmethod
    def es_update_field_annotation(index_version, project_name, kg_id, field_name, key, human_annotation):
        try:
            es = ES(config['es'][index_version + '_url'])
            index = data[project_name]['master_config']['index'][index_version]
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                doc = hits['hits']['hits'][0]['_source']
                _add_keys_to_dict(doc, ['knowledge_graph', field_name])
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
            logger.warning('Fail to update annotation to {}: project {}, kg_id {}, field {}, key {}'.format(
                index_version, project_name, kg_id, field_name, key
            ))

    @staticmethod
    def es_remove_field_annotation(index_version, project_name, kg_id, field_name, key=None):
        try:
            es = ES(config['es'][index_version + '_url'])
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
                    if key is None:  # delete all annotations
                        if 'human_annotation' in field_instance:
                            del field_instance['human_annotation']
                    else:  # delete annotation of a specific key
                        if field_instance['key'] == key:
                            del field_instance['human_annotation']
                            break
                res = es.load_data(index, type, doc, doc['doc_id'])
                if not res:
                    return True

            return False
        except Exception as e:
            logger.warning('Fail to remove annotation from {}: project {}, kg_id {}, field {}, key {}'.format(
                index_version, project_name, kg_id, field_name, key
            ))

    @staticmethod
    def write_to_field_file(project_name, field_name):
        file_path = os.path.join(_get_project_dir_path(project_name), 'field_annotations/' + field_name + '.csv')
        field_obj = data[project_name]['field_annotations']
        with codecs.open(file_path, 'w') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=['field_name', 'kg_id', 'key', 'human_annotation'],
                delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for kg_id_, kg_obj_ in field_obj.iteritems():
                for field_name_, field_obj_ in kg_obj_.iteritems():
                    if field_name_ == field_name:
                        for key_, key_obj_ in field_obj_.iteritems():
                            writer.writerow(
                                {'field_name': field_name_, 'kg_id': kg_id_,
                                 'key': key_, 'human_annotation': key_obj_['human_annotation']})

    @staticmethod
    def load_from_field_file(project_name):
        dir_path = os.path.join(_get_project_dir_path(project_name), 'field_annotations')
        for file_name in os.listdir(dir_path):
            name, ext = os.path.splitext(file_name)
            if ext != '.csv':
                continue
            file_path = os.path.join(dir_path, file_name)
            with codecs.open(file_path, 'r') as csvfile:
                reader = csv.DictReader(
                    csvfile, fieldnames=['field_name', 'kg_id', 'key', 'human_annotation'],
                    delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                next(reader, None)  # skip header
                for row in reader:
                    _add_keys_to_dict(data[project_name]['field_annotations'],
                                      [row['kg_id'], row['field_name'], row['key']])
                    data[project_name]['field_annotations'][row['kg_id']][row['field_name']][row['key']][
                        'human_annotation'] = row['human_annotation']


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
        FieldAnnotations.write_to_field_file(project_name, field_name)
        # load into ES
        FieldAnnotations.es_remove_field_annotation('full', project_name, kg_id, field_name, key)
        FieldAnnotations.es_remove_field_annotation('sample', project_name, kg_id, field_name, key)
        # commit to git
        # git_helper.commit(files=[project_name + '/field_annotations/' + field_name + '.csv'],
        #                   message='delete a field annotation: project {}, field {}, kg_id {}, key {}'
        #                   .format(project_name, field_name, kg_id, key))
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
                self.es_remove_tag_annotation('full', project_name, kg_id, tag_name)
                self.es_remove_tag_annotation('sample', project_name, kg_id, tag_name)
            if len(kg_item) == 0:
                del data[project_name]['entities'][entity_name][kg_id]

        # write to file
        self.write_to_tag_file(project_name, tag_name)
        # commit to git
        # git_helper.commit(files=[project_name + '/entity_annotations/' + tag_name + '.csv'],
        #                   message='delete all tag annotations: project {}, entity {}, tag {}'
        #                   .format(project_name, entity_name, tag_name))

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

        _add_keys_to_dict(data[project_name]['entities'][entity_name], [kg_id, tag_name])
        data[project_name]['entities'][entity_name][kg_id][tag_name]['human_annotation'] = human_annotation
        # write to file
        self.write_to_tag_file(project_name, tag_name)
        # load to ES
        self.es_update_tag_annotation('full', project_name, kg_id, tag_name, human_annotation)
        self.es_update_tag_annotation('sample', project_name, kg_id, tag_name, human_annotation)
        # commit to git
        # git_helper.commit(files=[project_name + '/entity_annotations/' + tag_name + '.csv'],
        #                   message='create /update a tag annotation: project {}, entity {}, tag {}'
        #                   .format(project_name, entity_name, tag_name))
        return rest.created()

    @requires_auth
    def put(self, project_name, tag_name, entity_name):
        return self.post(project_name, tag_name, entity_name)

    @staticmethod
    def es_update_tag_annotation(index_version, project_name, kg_id, tag_name, human_annotation):
        try:
            es = ES(config['es'][index_version + '_url'])
            index = data[project_name]['master_config']['index'][index_version]
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                doc = hits['hits']['hits'][0]['_source']
                _add_keys_to_dict(doc, ['knowledge_graph', '_tags', tag_name])
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
            logger.warning('Fail to update annotation to {}: project {}, kg_id {}, tag {}'
                           .format(index_version, project_name, kg_id, tag_name))

    @staticmethod
    def es_remove_tag_annotation(index_version, project_name, kg_id, tag_name):
        try:
            es = ES(config['es'][index_version + '_url'])
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
            logger.warning('Fail to remove annotation from {}: project {}, kg_id {}, tag {}'.format(
                index_version, project_name, kg_id, tag_name
            ))

    @staticmethod
    def write_to_tag_file(project_name, tag_name):
        file_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations/' + tag_name + '.csv')
        tag_obj = data[project_name]['entities']
        with codecs.open(file_path, 'w') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=['tag_name', 'entity_name', 'kg_id', 'human_annotation'],
                delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for entity_name_, entity_obj_ in tag_obj.iteritems():
                for kg_id_, kg_obj_ in entity_obj_.iteritems():
                    for tag_name_, tag_obj_ in kg_obj_.iteritems():
                        if tag_name_ == tag_name and 'human_annotation' in tag_obj_:
                            writer.writerow(
                                {'tag_name': tag_name_, 'entity_name': entity_name_,
                                 'kg_id': kg_id_, 'human_annotation': tag_obj_['human_annotation']})

    @staticmethod
    def load_from_tag_file(project_name):
        dir_path = os.path.join(_get_project_dir_path(project_name), 'entity_annotations')
        for file_name in os.listdir(dir_path):
            name, ext = os.path.splitext(file_name)
            if ext != '.csv':
                continue
            file_path = os.path.join(dir_path, file_name)
            with codecs.open(file_path, 'r') as csvfile:
                reader = csv.DictReader(
                    csvfile, fieldnames=['tag_name', 'entity_name', 'kg_id', 'human_annotation'],
                    delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                next(reader, None)  # skip header
                for row in reader:
                    _add_keys_to_dict(data[project_name]['entities'],
                                      [row['entity_name'], row['kg_id'], row['tag_name']])
                    data[project_name]['entities'][row['entity_name']][row['kg_id']][row['tag_name']][
                        'human_annotation'] = row['human_annotation']


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
        TagAnnotationsForEntityType.write_to_tag_file(project_name, tag_name)
        # remove from ES
        TagAnnotationsForEntityType.es_remove_tag_annotation('full', project_name, kg_id, tag_name)
        TagAnnotationsForEntityType.es_remove_tag_annotation('sample', project_name, kg_id, tag_name)
        # commit to git
        # git_helper.commit(files=[project_name + '/entity_annotations/' + tag_name + '.csv'],
        #                   message='delete a tag annotation: project {}, entity {}, tag {}, kg_id {}'
        #                   .format(project_name, entity_name, tag_name, kg_id))

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
        parser.add_argument('kg', required=False, type=str, help='knowledge graph')
        args = parser.parse_args()

        return_kg = True if args['kg'] is not None and \
                            args['kg'].lower() == 'true' else False

        if return_kg:
            ret['knowledge_graph'] = self.get_kg(project_name, kg_id, tag_name)

        return ret

    @staticmethod
    def get_kg(project_name, kg_id, tag_name):
        index_version = 'full'
        try:
            es = ES(config['es'][index_version + '_url'])
            index = data[project_name]['master_config']['index'][index_version]
            type = data[project_name]['master_config']['root_name']
            hits = es.retrieve_doc(index, type, kg_id)
            if hits:
                doc = hits['hits']['hits'][0]['_source']
                if 'knowledge_graph' not in doc:
                    return None
                return doc['knowledge_graph']

            return None
        except Exception as e:
            logger.warning('Fail to update annotation to: project {}, kg_id {}, tag {}'.format(
                project_name, kg_id, tag_name
            ))


@api.route('/projects/<project_name>/data')
class Data(Resource):
    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        parse = reqparse.RequestParser()
        parse.add_argument('file_data', type=werkzeug.FileStorage, location='files')
        parse.add_argument('file_name')
        parse.add_argument('file_type')
        parse.add_argument('sync')
        parse.add_argument('log')
        args = parse.parse_args()

        if args['file_name'] is None:
            return rest.bad_request('Invalid file_name')
        file_name = args['file_name'].strip()
        if len(file_name) == 0:
            return rest.bad_request('Invalid file_name')
        if args['file_data'] is None:
            return rest.bad_request('Invalid file_data')
        if args['file_type'] is None:
            return rest.bad_request('Invalid file_type')
        args['sync'] = False if args['sync'] is None or args['sync'].lower() != 'true' else True
        args['log'] = True if args['log'] is None or args['log'].lower() != 'false' else False

        # make root dir and save temp file
        src_file_path = os.path.join(_get_project_dir_path(project_name), 'data', '{}.tmp'.format(file_name))
        args['file_data'].save(src_file_path)
        dest_dir_path = os.path.join(_get_project_dir_path(project_name), 'data', file_name)
        if not os.path.exists(dest_dir_path):
            os.mkdir(dest_dir_path)

        if not args['sync']:
            t = threading.Thread(target=Data._update_catalog_worker,
                args=(project_name, file_name, args['file_type'], src_file_path, dest_dir_path, args['log'],),
                name='data_upload')
            t.start()
            data[project_name]['threads'].append(t)

            return rest.accepted()
        else:
            Data._update_catalog_worker(project_name, file_name, args['file_type'],
                                        src_file_path, dest_dir_path, args['log'])
            return rest.created()

    @staticmethod
    def _update_catalog_worker(project_name, file_name, file_type, src_file_path, dest_dir_path, log_on=True):
        def _write_log(content):
            with data[project_name]['locks']['catalog_log']:
                log_file.write('<#{}> {}: {}\n'.format(thread.get_ident(), file_name, content))

        log_path = os.path.join(_get_project_dir_path(project_name),
                                'working_dir/catalog_error.log') if log_on else os.devnull
        log_file = codecs.open(log_path, 'a')
        _write_log('start updating catalog')

        try:

            # generate catalog
            if file_type == 'json_lines':
                suffix = os.path.splitext(file_name)[-1]
                f = gzip.open(src_file_path, 'r') \
                    if suffix in ('.gz', '.gzip') else codecs.open(src_file_path, 'r')

                for line in f:
                    if len(line.strip()) == 0:
                        continue
                    obj = json.loads(line)

                    # raw_content
                    if 'raw_content' not in obj:
                        obj['raw_content'] = ''
                    try:
                        obj['raw_content'] = unicode(obj['raw_content']).encode('utf-8')
                    except:
                        pass

                    # doc_id
                    obj['doc_id'] = unicode(obj.get('doc_id', obj.get('_id', ''))).encode('utf-8')
                    if not Data.is_valid_doc_id(obj['doc_id']):
                        if len(obj['doc_id']) > 0:  # has doc_id but invalid
                            old_doc_id = obj['doc_id']
                            obj['doc_id'] = base64.b64encode(old_doc_id)
                            _write_log('base64 encoded doc_id from {} to {}'
                                       .format(old_doc_id, obj['doc_id']))
                        if not Data.is_valid_doc_id(obj['doc_id']):
                            # generate doc_id
                            # if there's raw_content, generate id based on raw_content
                            # if not, use the whole object
                            if len(obj['raw_content']) != 0:
                                obj['doc_id'] = Data.generate_doc_id(obj['raw_content'])
                            else:
                                obj['doc_id'] = Data.generate_doc_id(json.dumps(obj, sort_keys=True))
                            _write_log('Generated doc_id for object: {}'.format(obj['doc_id']))

                    # url
                    if 'url' not in obj:
                        obj['url'] = '{}/{}'.format(Data.generate_tld(file_name), obj['doc_id'])
                        _write_log('Generated URL for object: {}'.format(obj['url']))

                    # timestamp_crawl
                    if 'timestamp_crawl' not in obj:
                        # obj['timestamp_crawl'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        obj['timestamp_crawl'] = datetime.datetime.now().isoformat()
                    else:
                        try:
                            parsed_date = dateparser.parse(obj['timestamp_crawl'])
                            obj['timestamp_crawl'] = parsed_date.isoformat()
                        except:
                            _write_log('Can not parse timestamp_crawl: {}'.format(obj['doc_id']))
                            continue

                    # type
                    # this type will conflict with the attribute in logstash
                    if 'type' in obj:
                        obj['original_type'] = obj['type']
                        del obj['type']

                    # split raw_content and json
                    output_path_prefix = os.path.join(dest_dir_path, obj['doc_id'])
                    output_raw_content_path = output_path_prefix + '.html'
                    output_json_path = output_path_prefix + '.json'
                    with codecs.open(output_raw_content_path, 'w') as output:
                        output.write(obj['raw_content'])
                    with codecs.open(output_json_path, 'w') as output:
                        del obj['raw_content']
                        output.write(json.dumps(obj, indent=2))
                    # update data db
                    tld = obj.get('tld', Data.extract_tld(obj['url']))
                    with data[project_name]['locks']['data']:
                        data[project_name]['data'][tld] = data[project_name]['data'].get(tld, dict())
                        # if doc_id is already there, still overwrite it
                        exists_before = True if obj['doc_id'] in data[project_name]['data'][tld] else False
                        data[project_name]['data'][tld][obj['doc_id']] = {
                            'raw_content_path': output_raw_content_path,
                            'json_path': output_json_path,
                            'url': obj['url'],
                            'add_to_queue': False
                        }
                    # update status
                    if not exists_before:
                        with data[project_name]['locks']['status']:
                            data[project_name]['status']['total_docs'][tld] = \
                                data[project_name]['status']['total_docs'].get(tld, 0) + 1

                    # update data db & status file
                    set_catalog_dirty(project_name)
                    set_status_dirty(project_name)

                f.close()

            elif file_type == 'html':
                pass

                # notify action add data if needed
                # Actions._add_data(project_name)

        except Exception as e:
            logger.exception('exception in _update_catalog_worker')
            _write_log('Invalid file format')

        finally:

            # stop logging
            _write_log('done')
            log_file.close()

            # remove temp file
            os.remove(src_file_path)

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        parser = reqparse.RequestParser()
        parser.add_argument('type', type=str)
        args = parser.parse_args()
        ret = dict()
        log_path = os.path.join(_get_project_dir_path(project_name), 'working_dir/catalog_error.log')

        # if args['type'] == 'has_error':
        #     ret['has_error'] = os.path.getsize(log_path) > 0
        if args['type'] == 'error_log':
            ret['error_log'] = list()
            if os.path.exists(log_path):
                with codecs.open(log_path, 'r') as f:
                    ret['error_log'] = tail_file(f, 200)
        else:
            with data[project_name]['locks']['status']:
                for tld, num in data[project_name]['status']['total_docs'].iteritems():
                    ret[tld] = num
        return ret

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        input = request.get_json(force=True)
        tld_list = input.get('tlds', list())
        delete_from = input.get('from')
        if delete_from is None:
            return rest.bad_request('invalid attribute: from')

        if delete_from == 'file':
            t = threading.Thread(target=Data._delete_file_worker,
                                 args=(project_name, tld_list,),
                                 name='data_file_delete')
            t.start()
            data[project_name]['threads'].append(t)
        elif delete_from == 'kg':
            t = threading.Thread(target=Data._delete_es_worker,
                                 args=(project_name, tld_list,),
                                 name='data_kg_delete')
            t.start()
            data[project_name]['threads'].append(t)

        return rest.accepted()

    @staticmethod
    def _delete_file_worker(project_name, tld_list):

        for tld in tld_list:
            # update status
            with data[project_name]['locks']['status']:
                if tld in data[project_name]['status']['desired_docs']:
                    del data[project_name]['status']['desired_docs'][tld]
                if tld in data[project_name]['status']['added_docs']:
                    del data[project_name]['status']['added_docs'][tld]
                if tld in data[project_name]['status']['total_docs']:
                    del data[project_name]['status']['total_docs'][tld]
                set_status_dirty(project_name)

            # update data
            with data[project_name]['locks']['data']:
                if tld in data[project_name]['data']:
                    # remove data file
                    for k, v in data[project_name]['data'][tld].iteritems():
                        try:
                            os.remove(v['raw_content_path'])
                        except:
                            pass
                        try:
                            os.remove(v['json_path'])
                        except:
                            pass
                    # remove from catalog
                    del data[project_name]['data'][tld]
                    set_catalog_dirty(project_name)

    @staticmethod
    def _delete_es_worker(project_name, tld_list):
        query = '''
        {{
            "query": {{
                "match": {{
                    "tld.raw": "{tld}"
                }}
            }}
        }}
        '''
        es = ES(config['es']['sample_url'])
        for tld in tld_list:
            try:
                es.es.delete_by_query(index=project_name,
                                      doc_type=data[project_name]['master_config']['root_name'],
                                      body=query.format(tld=tld))
            except:
                logger.exception('error in _delete_es_worker')

    @staticmethod
    def generate_tld(file_name):
        return 'www.dig_{}.org'.format(re.sub(re_url, '_', file_name.lower()).strip())

    @staticmethod
    def generate_doc_id(content):
        return hashlib.sha256(content).hexdigest().upper()

    @staticmethod
    def is_valid_doc_id(doc_id):
        return re_doc_id.match(doc_id) and doc_id not in os_reserved_file_names

    @staticmethod
    def extract_tld(url):
        return tldextract.extract(url).domain + '.' + tldextract.extract(url).suffix


@api.route('/projects/<project_name>/actions/project_config')
class ActionProjectConfig(Resource):
    @requires_auth
    def post(self, project_name):  # frontend needs to fresh to get all configs again
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        try:
            parse = reqparse.RequestParser()
            parse.add_argument('file_data', type=werkzeug.FileStorage, location='files')
            args = parse.parse_args()

            # save to tmp path and test
            tmp_project_config_path = os.path.join(_get_project_dir_path(project_name),
                                                   'working_dir/uploaded_project_config.tar.gz')
            tmp_project_config_extracted_path = os.path.join(_get_project_dir_path(project_name),
                                                             'working_dir/uploaded_project_config')
            args['file_data'].save(tmp_project_config_path)
            with tarfile.open(tmp_project_config_path, 'r:gz') as tar:
                tar.extractall(tmp_project_config_extracted_path)

            # master_config
            with codecs.open(os.path.join(tmp_project_config_extracted_path, 'master_config.json'), 'r') as f:
                new_master_config = json.loads(f.read())
            # TODO: validation and sanitizing
            # overwrite indices
            new_master_config['index'] = {
                'sample': project_name,
                'full': project_name + '_deployed',
                'version': 0
            }
            # overwrite configuration
            if 'configuration' not in new_master_config:
                new_master_config['configuration'] = dict()
            new_master_config['configuration']['sandpaper_sample_url'] \
                = data[project_name]['master_config']['configuration']['sandpaper_sample_url']
            new_master_config['configuration']['sandpaper_full_url'] \
                = data[project_name]['master_config']['configuration']['sandpaper_full_url']
            # overwrite previous master config
            data[project_name]['master_config'] = new_master_config
            update_master_config_file(project_name)

            # replace dependencies
            distutils.dir_util.copy_tree(
                os.path.join(tmp_project_config_extracted_path, 'glossaries'),
                os.path.join(_get_project_dir_path(project_name), 'glossaries')
            )
            distutils.dir_util.copy_tree(
                os.path.join(tmp_project_config_extracted_path, 'spacy_rules'),
                os.path.join(_get_project_dir_path(project_name), 'spacy_rules')
            )
            distutils.dir_util.copy_tree(
                os.path.join(tmp_project_config_extracted_path, 'landmark_rules'),
                os.path.join(_get_project_dir_path(project_name), 'landmark_rules')
            )

            tmp_additional_etk_config = os.path.join(tmp_project_config_extracted_path,
                                                     'working_dir/additional_etk_config')
            if os.path.exists(tmp_additional_etk_config):
                distutils.dir_util.copy_tree(tmp_additional_etk_config,
                                             os.path.join(_get_project_dir_path(project_name),
                                                          'working_dir/additional_etk_config'))

            tmp_custom_etk_config = os.path.join(tmp_project_config_extracted_path,
                                                 'working_dir/custom_etk_config.json')
            if os.path.exists(tmp_custom_etk_config):
                shutil.copyfile(tmp_custom_etk_config,
                                os.path.join(_get_project_dir_path(project_name), 'working_dir/custom_etk_config.json'))

            tmp_landmark_config_path = os.path.join(tmp_project_config_extracted_path,
                                                    'working_dir/_landmark_config.json')
            if os.path.exists(tmp_landmark_config_path):
                with codecs.open(tmp_landmark_config_path, 'r') as f:
                    ActionProjectConfig.landmark_import(project_name, f.read())

            return rest.created()
        except Exception as e:
            logger.exception('fail to import project config')
            return rest.internal_error('fail to import project config')

        finally:
            # always clean up, or some of the files may affect new uploaded files
            if os.path.exists(tmp_project_config_path):
                os.remove(tmp_project_config_path)
            if os.path.exists(tmp_project_config_extracted_path):
                shutil.rmtree(tmp_project_config_extracted_path)

    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        export_path = os.path.join(_get_project_dir_path(project_name), 'working_dir/project_config.tar.gz')

        # tarzip file
        with tarfile.open(export_path, 'w:gz') as tar:
            tar.add(os.path.join(_get_project_dir_path(project_name), 'master_config.json'),
                    arcname='master_config.json')
            tar.add(os.path.join(_get_project_dir_path(project_name), 'glossaries'),
                    arcname='glossaries')
            tar.add(os.path.join(_get_project_dir_path(project_name), 'spacy_rules'),
                    arcname='spacy_rules')
            tar.add(os.path.join(_get_project_dir_path(project_name), 'landmark_rules'),
                    arcname='landmark_rules')
            # custom_etk_config
            custom_etk_config_path = os.path.join(_get_project_dir_path(project_name),
                                                  'working_dir/custom_etk_config.json')
            if os.path.exists(custom_etk_config_path):
                tar.add(custom_etk_config_path, arcname='working_dir/custom_etk_config.json')
            # additional_etk_config
            additional_etk_config_path = os.path.join(_get_project_dir_path(project_name),
                                                      'working_dir/additional_etk_config')
            if os.path.exists(additional_etk_config_path):
                tar.add(additional_etk_config_path, arcname='working_dir/additional_etk_config')

            landmark_config = ActionProjectConfig.landmark_export(project_name)
            # print 'config', len(landmark_config)
            if len(landmark_config) > 0:
                landmark_config_path = os.path.join(
                    _get_project_dir_path(project_name), 'working_dir/_landmark_config.json')
                write_to_file(json.dumps(landmark_config), landmark_config_path)
                tar.add(landmark_config_path, arcname='working_dir/_landmark_config.json')

        export_file_name = project_name + '_' + time.strftime("%Y%m%d%H%M%S") + '.tar.gz'
        ret = send_file(export_path, mimetype='application/gzip',
                        as_attachment=True, attachment_filename=export_file_name)
        ret.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return ret

    @staticmethod
    def landmark_export(project_name):
        try:
            url = config['landmark']['export'].format(project_name=project_name)
            resp = requests.post(url)
            return resp.json()
        except Exception as e:
            logger.exception('landmark export error')
            return list()

    @staticmethod
    def landmark_import(project_name, landmark_config):
        try:
            url = config['landmark']['import'].format(project_name=project_name)
            resp = requests.post(url, data=landmark_config)
        except Exception as e:
            logger.exception('landmark import error')


@api.route('/projects/<project_name>/actions/etk_filters')
class ActionProjectEtkFilters(Resource):
    @requires_auth
    def post(self, project_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        input = request.get_json(force=True)
        filtering_rules = input.get('filters', {})

        try:
            # validation
            for tld, rules in filtering_rules.iteritems():
                if tld.strip() == '' or not isinstance(rules, list):
                    return rest.bad_request('Invalid TLD')
                for rule in rules:
                    if 'field' not in rule or rule['field'].strip() == '':
                        return rest.bad_request('Invalid Field in TLD: {}'.format(tld))
                    if 'action' not in rule or rule['action'] not in ('no_action', 'keep', 'discard'):
                        return rest.bad_request('Invalid action in TLD: {}, Field {}'.format(tld, rule['field']))
                    if 'regex' not in rule:
                        return rest.bad_request('Invalid regex in TLD: {}, Field {}'.format(tld, rule['field']))
                    try:
                        re.compile(rule['regex'])
                    except re.error:
                        return rest.bad_request(
                            'Invalid regex in TLD: {}, Field: {}'.format(tld, rule['field']))

            # write to file
            dir_path = os.path.join(_get_project_dir_path(project_name),
                                    'working_dir/additional_etk_config')
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)
            config_path = os.path.join(dir_path, 'etk_filters.json')
            write_to_file(json.dumps(input), config_path)
            return rest.created()
        except Exception as e:
            logger.exception('fail to import ETK filters')
            return rest.internal_error('fail to import ETK filters')

    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        ret = {'filters': {}}
        config_path = os.path.join(_get_project_dir_path(project_name),
                                   'working_dir/additional_etk_config/etk_filters.json')
        if os.path.exists(config_path):
            with codecs.open(config_path, 'r') as f:
                ret = json.loads(f.read())

        return ret


@api.route('/projects/<project_name>/actions/<action_name>')
class Actions(Resource):
    @requires_auth
    def post(self, project_name, action_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        # if action_name == 'add_data':
        #     return self._add_data(project_name)
        if action_name == 'desired_num':
            return self.update_desired_num(project_name)
        elif action_name == 'extract':
            return self.etk_extract(project_name)
        elif action_name == 'recreate_mapping':
            return self.recreate_mapping(project_name)
        elif action_name == 'landmark_extract':
            return self.landmark_extract(project_name)
        elif action_name == 'reload_blacklist':
            return self.reload_blacklist(project_name)
        else:
            return rest.not_found('action {} not found'.format(action_name))

    @requires_auth
    def get(self, project_name, action_name):
        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        if action_name == 'extract':
            return self._get_extraction_status(project_name)
        else:
            return rest.not_found('action {} not found'.format(action_name))

    @requires_auth
    def delete(self, project_name, action_name):
        if action_name == 'extract':
            if not Actions._etk_stop(project_name):
                return rest.internal_error('failed to kill_etk in ETL')
            return rest.deleted()

    @staticmethod
    def _get_extraction_status(project_name):
        ret = dict()

        parser = reqparse.RequestParser()
        parser.add_argument('value', type=str)
        args = parser.parse_args()
        if args['value'] is None:
            args['value'] = 'all'

        if args['value'] in ('all', 'etk_status'):
            ret['etk_status'] = Actions._is_etk_running(project_name)

        if args['value'] in ('all', 'tld_statistics'):
            tld_list = dict()

            with data[project_name]['locks']['status']:
                for tld in data[project_name]['status']['total_docs'].iterkeys():
                    if tld not in data[project_name]['status']['desired_docs']:
                        data[project_name]['status']['desired_docs'][tld] = 0
                    if tld in data[project_name]['status']['total_docs']:
                        tld_obj = {
                            'tld': tld,
                            'total_num': data[project_name]['status']['total_docs'][tld],
                            'es_num': 0,
                            'es_original_num': 0,
                            'desired_num': data[project_name]['status']['desired_docs'][tld]
                        }
                        tld_list[tld] = tld_obj

            # query es count if doc exists
            query = """
            {
              "aggs": {
                  "group_by_tld_original": {
                    "filter": {
                      "bool": {
                        "must_not": {
                          "term": {
                            "created_by": "etk"
                          }
                        }
                      }
                    },
                    "aggs": {
                      "grouped": {
                        "terms": {
                          "field": "tld.raw",
                          "size": 2147483647
                        }
                      }
                    }
                  },
                  "group_by_tld": {
                    "terms": {
                      "field": "tld.raw",
                      "size": 2147483647
                    }
                  }
              },
              "size":0
            }
            """
            es = ES(config['es']['sample_url'])
            r = es.search(project_name, data[project_name]['master_config']['root_name'],
                          query, ignore_no_index=True, filter_path=['aggregations'])

            if r is not None:
                for obj in r['aggregations']['group_by_tld']['buckets']:
                    # check if tld is in uploaded file
                    tld = obj['key']
                    if tld not in tld_list:
                        tld_list[tld] = {
                            'tld': tld,
                            'total_num': 0,
                            'es_num': 0,
                            'es_original_num': 0,
                            'desired_num': 0
                        }
                    tld_list[tld]['es_num'] = obj['doc_count']

                for obj in r['aggregations']['group_by_tld_original']['grouped']['buckets']:
                    # check if tld is in uploaded file
                    tld = obj['key']
                    if tld not in tld_list:
                        tld_list[tld] = {
                            'tld': tld,
                            'total_num': 0,
                            'es_num': 0,
                            'es_original_num': 0,
                            'desired_num': 0
                        }
                    tld_list[tld]['es_original_num'] = obj['doc_count']

            ret['tld_statistics'] = tld_list.values()

        return ret

    @staticmethod
    def _is_etk_running(project_name):
        url = config['etl']['url'] + '/etk_status/' + project_name
        resp = requests.get(url)
        if resp.status_code // 100 != 2:
            return rest.internal_error('error in getting etk_staus')

        return resp.json()['etk_processes'] > 0

    @staticmethod
    def update_desired_num(project_name):
        # {
        #     "tlds": {
        #         'tld1': 100,
        #         'tld2': 200
        #     }
        # }
        input = request.get_json(force=True)
        tld_list = input.get('tlds', {})

        for tld, desired_num in tld_list.iteritems():
            desired_num = max(desired_num, 0)
            desired_num = min(desired_num, 999999999)
            with data[project_name]['locks']['status']:
                if tld not in data[project_name]['status']['desired_docs']:
                    data[project_name]['status']['desired_docs'][tld] = dict()
                data[project_name]['status']['desired_docs'][tld] = desired_num

        set_status_dirty(project_name)
        return rest.created()

    @staticmethod
    def landmark_extract(project_name):
        # {
        #     "tlds": {
        #         'tld1': 100,
        #         'tld2': 200
        #     }
        # }
        input = request.get_json(force=True)
        tld_list = input.get('tlds', {})
        payload = dict()

        for tld, num_to_run in tld_list.iteritems():
            if tld in data[project_name]['data']:

                # because the catalog can be huge, can not use a simple pythonic random here
                num_to_select = min(num_to_run, len(data[project_name]['data'][tld]))
                selected = set()
                while len(selected) < num_to_select:
                    cand_num = random.randint(0, num_to_select - 1)
                    if cand_num not in selected:
                        selected.add(cand_num)

                # construct payload
                idx = 0
                for doc_id, catalog_obj in data[project_name]['data'][tld].iteritems():
                    if idx not in selected:
                        idx += 1
                        continue
                    # payload format
                    # {
                    #     "tld1": {"documents": [{doc_id, raw_content_path, url}, {...}, ...]},
                    # }
                    payload[tld] = payload.get(tld, dict())
                    payload[tld]['documents'] = payload[tld].get('documents', list())
                    catalog_obj['doc_id'] = doc_id
                    payload[tld]['documents'].append(catalog_obj)
                    idx += 1

        url = config['landmark']['create'].format(project_name=project_name)
        resp = requests.post(url, json.dumps(payload), timeout=10)
        if resp.status_code // 100 != 2:
            return rest.internal_error('Landmark error: {}'.format(resp.status_code))

        return rest.accepted()

    @staticmethod
    def _generate_etk_config(project_name):
        new_extraction = True

        custom_etk_config_file_path = os.path.join(
            _get_project_dir_path(project_name), 'working_dir/custom_etk_config.json')
        etk_config_file_path = os.path.join(
            _get_project_dir_path(project_name), 'working_dir/etk_config.json')
        if os.path.exists(custom_etk_config_file_path):
            shutil.copy(custom_etk_config_file_path, etk_config_file_path)
        else:
            etk_config = etk_helper.generate_etk_config(data[project_name]['master_config'], config, project_name)
            etk_config_version = hashlib.sha256(json.dumps(etk_config)).hexdigest().upper()
            etk_config['etk_version'] = etk_config_version
            etk_config_snapshot_file_path = os.path.join(
                _get_project_dir_path(project_name), 'working_dir/etk_config_{}.json'.format(etk_config_version))
            # etk_config needs to be rewrite every time
            # since hash of the config can be the same to one of the previous versions
            write_to_file(json.dumps(etk_config, indent=2), etk_config_file_path)
            if not os.path.exists(etk_config_snapshot_file_path):
                write_to_file(json.dumps(etk_config, indent=2), etk_config_snapshot_file_path)
            else:
                new_extraction = False  # currently not in use
                # print 'start extraction: {} ({})'.format(etk_config_version[:6], 'new' if new_extraction else 'prev')

        return new_extraction

    @staticmethod
    def recreate_mapping(project_name):
        logger.info('recreate_mapping')

        # 1. kill etk (and clean up previous queue)
        data[project_name]['data_pushing_worker'].stop_adding_data = True
        if not Actions._etk_stop(project_name, clean_up_queue=True):
            return rest.internal_error('failed to kill_etk in ETL')

        # 2. create etk config and snapshot
        Actions._generate_etk_config(project_name)

        # add config for etl
        # when creating kafka container, group id is not there. set consumer to read from start.
        etl_config_path = os.path.join(_get_project_dir_path(project_name), 'working_dir/etl_config.json')
        if not os.path.exists(etl_config_path):
            etl_config = {
                "input_args": {
                    "auto_offset_reset": "earliest",
                    "fetch_max_bytes": 52428800,
                    "max_partition_fetch_bytes": 10485760,
                    "max_poll_records": 10
                },
                "output_args": {
                    "max_request_size": 10485760,
                    "compression_type": "gzip"
                }
            }
            write_to_file(json.dumps(etl_config, indent=2), etl_config_path)

        # 3. sandpaper
        # 3.1 delete previous index
        url = '{}/{}'.format(
            config['es']['sample_url'],
            project_name
        )
        try:
            resp = requests.delete(url, timeout=10)
        except:
            pass  # ignore no index error
        # 3.2 create new index
        url = '{}/mapping?url={}&project={}&index={}&endpoint={}'.format(
            config['sandpaper']['url'],
            config['sandpaper']['ws_url'],
            project_name,
            data[project_name]['master_config']['index']['sample'],
            config['es']['sample_url']
        )
        resp = requests.put(url, timeout=10)
        if resp.status_code // 100 != 2:
            return rest.internal_error('failed to create index in sandpaper')
        # 3.3 switch index
        url = '{}/config?url={}&project={}&index={}&endpoint={}'.format(
            config['sandpaper']['url'],
            config['sandpaper']['ws_url'],
            project_name,
            data[project_name]['master_config']['index']['sample'],
            config['es']['sample_url']
        )
        resp = requests.post(url, timeout=10)
        if resp.status_code // 100 != 2:
            return rest.internal_error('failed to switch index in sandpaper')

        # 4. clean up added data status
        logger.info('re-add data')
        with data[project_name]['locks']['status']:
            if 'added_docs' not in data[project_name]['status']:
                data[project_name]['status']['added_docs'] = dict()
            for tld in data[project_name]['status']['added_docs'].iterkeys():
                data[project_name]['status']['added_docs'][tld] = 0
        with data[project_name]['locks']['data']:
            for tld in data[project_name]['data'].iterkeys():
                for doc_id in data[project_name]['data'][tld]:
                    data[project_name]['data'][tld][doc_id]['add_to_queue'] = False
        set_status_dirty(project_name)

        # 5. restart extraction
        data[project_name]['data_pushing_worker'].stop_adding_data = False
        return Actions.etk_extract(project_name)

    @staticmethod
    def reload_blacklist(project_name):

        if project_name not in data:
            return rest.not_found('project {} not found'.format(project_name))

        # 1. kill etk
        if not Actions._etk_stop(project_name):
            return rest.internal_error('failed to kill_etk in ETL')

        # 2. generate etk config
        Actions._generate_etk_config(project_name)

        # 3. fetch and re-add data
        t = threading.Thread(target=Data._reload_blacklist_worker, args=(project_name,), name='reload_blacklist')
        t.start()
        data[project_name]['threads'].append(t)

        return rest.accepted()

    @staticmethod
    def _reload_blacklist_worker(project_name):
        # copy here to avoid modification while iteration
        for field_name, field_obj in data[project_name]['master_config']['fields'].items():

            if 'blacklists' not in field_obj or len(field_obj['blacklists']) == 0:
                continue

            # get all stop words and generate query
            # only use the last blacklist if there are multiple blacklists
            blacklist = data[project_name]['master_config']['fields'][field_name]['blacklists'][-1]
            file_path = os.path.join(_get_project_dir_path(project_name),
                                     'glossaries', '{}.txt'.format(blacklist))

            query_conditions = []
            with codecs.open(file_path, 'r') as f:
                for line in f:
                    key = line.strip()
                    if len(key) == 0:
                        continue
                    query_conditions.append(
                        '{{ "term": {{"knowledge_graph.{field_name}.key": "{key}"}} }}'
                            .format(field_name=field_name, key=key))

            query = """
            {{
                "size": 1000,
                "query": {{
                    "bool": {{
                        "should": [{conditions}]
                    }}
                }},
                "_source": ["doc_id", "tld"]
            }}
            """.format(conditions=','.join(query_conditions))
            logger.debug(query)

            # init query
            scroll_alive_time = '1m'
            es = ES(config['es']['sample_url'])
            r = es.search(project_name, data[project_name]['master_config']['root_name'], query,
                          params={'scroll': scroll_alive_time}, ignore_no_index=False)

            if r is None:
                return

            scroll_id = r['_scroll_id']
            Actions._re_add_docs(r, project_name)

            # scroll queries
            while True:
                # use the es object here directly
                r = es.es.scroll(scroll_id=scroll_id, scroll=scroll_alive_time)
                if r is None:
                    break
                if len(r['hits']['hits']) == 0:
                    break

                Actions._re_add_docs(r, project_name)

        Actions.etk_extract(project_name)

    @staticmethod
    def _re_add_docs(resp, project_name):

        input_topic = project_name + '_in'
        for obj in resp['hits']['hits']:
            doc_id = obj['_source']['doc_id']
            tld = obj['_source']['tld']

            try:
                logger.info('re-add doc %s (%s)', doc_id, tld)
                ret, msg = Actions._publish_to_kafka_input_queue(
                    doc_id, data[project_name]['data'][tld][doc_id], kafka_producer, input_topic)
                if not ret:
                    logger.error('Error of re-adding data to Kafka: %s', msg)
            except Exception as e:
                logger.exception('error in re_add_docs')

    @staticmethod
    def etk_extract(project_name, clean_up_queue=False):
        if Actions._is_etk_running(project_name):
            return rest.exists('already running')

        # etk_config_file_path = os.path.join(
        #     _get_project_dir_path(project_name), 'working_dir/etk_config.json')
        # if not os.path.exists(etk_config_file_path):
        #     return rest.not_found('No etk config')
        # recreate etk config every time
        Actions._generate_etk_config(project_name)

        url = '{}/{}'.format(
            config['es']['sample_url'],
            project_name
        )
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code // 100 != 2:
                return rest.not_found('No es index')
        except Exception as e:
            return rest.not_found('No es index')

        url = config['etl']['url'] + '/run_etk'
        payload = {
            'project_name': project_name,
            'number_of_workers': config['etl']['number_of_workers']
        }
        if clean_up_queue:
            payload['input_offset'] = 'seek_to_end'
            payload['output_offset'] = 'seek_to_end'
        resp = requests.post(url, json.dumps(payload), timeout=config['etl']['timeout'])
        if resp.status_code // 100 != 2:
            return rest.internal_error('failed to run_etk in ETL')

        return rest.accepted()

    @staticmethod
    def _etk_stop(project_name, wait_till_kill=True, clean_up_queue=False):

        url = config['etl']['url'] + '/kill_etk'
        payload = {
            'project_name': project_name
        }
        if clean_up_queue:
            payload['input_offset'] = 'seek_to_end'
            payload['output_offset'] = 'seek_to_end'
        resp = requests.post(url, json.dumps(payload), timeout=config['etl']['timeout'])
        if resp.status_code // 100 != 2:
            logger.error('failed to kill_etk in ETL')
            return False

        if wait_till_kill:
            while True:
                time.sleep(5)
                if not Actions._is_etk_running(project_name):
                    break
        return True

    @staticmethod
    def _publish_to_kafka_input_queue(doc_id, catalog_obj, producer, topic):
        try:
            with codecs.open(catalog_obj['json_path'], 'r') as f:
                doc_obj = json.loads(f.read())
            with codecs.open(catalog_obj['raw_content_path'], 'r') as f:
                doc_obj['raw_content'] = f.read()  # .decode('utf-8', 'ignore')
        except Exception as e:
            logger.exception('error in reading file from catalog')
            return False, 'error in reading file from catalog'
        try:
            r = producer.send(topic, doc_obj)
            r.get(timeout=60)  # wait till sent
            logger.info('sent %s to topic %s', doc_id, topic)
        except Exception as e:
            logger.exception('error in sending data to kafka queue')
            return False, 'error in sending data to kafka queue'

        return True, ''


class DataPushingWorker(threading.Thread):
    def __init__(self, project_name, sleep_interval):
        super(DataPushingWorker, self).__init__()
        self.project_name = project_name
        self.exit_signal = False
        self.stop_adding_data = False
        self.is_adding_data = False
        self.sleep_interval = sleep_interval

        # set up input kafka
        self.producer = kafka_producer
        self.input_topic = project_name + '_in'

    def get_status(self):
        return {
            'stop_adding_data': self.stop_adding_data,
            'is_adding_data': self.is_adding_data,
            'sleep_interval': self.sleep_interval
        }

    def run(self):
        logger.info('thread DataPushingWorker running... %s', self.project_name)
        while not self.exit_signal:
            if not self.stop_adding_data:
                self._add_data_worker(self.project_name, self.producer, self.input_topic)

            # wait interval
            t = self.sleep_interval * 10
            while t > 0 and not self.exit_signal:
                time.sleep(0.1)
                t -= 1

    def _add_data_worker(self, project_name, producer, input_topic):

        got_lock = data[project_name]['locks']['data'].acquire(False)
        try:
            # print '_add_data_worker got data lock?', got_lock
            if not got_lock or self.stop_adding_data:
                return

            for tld in data[project_name]['data'].iterkeys():
                if self.stop_adding_data:
                    break

                with data[project_name]['locks']['status']:
                    if tld not in data[project_name]['status']['added_docs']:
                        data[project_name]['status']['added_docs'][tld] = 0
                    if tld not in data[project_name]['status']['desired_docs']:
                        data[project_name]['status']['desired_docs'][tld] = \
                            data[project_name]['master_config'].get('default_desired_num', 0)
                    if tld not in data[project_name]['status']['total_docs']:
                        data[project_name]['status']['total_docs'][tld] = 0

                added_num = data[project_name]['status']['added_docs'][tld]
                total_num = data[project_name]['status']['total_docs'][tld]
                desired_num = data[project_name]['status']['desired_docs'][tld]
                desired_num = min(desired_num, total_num)

                # only add docs to queue if desired num is larger than added num
                if desired_num > added_num:
                    self.is_adding_data = True

                    # update mark in catalog
                    num_to_add = desired_num - added_num
                    added_num_this_round = 0
                    for doc_id in data[project_name]['data'][tld].iterkeys():

                        if not self.stop_adding_data:

                            # finished
                            if num_to_add <= 0:
                                break

                            # already added
                            if data[project_name]['data'][tld][doc_id]['add_to_queue']:
                                continue

                            # mark data
                            data[project_name]['data'][tld][doc_id]['add_to_queue'] = True
                            num_to_add -= 1
                            added_num_this_round += 1

                            # publish to kafka queue
                            ret, msg = Actions._publish_to_kafka_input_queue(
                                doc_id, data[project_name]['data'][tld][doc_id], producer, input_topic)
                            if not ret:
                                logger.error('Error of pushing data to Kafka: %s', msg)
                                # roll back
                                data[project_name]['data'][tld][doc_id]['add_to_queue'] = False
                                num_to_add += 1
                                added_num_this_round -= 1

                    self.is_adding_data = False

                    if added_num_this_round > 0:
                        with data[project_name]['locks']['status']:
                            data[project_name]['status']['added_docs'][tld] = added_num + added_num_this_round
                        set_catalog_dirty(project_name)
                        set_status_dirty(project_name)

        except Exception as e:
            logger.exception('exception in Actions._add_data_worker() data lock')
        finally:
            if got_lock:
                data[project_name]['locks']['data'].release()


class MemoryDumpWorker(threading.Thread):
    def __init__(self, project_name, sleep_interval, function, kwargs=dict()):
        super(MemoryDumpWorker, self).__init__()
        self.project_name = project_name
        self.exit_signal = False
        init_time = time.time()
        self.file_timestamp = init_time
        self.memory_timestamp = init_time

        self.sleep_interval = sleep_interval
        self.function = function
        self.kwargs = kwargs

    def get_status(self):
        return {
            'sleep_interval': self.sleep_interval,
            'file_timestamp': self.file_timestamp,
            'memory_timestamp': self.memory_timestamp,
            'is_dirty': self.file_timestamp != self.memory_timestamp
        }

    def run_function(self):
        # print self.memory_timestamp, self.file_timestamp
        memory_timestamp = self.memory_timestamp
        if self.file_timestamp < memory_timestamp:
            self.function(**self.kwargs)
            self.file_timestamp = memory_timestamp

    def run(self):
        logger.info('thread MemoryDumpWorker (%s) running... %s', self.function.__name__, self.project_name)
        while not self.exit_signal:
            self.run_function()

            # wait interval
            t = self.sleep_interval * 10
            while t > 0 and not self.exit_signal:
                time.sleep(0.1)
                t -= 1

        # make sure memory data is dumped
        self.run_function()


def ensure_sandpaper_is_on():
    try:
        # make sure es in on
        url = config['es']['sample_url']
        resp = requests.get(url)

        # make sure sandpaper is on
        url = config['sandpaper']['url']
        resp = requests.get(url)

    except requests.exceptions.ConnectionError:
        # es if not online, retry
        time.sleep(5)
        ensure_sandpaper_is_on()


def ensure_etl_engine_is_on():
    try:
        url = config['etl']['url']
        resp = requests.get(url, timeout=config['etl']['timeout'])

    except requests.exceptions.ConnectionError:
        # es if not online, retry
        time.sleep(5)
        ensure_etl_engine_is_on()


def ensure_kafka_is_on():
    global kafka_producer
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=config['kafka']['servers'],
            max_request_size=10485760,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip'
        )
    except NoBrokersAvailable as e:
        time.sleep(5)
        ensure_kafka_is_on()


def graceful_killer(signum, frame):
    logger.info('SIGNAL #%s received, notifying threads to exit...', signum)
    for project_name in data.iterkeys():
        try:
            stop_threads_and_locks(project_name)
        except:
            pass
        logger.info('threads exited, exiting main thread...')
    sys.exit()


def start_threads_and_locks(project_name):
    data[project_name]['locks']['data'] = threading.Lock()
    data[project_name]['locks']['status'] = threading.Lock()
    data[project_name]['locks']['catalog_log'] = threading.Lock()

    data[project_name]['data_pushing_worker'] = DataPushingWorker(
        project_name, config['data_pushing_worker_backoff_time'])
    data[project_name]['data_pushing_worker'].start()
    data[project_name]['status_memory_dump_worker'] = MemoryDumpWorker(
        project_name, config['status_memory_dump_backoff_time'],
        update_status_file, kwargs={'project_name': project_name})
    data[project_name]['status_memory_dump_worker'].start()
    data[project_name]['catalog_memory_dump_worker'] = MemoryDumpWorker(
        project_name, config['catalog_memory_dump_backoff_time'],
        update_catalog_file, kwargs={'project_name': project_name})
    data[project_name]['catalog_memory_dump_worker'].start()


def stop_threads_and_locks(project_name):
    try:
        data[project_name]['data_pushing_worker'].exit_signal = True
        data[project_name]['data_pushing_worker'].join()
        data[project_name]['status_memory_dump_worker'].exit_signal = True
        data[project_name]['status_memory_dump_worker'].join()
        data[project_name]['catalog_memory_dump_worker'].exit_signal = True
        data[project_name]['catalog_memory_dump_worker'].join()
        logger.info('threads of project %s exited', project_name)
    except:
        pass


if __name__ == '__main__':
    try:
        # prerequisites
        logger.info('ensure sandpaper is on...')
        ensure_sandpaper_is_on()
        logger.info('ensure etl engine is on...')
        ensure_etl_engine_is_on()
        logger.info('ensure kafka is on...')
        ensure_kafka_is_on()

        logger.info('register signal handler...')
        signal.signal(signal.SIGINT, graceful_killer)
        signal.signal(signal.SIGTERM, graceful_killer)

        # init
        for project_name in os.listdir(config['repo']['local_path']):
            project_dir_path = _get_project_dir_path(project_name)

            if os.path.isdir(project_dir_path) and \
                    not (project_name.startswith('.') or project_name.startswith('_')):
                data[project_name] = templates.get('project')
                logger.info('loading project %s...', project_name)

                # master config
                master_config_file_path = os.path.join(project_dir_path, 'master_config.json')
                if not os.path.exists(master_config_file_path):
                    logger.error('Missing master_config.json file for ' + project_name)
                with codecs.open(master_config_file_path, 'r') as f:
                    data[project_name]['master_config'] = json.loads(f.read())

                # annotations
                TagAnnotationsForEntityType.load_from_tag_file(project_name)
                FieldAnnotations.load_from_field_file(project_name)

                # data
                data_db_path = os.path.join(project_dir_path, 'data/_db.json')
                data_persistence.prepare_data_file(data_db_path)
                if os.path.exists(data_db_path):
                    with codecs.open(data_db_path, 'r') as f:
                        data[project_name]['data'] = json.loads(f.read())

                # status
                status_path = os.path.join(_get_project_dir_path(project_name), 'working_dir/status.json')
                data_persistence.prepare_data_file(status_path)
                if os.path.exists(status_path):
                    with codecs.open(status_path, 'r') as f:
                        data[project_name]['status'] = json.loads(f.read())
                        if 'added_docs' not in data[project_name]['status']:
                            data[project_name]['status']['added_docs'] = dict()
                        if 'desired_docs' not in data[project_name]['status']:
                            data[project_name]['status']['desired_docs'] = dict()
                        if 'total_docs' not in data[project_name]['status']:
                            data[project_name]['status']['total_docs'] = dict()
                # initialize total docs status every time
                for tld in data[project_name]['data'].iterkeys():
                    data[project_name]['status']['total_docs'][tld] \
                        = len(data[project_name]['data'][tld])
                update_status_file(project_name)

                # re-config sandpaper
                url = '{}/config?project={}&index={}&endpoint={}'.format(
                    config['sandpaper']['url'],
                    project_name,
                    data[project_name]['master_config']['index']['sample'],
                    config['es']['sample_url']
                )
                resp = requests.post(url, json=data[project_name]['master_config'], timeout=10)
                if resp.status_code // 100 != 2:
                    logger.error('failed to re-config sandpaper for project %s', project_name)

                # re-config etl engine
                url = config['etl']['url'] + '/create_project'
                payload = {
                    'project_name': project_name
                }
                resp = requests.post(url, json.dumps(payload), timeout=config['etl']['timeout'])
                if resp.status_code // 100 != 2:
                    logger.error('failed to re-config ETL Engine for project %s', project_name)

                # create project daemon thread
                start_threads_and_locks(project_name)

        # run app
        logger.info('starting web service...')
        app.run(debug=config['debug'], host=config['server']['host'], port=config['server']['port'], threaded=True)

    except KeyboardInterrupt:
        graceful_killer()
    except Exception as e:
        logger.exception('exception in main function')
