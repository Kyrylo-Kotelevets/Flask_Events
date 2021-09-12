from datetime import datetime

from sqlalchemy import exc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import case

from flask_app import db
from flask_app.models.base import BaseModel


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

    __table_args__ = (
        db.CheckConstraint("dt_start <= dt_end", name='start_before_end_constraint'),
    )

    def __str__(self):
        return self.title

    @hybrid_property
    def status(self):
        if self.dt_end < datetime.now():
            return "past"
        elif self.dt_start > datetime.now():
            return "current"
        return "future"

    @status.expression
    def status(self):
        return case([
            (self.dt_end < datetime.now(), "past"),
            (self.dt_start > datetime.now(), "current"),
        ], else_="future")

    @classmethod
    def find_by_title(cls, title: str):
        return cls.query.filter_by(title=title).first()

    @classmethod
    def find_by_status(cls, status: str):
        return cls.query.filter_by(status=status)

    @classmethod
    def filter_by_participant(cls, user_id: int):
        return cls.query.join(EventParticipantModel).filter(EventParticipantModel.participant_id == int(user_id))

    @classmethod
    def filter_by_guest(cls, user_id: int):
        return cls.query.join(EventGuestModel).filter(EventGuestModel.guest_id == int(user_id))

    @classmethod
    def filter_by_owner(cls, user_id: int):
        return cls.query.filter_by(owner_id=user_id)

    def update_in_db(self, data):
        EventModel.query.filter_by(id=self.id).update(data)
        db.session.commit()
