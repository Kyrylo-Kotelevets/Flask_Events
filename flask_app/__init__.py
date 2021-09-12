import os

from flask import Flask, jsonify
from flask_babel import Babel
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError
# from sqlalchemy.exc import InvalidRequestError

from . import config

# create Flask application
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# create babel
babel = Babel(app)

# Environment Configuration
app.config.from_object(config.Config)

# initialize the database connection
db = SQLAlchemy(app)

# initialize the database migration
migrate = Migrate(app, db)

# initialize api
api = Api(app, title='Flask Events')


from flask_app.models.event import EventModel
from flask_app.models.user import UserModel
from flask_app import urls


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err: ValidationError):
    return jsonify(err.messages), 400


# @app.errorhandler(InvalidRequestError)
# def handle_marshmallow_validation(err: InvalidRequestError):
#     return {"ERROR": str(err)}, 400
