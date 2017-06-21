from flask import Flask, render_template, Response, make_response
from flask import request, abort, redirect, url_for, send_file
from flask_cors import CORS, cross_origin

from config import config


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('updateIndex.html', url=config['backend_url'])

@app.route('/login')
def login():
    return render_template('login.html', url=config['server_url'])
    


@app.route('/details')
def pages():
    return render_template('projectDetailsUpdate.html')

if __name__ == '__main__':
    app.run(debug=config['debug'], host=config['host'], port=config['port'])