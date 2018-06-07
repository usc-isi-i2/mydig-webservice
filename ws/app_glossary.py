from app_base import *


@api.route('/projects/<project_name>/glossaries')
class ProjectGlossaries(Resource):
    @staticmethod
    def get_glossary_path(project_name, relative_path):
        return os.path.join(get_project_dir_path(project_name), 'glossaries/' + relative_path)

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
        file_path = ProjectGlossaries.get_glossary_path(project_name, name)

        args['glossary_file'].save(file_path)

        data[project_name]['master_config']['glossaries'][name] = {
            'mine_type': args.get('mime_type', 'text/plain'),
            'path': name
        }
        update_master_config_file(project_name)

        return rest.created()

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        return list(data[project_name]['master_config']['glossaries'].keys())

    # @requires_auth
    # def delete(self, project_name):
    #     if project_name not in data:
    #         return rest.not_found('Project {} not found'.format(project_name))
    #
    #     dir_path = os.path.join(get_project_dir_path(project_name), 'glossaries')
    #     shutil.rmtree(dir_path)
    #     os.mkdir(dir_path)  # recreate folder
    #     data[project_name]['master_config']['glossaries'] = dict()
    #     # remove all glossary names from all fields
    #     for k, v in data[project_name]['master_config']['fields'].items():
    #         if 'glossaries' in v and v['glossaries']:
    #             v['glossaries'] = []
    #     update_master_config_file(project_name)
    #     return rest.deleted()


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
        if args['glossary_name'] is None or args['glossary_file'] is None:
            return rest.bad_request('Invalid glossary_name or glossary_file')
        name = args['glossary_name'].strip()
        if len(name) == 0:
            return rest.bad_request('Invalid glossary_name')
        if name in data[project_name]['master_config']['glossaries']:
            return rest.exists('Glossary {} exists'.format(name))
        file_path = ProjectGlossaries.get_glossary_path(project_name, name)

        args['glossary_file'].save(file_path)

        data[project_name]['master_config']['glossaries'][name] = {
            'mine_type': 'application/gzip',
            'path': name
        }
        update_master_config_file(project_name)

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

        file_path = ProjectGlossaries.get_glossary_path(project_name,
                    data[project_name]['master_config']['glossaries'][glossary_name]['path'])
        mime_type = data[project_name]['master_config']['glossaries'][glossary_name].get('mime_type', 'text/plain')
        ret = send_file(file_path,
                        mimetype=mime_type,
                        as_attachment=True, attachment_filename=glossary_name)
        ret.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return ret

    @requires_auth
    def delete(self, project_name, glossary_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        if glossary_name not in data[project_name]['master_config']['glossaries']:
            return rest.not_found('Glossary {} not found'.format(glossary_name))

        file_path = ProjectGlossaries.get_glossary_path(project_name, glossary_name)

        os.remove(file_path)
        del data[project_name]['master_config']['glossaries'][glossary_name]
        # remove glossary_name from field which contains it
        for k, v in data[project_name]['master_config']['fields'].items():
            if 'glossaries' in v and glossary_name in v['glossaries']:
                v['glossaries'].remove(glossary_name)
        update_master_config_file(project_name)
        return rest.deleted()
