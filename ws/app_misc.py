import yaml
from app_base import *


@app.route('/spec')
def spec():
    return render_template('swagger_index.html', title='MyDIG web service API reference', spec_path='spec.yaml')


@app.route('/spec.yaml')
def spec_file_path():
    with open('spec.yaml', 'r') as f:
        c = yaml.load(f)
        c['host'] = request.host
    return Response(yaml.dump(c), mimetype='text/x-yaml')


@app.route('/')
def home():
    return 'MyDIG Web Service\n'


@api.route('/authentication')
class Authentication(Resource):
    @requires_auth
    def get(self):
        # no need to do anything here
        # if user can pass the basic auth, it will return ok here
        # or it will be blocked by auth verification
        return rest.ok()


@api.route('/projects/<project_name>/debug/<mode>')
class ProjectDebug(Resource):
    @requires_auth
    def get(self, project_name, mode):
        if mode == 'threads':
            ret = {
                'threads': dict(),
                'data_pushing_worker': data[project_name]['data_pushing_worker'].get_status(),
                'status_memory_dump_worker': data[project_name]['status_memory_dump_worker'].get_status(),
                'catalog_memory_dump_worker': data[project_name]['catalog_memory_dump_worker'].get_status()
            }
            for t in data[project_name]['threads']:
                ret['threads'][t.ident] = {
                    'is_alive': t.is_alive(),
                    'name': t.name
                }
            return ret

        elif mode == 'etk_stdout':
            size = request.args.get('size', '20')
            worker_id = request.args.get('worker_id', '*')
            cmd = 'tail -n {size} {dir_path}/etk_stdout_{worker_id}.txt'.format(
                size=size,
                dir_path=os.path.join(get_project_dir_path(project_name), 'working_dir'),
                worker_id=worker_id)
            logger.debug('getting etk_stdout: %s', cmd)
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            return Response(proc.stdout.read(), mimetype='text/plain')

        return dict()
