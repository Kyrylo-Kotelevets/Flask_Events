import os

import requests
from flask_login import UserMixin
from sqlalchemy import exc
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash

from flask_app import db


class UserModel(UserMixin, db.Model):
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
        db.CheckConstraint("LENGTH(username) > 3", name='username_len_constraint'),
        db.CheckConstraint("email LIKE '%@%'", name='email_constraint'),
    )

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if password is None:
            self._password = None
        if self._password is None:
            self._password = generate_password_hash(password)
        else:
            raise Exception("Password already provided")

    def check_password(self, password) -> bool:
        if not self._password or not password:
            return False
        return check_password_hash(self._password, password)

    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_by_id(cls, uid: str):
        return UserModel.query.filter_by(id=uid).first()

    @classmethod
    def find_by_username(cls, username: str):
        return UserModel.query.filter_by(username=username).first()

    @classmethod
    def exists_local(cls, username: str) -> bool:
        return bool(UserModel.find_by_username(username))

    @classmethod
    def exists_remote(cls, username: str) -> bool:
        return bool(requests.get('{}/api/user/{}'.format(os.getenv('BOOKS_APP_URL'), username)))

    @classmethod
    def exists(cls, username):
        return UserModel.exists_local(username) or UserModel.exists_remote(username)

    @classmethod
    def get_or_create(cls, username: str):
        user = UserModel.find_by_username(username)
        if user is None:
            user = UserModel(username=username)
            user.save_to_db()
        return user

    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        # try:
        #     db.session.delete(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()

    def update_in_db(self, data):
        UserModel.query.filter_by(id=self.id).update(data)
        db.session.commit()
