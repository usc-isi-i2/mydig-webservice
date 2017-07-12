workflow_xml_start = """<workflow-app name="etk-april-2017" xmlns="uri:oozie:workflow:0.5">
  <global>
            <configuration>
                <property>
                    <name>oozie.launcher.mapreduce.map.memory.mb</name>
                    <value>10000</value>
                </property>
            </configuration>
  </global>
    <start to="shell-1120"/>
    <kill name="Kill">
        <message>Action failed, error message[${wf:errorMessage(wf:lastErrorNode())}]</message>
    </kill>
    <action name="shell-1120">
        <shell xmlns="uri:oozie:shell-action:0.1">
            <job-tracker>${jobTracker}</job-tracker>
            <name-node>${nameNode}</name-node>
            <configuration>
                <property>
                    <name>mapred.input.dir.recursive</name>
                    <value>true</value>
                </property>
                <property>
                    <name>oozie.action.max.output.data</name>
                    <value>8192</value>
                </property>
            </configuration>
            <exec>./run.sh</exec>
"""

workflow_xml_end = """              <capture-output/>
        </shell>
        <ok to="End"/>
        <error to="Kill"/>
    </action>
    <end name="End"/>
</workflow-app>"""


class WM(object):
    def __init__(self):
        self.workflow_xml_start = workflow_xml_start
        self.workflow_xml_end = workflow_xml_end

    @staticmethod
    def create_file_property_for_workflow_xml(file_path):
        v = file_path.split('/')
        file_name = v[len(v) - 1].strip()
        if file_name and file_name != '':
            return '<file>{}#{}</file>'.format(file_path, file_name)

    @staticmethod
    def create_archive_property_for_workflow_xml(file_path, extension_length=3):
        v = file_path.split('/')
        file_name = v[len(v) - 1].strip()
        file_name = file_name[0:len(file_name) - (extension_length + 1)]  # +1 is for the '.'
        if file_name and file_name != '':
            return '<archive>{}#{}</archive>'.format(file_path, file_name)

    @staticmethod
    def create_arguments_for_workflow_xml(argument):
        return '<argument>{}</argument>'.format(argument)


if __name__ == '__main__':
    # print WM.create_file_property_for_workflow_xml('/user/worker/etk/lib/dictionaries/eyecolors.json.gz')
    # print WM.create_archive_property_for_workflow_xml('/user/worker/etk/lib/etk_env.zip')
    wm = WM()
    files = wm.create_file_property_for_workflow_xml('/user/worker/etk/lib/dictionaries/eyecolors.json.gz')
    archive = wm.create_archive_property_for_workflow_xml('/user/worker/etk/lib/etk_env.zip')
    argument = wm.create_arguments_for_workflow_xml('extraction_config.json')
    wf = wm.workflow_xml_start +  argument + files + archive + wm.workflow_xml_end
    print wf
