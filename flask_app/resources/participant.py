"""
Module with Event participants endpoints
"""

from typing import Dict, Tuple

from flask import request, Response, jsonify
from flask_login import login_required, current_user
from flask_restx import Resource

from flask_app.models.event import EventModel
from flask_app.models.user import UserModel
from flask_app.pagination.pagination import create_pagination
from flask_app.resources.event import EventResource
from flask_app.schemas.event import event_short_list_schema
from flask_app.schemas.user import user_short_list_schema


class UserEventsAsParticipant(Resource):
    @staticmethod
    @login_required
    def get() -> Tuple[Dict, int]:
        """Method for retrieving a list of events
        where the current user in the participants list

        Returns
        -------
        Tuple[Dict, int]
            Response message and status code
        """
        filters = dict(request.args)
        page = int(filters.pop("page", 1))
        limit = int(filters.pop("limit", 2))

        queryset = EventModel.filter_by_participant(user_id=current_user.id)
        paginated_events = queryset.paginate(page, limit, error_out=False)
        response = create_pagination(items=paginated_events,
                                     schema=event_short_list_schema,
                                     page=page,
                                     limit=limit,
                                     base_url=request.base_url)
        return response, 200


class UserAsParticipant(EventResource):
    """
    Resource for registering and unregistering
    as a participant fo event
    """
    @login_required
    def get(self, event_id: int) -> Response:
        """Method for checking registration as a participant

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Response
            Response message with status code
        """
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
    def post(self, event_id: int) -> Response:
        """Method for registering as a participant

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Response
            Response message with status code
        """
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
            self.event.add_participant(current_user)

            return jsonify({
                "status": 200,
                "message": "Successfully register as a participant"
            })

    @login_required
    def delete(self, event_id: int) -> Response:
        """Method for unregistering from participants

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Response
            Response message with status code
        """
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
    """
    Resource for managing Event participants list
    """
    def get(self, event_id: int) -> Response:
        """Method for retrieving a list of event participants

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Response
            Response message with status code
        """
        return jsonify({
            "status": 200,
            "guests": user_short_list_schema.dump(self.event.participants)
        })

    @EventResource.admin_or_owner_required
    def post(self, event_id: int) -> Response:
        """Method for adding new participant

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Response
            Response message with status code
        """
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

            self.event.add_participant(participant)

        return jsonify({
            "status": 200,
            "message": "All users were successfully registered for event participants"
        })

    @EventResource.admin_or_owner_required
    def delete(self, event_id: int) -> Response:
        """Method for deleting participant

        Parameters
        ----------
        event_id : int
            Event id

        Returns
        -------
        Response
            Response message with status code
        """
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
