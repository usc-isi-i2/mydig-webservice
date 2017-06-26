# it should be ran in etk_env

from optparse import OptionParser
import json
import spacy
import sys
from config import config

sys.path.append(os.path.join(config['etk']['path'], 'etk'))
import core


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--input", action="store", type="string", dest="input_path")
    parser.add_option("-f", "--field", action="store", type="string", dest="field_name")
    (options, args) = parser.parse_args()

    with open(options.input_path, 'r') as f:
        obj = json.loads(f.read())

    custom_nlp = spacy.load('en')
    c = core.Core()

    d = dict()
    d['simple_tokens_original_case'] = c.extract_tokens_from_crf(
        c.extract_crftokens(obj['test_text'], lowercase=False))

    config = dict()
    config['field_name'] = options.field_name

    results = c.extract_using_custom_spacy(d, config, field_rules=obj)

    obj['test_tokens'] =d['simple_tokens_original_case']
    obj['results'] = results

    with open(options.input_path, 'w') as f:
        f.write(json.dumps(obj, indent=2))

    sys.exit(0)
