from app_base import *
from tldextract import tldextract
import io


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
        parse.add_argument('dataset')
        parse.add_argument('sync')
        parse.add_argument('log')
        args = parse.parse_args()

        file_type = args['file_type']
        file_data = args['file_data']

        dataset = args['dataset'] if args['dataset'] else 'mydig_dataset'

        if args['file_name'] is None:
            return rest.bad_request('Invalid file_name')
        file_name = args['file_name'].strip()
        if len(file_name) == 0:
            return rest.bad_request('Invalid file_name')
        if file_data is None:
            return rest.bad_request('Invalid file_data')
        if file_type is None:
            return rest.bad_request('Invalid file_type')
        args['sync'] = False if args['sync'] is None or args['sync'].lower() != 'true' else True
        args['log'] = True if args['log'] is None or args['log'].lower() != 'false' else False

        user_uploaded_file_path = None
        if file_type == 'csv' or file_type == 'html':
            """
                handle csv or tsv or xls or xlsx or html
                -----------------------------------
                TODO handled zipped files

                1. Create a cdr object and add the field `raw_content_path`
                2. store this file in the directory `user_uploaded_files`

            """
            user_uploaded_file_path = os.path.join(get_project_dir_path(project_name), 'user_uploaded_files', file_name)
            file_data.save(user_uploaded_file_path)

            new_file_data = dict()
            if file_type == 'csv':
                new_file_data['raw_content'] = ''
                new_file_data['raw_content_path'] = user_uploaded_file_path
            elif file_type == 'html':
                new_file_data['raw_content'] = open(user_uploaded_file_path, mode='rb').read().decode('utf-8')

            new_file_data['dataset'] = dataset
            new_file_data['tld'] = dataset
            new_file_data['file_name'] = file_name

            file_data = werkzeug.FileStorage(stream=io.BytesIO(bytes(json.dumps(new_file_data), encoding='utf-8')))

            file_name = '{}.jl'.format(file_name)
            file_type = 'json_lines'

        # make root dir and save temp file
        src_file_path = os.path.join(get_project_dir_path(project_name), 'data', '{}.tmp'.format(file_name))

        file_data.save(src_file_path)
        dest_dir_path = os.path.join(get_project_dir_path(project_name), 'data', file_name)
        if not os.path.exists(dest_dir_path):
            os.mkdir(dest_dir_path)

        if not args['sync']:
            t = threading.Thread(target=Data._update_catalog_worker,
                                 args=(project_name, file_name, file_type, src_file_path, dest_dir_path,
                                       args['log'], dataset, user_uploaded_file_path),
                                 name='data_upload')
            t.start()
            data[project_name]['threads'].append(t)

            return rest.accepted()
        else:
            Data._update_catalog_worker(project_name, file_name, file_type, src_file_path, dest_dir_path, args['log'],
                                        dataset=dataset, user_uploaded_file_path=user_uploaded_file_path)
            return rest.created()

    @staticmethod
    def _update_catalog_worker(project_name, file_name, file_type, src_file_path, dest_dir_path, log_on=True,
                               dataset=None, user_uploaded_file_path=None):
        def _write_log(content):
            with data[project_name]['locks']['catalog_log']:
                log_file.write('<#{}> {}: {}\n'.format(threading.get_ident(), file_name, content))

        log_path = os.path.join(get_project_dir_path(project_name),
                                'working_dir/catalog_error.log') if log_on else os.devnull
        log_file = open(log_path, 'a')
        _write_log('start updating catalog')

        try:
            if file_type == 'json_lines':
                suffix = os.path.splitext(file_name)[-1]
                f = gzip.open(src_file_path, mode='r', encoding='utf-8') \
                    if suffix in ('.gz', '.gzip') \
                    else open(src_file_path, mode='r', encoding='utf-8')

                for line in f:
                    if len(line.strip()) == 0:
                        continue
                    objs = json.loads(line)
                    if not isinstance(objs, list):
                        objs = [objs]
                    for obj in objs:
                        # raw_content
                        if 'raw_content' not in obj:
                            obj['raw_content'] = ''

                        # doc_id
                        obj['doc_id'] = obj.get('doc_id', obj.get('_id', ''))
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
                        tld_from_url = None
                        if 'url' not in obj:
                            obj['url'] = '{}/{}'.format(Data.generate_tld(file_name), obj['doc_id'])
                            _write_log('Generated URL for object: {}'.format(obj['url']))
                        else:
                            tld_from_url = Data.extract_tld(obj['url'])

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

                        if 'tld' not in obj:
                            if tld_from_url is not None:
                                tld = tld_from_url
                            else:
                                tld = dataset if dataset is not None else obj.get('tld', Data.extract_tld(obj['url']))
                            obj['tld'] = tld

                        tld = obj['tld']

                        with open(output_raw_content_path, 'w', encoding='utf-8') as output:
                            output.write(obj['raw_content'])
                        with open(output_json_path, 'w', encoding='utf-8') as output:
                            del obj['raw_content']
                            output.write(json.dumps(obj, indent=2))

                        # update data db
                        with data[project_name]['locks']['data']:
                            data[project_name]['data'][tld] = data[project_name]['data'].get(tld, dict())
                            # if doc_id is already there, still overwrite it
                            exists_before = True if obj['doc_id'] in data[project_name]['data'][tld] else False
                            data[project_name]['data'][tld][obj['doc_id']] = {
                                'raw_content_path': output_raw_content_path,
                                'json_path': output_json_path,
                                'url': obj['url'],
                                'add_to_queue': False,
                                'user_uploaded_file_path': user_uploaded_file_path if user_uploaded_file_path else ''
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
        log_path = os.path.join(get_project_dir_path(project_name), 'working_dir/catalog_error.log')

        # if args['type'] == 'has_error':
        #     ret['has_error'] = os.path.getsize(log_path) > 0
        if args['type'] == 'error_log':
            ret['error_log'] = list()
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    ret['error_log'] = tail_file(f, 200)
        else:
            with data[project_name]['locks']['status']:
                for tld, num in data[project_name]['status']['total_docs'].items():
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
                    for k, v in data[project_name]['data'][tld].items():
                        try:
                            os.remove(v['raw_content_path'])
                        except:
                            pass
                        try:
                            os.remove(v['json_path'])
                        except:
                            pass
                        try:
                            if v['user_uploaded_file_path'].strip() != '':
                                os.remove(v['user_uploaded_file_path'])
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
            # delete from kg
            try:
                es.es.delete_by_query(index=project_name,
                                      doc_type=data[project_name]['master_config']['root_name'],
                                      body=query.format(tld=tld))
            except:
                logger.exception('error in _delete_es_worker')

            # update status
            with data[project_name]['locks']['status']:
                if tld in data[project_name]['status']['added_docs']:
                    data[project_name]['status']['added_docs'][tld] = 0
                    data[project_name]['status']['desired_docs'][tld] = 0
                    set_status_dirty(project_name)

            # update data
            with data[project_name]['locks']['data']:
                if tld in data[project_name]['data']:

                    for doc_id in data[project_name]['data'][tld].keys():
                        data[project_name]['data'][tld][doc_id]['add_to_queue'] = False

                    set_catalog_dirty(project_name)

    @staticmethod
    def generate_tld(file_name):
        return 'www.dig_{}.org'.format(re.sub(re_url, '_', file_name.lower()).strip())

    @staticmethod
    def generate_doc_id(content):
        try:
            return hashlib.sha256(content).hexdigest().upper()
        except:
            return hashlib.sha256(content.encode('utf-8')).hexdigest().upper()

    @staticmethod
    def is_valid_doc_id(doc_id):
        return re_doc_id.match(doc_id) and doc_id not in os_reserved_file_names

    @staticmethod
    def extract_tld(url):
        return tldextract.extract(url).domain + '.' + tldextract.extract(url).suffix
