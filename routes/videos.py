from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import exc
from datetime import datetime, timedelta
import magic
import re

# personal imports
from models import User, UserSchema, Video, Video_Format, VideoSchema, VideoFormatSchema, Comment, CommentSchema
from app import app, db
from routes.auth import token_optional, token_required

#######################################
### STARTING TO DEFINE ROUTES HERE ####
#######################################
videos_api = Blueprint('videos_api', __name__)

# get all videos
@videos_api.route('/videos', methods=['GET'])
def getVideos():
    query_params = request.args
    name = query_params.get('name', None, type=str)
    page = query_params.get('page', 1, type=int)
    perPage = query_params.get('perPage', 20, type=int)

    if name:
        paginate = Video.query.filter(Video.name.like(name + '%')).paginate(page = page, per_page = perPage, error_out = False) # if error_out = False, page and perPage defauls to 1 & 20 respectivly
    else:
        paginate = Video.query.paginate(page = page, per_page = perPage, error_out = False) # if error_out = False, page and perPage defauls to 1 & 20 respectivly
    
    videos = paginate.items
    total = paginate.pages # total of pages for parameter perPage

    if not videos:
        videos = [] # possible options here: return empty array, or return 404 not found ? not sure

    schema = VideoSchema(many=True)
    output = schema.dump(videos)

    return jsonify({
        'message': 'OK',
        'data': output,
        'pager': {
            'current': page,
            'total': total
        }
    })

# get user's videos
@videos_api.route('/user/<int:userId>/videos', methods=['GET'])
def getUserVideos(userId):
    query_params = request.args
    page = query_params.get('page', 1, type=int)
    perPage = query_params.get('perPage', 20, type=int)

    paginate = Video.query.filter_by(user_id=userId).paginate(page = page, per_page = perPage, error_out = False) # if error_out = False, page and perPage defauls to 1 & 20 respectivly
    
    videos = paginate.items
    total = paginate.pages # total of pages for parameter perPage

    if not videos:
        videos = [] # possible options here: return empty array, or return 404 not found ? not sure

    schema = VideoSchema(many=True)
    output = schema.dump(videos)

    return jsonify({
        'message': 'OK',
        'data': output,
        'pager': {
            'current': page,
            'total': total
        }
    })

# create new video
@videos_api.route('/user/<int:userId>/video', methods=['POST'])
@token_required
def createVideo(current_user, userId):
    # see: http://flask.pocoo.org/docs/1.0/patterns/fileuploads/
    # and: https://werkzeug.palletsprojects.com/en/0.14.x/datastructures/#werkzeug.datastructures.FileStorage
    # and: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Complete_list_of_MIME_types
    ### user verif
    user = User.query.filter_by(id=userId).first()

    if not user:
        return jsonify({
            'message': 'User not found',
        }), 404
    
    if (current_user is None or current_user.id != user.id):
        return jsonify({
            'message': 'Forbidden',
        }), 403

    ### file form verif
    if ('source' not in request.files or
        request.files['source'].filename == ''):
        return jsonify({
            'message': 'Bad request',
            'code': 10020, # no file 
            'data': ''
        }), 400

    file = request.files['source']
    data = request.get_json() or request.form
    name = data.get('name')
    ### file mimetype check and save to storage
    pattern = re.compile(r'^video\/')
    file_mimetype = magic.from_buffer(file.read(1024), mime=True)
    file.stream.seek(0)

    if pattern.match(file_mimetype):
        file_path = secure_filename(user.username + '_' + str(datetime.utcnow()) + '_' + file.filename)
        file.save(app.config['UPLOAD_FOLDER'] + file_path)
    else:
        return jsonify({
            'message': 'Bad request',
            'code': 10021, # wrong file type
            'data': ''
        }), 400

    ## save to db
    try:
        newVideo = Video(
            name = name or secure_filename(file.filename),
            source = (app.config['UPLOAD_FOLDER'] + file_path),
            user_id = user.id,
            created_at = datetime.utcnow()
        )
        db.session.add(newVideo)
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

    schema = VideoSchema()
    output = schema.dump(newVideo)

    return jsonify({
        'message': 'OK',
        'data': output
    }), 201

# encoding video
@videos_api.route('/video/<int:videoId>', methods=['PATCH'])
@token_required
def encodeVideo(current_user, videoId):
    if not current_user:
        return jsonify({
            'message': 'Forbidden',
        }), 403
    
    user = User.query.filter_by(id=current_user.id).first()
    if not user:
        return jsonify({
            'message': 'Forbidden',
        }), 403

    ### file form verif
    if ('file' not in request.files or
        request.files['file'].filename == ''):
        return jsonify({
            'message': 'Bad request',
            'code': 10020, # no file 
            'data': ''
        }), 400

    file = request.files['file']
    data = request.get_json() or request.form
    format = data.get('format')

    format_pattern = re.compile(r'[0-9]*')
    if (format is None or type(format) is not (str or number) or format_pattern.fullmatch(format) is None):
        return jsonify({
            'message': 'Bad request',
            'code': 10021, # no or wrong format specified
            'data': ''
        }), 400

    pattern = re.compile(r'^video\/')
    file_mimetype = magic.from_buffer(file.read(1024), mime=True)
    file.stream.seek(0)

    if pattern.match(file_mimetype):
        file_path = secure_filename(user.username + '_' + str(datetime.utcnow()) + '_' + format + '_' + file.filename)
        file.save(app.config['UPLOAD_FOLDER'] + file_path)
    else:
        return jsonify({
            'message': 'Bad request',
            'code': 10021, # wrong file type
            'data': ''
        }), 400

    ## save to db
    exists_format = Video_Format.query.filter_by(video_id=videoId, code=format).first()
    if exists_format is not None:
        exists_format.uri = app.config['UPLOAD_FOLDER'] + file_path
        db.session.commit()
    else:
        try:
            newFormat = Video_Format(
                code = format,
                uri = (app.config['UPLOAD_FOLDER'] + file_path),
                video_id = videoId,
            )
            db.session.add(newFormat)
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

    schema = VideoFormatSchema()
    if exists_format:
        output = schema.dump(exists_format)
    else:
        output = schema.dump(newFormat)


    return jsonify({
        'message': 'OK',
        'data': output
    }), 200

# update video
@videos_api.route('/video/<int:videoId>', methods=['PUT'])
@token_required
def updateVideo(current_user, videoId):
    if not current_user:
        return jsonify({
            'message': 'Forbidden',
        }), 403
    
    user = User.query.filter_by(id=current_user.id).first()
    if not user:
        return jsonify({
            'message': 'Forbidden',
        }), 403

    data = request.get_json() or request.form
    name = data.get('name')

    if (name is None or type(name) is not (str)):
        return jsonify({
            'message': 'Bad request',
            'code': 10001, # invalid form
            'data': ''
        }), 400
    
    video = Video.query.filter_by(id=videoId).first()
    if not video:
        return jsonify({
            'message': 'Video not found',
        }), 404

    video.name = name
    db.session.commit()

    schema = VideoSchema()
    output = schema.dump(video)

    return jsonify({
        'message': 'OK',
        'data': output
    }), 200

# delete video
@videos_api.route('/video/<int:videoId>', methods=['DELETE'])
@token_required
def deleteVideo(current_user, videoId):
    if not current_user:
        return jsonify({
            'message': 'Forbidden',
        }), 403
    
    user = User.query.filter_by(id=current_user.id).first()
    if not user:
        return jsonify({
            'message': 'Forbidden',
        }), 403

    video = Video.query.filter_by(id=videoId).first()
    if not video:
        return jsonify({
            'message': 'Video not found',
        }), 404

    db.session.delete(video)
    db.session.commit()

    return jsonify({}), 204
    
# comment video
@videos_api.route('/video/<int:videoId>/comment', methods=['POST'])
@token_required
def commentVideo(current_user, videoId):
    if not current_user:
        return jsonify({
            'message': 'Forbidden',
        }), 403
    
    user = User.query.filter_by(id=current_user.id).first()
    if not user:
        return jsonify({
            'message': 'Forbidden',
        }), 403

    data = request.get_json() or request.form
    body = data.get('body')

    if (body is None or type(body) is not (str)):
        return jsonify({
            'message': 'Bad request',
            'code': 10001, # invalid form
            'data': ''
        }), 400
    
    video = Video.query.filter_by(id=videoId).first()
    if not video:
        return jsonify({
            'message': 'Video not found',
        }), 404

    try:
        newComment = Comment(
            body = body,
            user_id = current_user.id,
            video_id = video.id
        )
        db.session.add(newComment)
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

    schema = CommentSchema()
    output = schema.dump(newComment)

    return jsonify({
        'message': 'OK',
        'data': output
    }), 200

# get video's comments
@videos_api.route('/video/<int:videoId>/comments', methods=['GET'])
def getVideoComments(videoId):
    query_params = request.args
    page = query_params.get('page', 1, type=int)
    perPage = query_params.get('perPage', 20, type=int)

    paginate = Comment.query.filter_by(video_id=videoId).paginate(page = page, per_page = perPage, error_out = False) # if error_out = False, page and perPage defauls to 1 & 20 respectivly
    
    comments = paginate.items
    total = paginate.pages # total of pages for parameter perPage

    if not comments:
        comments = [] # possible options here: return empty array, or return 404 not found ? not sure

    schema = CommentSchema(many=True)
    output = schema.dump(comments)

    return jsonify({
        'message': 'OK',
        'data': output,
        'pager': {
            'current': page,
            'total': total
        }
    })

@videos_api.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
