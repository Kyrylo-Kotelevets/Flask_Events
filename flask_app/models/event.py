import json
import os
from datetime import datetime
import requests

from sqlalchemy import exc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import case

from flask_app import db
from flask_app.models.base import BaseModel
from flask_app.models.user import UserModel
from flask_app.models.artifact import ArtifactModel
from sqlalchemy.orm import backref


class EventGuestModel(db.Model):
    __tablename__ = 'event_guest'

    event_id = db.Column(db.Integer,
                         db.ForeignKey("event.id", ondelete="CASCADE"),
                         primary_key=True)
    guest_id = db.Column(db.Integer,
                         db.ForeignKey("user.id", ondelete="CASCADE"),
                         primary_key=True)

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        # try:
        #     db.session.add(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        # try:
        #     db.session.delete(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()


class EventParticipantModel(db.Model):
    __tablename__ = 'event_participant'

    event_id = db.Column(db.Integer,
                         db.ForeignKey("event.id", ondelete="CASCADE"),
                         primary_key=True)
    participant_id = db.Column(db.Integer,
                               db.ForeignKey("user.id", ondelete="CASCADE"),
                               primary_key=True)

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        # try:
        #     db.session.add(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        # try:
        #     db.session.delete(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()


class EventArtifactModel(db.Model):
    __tablename__ = 'event_artifact'

    event_id = db.Column(db.Integer,
                         db.ForeignKey("event.id", ondelete="CASCADE"),
                         primary_key=True)
    artifact_id = db.Column(db.Integer,
                            db.ForeignKey("artifact.id", ondelete="CASCADE"),
                            primary_key=True)

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        # try:
        #     db.session.add(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        # try:
        #     db.session.delete(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()


class EventModel(db.Model, BaseModel):
    __tablename__ = 'event'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False, unique=True)
    summary = db.Column(db.String(1028), nullable=True)

    dt_start = db.Column(db.DateTime, default=datetime.utcnow)
    dt_end = db.Column(db.DateTime, default=datetime.utcnow)

    owner_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    guests = db.relationship("UserModel", secondary="event_guest", cascade='all, delete')
    participants = db.relationship("UserModel", secondary="event_participant", cascade='all, delete')
    artifacts = db.relationship("ArtifactModel", secondary="event_artifact", cascade='all, delete')

    __table_args__ = (
        db.CheckConstraint("dt_start <= dt_end", name='start_before_end_constraint'),
    )

    def __str__(self):
        return self.title

    def add_participant(self, user: UserModel) -> None:
        if user in self.guests:
            raise exc.IntegrityError("User can not be guest and participant", params=None, orig=None)
        if user in self.participants:
            raise exc.IntegrityError("User already in guests list", params=None, orig=None)

        self.participants.append(user)
        if UserModel.exists_remote(user.username):
            responce = requests.get("{}/api/user/{}".format(os.getenv('BOOKS_APP_URL'), user.username))
            json_data = json.loads(responce.text)

            if json_data["books"]:
                book = json_data["books"][0]
                url = "{}/books/{}/".format(os.getenv('BOOKS_APP_URL'), book['id'])
                artifact = ArtifactModel.find_by_url(url)

                if artifact is None:
                    artifact = ArtifactModel(url=url)
                    artifact.save_to_db()

                self.artifacts.append(artifact)
        self.save_to_db()

    def add_guest(self, user: UserModel) -> None:
        if user in self.guests:
            raise exc.IntegrityError("User can not be guest and participant", params=None, orig=None)
        if user in self.participants:
            raise exc.IntegrityError("User already in participant list", params=None, orig=None)
        self.guests.append(user)
        self.save_to_db()

    @hybrid_property
    def status(self):
        if self.dt_end < datetime.now():
            return "past"
        elif self.dt_start < datetime.now():
            return "current"
        return "future"

    @status.expression
    def status(self):
        return case([
            (self.dt_end < datetime.now(), "past"),
            (self.dt_start < datetime.now(), "current"),
        ], else_="future")

    @classmethod
    def find_by_title(cls, title: str):
        return cls.query.filter_by(title=title).first()

    @classmethod
    def find_by_status(cls, status: str, queryset=None):
        queryset = queryset or cls.query
        return queryset.filter_by(status=status)

    @classmethod
    def filter_by_participant(cls, user_id: int, queryset=None):
        queryset = queryset or cls.query
        return queryset.join(EventParticipantModel).filter(EventParticipantModel.participant_id == int(user_id))

    @classmethod
    def filter_by_guest(cls, user_id: int, queryset=None):
        queryset = queryset or cls.query
        return queryset.join(EventGuestModel).filter(EventGuestModel.guest_id == int(user_id))

    @classmethod
    def filter_by_owner(cls, user_id: int):
        return cls.query.filter_by(owner_id=user_id)

    @classmethod
    def get_list(cls, query_params = None):
        if query_params is None:
            query_params = dict()

        order_by = getattr(cls, query_params.pop("order_by", "dt_start"))
        order = query_params.pop("order", "asc")
        order_by = order_by.desc() if order == "desc" else order_by.asc()

        query = cls.query
        query = EventModel.find_by_status(query_params.get("status", "future"), query)

        return query.order_by(order_by)

    def update_in_db(self, data):
        EventModel.query.filter_by(id=self.id).update(data)
        db.session.commit()
