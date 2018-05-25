from app_base import *


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
        return rest.deleted()
