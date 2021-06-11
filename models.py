##
## FILE WHERE WE DEFINE THE MODELS
## AND THE ASSOCIATED SCHEMAS
##

from app import db, ma
from datetime import datetime

################
#### MODELS ####
################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    pseudo = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    videos = db.relationship('Video', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    view = db.Column(db.Integer, default=0)
    enabled = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    formats = db.relationship('Video_Format', backref='video', lazy='dynamic')
    comments = db.relationship('Comment', backref='video', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

class Video_Format(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False)
    uri = db.Column(db.String(100), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255), nullable=False)
    expired_at = db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#################
#### SCHEMAS ####
#################

class TokenSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Token
        load_instance=True

class CommentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Comment
        load_instance=True

class VideoFormatSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Video_Format
        load_instance=True

class VideoSchema(ma.SQLAlchemyAutoSchema):
    formats = ma.Nested(VideoFormatSchema, many=True)
    comments = ma.Nested(CommentSchema, many=True)
    class Meta:
        model = Video
        load_instance=True

class UserSchema(ma.SQLAlchemyAutoSchema):
    videos = ma.Nested(VideoSchema, many=True)
    class Meta:
        model = User
        load_instance=True
