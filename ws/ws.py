from app_base import *
from app_misc import *
from app_data import *
from app_project import *
from app_tag import *
from app_field import *
from app_table import *
from app_annotation import *
from app_spacy import *
from app_glossary import *
from app_search import *
from app_action import *
import happybase


def ensure_sandpaper_is_on():
    try:
        # make sure es in on
        url = config['es']['sample_url']
        resp = requests.get(url)

        # make sure sandpaper is on
        url = config['sandpaper']['url']
        resp = requests.get(url)

    except requests.exceptions.ConnectionError:
        # es if not online, retry
        time.sleep(5)
        ensure_sandpaper_is_on()


def ensure_etl_engine_is_on():
    try:
        url = config['etl']['url']
        resp = requests.get(url, timeout=config['etl']['timeout'])

    except requests.exceptions.ConnectionError:
        # es if not online, retry
        time.sleep(5)
        ensure_etl_engine_is_on()


def ensure_kafka_is_on():
    global g_vars
    try:
        g_vars['kafka_producer'] = KafkaProducer(
            bootstrap_servers=config['kafka']['servers'],
            max_request_size=10485760,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip'
        )
    except NoBrokersAvailable as e:
        time.sleep(5)
        ensure_kafka_is_on()


def ensure_hbase_is_on():
    global g_vars
    try:
        g_vars['hbase_adapter'] = HBaseAdapter('hbase')
    except:
        time.sleep(5)
        ensure_hbase_is_on()


def graceful_killer(signum, frame):
    logger.info('SIGNAL #%s received, notifying threads to exit...', signum)
    for project_name in data.keys():
        try:
            stop_threads_and_locks(project_name)
        except:
            pass
        logger.info('threads exited, exiting main thread...')
    sys.exit()


if __name__ == '__main__':
    try:
        # prerequisites
        logger.info('ensure sandpaper is on...')
        ensure_sandpaper_is_on()
        logger.info('ensure etl engine is on...')
        ensure_etl_engine_is_on()
        logger.info('ensure kafka is on...')
        ensure_kafka_is_on()
        logger.info('ensure hbase is on...')
        ensure_hbase_is_on()

        logger.info('register signal handler...')
        signal.signal(signal.SIGINT, graceful_killer)
        signal.signal(signal.SIGTERM, graceful_killer)

        # init
        for project_name in os.listdir(config['repo']['local_path']):
            project_dir_path = get_project_dir_path(project_name)

            if os.path.isdir(project_dir_path) and \
                    not (project_name.startswith('.') or project_name.startswith('_')):
                data[project_name] = templates.get('project')
                logger.info('loading project %s...', project_name)

                # master config
                master_config_file_path = os.path.join(project_dir_path, 'master_config.json')
                if not os.path.exists(master_config_file_path):
                    logger.error('Missing master_config.json file for ' + project_name)
                with open(master_config_file_path, 'r') as f:
                    data[project_name]['master_config'] = json.loads(f.read())

                # annotations
                TagAnnotationsForEntityType.load_from_tag_file(project_name)
                FieldAnnotations.load_from_field_file(project_name)

                # data
                data_db_path = os.path.join(project_dir_path, 'data/_db.json')
                data_persistence.prepare_data_file(data_db_path)
                if os.path.exists(data_db_path):
                    with open(data_db_path, 'r') as f:
                        data[project_name]['data'] = json.loads(f.read())

                # status
                status_path = os.path.join(get_project_dir_path(project_name), 'working_dir/status.json')
                data_persistence.prepare_data_file(status_path)
                if os.path.exists(status_path):
                    with open(status_path, 'r') as f:
                        data[project_name]['status'] = json.loads(f.read())
                        if 'added_docs' not in data[project_name]['status']:
                            data[project_name]['status']['added_docs'] = dict()
                        if 'desired_docs' not in data[project_name]['status']:
                            data[project_name]['status']['desired_docs'] = dict()
                        if 'total_docs' not in data[project_name]['status']:
                            data[project_name]['status']['total_docs'] = dict()
                # initialize total docs status every time
                for tld in data[project_name]['data'].keys():
                    data[project_name]['status']['total_docs'][tld] \
                        = len(data[project_name]['data'][tld])
                update_status_file(project_name)

                # re-config sandpaper
                url = '{}/config?project={}&index={}&endpoint={}'.format(
                    config['sandpaper']['url'],
                    project_name,
                    data[project_name]['master_config']['index']['sample'],
                    config['es']['sample_url']
                )
                resp = requests.post(url, json=data[project_name]['master_config'], timeout=10)
                if resp.status_code // 100 != 2:
                    logger.error('failed to re-config sandpaper for project %s', project_name)

                # re-config etl engine
                url = config['etl']['url'] + '/create_project'
                payload = {
                    'project_name': project_name
                }
                resp = requests.post(url, json.dumps(payload), timeout=config['etl']['timeout'])
                if resp.status_code // 100 != 2:
                    logger.error('failed to re-config ETL Engine for project %s', project_name)

                # create project daemon thread
                start_threads_and_locks(project_name)

        # run app
        logger.info('starting web service...')
        app.run(debug=config['debug'], host=config['server']['host'], port=config['server']['port'], threaded=True)

    except KeyboardInterrupt:
        graceful_killer()
    except Exception as e:
        logger.exception('exception in main function')
