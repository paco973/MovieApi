from flask import Blueprint, jsonify, request
from sqlalchemy import exc
from functools import wraps
from datetime import datetime, timedelta

import jwt
import re

# personal imports
from models import User, UserSchema, Token
from app import app, db, flask_bcrypt

# token decorators
# 1st blocks workflow and return error if no token of wrong token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-token')
        print(jwt.decode(token, verify=False))
        if token is None:
            return jsonify({
                'message': 'Unauthorized',
            }), 401

        try: 
            decoded = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id = decoded['id']).first()
        except:
            return jsonify({
                'message': 'Unauthorized',
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated

# 2nd return no error on missing token 
def token_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-token')

        if token is None:
            current_user = None
            return f(current_user, *args, **kwargs)

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id = data['id']).first()
        except:
            return jsonify({
                'message': 'Unauthorized',
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated

#######################################
### STARTING TO DEFINE ROUTES HERE ####
#######################################
auth_api = Blueprint('auth_api', __name__)

# auth
@auth_api.route('/auth', methods=['POST'])
def auth():
    data = request.get_json() or request.form
    login = data.get('login')
    password = data.get('password')

    pattern = re.compile(r'[a-zA-Z0-9_-]*')
    
    if (
        login is None or type(login) is not str or
        password is None or type(password) is not str
        ):
        return jsonify({
            'message': 'Bad request',
            'code': 10001,
            'data': ''
        }), 400

    if pattern.fullmatch(login):
        user = User.query.filter_by(username = login).first()
    else:
        user = User.query.filter_by(email = login).first()

    if not user:
        return jsonify({
            'message': 'Not found',
        }), 404

    if flask_bcrypt.check_password_hash(user.password, password):
        expired_date = datetime.utcnow() + timedelta(minutes=60)
        token = jwt.encode({'id': user.id, 'exp': expired_date}, app.config['SECRET_KEY'])

        try:
            newToken = Token(
                code = token,
                expired_at = expired_date,
                user_id = user.id
            )
            db.session.add(newToken)
            db.session.commit()
        except exc.IntegrityError as err:
            db.session.rollback()
            return jsonify({
                'message': 'Bad request',
                'data': err.args
            }), 400
        except Exception as err:
            db.session.rollback()
            return jsonify({
                'message': 'Internal server error',
                'data': err.args
            }), 500
        
        return jsonify({
            'message': 'OK',
            'data' : token.decode('utf-8')
        }), 200
    else:
        return jsonify({
            'message': 'Bad request',
            'code': 10010, # password doesn't match
            'data': ''
        }), 400
