import os
import json
import codecs
from config import config

def consolidate_landmark_rules(master_config, project_name):
    consolidated_rules = dict()
    if 'repo_landmark' not in master_config:
        raise KeyError('landmark repository path not defined in the master config')

    landmark_repo_path = os.path.join(os.path.dirname(__file__), master_config['repo_landmark']['local_path'])
    landmark_rules_path = os.path.join(landmark_repo_path, project_name + "/landmark")

    if not os.path.exists(landmark_rules_path):
        raise Exception('landmark rules path does not exist: {}'.format(landmark_rules_path))

    for rules_file_name in os.listdir(landmark_rules_path):
        if not rules_file_name.startswith('.') and rules_file_name.endswith('json'):
            rules_file = json.load(codecs.open(os.path.join(landmark_rules_path, rules_file_name)))
            tld = rules_file['metadata']['tld']
            rules = rules_file['rules']
            if tld not in consolidated_rules:
                consolidated_rules[tld] = list()
            o = dict()
            o['tld'] = tld
            o['rules'] = rules
            consolidated_rules[tld].append(o)
    return rename_field_names(consolidated_rules)


def rename_field_names(consolidated_rules):
    for tld in consolidated_rules.keys():
        rules_list = consolidated_rules[tld]
        for i in range(0, len(rules_list)):
            rules = rules_list[i]['rules']
            for j in range(0, len(rules)):
                rule = rules[j]
                rule['name'] = '{}-{}-{}'.format(rule['name'].split('-')[0], i, j)
    return consolidated_rules

if __name__ == '__main__':
    master_config = config
    print json.dumps(consolidate_landmark_rules(master_config, 'project02'), indent=2)
