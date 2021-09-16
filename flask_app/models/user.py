import os
from typing import Optional, Dict

import requests
from flask_login import UserMixin
from flask_sqlalchemy import BaseQuery
# from sqlalchemy import exc
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash

from flask_app import db
from flask_app.models.base import EntityModel


class UserModel(UserMixin, db.Model, EntityModel):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    _password = db.Column(db.String(128), nullable=True)

    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True)

    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    events = db.relationship("EventModel", backref="owner", cascade='all, delete')

    __table_args__ = (
        db.CheckConstraint("LENGTH(username) >= 2", name='username_len_constraint'),
        db.CheckConstraint("email LIKE '%@%'", name='email_constraint'),
    )

    @hybrid_property
    def password(self) -> str:
        """
        Property for password
        """
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        """
        Setter for password save as a hash
        """
        if password is None:
            self._password = None
        if self._password is None:
            self._password = generate_password_hash(password)
        else:
            raise Exception("Password already provided")

    def check_password(self, password: str) -> bool:
        """Method for checking password. Passwords are compared as a hash

        Parameters
        ----------
        password : str
            Password as a plain text

        Returns
        -------
        bool
            True if passwords hash are same, False otherwise
        """
        if not self._password or not password:
            return False
        return check_password_hash(self._password, password)

    @classmethod
    def find_by_username(cls, username: str) -> Optional['UserModel']:
        """Method for searching by username

        Parameters
        ----------
        username : str
            Username pattern for search

        Returns
        -------
        Optional['EventModel']
            Search result, None if user with given username does not exist
        """
        return UserModel.query.filter_by(username=username).first()

    @classmethod
    def exists_local(cls, username: str) -> bool:
        """Method for check if user with given username
        exists in local database

        Parameters
        ----------
        username : str
            Username for search

        Returns
        -------
        bool
            True if exists, False otherwise
        """
        return bool(UserModel.find_by_username(username))

    @classmethod
    def exists_remote(cls, username: str) -> bool:
        """Method for check if user with given username
        exists in remove service

        Parameters
        ----------
        username : str
            Username for search

        Returns
        -------
        bool
            True if exists, False otherwise
        """
        return bool(requests.get('{}/api/user/{}'.format(os.getenv('BOOKS_APP_URL'), username)))

    @classmethod
    def exists(cls, username: str) -> bool:
        """Method for check if user with given username
        exists in remove or local service

        Parameters
        ----------
        username : str
            Username for search

        Returns
        -------
        bool
            True if exists somewhere, False otherwise
        """
        return UserModel.exists_local(username) or UserModel.exists_remote(username)

    @classmethod
    def get_or_create(cls, username: str) -> 'UserModel':
        """Method to get the user even if it doesn't exist

        Parameters
        ----------
        username : str
            Username for search

        Returns
        -------
        UserModel
            Founded of created user
        """
        user = UserModel.find_by_username(username)
        if user is None:
            user = UserModel(username=username)
            user.save_to_db()
        return user

    @classmethod
    def filter_by_username(cls, subname: str, queryset: Optional[BaseQuery] = None) \
            -> Optional['UserModel']:
        """Method for searching by event title

        Parameters
        ----------
        subname : str
            User subname pattern for search
        queryset : Optional[BaseQuery]
            Users for search in, None by default for searching in all

        Returns
        -------
        Optional['UserModel']
            Search result, None if not exists
        """
        look_for = '%{0}%'.format(subname)
        queryset = queryset or cls.query
        return queryset.filter(UserModel.username.like(look_for))

    @classmethod
    def get_list(cls, query_params: Optional[Dict] = None) \
            -> Optional['UserModel']:
        """Method for getting users by specified filters

        Parameters
        ----------
        query_params : Optional[Dict]
            Filters for applying

        Returns
        -------
        Optional['UserModel']
            Search result, None if no users with all filter values exists
        """
        if query_params is None:
            query_params = dict()

        order_by = getattr(cls, query_params.pop("order_by", "username"))
        order = query_params.pop("order", "asc")
        order_by = order_by.desc() if order == "desc" else order_by.asc()

        query = cls.query
        query = UserModel.filter_by_username(query_params.get("username", ""), query)

        return query.order_by(order_by)

    def update_in_db(self, data):
        """
        Update data in the database
        """
        UserModel.query.filter_by(id=self.id).update(data)
        db.session.commit()
