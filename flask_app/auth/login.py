import json
import os

import jwt
import requests
from flask import request, jsonify, Response
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_restx import Resource

from flask_app import app, db
from flask_app.models.user import UserModel
from flask_app.schemas.user import user_full_schema

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized_callback():
    return Response("Authorization required", status=403)


@login_manager.user_loader
def load_user(user_id):
    return UserModel.query.get(int(user_id))


def decode_token(token: str):
    return jwt.decode(token, os.getenv('SECRET_KEY'), algorithms='HS256')


def encode_token(username: str, password: str):
    return jwt.encode({"username": username, "password": password}, os.getenv('SECRET_KEY'), algorithm='HS256')


def jwt_login(username: str, password: str) -> bool:
    jwt_token = encode_token(username, password)
    response = requests.post('{}/api/jwt-auth/'.format(os.getenv('BOOKS_APP_URL')),
                             headers={'Content-Type': 'application/json'},
                             data=json.dumps({"token": jwt_token}))

    if response.status_code == 200:
        jwt_data = decode_token(json.loads(response.text)["jwt"])

        user = UserModel.get_or_create(username)
        user.password = password
        user.first_name = jwt_data["first_name"]
        user.first_name = jwt_data["first_name"]
        user.email = jwt_data["email"]
        user.is_admin = jwt_data["is_admin"]
        db.session.commit()

        return True
    else:
        return False


class Login(Resource):
    @classmethod
    def post(cls):
        if current_user.is_authenticated:
            return jsonify({
                "status": 403,
                "massage": "Already logged in as <{}>".format(current_user.username)
            })

        user_data = request.get_json(force=True)
        username = user_data.get('username')
        password = user_data.get('password')

        if username is None or password is None:
            return jsonify({
                "status": 400,
                "massage": "Username or password wasn`t provided"
            })

        if not UserModel.exists(username):
            return jsonify({
                "status": 404,
                "massage": "No user founded with username <{}>".format(username)
            })

        user = UserModel.get_or_create(username)

        if not jwt_login(username, password) and not user.check_password(password):
            return jsonify({
                "status": 401,
                "massage": "Invalid password"
            })

        login_user(user)
        db.session.commit()

        return jsonify({
            "status": 200,
            "message": "Successfully logged in as <{}>".format(username),
            "profile": user_full_schema.dump(user)
        })


class SignUp(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json(force=True)
        username = user_json.get('username')
        password = user_json.get('password')

        if username is None or password is None:
            return jsonify({
                "status": 400,
                "massage": "Username or password wasn`t provided"
            })
        elif UserModel.exists_local(username):
            return {"status": 401, "message": "User already exists"}
        elif UserModel.exists_remote(username):
            return {"status": 401, "message": "User already exists in remote service"}
        else:
            user = UserModel(username=username,
                             first_name=user_json.get("first_name"),
                             last_name=user_json.get("last_name"),
                             email=user_json.get("email"))
            user.password = password
            user.save_to_db()
            return user_full_schema.dump(user), 200


class Logout(Resource):
    @classmethod
    @login_required
    def post(cls):
        logout_user()
        return jsonify({
            "result": 200,
            "message": "Logout success"
        })
