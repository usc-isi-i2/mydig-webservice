# http://flask.pocoo.org/snippets/8/
from functools import wraps
from flask import request, Response

from config import config
import rest

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username in config['users'] and config['users'][username] == password

def authenticate(restful=True):
    """Sends a 401 response that enables basic auth"""
    if not restful:
        return Response('Invalid credentials', 401)
    return rest.unauthorized('Invalid credentials')

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def requires_auth_html(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate(False)
        return f(*args, **kwargs)
    return decorated