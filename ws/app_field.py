from app_base import *


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
                ('string', 'location', 'username', 'date', 'email', 'hyphenated', 'phone', 'image', 'kg_id', 'number',
                 'text'):
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
        if field_obj['type'] != 'number' and (
                        'enable_scoring_coefficient' in field_obj or 'scoring_coefficient' in field_obj):
            return False, 'Invalid field attributes: scoring_coefficient, enable_scoring_coefficient'
        if 'enable_scoring_coefficient' in field_obj and not isinstance(field_obj['enable_scoring_coefficient'], bool):
            return False, 'Invalid field attribute: enable_scoring_coefficient'
        if 'scoring_coefficient' in field_obj and not (
                    isinstance(field_obj['scoring_coefficient'], float) or isinstance(field_obj['scoring_coefficient'],
                                                                                      int)):
            return False, 'Invalid field attribute: scoring_coefficient'
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
        return rest.deleted()
