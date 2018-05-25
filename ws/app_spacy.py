from app_base import *

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

        path = os.path.join(get_project_dir_path(project_name), 'spacy_rules/' + field_name + '.json')
        data[project_name]['master_config']['fields'][field_name]['number_of_rules'] = len(obj['rules'])
        # data[project_name]['master_config']['spacy_field_rules'] = {field_name: path}
        update_master_config_file(project_name)
        write_to_file(json.dumps(obj, indent=2), path)

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

        path = os.path.join(get_project_dir_path(project_name), 'spacy_rules/' + field_name + '.json')
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

        path = os.path.join(get_project_dir_path(project_name), 'spacy_rules/' + field_name + '.json')
        if not os.path.exists(path):
            return rest.not_found('no spacy rules')
        os.remove(path)
        data[project_name]['master_config']['fields'][field_name]['number_of_rules'] = 0
        # del data[project_name]['master_config']['spacy_field_rules'][field_name]
        update_master_config_file(project_name)
        return rest.deleted()