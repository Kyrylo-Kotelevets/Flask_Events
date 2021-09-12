from flask import request, jsonify
from flask_login import login_required, current_user
from flask_restx import Resource

from flask_app.models.event import EventModel
from flask_app.models.user import UserModel
from flask_app.resources.event import EventResource
from flask_app.schemas.event import event_short_list_schema
from flask_app.schemas.user import user_short_list_schema


class UserEventsAsParticipant(Resource):
    @staticmethod
    @login_required
    def get():
        return event_short_list_schema.dump(EventModel.filter_by_participant(user_id=current_user.id))


class UserAsParticipant(EventResource):
    @login_required
    def get(self, event_id: int):
        if current_user in self.event.participants:
            return jsonify({
                "status": 200,
                "message": "You are registered as a participant"
            })
        elif current_user in self.event.guests:
            return jsonify({
                "status": 200,
                "message": "You are registered as a guest"
            })
        else:
            return jsonify({
                "status": 200,
                "message": "You are not registered as a participant"
            })

    @login_required
    def post(self, event_id: int):
        if current_user in self.event.guests:
            return jsonify({
                "status": 404,
                "message": "You already registered as a guest"
            })
        elif current_user in self.event.participants:
            return jsonify({
                "status": 404,
                "message": "You already registered as a participant"
            })
        else:
            self.event.participants.append(current_user)
            self.event.save_to_db()

            return jsonify({
                "status": 200,
                "message": "Successfully register as a participant"
            })

    @login_required
    def delete(self, event_id: int):
        if current_user not in self.event.participants:
            return jsonify({
                "status": 404,
                "message": "You are not registered as a participant"
            })
        else:
            self.event.participants.remove(current_user)
            self.event.save_to_db()

            return jsonify({
                "status": 200,
                "message": "Successfully unregister from participants"
            })


class EventParticipants(EventResource):
    def get(self, event_id: int):
        return user_short_list_schema.dump(self.event.participants), 200

    @EventResource.admin_or_owner_required
    def post(self, event_id: int):
        body = request.get_json(force=True)

        if not body.get('participants'):
            return jsonify({
                "status": 404,
                "message": "Empty or unprovided participants list"
            })

        for username in body.get('participants'):
            participant = UserModel.find_by_username(username)

            if participant is None:
                if UserModel.exists_remote(username):
                    participant = UserModel(username=username)
                    participant.save_to_db()
                else:
                    return jsonify({
                        "status": 404,
                        "message": "User <{}> not found".format(username)
                    })

            if participant in self.event.guests:
                return jsonify({
                        "status": 400,
                        "message": "<{}> already registered for event as guest".format(participant.username)
                    })

            if participant in self.event.participants:
                return jsonify({
                        "status": 400,
                        "message": "<{}> already registered for event as participant".format(participant.username)
                    })

            self.event.participants.append(participant)
            self.event.save_to_db()

        return jsonify({
            "status": 200,
            "message": "All users were successfully registered for event participants"
        })

    @EventResource.admin_or_owner_required
    def delete(self, event_id: int):
        body = request.get_json(force=True)

        if not body.get('participants'):
            return jsonify({
                "status": 404,
                "message": "Empty or unprovided participants list"
            })

        for username in body.get('participants'):
            participant = UserModel.find_by_username(username)

            if (participant is None) or (participant not in self.event.participants):
                return jsonify({
                    "status": 404,
                    "message": "User <{}> not in participants list".format(username)
                })

            self.event.participants.remove(participant)
            self.event.save_to_db()

        return jsonify({
            "status": 200,
            "message": "All users were successfully unregistered from event participants"
        })