##
## FILE WHERE WE RUN THE APP,
## IMPORTING OTHER STUFFS IN HERE (app, blueprints, models to create db..)
##

from app import app
from models import *

from routes.users import users_api
from routes.auth import auth_api
from routes.videos import videos_api

app.register_blueprint(users_api)
app.register_blueprint(auth_api)
app.register_blueprint(videos_api)

if __name__ == '__main__': # only run if called from this file (name = main in this case only)
    db.create_all(app=app) # create tables if not exists
    app.run(port=int(1407)) # listen on port 1407