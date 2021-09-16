"""
The module is used to describe database Event model and its m2m relationships
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict

import requests
from flask_sqlalchemy import BaseQuery
from sqlalchemy import exc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import case

from flask_app import db
from flask_app.models.artifact import ArtifactModel
from flask_app.models.base import EntityModel, RelationshipModel
from flask_app.models.user import UserModel


class EventGuestModel(db.Model, RelationshipModel):
    """
    Many-to-Many relationship model between Event and User
    """
    __tablename__ = 'event_guest'

    event_id = db.Column(db.Integer,
                         db.ForeignKey("event.id", ondelete="CASCADE"),
                         primary_key=True)
    guest_id = db.Column(db.Integer,
                         db.ForeignKey("user.id", ondelete="CASCADE"),
                         primary_key=True)


class EventParticipantModel(db.Model, RelationshipModel):
    """
    Many-to-Many relationship model between Event and User
    """
    __tablename__ = 'event_participant'

    event_id = db.Column(db.Integer,
                         db.ForeignKey("event.id", ondelete="CASCADE"),
                         primary_key=True)
    participant_id = db.Column(db.Integer,
                               db.ForeignKey("user.id", ondelete="CASCADE"),
                               primary_key=True)


class EventArtifactModel(db.Model, RelationshipModel):
    """
    Many-to-Many relationship model between Event and Artifact
    """
    __tablename__ = 'event_artifact'

    event_id = db.Column(db.Integer,
                         db.ForeignKey("event.id", ondelete="CASCADE"),
                         primary_key=True)
    artifact_id = db.Column(db.Integer,
                            db.ForeignKey("artifact.id", ondelete="CASCADE"),
                            primary_key=True)


class EventModel(db.Model, EntityModel):
    """
    Entity Event Model
    """
    __tablename__ = 'event'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False, unique=True)
    summary = db.Column(db.String(1028), nullable=True)

    dt_start = db.Column(db.DateTime, default=datetime.utcnow)
    dt_end = db.Column(db.DateTime, default=datetime.utcnow)

    owner_id = db.Column(db.Integer(),
                         db.ForeignKey('user.id', ondelete='CASCADE'))
    guests = db.relationship("UserModel",
                             secondary="event_guest",
                             cascade='all, delete')
    participants = db.relationship("UserModel",
                                   secondary="event_participant",
                                   cascade='all, delete')
    artifacts = db.relationship("ArtifactModel",
                                secondary="event_artifact",
                                cascade='all, delete')

    __table_args__ = (
        db.CheckConstraint("dt_start <= dt_end", name='start_before_end_constraint'),
    )

    def __repr__(self) -> str:
        """
        Converts Event to the string
        """
        return "<Event (id = {}, title = {}>".format(self.id, self.title)

    def add_participant(self, user: UserModel) -> None:
        """Add given user to the participants list

        Parameters
        ----------
        user : UserModel
            User to adding
        """
        if user in self.guests:
            raise exc.IntegrityError("User can not be guest and participant",
                                     params=None, orig=None)
        if user in self.participants:
            raise exc.IntegrityError("User already in guests list",
                                     params=None, orig=None)

        self.participants.append(user)

        # If user is an author
        if UserModel.exists_remote(user.username):
            response = requests.get("{}/api/user/{}".
                                    format(os.getenv('BOOKS_APP_URL'), user.username))
            json_data = json.loads(response.text)

            if json_data["books"]:
                book = json_data["books"][0]
                url = "{}/books/{}/".format(os.getenv('BOOKS_APP_URL'), book['id'])
                artifact = ArtifactModel.find_by_url(url)

                # If it is new artifact
                if artifact is None:
                    artifact = ArtifactModel(url=url)
                    artifact.save_to_db()

                self.artifacts.append(artifact)
        self.save_to_db()

    def add_guest(self, user: UserModel) -> None:
        """Add given user to the guests list

        Parameters
        ----------
        user : UserModel
            User to adding
        """
        if user in self.guests:
            raise exc.IntegrityError("User can not be guest and participant",
                                     params=None, orig=None)
        if user in self.participants:
            raise exc.IntegrityError("User already in participant list",
                                     params=None, orig=None)
        self.guests.append(user)
        self.save_to_db()

    @hybrid_property
    def status(self) -> str:
        """
        Status property
        """
        if self.dt_end < datetime.now():
            return "past"
        if self.dt_start < datetime.now():
            return "current"
        return "future"

    @status.expression
    def status(self) -> str:
        """
        Status property for SQL expressions
        """
        return case([
            (self.dt_end < datetime.now(), "past"),
            (self.dt_start < datetime.now(), "current"),
        ], else_="future")

    @classmethod
    def find_by_title(cls, title: str, queryset: Optional[BaseQuery] = None) \
            -> Optional['EventModel']:
        """Method for searching by event title

        Parameters
        ----------
        title : str
            Event title pattern for search
        queryset : Optional[BaseQuery]
            Events for search in, None by default for searching in all

        Returns
        -------
        Optional['EventModel']
            Search result, None if not exists
        """
        queryset = queryset or cls.query
        return queryset.filter_by(title=title).first()

    @classmethod
    def filter_by_subtitle(cls, subtitle: str, queryset: Optional[BaseQuery] = None) \
            -> Optional['EventModel']:
        """Method for searching by event title

        Parameters
        ----------
        subtitle : str
            Event subtitle pattern for search
        queryset : Optional[BaseQuery]
            Events for search in, None by default for searching in all

        Returns
        -------
        Optional['EventModel']
            Search result, None if not exists
        """
        look_for = '%{0}%'.format(subtitle)
        queryset = queryset or cls.query
        return queryset.filter(EventModel.title.like(look_for))

    @classmethod
    def filter_by_status(cls, status: str, queryset: Optional[BaseQuery] = None) \
            -> Optional['EventModel']:
        """Method for searching by event status

        Parameters
        ----------
        status : str
            Event status pattern for search
        queryset : Optional[BaseQuery]
            Events for search in, None by default for searching in all

        Returns
        -------
        Optional['EventModel']
            Search result, None if no events with given status exists
        """
        queryset = queryset or cls.query
        return queryset.filter_by(status=status)

    @classmethod
    def filter_by_participant(cls, user_id: int, queryset: Optional[BaseQuery] = None) \
            -> Optional['EventModel']:
        """Method for searching by event participants

        Parameters
        ----------
        user_id : int
            User id for events filtering
        queryset : Optional[BaseQuery]
            Events for search in, None by default for searching in all

        Returns
        -------
        Optional['EventModel']
            Search result, None if no events with given participant exists
        """
        queryset = queryset or cls.query
        return queryset.join(EventParticipantModel).\
            filter(EventParticipantModel.participant_id == int(user_id))

    @classmethod
    def filter_by_guest(cls, user_id: int, queryset: Optional[BaseQuery] = None) \
            -> Optional['EventModel']:
        """Method for searching by event guests

        Parameters
        ----------
        user_id : int
            User id for events filtering
        queryset : Optional[BaseQuery]
            Events for search in, None by default for searching in all

        Returns
        -------
        Optional['EventModel']
            Search result, None if no events with given guest exists
        """
        queryset = queryset or cls.query
        return queryset.join(EventGuestModel).\
            filter(EventGuestModel.guest_id == int(user_id))

    @classmethod
    def filter_by_owner(cls, user_id: int, queryset: Optional[BaseQuery] = None) \
            -> Optional['EventModel']:
        """Method for searching by event owner

        Parameters
        ----------
        user_id : int
            User id for events filtering
        queryset : Optional[BaseQuery]
            Events for search in, None by default for searching in all

        Returns
        -------
        Optional['EventModel']
            Search result, None if no events with given owner id exists
        """
        queryset = queryset or cls.query
        return queryset.filter_by(owner_id=user_id)

    @classmethod
    def get_list(cls, query_params: Optional[Dict] = None) -> Optional['EventModel']:
        """Method for getting events by specified filters

        Parameters
        ----------
        query_params : Optional[Dict]
            Filters for applying

        Returns
        -------
        Optional['EventModel']
            Search result, None if no events with all filter values exists
        """
        if query_params is None:
            query_params = dict()

        order_by = getattr(cls, query_params.pop("order_by", "dt_start"))
        order = query_params.pop("order", "asc")
        order_by = order_by.desc() if order == "desc" else order_by.asc()

        query = cls.query
        query = EventModel.filter_by_status(query_params.get("status", "future"), query)
        query = EventModel.filter_by_subtitle(query_params.get("title", ""), query)

        if query_params.get("owner_id"):
            query = EventModel.filter_by_owner(query_params.get("owner_id"), query)
        if query_params.get("guest_id"):
            query = EventModel.filter_by_guest(query_params.get("guest_id"), query)
        if query_params.get("participant_id"):
            query = EventModel.filter_by_participant(query_params.get("participant_id"), query)

        return query.order_by(order_by)

    def update_in_db(self, data):
        """
        Update data in the database
        """
        EventModel.query.filter_by(id=self.id).update(data)
        db.session.commit()
