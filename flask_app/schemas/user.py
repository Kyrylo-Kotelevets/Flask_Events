from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_app.models.user import UserModel
from marshmallow import post_load


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        ordered = True
        include_fk = True
        model = UserModel

        fields = ("id", "username", "first_name", "last_name", "email", "is_admin",)
        dump_only = ("id", )

    @post_load
    def make_event(self, data, **kwargs):
        return UserModel(**data)


user_full_schema = UserSchema()
user_full_list_schema = UserSchema(many=True)

user_short_schema = UserSchema(only=("username", "first_name", "last_name", "is_admin"))
user_short_list_schema = UserSchema(only=("username", "first_name", "last_name", "is_admin"), many=True)
