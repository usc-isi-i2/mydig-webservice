# it should be ran in etk_env
# and install flask

import json
import sys
import os
sys.path.append(os.path.join('../ws'))
from config import config
from flask import Flask, request
sys.path.append(os.path.join(config['etk']['path']))
from etk.etk import ETK
from etk.extractors.spacy_rule_extractor import SpacyRuleExtractor


app = Flask(__name__)

etk = ETK('./etk_spacy.log')


@app.route('/')
def home():
    return 'etk daemon running...'


@app.route('/test_spacy_rules', methods=['POST'])
def test_spacy_rules():

    try:
        obj = request.get_json(force=True)

        rule_extractor = SpacyRuleExtractor(
            etk.default_nlp,
            obj, "test_extractor")
        tokens = rule_extractor.tokenizer.tokenize_to_spacy_doc(obj['test_text'])
        obj['test_tokens'] = []
        for t in tokens:
            obj['test_tokens'].append({
                'index': t.i,
                'whitespace': t.whitespace_,
                'text': t.text
            })
        obj['results'] = []
        for extraction in rule_extractor.extract(obj['test_text']):
            obj['results'].append({
                'confidence': extraction.confidence,
                'start_token': extraction.provenance['start_token'],
                'end_token': extraction.provenance['end_token'],
                'start_char': extraction.provenance['start_char'],
                'end_char': extraction.provenance['end_char'],
                'identifier': extraction.rule_id,
                'text': extraction.value,
                'token_based_match_mapping': extraction.token_based_match_mapping
            })

        return json.dumps(obj), 201

    except Exception as e:
        print(e)
        return json.dumps({'message': 'exception: {}'.format(e.message)}), 400

if __name__ == '__main__':
    app.run(host=config['etk']['daemon']['host'], port=config['etk']['daemon']['port'],
            debug=config['debug'], threaded=True)
