from app_base import *
from app_action import *


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
        project_dir_path = get_project_dir_path(project_name)

        if not os.path.exists(project_dir_path):
            os.makedirs(project_dir_path)

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
        os.makedirs(os.path.join(project_dir_path, 'field_annotations'))
        os.makedirs(os.path.join(project_dir_path, 'entity_annotations'))
        os.makedirs(os.path.join(project_dir_path, 'glossaries'))
        # dst_dir = os.path.join(get_project_dir_path(project_name), 'glossaries')
        # src_dir = config['default_glossaries_path']
        # for file_name in os.listdir(src_dir):
        #     full_file_name = os.path.join(src_dir, file_name)
        #     if os.path.isfile(full_file_name):
        #         shutil.copy(full_file_name, dst_dir)
        os.makedirs(os.path.join(project_dir_path, 'spacy_rules'))
        # dst_dir = os.path.join(project_dir_path, 'spacy_rules')
        # src_dir = config['default_spacy_rules_path']
        # for file_name in os.listdir(src_dir):
        #     full_file_name = os.path.join(src_dir, file_name)
        #     if os.path.isfile(full_file_name):
        #         shutil.copy(full_file_name, dst_dir)
        os.makedirs(os.path.join(project_dir_path, 'data'))
        os.makedirs(os.path.join(project_dir_path, 'working_dir'))
        os.makedirs(os.path.join(project_dir_path, 'working_dir/generated_em'))
        os.makedirs(os.path.join(project_dir_path, 'working_dir/additional_ems'))
        os.makedirs(os.path.join(project_dir_path, 'landmark_rules'))

        update_status_file(project_name)  # create status file after creating the working_dir

        start_threads_and_locks(project_name)

        logger.info('project %s created.' % project_name)
        return rest.created()

    @requires_auth
    def get(self):
        return list(data.keys())

    @staticmethod
    def validate(pro_obj):
        """
        :return: bool, message
        """
        if 'image_prefix' not in pro_obj or not isinstance(pro_obj['image_prefix'], str):
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
        if pro_obj['show_original_search'] not in ('V2', 'V1'):
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
            shutil.rmtree(os.path.join(get_project_dir_path(project_name)))
        except Exception as e:
            logger.error('delete project error: %s', e)
            return rest.internal_error('delete project error')

        return rest.deleted()