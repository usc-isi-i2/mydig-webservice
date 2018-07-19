import os
import json
from . import em_additional_em_helper


class EmBaseGenerator(object):
    def __init__(self, template_path: str = 'template.tpl'):
        with open(template_path, 'r') as f:
            self.template = f.read()

        self.predefined_extractors = {
            'bitcoin_address': {
                'name': 'BitcoinAddressExtractor',
                'params': ''
            },
            'cryptographic': {
                'name': 'CryptographicHashExtractor',
                'params': ''
            },
            'cve': {
                'name': 'CVEExtractor',
                'params': ''
            },
            'date': {
                'name': 'DateExtractor',
                'params': 'etk'
            },
            'hostname': {
                'name': 'HostnameExtractor',
                'params': ''
            },
            'ip_address': {
                'name': 'IPAddressExtractor',
                'params': ''
            },
            'table_extractor': {
                'name': 'TableExtractor',
                'params': ''
            },
            'url': {
                'name': 'URLExtractor',
                'params': ''
            }
        }

    def generate_em_base(self, master_config: dict,
                         glossary_dir='', inferlink_dir='',
                         working_dir='', spacy_dir='') -> str:

        configs = master_config
        fields = configs['fields']
        glossaries = configs['glossaries']
        extractors = []
        executions = []
        for f in fields:
            if 'glossaries' in fields[f] and fields[f]['glossaries']:
                glossary_name = fields[f]['glossaries'][0]
                glossary_path = ''
                case_sensitive = False
                if glossary_name in glossaries:
                    if 'path' in glossaries[glossary_name]:
                        glossary_path = os.path.join(glossary_dir, glossaries[glossary_name]['path'])
                    if 'ngram_distribution' in glossaries[glossary_name]:
                        ngrams = max(glossaries[glossary_name]['ngram_distribution'].keys())
                    if 'case_sensitive' in glossaries[glossary_name]:
                        case_sensitive = glossaries[glossary_name]['case_sensitive']
                if glossary_path:
                    extractors.append(self.indent(
                        self.generate_glossary_extractor(f, glossary_path, case_sensitive=case_sensitive), 8) + '\n')
                    executions.append(self.indent(self.generate_execution(f), 12) + '\n')
            elif 'rule_extractor_enabled' in fields[f] and fields[f]['rule_extractor_enabled']:
                spacy_rule_path = os.path.join(spacy_dir, '{id}.json'.format(id=f))
                extractors.append(self.indent(self.generate_spacy_rule_extractor(f, spacy_rule_path), 8) + '\n')
                executions.append(self.indent(self.generate_execution(f), 12) + '\n')
            elif 'predefined_extractor' in fields[f] and fields[f]['predefined_extractor']:
                name = fields[f]['predefined_extractor']
                if name in self.predefined_extractors:
                    statement = self.generate_extractor_simple(
                        f, self.predefined_extractors[name]['name'], self.predefined_extractors[name]['params'])
                    extractors.append(self.indent(statement, 8) + '\n')
                    executions.append(self.indent(self.generate_execution(f), 12) + '\n')

        # inferlink
        inferlink_extractors = {}
        for rule_file in os.listdir(inferlink_dir):
            if not rule_file.endswith('.json'):
                continue
            rule_file = os.path.join(inferlink_dir, rule_file)

            with open(rule_file) as f:
                tld = json.load(f)['metadata']['tld']
                inferlink_extractors[tld] = rule_file
        extractors.append(self.indent(self.generate_inferlink_extractors(inferlink_extractors), 8))

        final = self.template.replace('${extractor_list}', ''.join(extractors)) \
            .replace('${execution_list}', ''.join(executions))
        final = em_additional_em_helper.replace_variables(final, glossary_dir)
        return final

    @staticmethod
    def indent(content, indent=4):
        indent_chars = ' ' * indent
        ret = ''
        for line in content.split('\n'):
            ret += indent_chars + line + '\n'
        return ret

    @staticmethod
    def generate_inferlink_extractors(inferlink_extractors):
        kvs = ""
        for tld, path in inferlink_extractors.items():
            kvs += "    '{tld}': InferlinkExtractor(InferlinkRuleSet(""" \
                   "InferlinkRuleSet.load_rules_file('{path}'))),\n".format(tld=tld, path=path)

        return "self.inferlink_extractors = {\n" + kvs + "\n}"

    @staticmethod
    def generate_execution(field_id: str) -> str:
        template = "for extraction in doc.extract(self.{id}_extractor, text): " \
                   "doc.kg.add_value('{id}', value=extraction.value)"
        return template.format(id=field_id)

    @staticmethod
    def generate_glossary_extractor(field_id: str, glossary_path: str,
                                    ngrams: int = 2, case_sensitive: bool = False, read_json = False) -> str:
        if '.json' in glossary_path:
            read_json = True
        template = "self.{id}_extractor = GlossaryExtractor(self.etk.load_glossary('{path}', read_json='{read_json_bool}'), " \
                   "'{id}_extractor', self.etk.default_tokenizer, case_sensitive={case_sensitive}, ngrams={ngrams})"
        return template.format(id=field_id, path=glossary_path, case_sensitive=str(case_sensitive), ngrams=str(ngrams),
                               read_json_bool=read_json)

    @staticmethod
    def generate_spacy_rule_extractor(field_id: str, path: str) -> str:
        template = "self.{id}_extractor = SpacyRuleExtractor(self.etk.default_nlp, " \
                   "self.etk.load_spacy_rule('{path}'), '{id}_extractor')"
        return template.format(id=field_id, path=path)

    @staticmethod
    def generate_extractor_simple(field_id: str, extractor_name: str, params: str = ''):
        template = "self.{id}_extractor = {name}({params})"
        return template.format(id=field_id, name=extractor_name, params=params)
