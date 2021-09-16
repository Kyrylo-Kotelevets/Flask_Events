"""
Module with User Endpoints
"""
from functools import wraps
from typing import Callable, Dict, Tuple

from flask import Response
from flask import request, jsonify
from flask_login import current_user, login_required
from flask_restx import Resource

from flask_app.auth.checkers import admin_required
from flask_app.models.user import UserModel
from flask_app.pagination.pagination import create_pagination
from flask_app.schemas.user import user_full_schema, user_short_list_schema


class UserResource(Resource):
    """
    Base resource class for User model
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes user
        """
        super().__init__(*args, **kwargs)
        self.user = None

    @login_required
    def dispatch_request(self, *args, **kwargs):
        """
        Checks if the user exists,
        and if so, then initializes it
        """
        username = kwargs.get("username")
        user = UserModel.find_by_username(username)

        if user is None:
            return jsonify({
                "status": 404,
                "message": "User <{}> not found".format(username)
            })

        self.user = user
        return super().dispatch_request(*args, **kwargs)

    @staticmethod
    def admin_or_owner_required(foo: Callable) -> Callable:
        """
        Decorator for checking admin or owner access rights
        """
        @login_required
        @wraps(foo)
        def wrapper(_, username):
            if not current_user.is_admin and current_user != UserModel.find_by_username(username):
                return Response("Admin or owner account required", status=403)
            return foo(_, username)

        return wrapper


class UserList(Resource):
    """
    Resource for retrieving exists and adding new users
    """
    @classmethod
    def get(cls) -> Tuple[Dict, int]:
        """Method for retrieving list of all Users

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        filters = dict(request.args)
        page = int(filters.pop("page", 1))
        limit = int(filters.pop("limit", 5))

        queryset = UserModel.get_list(filters)
        paginated_users = queryset.paginate(page, limit, error_out=False)
        response = create_pagination(items=paginated_users,
                                     schema=user_short_list_schema,
                                     page=page,
                                     limit=limit,
                                     query_params=filters,
                                     base_url=request.base_url)
        return response, 200

    @classmethod
    @admin_required
    def post(cls):
        """Method for creating new User

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
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
    """
    Resource for managing User details
    """
    @UserResource.admin_or_owner_required
    def get(self, username: str) -> Tuple[Dict, int]:
        """Method for retrieving details about the User

        Parameters
        ----------
        username : int
            User`s username

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        return user_full_schema.dump(self.user), 200

    @UserResource.admin_or_owner_required
    def patch(self, username: str) -> Tuple[Dict, int]:
        """Method for partial updating details about the User

        Parameters
        ----------
        username : int
            User`s username

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
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
        """Method for deleting the User

        Parameters
        ----------
        username : int
            User`s username

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        if current_user == self.user:
            return {"message": "Sorry, but you can`t delete yourself"}, 403

        self.user.delete_from_db()
        return {"message": "User <{}> deleted".format(username)}, 200
