import os
import json
import codecs
from config import config

default_etk_config = {
    "document_id": "_id",
    "extraction_policy": "replace",
    "error_handling": "raise_error",
    "resources": {
        "dictionaries": {},
        "landmark": []
    },
    "content_extraction": {
        "input_path": "raw_content",
        "extractors": {
            "readability": [
                {
                    "strict": "yes",
                    "extraction_policy": "keep_existing",
                    "field_name": "content_strict"
                },
                {
                    "strict": "no",
                    "extraction_policy": "keep_existing",
                    "field_name": "content_relaxed"
                }
            ],
            "title": {
                "extraction_policy": "keep_existing"
            },
            "landmark": {
                "field_name": "inferlink_extractions",
                "extraction_policy": "keep_existing",
                "landmark_threshold": 0.5
            }
        }
    }
}


def consolidate_landmark_rules(landmark_rules_path):
    consolidated_rules = dict()

    if not os.path.exists(landmark_rules_path):
        raise Exception('landmark rules path does not exist: {}'.format(landmark_rules_path))

    for rules_file_name in os.listdir(landmark_rules_path):
        if not rules_file_name.startswith('.') and rules_file_name.endswith(
                'json') and rules_file_name != 'consolidated_rules.json':
            rules_file = json.load(codecs.open(os.path.join(landmark_rules_path, rules_file_name)))
            tld = rules_file['metadata']['tld']
            rules = rules_file['rules']
            if tld not in consolidated_rules:
                consolidated_rules[tld] = list()
            o = dict()
            o['tld'] = tld
            o['rules'] = rules
            consolidated_rules[tld].append(o)

    # Rename field names so as to make them unique across rule sets
    for tld in consolidated_rules.keys():
        rules_list = consolidated_rules[tld]
        for i in range(0, len(rules_list)):
            rules = rules_list[i]['rules']
            for j in range(0, len(rules)):
                rule = rules[j]
                rule['name'] = '{}-{}-{}'.format(rule['name'].split('-')[0], i, j)
    return consolidated_rules


def unique_landmark_field_names(consolidated_rules):
    fields = set()
    for tld in consolidated_rules.keys():
        rules_list = consolidated_rules[tld]
        for landmark_rules in rules_list:
            rules = landmark_rules['rules']
            for rule in rules:
                fields.add(rule['name'])
    return list(fields)


def create_fields_to_landmark_fields_mapping(defined_fields, consolidated_rules):
    mapping = dict()
    unique_fields = unique_landmark_field_names(consolidated_rules)

    for field in defined_fields.keys():
        field_name = defined_fields[field]['name']
        for unique_field in unique_fields:
            if field_name in unique_field:
                if field_name not in mapping:
                    mapping[field_name] = list()
                mapping[field_name].append(unique_field)
    return mapping


def generate_etk_config(project_master_config, webservice_config, project_name):
    defined_fields = project_master_config['fields']
    if 'repo_landmark' not in webservice_config:
        raise KeyError('landmark repository path not defined in the master config')

    landmark_repo_path = os.path.join(os.path.dirname(__file__), webservice_config['repo_landmark']['local_path'])
    landmark_rules_path = os.path.join(landmark_repo_path, project_name + "/landmark")
    consolidated_rules = consolidate_landmark_rules(landmark_rules_path)
    output_landmark_file_path = landmark_rules_path + "/consolidated_rules.json"
    o_file = codecs.open(output_landmark_file_path, 'w')
    o_file.write(json.dumps(consolidated_rules))
    o_file.close()
    # Add this file location to default etk config for landmark
    default_etk_config['resources']['landmark'].append(output_landmark_file_path)
    mapping = create_fields_to_landmark_fields_mapping(defined_fields, consolidated_rules)

    if 'data_extraction' not in default_etk_config:
        default_etk_config['data_extraction'] = list()
    data_e_object = dict()
    inferlink_field_name = default_etk_config['content_extraction']['extractors']['landmark']['field_name']
    data_e_object['input_path'] = ["*.{}.*.text.`parent`".format(inferlink_field_name)]
    data_e_object['fields'] = dict()
    for field_name in mapping.keys():
        data_e_object['fields'][field_name] = create_landmark_data_extractor_for_field(mapping[field_name])
    default_etk_config['data_extraction'].append(data_e_object)
    return default_etk_config


def create_landmark_data_extractor_for_field(mapped_fields):
    return {
        "extractors": {
            "extract_from_landmark": {
                "config": {
                    "fields": mapped_fields
                }
            }
        }
    }


if __name__ == '__main__':
    webservice_config = config
    # print json.dumps(consolidate_landmark_rules(webservice_config, 'project02'), indent=2)
    project_master_config = json.load(codecs.open('/Users/amandeep/Github/mydig-projects/project02/master_config.json'))
    print json.dumps(generate_etk_config(project_master_config, webservice_config, 'project02'), indent=2)
    # print unique_landmark_field_names(consolidate_landmark_rules(webservice_config, 'project02'))
