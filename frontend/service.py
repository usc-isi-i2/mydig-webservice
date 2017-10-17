from flask import Flask, render_template, Response, make_response
from flask import request, abort, redirect, url_for, send_file
from flask_cors import CORS, cross_origin

import sys
import os
sys.path.append(os.path.join('../ws'))
from config import config


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('updateIndex.html')

@app.route('/constants')
def constant():
    return render_template('constants.html',
        backend_url=config['frontend']['backend_url'],
        landmark_url=config['frontend']['landmark_url'],
        digui_url=config['frontend']['digui_url'],
        kibana_url=config['frontend']['kibana_url'],
        spacy_ui_url=config['frontend']['spacy_ui_url'],
        spacy_backend_sever_name_base64=config['frontend']['spacy_backend_sever_name_base64'],
        spacy_backend_auth_base64=config['frontend']['spacy_backend_auth_base64']
    )


# @app.route('/login')
# def login():
#     return render_template('login.html')


@app.route('/details')
def pages():
    return render_template('projectDetailsUpdate.html')

if __name__ == '__main__':
    app.run(debug=config['debug'], host=config['frontend']['host'], port=config['frontend']['port'], threaded=True)