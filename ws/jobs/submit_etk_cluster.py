from manage_oozie_jobs import OozieJobs
from manage_workflow_xml import WM
from hdfs_operations import HdfsOp
import gzip
import json, codecs
import os


class SubmitEtk(object):
    def __init__(self):
        # http://10.1.94.54:14000/webhdfs/v1?user.name=aglahe&op=LISTSTATUS
        # https://webhdfs.memexproxy.com/webhdfs/v1?user.name=aglahe&op=LISTSTATUS
        self.web_hdfs_url = "http://10.1.94.54:14000/webhdfs/v1?user.name={}"
        self.oozie_url = "http://10.1.94.54:11000/oozie"
        self.worker_dir_path = '/user/worker/etk'
        self.default_lib_path = '{}/{}/lib/{}'
        self.files_to_upload = dict()
        self.hdfsop = HdfsOp()
        self.wf_application_path = "/user/worker/summer_evaluation_2017/workflows/etk/{0}"
        self.wm = WM()

    @staticmethod
    def get_file_name_from_path(file_path):
        v = file_path.split('/')
        return v[len(v) - 1].strip()

    def add_things_to_upload(self, key, source, destination):
        # print self.files_to_upload
        self.files_to_upload[key] = dict()
        self.files_to_upload[key]['source'] = source
        self.files_to_upload[key]['destination'] = destination

    def create_worflow_xml(self, etk_config, project_name, workflow_manager):
        # Add arguments for etk
        arguments = ['${INPUT}', '${OUTPUT}', 'extraction_config.json', '-p 1000']
        argument_xml = ''
        for argument in arguments:
            argument_xml += workflow_manager.create_arguments_for_workflow_xml(argument)

        # read etk and add all the files to workflow xml
        files = ''
        if 'resources' in etk_config:
            if 'dictionaries' in etk_config['resources']:
                dictionaries = etk_config['resources']['dictionaries']
                for k, v in dictionaries.items():
                    f = self.default_lib_path.format(self.worker_dir_path, project_name,
                                                     self.get_file_name_from_path(v))
                    files += workflow_manager.create_file_property_for_workflow_xml(f)
                    self.add_things_to_upload(k, v, f)
            if 'landmark' in etk_config['resources']:
                landmark = etk_config['resources']['landmark']
                if len(landmark) > 0:
                    landmark_f = landmark[0]
                    f = self.default_lib_path.format(self.worker_dir_path, project_name,
                                                     self.get_file_name_from_path(landmark_f))
                    files += workflow_manager.create_file_property_for_workflow_xml(f)
                    self.add_things_to_upload('landmark', landmark_f, f)
            if 'spacy_field_rules' in etk_config['resources']:
                spacy_field_rules = etk_config['resources']['spacy_field_rules']
                for k, v in spacy_field_rules.items():
                    f = self.default_lib_path.format(self.worker_dir_path, project_name,
                                                     self.get_file_name_from_path(v))
                    files += workflow_manager.create_file_property_for_workflow_xml(f)
                    self.add_things_to_upload(k, v, f)

        # upload extraction_config
        # but first change the path of resources
        etk_config = self.reformat_etk_config(etk_config)
        e_f = codecs.open('/tmp/extraction_config.json', 'w')
        e_f.write(json.dumps(etk_config))
        e_f.close()
        e_e_f = self.default_lib_path.format(self.worker_dir_path, project_name,
                                             self.get_file_name_from_path('/tmp/extraction_config.json'))
        files += workflow_manager.create_file_property_for_workflow_xml(e_e_f)
        self.add_things_to_upload('extraction_config.json', '/tmp/extraction_config.json', e_e_f)

        # add some defaults to files
        """
        <file>/user/worker/etk/lib/run_etk_spark.py#run_etk_spark.py</file>
            <file>/user/worker/etk/lib/etk_env.zip#etk_env.zip</file>
            <file>/user/worker/etk/lib/python-lib.zip#python-lib.zip</file>
            <file>/user/worker/etk/lib/run_template.sh#run_template.sh</file>
            <file>/user/worker/etk/lib/pyspark#pyspark</file>
        """
        files += workflow_manager.create_file_property_for_workflow_xml(
            '{}/lib/etk_env.zip'.format(self.worker_dir_path))

        files += workflow_manager.create_file_property_for_workflow_xml(
            '{}/lib/run_etk_spark.py'.format(self.worker_dir_path))

        files += workflow_manager.create_file_property_for_workflow_xml(
            '{}/lib/python-lib.zip'.format(self.worker_dir_path))

        files += workflow_manager.create_file_property_for_workflow_xml(
            '{}/lib/pyspark'.format(self.worker_dir_path))

        # put everything else in project's lib
        def_fs = ['run.sh']
        for def_f in def_fs:
            if def_f == 'run.sh':
                self.add_things_to_upload('run.sh', 'run.sh',
                                          self.default_lib_path.format(self.worker_dir_path, project_name, def_f))
                files += workflow_manager.create_file_property_for_workflow_xml(
                    'hdfs://' + self.default_lib_path.format(self.worker_dir_path, project_name, def_f))

        # add the etk env, this should be pretty constant and wouldn't have to be updated
        archive = workflow_manager.create_archive_property_for_workflow_xml(
            '{}/lib/etk_env.zip'.format(self.worker_dir_path))

        return '{}{}{}{}{}'.format(workflow_manager.workflow_xml_start, argument_xml, files, archive,
                                   workflow_manager.workflow_xml_end)

    def update_etk_lib_cluster(self, etk_config, project_name):
        #  update the workflow.xml and upload to the self.wf_application_path.format(project_name)
        workflow_xml = self.create_worflow_xml(etk_config, project_name, self.wm)
        temp_workflow_file = codecs.open('workflow.xml', 'w')
        temp_workflow_file.write(workflow_xml)
        temp_workflow_file.close()
        temp_workflow_file = codecs.open('workflow.xml', 'r')
        # create wf application path
        self.hdfsop.create_dir(self.wf_application_path.format(project_name))
        self.hdfsop.create_or_overwrite_file(self.wf_application_path.format(project_name) + '/workflow.xml',
                                             temp_workflow_file)

        # update run_sh
        run_content = self.create_run_sh()
        run_f = codecs.open('run.sh', 'w')
        run_f.write(run_content)
        run_f.close()

        # upload the dicts and other resources to cluster
        self.upload_files_to_hdfs()

        return True

    def reformat_etk_config(self, etk_config):
        if 'resources' in etk_config:
            if 'dictionaries' in etk_config['resources']:
                dictionaries = etk_config['resources']['dictionaries']
                for k, v in dictionaries.items():
                    f = self.get_file_name_from_path(v)
                    dictionaries[k] = f
            if 'landmark' in etk_config['resources']:
                landmark = etk_config['resources']['landmark']
                if len(landmark) > 0:
                    landmark_f = landmark[0]
                    f = self.get_file_name_from_path(landmark_f)
                    etk_config['resources']['landmark'][0] = f
            if 'spacy_field_rules' in etk_config['resources']:
                spacy_field_rules = etk_config['resources']['spacy_field_rules']
                for k, v in spacy_field_rules.items():
                    f = self.get_file_name_from_path(v)
                    spacy_field_rules[k] = f
        return etk_config

    def upload_files_to_hdfs(self):
        for file_name in self.files_to_upload.keys():
            f = self.files_to_upload[file_name]
            success = self.hdfsop.create_or_overwrite_file(f['destination'], codecs.open(f['source']))
            if not success:
                raise Exception('file upload failed, {}, {}, {}'.format(file_name, f['source'], f['destination']))
        return True

    def create_run_sh(self):
        """
        --files consolidated_rules.json,ethnicities.json.gz,haircolors.json.gz,
        eyecolors.json.gz,states_usa_canada.json.gz,adult_services.json.gz,countries.json.gz,
        stop_words.json.gz,city.json.gz,spacy_field_rules.json,states_usa_codes.json.gz,city_dict_alt_15000.json,
        country_codes_dict.json,states-to-codes-lower.json,cities_accepted_without_state.json \
        run_etk_spark.py \
        $@
        """
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_template.sh')
        run_content = codecs.open(script_path, 'r').read()
        run_content += ' --files '
        local_files = list()
        for k in self.files_to_upload.keys():
            local_files.append(self.get_file_name_from_path(self.files_to_upload[k]['source']))
        list_files = ','.join(local_files) + ' '
        run_content += list_files + ' '
        run_content += 'run_etk_spark.py $@'
        return run_content

    def submit_etk_cluster(self, master_project_config, project_name):

        property_dict = dict()
        property_dict["user.name"] = "asingh"
        property_dict[
            "oozie.wf.application.path"] = 'hdfs://memex:8020' + self.wf_application_path.format(project_name) + '/'
        property_dict["jobTracker"] = "memex-rm.xdata.data-tactics-corp.com:8032"
        property_dict["nameNode"] = "hdfs://memex"
        property_dict["oozie.use.system.libpath"] = "True"
        property_dict['INPUT'] = '/user/worker/cdr3/domain5/es/full'
        current_version = master_project_config['index']['version']
        property_dict['OUTPUT'] = '/user/worker/cdr3/domain5/etk_out/{}/{}'.format(project_name, str(current_version))
        oj = OozieJobs(oozie_url=self.oozie_url)
        return oj.submit_oozie_jobs(property_dict)


if __name__ == '__main__':
    etk_config = '/data/github/mydig-projects/my_project/working_dir/etk_config.json'
    s = SubmitEtk()

    wm = WM()
    # print s.create_worflow_xml(json.load(codecs.open(etk_config)), 'my_project', wm)
    s.update_etk_lib_cluster(json.load(codecs.open(etk_config)), 'my_project')
    master_project_config = json.load(codecs.open('/data/github/mydig-projects/my_project/master_config.json'))
    print s.submit_etk_cluster(master_project_config, 'my_project').content
