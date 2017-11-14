# it should be ran in etk_env
# and install flask

import json
import spacy
import sys
import os
sys.path.append(os.path.join('../ws'))
from config import config
sys.path.append(os.path.join(config['etk']['path'], 'etk'))
import core

from flask import Flask, request

app = Flask(__name__)

custom_nlp = spacy.load('en')
c = core.Core()


@app.route('/')
def home():
    return 'etk daemon running...'


@app.route('/test_spacy_rules', methods=['POST'])
def test_spacy_rules():

    try:
        obj = request.get_json(force=True)

        d = dict()
        d['simple_tokens_original_case'] = c.extract_tokens_from_crf(
            c.extract_crftokens(obj['test_text'], lowercase=False))

        config = dict()
        config['field_name'] = obj['field_name']
        if 'infer_rule' in obj and obj['infer_rule']:
            p_filtered = [[x.decode('string_escape').decode("utf-8") for x in pp if x] for pp in obj['positive_examples']]
            if not (p_filtered == [[]] or p_filtered == []):
                infered_rule = c.infer_rule_using_custom_spacy(d, p_filtered)
                obj["rules"].append(infered_rule)
        results = c.extract_using_custom_spacy(d, config, field_rules=obj)

        obj['test_tokens'] = d['simple_tokens_original_case']
        obj['results'] = results

        return json.dumps(obj), 201

    except Exception as e:
        print e
        return json.dumps({'message': 'exception: {}'.format(e.message)}), 400

if __name__ == '__main__':
    app.run(host=config['etk']['daemon']['host'], port=config['etk']['daemon']['port'],
            debug=config['debug'], threaded=True)
