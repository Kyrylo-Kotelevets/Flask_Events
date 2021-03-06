"""
Module with Event Schema
"""

from typing import Dict

from marshmallow import fields, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from flask_app.models.event import EventModel
from flask_app.schemas.user import user_short_schema, user_short_list_schema
from flask_app.schemas.artifact import artifact_list_schema


class EventSchema(SQLAlchemyAutoSchema):
    """
    Event Schema
    """
    title = fields.String(
        required=True,
        error_messages={
            'required': 'Sorry, Title field is required',
            'null': 'Sorry, Title field cannot be null',
            'invalid': 'Sorry, Title field must be a string'})

    dt_start = fields.DateTime(
        required=True,
        error_messages={
            'required': 'Sorry, Start datetime field is required',
            'null': 'Sorry, Start datetime field cannot be null',
            'invalid': 'Sorry, Start datetime field must be in format YYYY-MM-DD HH:MM'})

    dt_end = fields.DateTime(
        required=True,
        error_messages={
            'required': 'Sorry, End datetime field is required',
            'null': 'Sorry, End datetime field cannot be null',
            'invalid': 'Sorry, End datetime field must be in format YYYY-MM-DD HH:MM'})

    participants = fields.Nested(user_short_list_schema, many=True)
    guests = fields.Nested(user_short_list_schema, many=True)
    artifacts = fields.Nested(artifact_list_schema, many=True)
    owner = fields.Nested(user_short_schema, many=False)

    status = fields.String()

    class Meta:
        """
        Connecting Schema to the Event Model
        """
        ordered = True
        include_fk = True
        model = EventModel
        fields = ("id", "title", "summary", "status",
                  "dt_start", "dt_end",
                  "owner", "participants", "guests",
                  "artifacts")
        dump_only = ("id", "status", "participants", "guests", "owner")

    @post_load
    def make_event(self, data: Dict, **kwargs) -> EventModel:
        """
        Method for returning EventModel
        """
        return EventModel(**data)


event_full_schema = EventSchema()
event_full_list_schema = EventSchema(many=True)

event_short_schema = EventSchema(exclude=("summary", "participants", "guests", "artifacts"))
event_short_list_schema = EventSchema(exclude=("summary", "participants", "guests", "artifacts"), many=True)
