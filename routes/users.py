from flask import Blueprint, jsonify, request
from sqlalchemy import exc
from datetime import datetime, timedelta
import re

# personal imports
from models import User, UserSchema, Video, VideoSchema
from app import db, flask_bcrypt
from routes.auth import token_optional, token_required

users_api = Blueprint('users_api', __name__)

# get all users
@users_api.route('/users', methods=['GET'])
def getUsers():
    query_params = request.args
    pseudo = query_params.get('pseudo', None, type=str)
    page = query_params.get('page', 1, type=int)
    perPage = query_params.get('perPage', 20, type=int)

    if pseudo:
        paginate = User.query.filter_by(pseudo = pseudo).paginate(page = page, per_page = perPage, error_out = False) # if error_out = False, page and perPage defauls to 1 & 20 respectivly
    else:
        paginate = User.query.paginate(page = page, per_page = perPage, error_out = False) # if error_out = False, page and perPage defauls to 1 & 20 respectivly
    
    users = paginate.items
    total = paginate.pages # total of pages for parameter perPage

    if not users:
        users = [] # possible options here: return empty array, or return 404 not found ? not sure

    schema = UserSchema(only=('id', 'username', 'pseudo', 'created_at'), many=True)
    output = schema.dump(users)

    return jsonify({
        'message': 'OK',
        'data': output,
        'pager': {
            'current': page,
            'total': total
        }
    })

# get one user
@users_api.route('/user/<int:userId>', methods=['GET'])
@token_optional
def getUser(current_user, userId):
    user = User.query.filter_by(id=userId).first()

    if not user:
        return jsonify({
            'message': 'Not found',
        }), 404

    if current_user is not None and current_user.id == user.id:
        schema = UserSchema(only=('id', 'username', 'pseudo', 'email', 'created_at', 'password', 'videos'))
    else :
        schema = UserSchema(only=('id', 'username', 'pseudo', 'created_at'))

    output = schema.dump(user)
    # video_schema = VideoSchema(many=True)
    # videos = Video.query.filter_by(user_id=userId).all()
    # output['videos'] = video_schema.dump(videos).data

    return jsonify({
        'message': 'OK',
        'data': output
    }), 200

# create a new user
@users_api.route('/user', methods=['POST'])
def createUser():
    data = request.get_json() or request.form
    username = data.get('username')
    pseudo = data.get('pseudo')
    email = data.get('email')
    password = data.get('password')

    pattern = re.compile(r'[a-zA-Z0-9_-]*')

    if (
        data is None or
        username is None or type(username) is not str or pattern.fullmatch(username) is None or
        pseudo and (type(pseudo) is not str or pattern.fullmatch(pseudo) is None) or
        email is None or type(email) is not str or
        password is None or type(password) is not str
        ):
        return jsonify({
            'message': 'Bad request',
            'code': 10001, # invalid form
            'data': ''
        }), 400

    try:
        newUser = User(
            username = username,
            pseudo = pseudo or username,
            email = email,
            password = flask_bcrypt.generate_password_hash(password, rounds=10).decode('utf-8'),
            created_at = datetime.utcnow()
        )
        db.session.add(newUser)
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

    schema = UserSchema(only=('id', 'username', 'pseudo', 'email', 'created_at'))
    output = schema.dump(newUser)

    return jsonify({
        'message': 'OK',
        'data': output
    }), 201

# delete a user
@users_api.route('/user/<int:userId>', methods=['DELETE'])
@token_required
def deleteUser(current_user, userId):
    user = User.query.filter_by(id=userId).first()

    if not user:
        return jsonify({
            'message': 'Not found',
        }), 404

    if (current_user is None or current_user.id != user.id):
        return jsonify({
            'message': 'Forbidden',
        }), 403

    db.session.delete(user)
    db.session.commit()

    return jsonify({}), 204

# modify a user
@users_api.route('/user/<int:userId>', methods=['PUT'])
@token_required
def modifyUser(current_user, userId):
    user = User.query.filter_by(id=userId).first()

    if not user:
        return jsonify({
            'message': 'Not found',
        }), 404
    
    if (current_user is None or current_user.id != user.id):
        return jsonify({
            'message': 'Forbidden',
        }), 403
    
    data = request.get_json() or request.form
    username = data.get('username')
    pseudo = data.get('pseudo')
    email = data.get('email')
    password = data.get('password')

    pattern = re.compile(r'[a-zA-Z0-9_-]*')

    if (
        data is None or
        username is None or type(username) is not str or pattern.fullmatch(username) is None or
        pseudo and (type(pseudo) is not str or pattern.fullmatch(pseudo) is None) or
        email is None or
        password is None
        ):
        return jsonify({
            'message': 'Bad request',
            'code': 10001,
            'data': ''
        }), 400

    try:
        user.username = username #unique
        user.pseudo = pseudo or None
        user.email = email #unique
        user.password = flask_bcrypt.generate_password_hash(password, rounds=10).decode('utf-8')
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

    schema = UserSchema(only=('id', 'username', 'pseudo', 'email', 'created_at'))
    output = schema.dump(user)

    return jsonify({
        'message': 'OK',
        'data': output
    }), 201
