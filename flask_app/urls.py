from flask_app.auth.login import Login, Logout, SignUp
from flask_app.resources.event import UserEventsAsOwner, EventList, RetrieveUpdateDestroyEvent
from flask_app.resources.guest import UserEventsAsGuest, UserAsGuest, EventGuests
from flask_app.resources.participant import UserEventsAsParticipant, UserAsParticipant, EventParticipants
from flask_app.resources.user import UserList, RetrieveUpdateDestroyUser
from . import api

# user login - post
api.add_resource(Login, "/login")
api.add_resource(SignUp, "/signup")
api.add_resource(Logout, "/logout")

api.add_resource(UserList, "/user")
api.add_resource(RetrieveUpdateDestroyUser, "/user/<string:username>")

api.add_resource(EventList, "/event")
api.add_resource(RetrieveUpdateDestroyEvent, "/event/<int:event_id>")
api.add_resource(EventParticipants, "/event/<int:event_id>/participants")
api.add_resource(EventGuests, "/event/<int:event_id>/guests")

api.add_resource(UserAsGuest, "/event/<int:event_id>/me_guest")
api.add_resource(UserAsParticipant, "/event/<int:event_id>/me_participant")

api.add_resource(UserEventsAsParticipant, "/where_i_participant")
api.add_resource(UserEventsAsGuest, "/where_i_guest")
api.add_resource(UserEventsAsOwner, "/my_events")
