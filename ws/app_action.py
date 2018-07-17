from app_base import *
from app_data import *

import etk_helper


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
            tmp_project_config_path = os.path.join(get_project_dir_path(project_name),
                                                   'working_dir/uploaded_project_config.tar.gz')
            tmp_project_config_extracted_path = os.path.join(get_project_dir_path(project_name),
                                                             'working_dir/uploaded_project_config')
            args['file_data'].save(tmp_project_config_path)
            with tarfile.open(tmp_project_config_path, 'r:gz') as tar:
                tar.extractall(tmp_project_config_extracted_path)

            # master_config
            with open(os.path.join(tmp_project_config_extracted_path, 'master_config.json'), 'r') as f:
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
                os.path.join(get_project_dir_path(project_name), 'glossaries')
            )
            distutils.dir_util.copy_tree(
                os.path.join(tmp_project_config_extracted_path, 'spacy_rules'),
                os.path.join(get_project_dir_path(project_name), 'spacy_rules')
            )
            distutils.dir_util.copy_tree(
                os.path.join(tmp_project_config_extracted_path, 'landmark_rules'),
                os.path.join(get_project_dir_path(project_name), 'landmark_rules')
            )
            distutils.dir_util.copy_tree(
                os.path.join(tmp_project_config_extracted_path, 'working_dir/generated_em'),
                os.path.join(get_project_dir_path(project_name), 'working_dir/generated_em')
            )
            distutils.dir_util.copy_tree(
                os.path.join(tmp_project_config_extracted_path, 'working_dir/additional_ems'),
                os.path.join(get_project_dir_path(project_name), 'working_dir/additional_ems')
            )

            # etl config
            tmp_etl_config = os.path.join(tmp_project_config_extracted_path,
                                          'working_dir/etl_config.json')
            if os.path.exists(tmp_etl_config):
                shutil.copyfile(tmp_etl_config, os.path.join(get_project_dir_path(project_name),
                                                             'working_dir/etl_config.json'))

            # landmark
            tmp_landmark_config_path = os.path.join(tmp_project_config_extracted_path,
                                                    'working_dir/_landmark_config.json')
            if os.path.exists(tmp_landmark_config_path):
                with open(tmp_landmark_config_path, 'r') as f:
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

        export_path = os.path.join(get_project_dir_path(project_name), 'working_dir/project_config.tar.gz')

        # tarzip file
        with tarfile.open(export_path, 'w:gz') as tar:
            tar.add(os.path.join(get_project_dir_path(project_name), 'master_config.json'),
                    arcname='master_config.json')
            tar.add(os.path.join(get_project_dir_path(project_name), 'glossaries'),
                    arcname='glossaries')
            tar.add(os.path.join(get_project_dir_path(project_name), 'spacy_rules'),
                    arcname='spacy_rules')
            tar.add(os.path.join(get_project_dir_path(project_name), 'landmark_rules'),
                    arcname='landmark_rules')
            tar.add(os.path.join(get_project_dir_path(project_name), 'working_dir/generated_em'),
                    arcname='working_dir/generated_em')
            tar.add(os.path.join(get_project_dir_path(project_name), 'working_dir/additional_ems'),
                    arcname='working_dir/additional_ems')

            # etl config
            etl_config_path = os.path.join(get_project_dir_path(project_name),
                                           'working_dir/etl_config.json')
            if os.path.exists(etl_config_path):
                tar.add(etl_config_path, arcname='working_dir/etl_config.json')

            # landmark
            landmark_config = ActionProjectConfig.landmark_export(project_name)
            if len(landmark_config) > 0:
                landmark_config_path = os.path.join(
                    get_project_dir_path(project_name), 'working_dir/_landmark_config.json')
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


# @api.route('/projects/<project_name>/actions/etk_filters')
# class ActionProjectEtkFilters(Resource):
#     @requires_auth
#     def post(self, project_name):
#         if project_name not in data:
#             return rest.not_found('project {} not found'.format(project_name))
#
#         input = request.get_json(force=True)
#         filtering_rules = input.get('filters', {})
#
#         try:
#             # validation
#             for tld, rules in filtering_rules.items():
#                 if tld.strip() == '' or not isinstance(rules, list):
#                     return rest.bad_request('Invalid TLD')
#                 for rule in rules:
#                     if 'field' not in rule or rule['field'].strip() == '':
#                         return rest.bad_request('Invalid Field in TLD: {}'.format(tld))
#                     if 'action' not in rule or rule['action'] not in ('no_action', 'keep', 'discard'):
#                         return rest.bad_request('Invalid action in TLD: {}, Field {}'.format(tld, rule['field']))
#                     if 'regex' not in rule:
#                         return rest.bad_request('Invalid regex in TLD: {}, Field {}'.format(tld, rule['field']))
#                     try:
#                         re.compile(rule['regex'])
#                     except re.error:
#                         return rest.bad_request(
#                             'Invalid regex in TLD: {}, Field: {}'.format(tld, rule['field']))
#
#             # write to file
#             dir_path = os.path.join(get_project_dir_path(project_name), 'working_dir')
#             if not os.path.exists(dir_path):
#                 os.mkdir(dir_path)
#             config_path = os.path.join(dir_path, 'etk_filters.json')
#             write_to_file(json.dumps(input), config_path)
#             return rest.created()
#         except Exception as e:
#             logger.exception('fail to import ETK filters')
#             return rest.internal_error('fail to import ETK filters')
#
#     def get(self, project_name):
#         if project_name not in data:
#             return rest.not_found('project {} not found'.format(project_name))
#
#         ret = {'filters': {}}
#         config_path = os.path.join(get_project_dir_path(project_name),
#                                    'working_dir/etk_filters.json')
#         if os.path.exists(config_path):
#             with open(config_path, 'r') as f:
#                 ret = json.loads(f.read())
#
#         return ret


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
                for tld in data[project_name]['status']['total_docs'].keys():
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

            ret['tld_statistics'] = list(tld_list.values())

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

        for tld, desired_num in tld_list.items():
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

        for tld, num_to_run in tld_list.items():
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
                for doc_id, catalog_obj in data[project_name]['data'][tld].items():
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
        glossary_dir = os.path.join(get_project_dir_path(project_name), 'glossaries')
        inferlink_dir = os.path.join(get_project_dir_path(project_name), 'landmark_rules')
        working_dir = os.path.join(get_project_dir_path(project_name), 'working_dir')
        spacy_dir = os.path.join(get_project_dir_path(project_name), 'spacy_rules')
        content = etk_helper.generate_base_etk_module(
            data[project_name]['master_config'],
            glossary_dir=glossary_dir,
            inferlink_dir=inferlink_dir,
            working_dir=working_dir,
            spacy_dir=spacy_dir
        )
        revision = hashlib.sha256(content.encode('utf-8')).hexdigest().upper()[:6]
        output_path = os.path.join(get_project_dir_path(project_name),
                                   'working_dir/generated_em', 'em_base.py'.format(revision))
        archive_output_path = os.path.join(get_project_dir_path(project_name),
                                           'working_dir/generated_em', 'archive_em_{}.py'.format(revision))
        additional_ems_path = os.path.join(get_project_dir_path(project_name), 'working_dir/additional_ems')
        generated_additional_ems_path = os.path.join(get_project_dir_path(project_name),
                                                     'working_dir/generated_additional_ems')
        etk_helper.generated_additional_ems(additional_ems_path, generated_additional_ems_path, glossary_dir, inferlink_dir, working_dir, spacy_dir)
        write_to_file(content, output_path)
        write_to_file(content, archive_output_path)

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
        etl_config_path = os.path.join(get_project_dir_path(project_name), 'working_dir/etl_config.json')
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
            for tld in data[project_name]['status']['added_docs'].keys():
                data[project_name]['status']['added_docs'][tld] = 0
        with data[project_name]['locks']['data']:
            for tld in data[project_name]['data'].keys():
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
            file_path = os.path.join(get_project_dir_path(project_name),
                                     'glossaries', '{}.txt'.format(blacklist))

            query_conditions = []
            with open(file_path, 'r') as f:
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
                    doc_id, data[project_name]['data'][tld][doc_id], g_vars['kafka_producer'], input_topic)
                if not ret:
                    logger.error('Error of re-adding data to Kafka: %s', msg)
            except Exception as e:
                logger.exception('error in re_add_docs')

    @staticmethod
    def etk_extract(project_name, clean_up_queue=False):
        if Actions._is_etk_running(project_name):
            return rest.exists('already running')

        # etk_config_file_path = os.path.join(
        #     get_project_dir_path(project_name), 'working_dir/etk_config.json')
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
            with open(catalog_obj['json_path'], 'r') as f:
                doc_obj = json.loads(f.read())
            with open(catalog_obj['raw_content_path'], 'r') as f:
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
        self.producer = g_vars['kafka_producer']
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
            if not got_lock or self.stop_adding_data:
                return

            for tld in data[project_name]['data'].keys():
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
                    for doc_id in data[project_name]['data'][tld].keys():

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
