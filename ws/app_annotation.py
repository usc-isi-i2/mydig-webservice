from app_base import *


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
        file_path = os.path.join(get_project_dir_path(project_name), 'field_annotations/' + field_name + '.csv')
        field_obj = data[project_name]['field_annotations']
        with codecs.open(file_path, 'w') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=['field_name', 'kg_id', 'key', 'human_annotation'],
                delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for kg_id_, kg_obj_ in field_obj.items():
                for field_name_, field_obj_ in kg_obj_.items():
                    if field_name_ == field_name:
                        for key_, key_obj_ in field_obj_.items():
                            writer.writerow(
                                {'field_name': field_name_, 'kg_id': kg_id_,
                                 'key': key_, 'human_annotation': key_obj_['human_annotation']})

    @staticmethod
    def load_from_field_file(project_name):
        dir_path = os.path.join(get_project_dir_path(project_name), 'field_annotations')
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
            # if tag_name in kg_item.keys():
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

        return rest.deleted()

    @requires_auth
    def get(self, project_name, tag_name, entity_name):
        if project_name not in data:
            return rest.not_found('Project: {} not found'.format(project_name))
        if tag_name not in data[project_name]['master_config']['tags']:
            return rest.not_found('Tag {} not found'.format(tag_name))

        result = dict()
        if entity_name in data[project_name]['entities']:
            for kg_id, kg_item in data[project_name]['entities'][entity_name].items():
                for tag_name_, annotation in kg_item.items():
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
        file_path = os.path.join(get_project_dir_path(project_name), 'entity_annotations/' + tag_name + '.csv')
        tag_obj = data[project_name]['entities']
        with codecs.open(file_path, 'w') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=['tag_name', 'entity_name', 'kg_id', 'human_annotation'],
                delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for entity_name_, entity_obj_ in tag_obj.items():
                for kg_id_, kg_obj_ in entity_obj_.items():
                    for tag_name_, tag_obj_ in kg_obj_.items():
                        if tag_name_ == tag_name and 'human_annotation' in tag_obj_:
                            writer.writerow(
                                {'tag_name': tag_name_, 'entity_name': entity_name_,
                                 'kg_id': kg_id_, 'human_annotation': tag_obj_['human_annotation']})

    @staticmethod
    def load_from_tag_file(project_name):
        dir_path = os.path.join(get_project_dir_path(project_name), 'entity_annotations')
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