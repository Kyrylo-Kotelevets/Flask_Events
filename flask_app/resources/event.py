"""
Module with Event Endpoints
"""
from functools import wraps
from typing import Callable, Dict, Tuple

from flask import Response
from flask import request, jsonify
from flask_login import login_required, current_user
from flask_restx import Resource

from flask_app import db
from flask_app.models.event import EventModel
from flask_app.pagination.pagination import create_pagination
from flask_app.schemas.event import event_full_schema, event_short_list_schema


class EventResource(Resource):
    """
    Base resource class for Event model
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes event
        """
        super().__init__(*args, **kwargs)
        self.event = None

    def dispatch_request(self, *args, **kwargs):
        """
        Checks if the event exists and has not passed,
        and if so, then initializes it
        """
        event = EventModel.find_by_id(kwargs.get("event_id"))
        if event is None:
            return jsonify({
                "status": 404,
                "message": "Event not found"
            })
        if event.status == "past" and request.method != "GET":
            return jsonify({
                "status": 404,
                "message": "You can not apply changes to past event"
            })
        self.event = event
        return super().dispatch_request(*args, **kwargs)

    @staticmethod
    def owner_required(foo: Callable) -> Callable:
        """
        Decorator for checking owner access rights
        """
        @login_required
        @wraps(foo)
        def wrapper(_, event_id):
            if current_user != EventModel.find_by_id(event_id).owner:
                return Response("Owner account required", status=403)
            return foo(_, event_id)

        return wrapper

    @staticmethod
    def admin_or_owner_required(foo: Callable) -> Callable:
        """
        Decorator for checking admin or owner access rights
        """
        @login_required
        @wraps(foo)
        def wrapper(_, event_id):
            if not current_user.is_admin and current_user != EventModel.find_by_id(event_id).owner:
                return Response("Admin or Owner account required", status=403)
            return foo(_, event_id)

        return wrapper


class UserEventsAsOwner(Resource):
    """
    Resource for providing a list of events
    where the current user is the owner
    """
    @staticmethod
    @login_required
    def get() -> Tuple[Dict, int]:
        """Method for retrieving a list of events
        where the current user is the owner

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        return event_short_list_schema.dump(EventModel.filter_by_owner(user_id=current_user.id))


class EventList(Resource):
    """
    Resource for retrieving old and adding new events
    """
    @staticmethod
    def get() -> Tuple[Dict, int]:
        """Method for retrieving list of all Events

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        filters = dict(request.args)
        page = int(filters.pop("page", 1))
        limit = int(filters.pop("limit", 2))

        queryset = EventModel.get_list(query_params=filters)
        paginated_events = queryset.paginate(page, limit, error_out=False)
        response = create_pagination(items=paginated_events,
                                     schema=event_short_list_schema,
                                     page=page,
                                     limit=limit,
                                     query_params=filters,
                                     base_url=request.base_url)
        return response, 200

    @staticmethod
    @login_required
    def post() -> Tuple[Dict, int]:
        """Method for creating new Event

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        event_json = request.get_json(force=True)

        if EventModel.find_by_title(event_json.get('title')):
            return {"message": "Event already exists"}, 400

        event = event_full_schema.load(event_json)
        event.owner = current_user

        # If user tries to create past event
        if event.status == "past":
            db.session.rollback()
            return {"message": "You can not create past event"}, 400

        event.save_to_db()
        return event_full_schema.dump(event), 200


class RetrieveUpdateDestroyEvent(EventResource):
    """
    Resource for managing Event details
    """
    def get(self, event_id: int) -> Tuple[Dict, int]:
        """Method for retrieving details about the Event

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        return event_full_schema.dump(self.event), 200

    @EventResource.admin_or_owner_required
    def patch(self, event_id: int) -> Tuple[Dict, int]:
        """Method for partial updating details about the Event

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        event_json = request.get_json(force=True)

        # Check if any parameter not in columns
        for key_name in event_json.keys():
            if key_name not in self.event.__table__.columns:
                return {"message": "<{}> no such attribute in event".format(key_name)}, 404

        self.event.update_in_db(data=event_json)
        return event_full_schema.dump(self.event), 200

    @EventResource.admin_or_owner_required
    def delete(self, event_id: int) -> Tuple[Dict, int]:
        """Method for deleting the Event

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        self.event.delete_from_db()
        return {"message": "Event deleted"}, 200
