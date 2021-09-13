from flask import request, jsonify
from flask_login import login_required, current_user
from flask_restx import Resource

from flask_app.models.event import EventModel
from flask_app.models.user import UserModel
from flask_app.resources.event import EventResource
from flask_app.schemas.event import event_short_list_schema
from flask_app.schemas.user import user_short_list_schema


class UserEventsAsGuest(Resource):
    @staticmethod
    @login_required
    def get():
        return event_short_list_schema.dump(EventModel.filter_by_guest(user_id=current_user.id))


class UserAsGuest(EventResource):
    @login_required
    def get(self, event_id: int):
        if current_user in self.event.guests:
            return jsonify({
                "status": 200,
                "message": "You are registered as a guest"
            })
        elif current_user in self.event.participants:
            return jsonify({
                "status": 200,
                "message": "You are registered as a participant"
            })
        else:
            return jsonify({
                "status": 200,
                "message": "You are not registered as a guest"
            })

    @login_required
    def post(self, event_id: int):
        if current_user in self.event.participants:
            return jsonify({
                "status": 404,
                "message": "You already registered as a participant"
            })
        elif current_user in self.event.guests:
            return jsonify({
                "status": 404,
                "message": "You already registered as a guest"
            })
        else:
            self.event.add_guest(current_user)
            return jsonify({
                "status": 200,
                "message": "Successfully register as a guest"
            })

    @login_required
    def delete(self, event_id: int):
        if current_user not in self.event.guests:
            return jsonify({
                "status": 404,
                "message": "You are not registered as a guest"
            })
        else:
            self.event.guests.remove(current_user)
            self.event.save_to_db()

            return jsonify({
                "status": 200,
                "message": "Successfully unregister from guests"
            })


class EventGuests(EventResource):
    def get(self, event_id: int):
        return user_short_list_schema.dump(self.event.guests), 200

    @EventResource.admin_or_owner_required
    def post(self, event_id: int):
        body = request.get_json(force=True)

        if not body.get("guests"):
            return jsonify({
                "status": 404,
                "message": "Empty or unprovided guests list"
            })

        for username in body.get("guests"):
            guest = UserModel.find_by_username(username)

            if guest is None:
                if UserModel.exists_remote(username):
                    guest = UserModel(username=username)
                    guest.save_to_db()
                else:
                    return jsonify({
                        "status": 404,
                        "message": "User <{}> not found".format(username)
                    })

            if guest in self.event.participants:
                return jsonify({
                        "status": 400,
                        "message": "<{}> already registered for event as participants".format(guest.username)
                    })

            if guest in self.event.guests:
                return jsonify({
                        "status": 400,
                        "message": "<{}> already registered for event as guest".format(guest.username)
                    })

            self.event.add_guests(guest)

        return jsonify({
            "status": 200,
            "message": "All users were successfully registered for event guests"
        })

    @EventResource.admin_or_owner_required
    def delete(self, event_id: int):
        body = request.get_json(force=True)

        if not body.get("guests"):
            return jsonify({
                "status": 404,
                "message": "Empty or unprovided guests list"
            })

        for username in body.get('guests'):
            guest = UserModel.find_by_username(username)

            if (guest is None) or (guest not in self.event.guests):
                return jsonify({
                    "status": 404,
                    "message": "User <{}> not in guests list".format(username)
                })

            self.event.guests.remove(guest)
            self.event.save_to_db()

        return jsonify({
            "status": 200,
            "message": "All users were successfully unregistered from event guests"
        })
