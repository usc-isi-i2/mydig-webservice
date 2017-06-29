import os
import json
import codecs
from config import config

default_etk_config_str = """{
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
            },
            "table": {
                "field_name": "table"
            }
        }
    },
    "kg_enhancement": {
        "input_path": "knowledge_graph.`parent`",
        "fields": {
            "populated_places": {
                "priority": 0,
                "extractors": {
                    "geonames_lookup": {
                        "config": {}
                    }
                }
            },
            "country": {
                "priority": 1,
                "extractors": {
                    "country_from_states": {
                        "config": {}
                    }
                }
            },
            "city_state_pair": {
                "priority": 2,
                "extractors": {
                    "create_city_state_pair": {
                        "config": {}
                    }
                }
            }
        }
    }
}"""

out_of_the_box_fields_and_extractors = {
    "social_media": "extract_using_spacy",
    "review_id": "extract_review_id",
    "posting_date": "extract_using_spacy",
    "phone": "extract_phone",
    "email": "extract_email",
    "address": "extract_using_spacy",
    "website": "extract_website_domain"
}

inferlink_fields_post_filter = {
    'phone': 'extract_phone',
    'email': 'extract_email',
    'posting_date': 'parse_date'
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
            for rule in rules:
                rule['removehtml'] = True
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


def generate_etk_config(project_master_config, webservice_config, project_name, document_id='doc_id',
                        content_extraction_only=False):
    if 'repo_landmark' not in webservice_config:
        raise KeyError('landmark repository path not defined in the master config')
    default_etk_config = json.loads(default_etk_config_str)
    default_etk_config['document_id'] = document_id
    landmark_repo_path = os.path.join(os.path.dirname(__file__), webservice_config['repo_landmark']['local_path'])
    project_local_path = os.path.join(os.path.dirname(__file__), webservice_config['repo']['local_path'])
    landmark_rules_path = os.path.join(landmark_repo_path, project_name + "/landmark")
    consolidated_rules = consolidate_landmark_rules(landmark_rules_path)
    output_landmark_file_path = landmark_rules_path + "/consolidated_rules.json"
    o_file = codecs.open(output_landmark_file_path, 'w')
    o_file.write(json.dumps(consolidated_rules))
    o_file.close()

    # Add this file location to default etk config for landmark
    default_etk_config['resources']['landmark'].append(output_landmark_file_path)
    defined_fields = project_master_config['fields']
    mapping = create_fields_to_landmark_fields_mapping(defined_fields, consolidated_rules)

    if 'data_extraction' not in default_etk_config:
        default_etk_config['data_extraction'] = list()
    data_e_object = dict()
    inferlink_field_name = 'inferlink_extractions'
    try:
        inferlink_field_name = default_etk_config['content_extraction']['extractors']['landmark']['field_name']
    except:
        pass
    data_e_object['input_path'] = ["*.{}.*.text.`parent`".format(inferlink_field_name)]
    data_e_object['fields'] = dict()
    for field_name in mapping.keys():
        data_e_object['fields'][field_name] = create_landmark_data_extractor_for_field(mapping[field_name], field_name)
    default_etk_config['data_extraction'].append(data_e_object)

    if content_extraction_only:
        return default_etk_config

    etk_config = add_custom_spacy_extractors(add_glossary_extraction(default_etk_config, project_master_config),
                                             project_master_config, project_name, project_local_path)
    etk_config = add_default_field_extractors(project_master_config, etk_config)
    return etk_config


def create_landmark_data_extractor_for_field(mapped_fields, field_name):
    de = {
        "extractors": {
            "extract_from_landmark": {
                "config": {
                    "fields": mapped_fields
                }
            }
        }
    }

    if field_name == 'phone' or field_name == 'email' or field_name == 'posting_date':
        de['extractors']['extract_from_landmark']['config']['post_filter'] = [inferlink_fields_post_filter[field_name]]

    return de


def add_table_extractor_config(etk_config=json.loads(default_etk_config_str), table_classifier="some_path",
                               sem_labels="some_path", sem_labels_mapping="some_path"):
    # add table extractor to the content_extraction
    etk_config['content_extraction']['extractors']['table'] = {
        "field_name": "table",
        "extraction_policy": "keep_existing"
    }

    # add pickle to resources
    pickle = dict()
    pickle['table_classifier'] = table_classifier
    pickle['sem_labels'] = sem_labels
    pickle['sem_labels_mapping'] = sem_labels_mapping
    etk_config['resources']['pickle'] = pickle

    # add data_extraction
    de = [
        {
            "input_path": [
                "*.table[*]"
            ],
            "fields": {
                "table_type": {
                    "extractors": {
                        "classify_table": {
                            "config": {
                                "model": "table_classifier",
                                "sem_types": "sem_labels"
                            },
                            "extraction_policy": "replace"
                        }
                    }
                }
            }
        },
        {
            "input_path": [
                "*.table[*].data_extraction.table_type.classify_table.results[*]"
            ],
            "fields": {
                "*": {
                    "extractors": {
                        "table_data_extractor": {
                            "config": {
                                "method": "rule_based",
                                "model": "sem_labels_mapping",
                                "sem_types": "sem_labels"
                            },
                            "extraction_policy": "replace"
                        }
                    }
                }
            }
        }
    ]
    if 'data_extraction' not in etk_config:
        etk_config['data_extraction'] = list()
    etk_config['data_extraction'].extend(de)
    return etk_config


def choose_ngram(ngram_distribution):
    """{
        "ngram_distribution": {
            "1": 4
            }
        }"""
    max = -1
    for ngram_len in ngram_distribution.keys():
        ngram_len = int(ngram_len)
        if max < ngram_len < 4:
            max = ngram_len
    return max


def create_dictionary_data_extractor_for_field(ngram, dictionary_name):
    return {
        "extract_using_dictionary": {
            "config": {
                "dictionary": dictionary_name,
                "ngrams": ngram
            }
        }
    }


def add_glossary_extraction(etk_config, project_master_config):
    defined_fields = project_master_config['fields']
    glossaries = project_master_config['glossaries']

    if 'data_extraction' not in etk_config:
        etk_config['data_extraction'] = list()

    de_obj = dict()
    # even if we have multiple data extraction blocks with same input paths, the etk will do the right thing in running
    # the extraction efficiently
    de_obj['input_path'] = [
        "*.content_strict.text.`parent`",
        "*.content_relaxed.text.`parent`",
        "*.title.text.`parent`",
        "*.inferlink_extractions.*.text.`parent`"
    ]
    de_obj['fields'] = dict()

    for field in defined_fields.keys():
        field_definition = defined_fields[field]
        field_name = field_definition['name']
        if 'glossaries' in field_definition and len(field_definition['glossaries']) > 0:
            field_glossaries = field_definition['glossaries']
            for glossary in field_glossaries:
                if glossary in glossaries.keys():
                    g_path = glossaries[glossary]['path']
                    ngram = choose_ngram(glossaries[glossary]['ngram_distribution'])

                    # glossary path to etk
                    etk_config['resources']['dictionaries'][glossary] = g_path

                    # add this to data extraction part in etk config
                    if field_name not in de_obj['fields']:
                        de_obj['fields'][field_name] = dict()

                    if 'extractors' not in de_obj['fields'][field_name]:
                        de_obj['fields'][field_name]['extractors'] = dict()

                    de_obj['fields'][field_name]['extractors'].update(
                        create_dictionary_data_extractor_for_field(ngram, glossary))
    etk_config['data_extraction'].append(de_obj)
    return etk_config


def add_default_field_extractors(project_master_config, etk_config):
    de_obj = dict()
    # even if we have multiple data extraction blocks with same input paths, the etk will do the right thing in running
    # the extraction efficiently
    de_obj['input_path'] = [
        "*.content_strict.text.`parent`",
        "*.content_relaxed.text.`parent`",
        "*.title.text.`parent`",
        "*.inferlink_extractions.*.text.`parent`"
    ]
    de_obj['fields'] = dict()

    fields = project_master_config['fields']

    for field in fields.keys():
        field_definition = fields[field]
        field_name = field_definition['name']
        if 'predefined_extractor' in field_definition and field_definition['predefined_extractor'].strip() != '':
            default_field = field_definition['predefined_extractor']
            if default_field in out_of_the_box_fields_and_extractors:
                extractor = out_of_the_box_fields_and_extractors[default_field]
                de_obj['fields'][field_name] = dict()
                de_obj['fields'][field_name]['extractors'] = dict()
                de_obj['fields'][field_name]['extractors'][extractor] = dict()
                de_obj['fields'][field_name]['extractors'][extractor]['config'] = dict()

    if de_obj['fields'].keys() > 0:
        if 'data_extraction' not in etk_config:
            etk_config['data_extraction'] = list()
        etk_config['data_extraction'].append(de_obj)
    return etk_config


def add_custom_spacy_extractors(etk_config, project_master_config, project_name, project_local_path):
    if 'data_extraction' not in etk_config:
        etk_config['data_extraction'] = list()

    de_obj = dict()
    # even if we have multiple data extraction blocks with same input paths, the etk will do the right thing in running
    # the extraction efficiently
    de_obj['input_path'] = [
        "*.content_strict.text.`parent`",
        "*.content_relaxed.text.`parent`",
        "*.title.text.`parent`"
    ]
    de_obj['fields'] = dict()

    fields = project_master_config['fields']
    for field in fields.keys():
        if 'rule_extractor_enabled' in fields[field] and fields[field]['rule_extractor_enabled']:
            field_name = fields[field]['name']
            field_rule_file_path = os.path.join(project_local_path, project_name, 'spacy_rules/' + field_name + '.json')
            de_obj['fields'][field_name] = dict()
            de_obj['fields'][field_name]['extractors'] = dict()
            de_obj['fields'][field_name]['extractors']['extract_using_custom_spacy'] = dict()
            de_obj['fields'][field_name]['extractors']['extract_using_custom_spacy']['config'] = dict()
            de_obj['fields'][field_name]['extractors']['extract_using_custom_spacy']['config'][
                'spacy_field_rules'] = field_name

            if 'spacy_field_rules' not in etk_config['resources']:
                etk_config['resources']['spacy_field_rules'] = dict()

            etk_config['resources']['spacy_field_rules'][field_name] = field_rule_file_path

    etk_config['data_extraction'].append(de_obj)
    return etk_config


if __name__ == '__main__':
    webservice_config = config
    # print json.dumps(consolidate_landmark_rules(webservice_config, 'project02'), indent=2)
    # project_master_config = json.load(codecs.open('/Users/amandeep/Github/mydig-projects/project02/master_config.json'))
    project_master_config = json.load(codecs.open('/Users/amandeep/Github/mydig-projects/dig3-ht/master_config.json'))
    print json.dumps(generate_etk_config(project_master_config, webservice_config, 'project02', document_id='gtufhf',
                                         content_extraction_only=True),
                     indent=2)
    # print unique_landmark_field_names(consolidate_landmark_rules(webservice_config, 'project02'))
    # ngram_dist = {
    #     "1" : 4,
    #     "2" : 2,
    #     "5" : 45,
    #     "23" : 3
    # }
    #
    # print choose_ngram(ngram_dist)
