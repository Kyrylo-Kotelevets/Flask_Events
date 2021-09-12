from functools import wraps

from flask import Response
from flask import request, jsonify
from flask_login import current_user, login_required
from flask_restx import Resource

from flask_app.auth.checkers import admin_required
from flask_app.models.user import UserModel
from flask_app.schemas.user import user_full_schema, user_short_list_schema, user_full_list_schema


class UserResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    @login_required
    def dispatch_request(self, *args, **kwargs):
        username = kwargs.get("username")
        user = UserModel.find_by_username(username)

        if user is None:
            return jsonify({
                "status": 404,
                "message": "User <{}> not found".format(username)
            })
        else:
            self.user = user
            return super().dispatch_request(*args, **kwargs)

    @staticmethod
    def admin_or_owner_required(foo):
        @wraps(foo)
        def wrapper(_, username):
            if not current_user.is_admin and current_user != UserModel.find_by_username(username):
                return Response("Admin or owner account required", status=403)
            return foo(_, username)

        return wrapper


class UserList(Resource):
    @classmethod
    def get(cls):
        if current_user.is_authenticated and current_user.is_admin:
            return user_full_list_schema.dump(UserModel.find_all()), 200
        else:
            return user_short_list_schema.dump(UserModel.find_all()), 200

    @classmethod
    @admin_required
    def post(cls):
        user_json = request.get_json(force=True)
        username = user_json.get('username')
        password = user_json.get('password')

        if (username is None) or (password is None):
            return jsonify({
                "status": 400,
                "massage": "Username or password wasn`t provided"
            })
        elif UserModel.exists(username):
            return {"status": 401, "reason": "User already exist"}
        else:
            user = UserModel(username=username,
                             first_name=user_json.get("first_name"),
                             last_name=user_json.get("last_name"),
                             email=user_json.get("email"),
                             is_admin=bool(user_json.get('is_admin')))
            user.password = password
            user.save_to_db()
            return user_full_schema.dump(user), 200


class RetrieveUpdateDestroyUser(UserResource):
    @UserResource.admin_or_owner_required
    def get(self, username: str):
        return user_full_schema.dump(self.user), 200

    @UserResource.admin_or_owner_required
    def patch(self, username: str):
        user_json = request.get_json(force=True)

        if ("is_admin" in user_json.keys()) and (current_user == self.user):
            return {"message": "You can`t change admin status for yourself"}, 403

        if ("username" in user_json.keys()) and (current_user != self.user):
            return {"message": "You can`t change username for other user"}, 403

        if ("password" in user_json.keys()) and (current_user != self.user):
            return {"message": "You can`t change password for other user"}, 403

        for key_name in user_json.keys():
            if key_name not in self.user.__table__.columns:
                return {"message": "<{}> no such attribute in user data".format(key_name)}, 404

        self.user.update_in_db(data=user_json)
        return user_full_schema.dump(self.user), 200

    @UserResource.admin_or_owner_required
    def delete(self, username: str):
        if current_user == self.user:
            return {"message": "Sorry, but you can`t delete yourself"}, 403

        self.user.delete_from_db()
        return {"message": "User <{}> deleted".format(username)}, 200


# class UserListId(Resource):
#     @classmethod
#     def get(cls, user_id):
#         user_data = UserModel.query.get(user_id)
#
#         if user_data:
#             return user_schema.dump(user_data), 200
#
#         return {"status": 404, 'message': USER_NOT_FOUND}
#
#     @classmethod
#     @login_required
#     def delete(cls, user_id) -> dict:
#         if current_user.is_authenticated and current_user.is_admin:
#             user_data = UserModel.query.get(user_id)
#
#             if user_data:
#                 user_data.delete_from_db()
#                 return {"status": 200, 'message': "User Deleted successfully"}
#
#             return {"status": 404, 'message': USER_NOT_FOUND}
#
#         return {"status": 401, "reason": "User is not admin"}
#
#     @classmethod
#     @login_required
#     def put(cls, user_id):
#         if current_user.is_authenticated and current_user.is_admin:
#             user_data = UserModel.query.get(user_id)
#             user_json = request.get_json()
#
#             if not user_data:
#                 return {"status": 404, 'message': USER_NOT_FOUND}
#
#             if user_already_exist(user_json):
#                 return {"status": 401, "reason": "User already exist"}
#
#             try:
#                 user_data.username = UserModel.validate_username(user_json['username'])
#                 user_data.password = user_json['password']
#                 user_data.first_name = UserModel.validate_username(user_json['name'])
#                 user_data.last_name = UserModel.validate_username(user_json['name'])
#                 user_data.email = UserModel.validate_email(user_json['email'])
#             except AssertionError:
#                 return {"status": 401, "message": "Invalid data"}
#
#             user_data.save_to_db()
#             return user_schema.dump(user_data), 200
#
#         return {"status": 401, "reason": "User is not admin"}
