from app_base import *

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
        return rest.deleted()