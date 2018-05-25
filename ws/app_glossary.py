from app_base import *


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
        file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + name + '.txt')
        gzip_file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + name + '.txt.gz')
        json_file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + name + '.json.gz')

        content = args['glossary_file'].stream.read()
        with gzip.open(gzip_file_path, 'w') as f:
            f.write(content)
        with gzip.open(json_file_path, 'w') as f:
            f.write(ProjectGlossaries.convert_glossary_to_json(content))
        write_to_file(content, file_path)
        # file.save(file_path)

        self.compute_statistics(project_name, name, json_file_path)

        return rest.created()

    @requires_auth
    def get(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        return list(data[project_name]['master_config']['glossaries'].keys())

    @requires_auth
    def delete(self, project_name):
        if project_name not in data:
            return rest.not_found('Project {} not found'.format(project_name))

        dir_path = os.path.join(get_project_dir_path(project_name), 'glossaries')
        shutil.rmtree(dir_path)
        os.mkdir(dir_path)  # recreate folder
        data[project_name]['master_config']['glossaries'] = dict()
        # remove all glossary names from all fields
        for k, v in data[project_name]['master_config']['fields'].items():
            if 'glossaries' in v and v['glossaries']:
                v['glossaries'] = []
        update_master_config_file(project_name)
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

        # t = CrfTokenizer()
        # t.setRecognizeHtmlEntities(True)
        # t.setRecognizeHtmlTags(True)
        # t.setSkipHtmlTags(True)

        for line in lines:
            line = line.strip()
            if len(line) == 0:  # trim empty line
                continue
            # line = ' '.join(t.tokenize(line))
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

        file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + name + '.txt')
        gzip_file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + name + '.txt.gz')
        json_file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + name + '.json.gz')

        # file = args['glossary_file']
        # file.save(file_path)

        content = args['glossary_file'].stream.read()
        with gzip.open(gzip_file_path, 'w') as f:
            f.write(content)
        with gzip.open(json_file_path, 'w') as f:
            f.write(ProjectGlossaries.convert_glossary_to_json(content))
        write_to_file(content, file_path)

        ProjectGlossaries.compute_statistics(project_name, glossary_name, json_file_path)
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

        file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.txt.gz')
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

        file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.txt')
        gzip_file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.txt.gz')
        json_file_path = os.path.join(get_project_dir_path(project_name), 'glossaries/' + glossary_name + '.json.gz')
        os.remove(file_path)
        os.remove(gzip_file_path)
        os.remove(json_file_path)
        del data[project_name]['master_config']['glossaries'][glossary_name]
        # remove glossary_name from field which contains it
        for k, v in data[project_name]['master_config']['fields'].items():
            if 'glossaries' in v and glossary_name in v['glossaries']:
                v['glossaries'].remove(glossary_name)
        update_master_config_file(project_name)
        return rest.deleted()
