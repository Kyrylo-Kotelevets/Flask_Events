import json
from functools import wraps

from flask import Response
from flask import request, jsonify
from flask_login import login_required, current_user
from flask_restx import Resource

from flask_app.models.event import EventModel
from flask_app.schemas.event import event_full_schema, event_short_list_schema


class EventResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = None

    def dispatch_request(self, *args, **kwargs):
        event = EventModel.find_by_id(kwargs.get("event_id"))
        if event is None:
            return jsonify({
                "status": 404,
                "message": "Event not found"
            })
        else:
            self.event = event
            return super().dispatch_request(*args, **kwargs)

    @staticmethod
    def owner_required(foo):
        @login_required
        @wraps(foo)
        def wrapper(_, event_id):
            if current_user != EventModel.find_by_id(event_id).owner:
                return Response("GOOD", status=403)
            return foo(_, event_id)

        return wrapper

    @staticmethod
    def admin_or_owner_required(foo):
        @login_required
        @wraps(foo)
        def wrapper(_, event_id):
            if not current_user.is_admin and current_user != EventModel.find_by_id(event_id).owner:
                return Response("GOOD", status=403)
            return foo(_, event_id)

        return wrapper


class UserEventsAsOwner(Resource):
    @staticmethod
    @login_required
    def get():
        return event_short_list_schema.dump(EventModel.filter_by_owner(user_id=current_user.id))


class EventList(Resource):
    @staticmethod
    def get():
        filters = json.loads(request.args.get("filters"))
        if filters:
            return event_short_list_schema.dump(EventModel.find_by_status(filters["status"])), 200
        else:
            return event_short_list_schema.dump(EventModel.find_all()), 200

    @staticmethod
    @login_required
    def post():
        event_json = request.get_json(force=True)

        if EventModel.find_by_title(event_json.get('title')):
            return {'message': 'Event already exists'}, 400

        event = event_full_schema.load(event_json)
        event.owner = current_user
        event.save_to_db()

        return event_full_schema.dump(event), 200


class RetrieveUpdateDestroyEvent(EventResource):
    def get(self, event_id: int):
        return event_full_schema.dump(self.event), 200

    @EventResource.admin_or_owner_required
    def patch(self, event_id: int):
        event_json = request.get_json(force=True)

        for key_name in event_json.keys():
            if key_name not in self.event.__table__.columns:
                return {"message": "<{}> no such attribute in event".format(key_name)}, 404

        self.event.update_in_db(data=event_json)
        return event_full_schema.dump(self.event), 200

    @EventResource.admin_or_owner_required
    def delete(self, event_id: int):
        self.event.delete_from_db()
        return {'message': 'Event deleted'}, 200