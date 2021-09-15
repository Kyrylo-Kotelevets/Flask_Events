from faker import Faker

from flask_app import db
from flask_app.models.event import EventModel
from flask_app.models.user import UserModel
from sqlalchemy.sql.expression import func
from random import randint


def seed_event(count: int = 10):
    fake = Faker()
    for _ in range(count):
        start_datetime = fake.date_time_between('-1y', '+1y')
        end_datetime = fake.date_time_between(start_datetime, "+1M")

        event = EventModel(title=" ".join(fake.words(randint(1, 5))),
                           summary=fake.text(128),
                           dt_start=start_datetime,
                           dt_end=end_datetime,
                           owner=UserModel.query.order_by(func.random()).first())

        for user in UserModel.query.order_by(func.random()).limit(randint(1, 4)):
            event.add_participant(user)

        for user in UserModel.query.order_by(func.random()).limit(randint(1, 8)):
            if user not in event.participants:
                event.add_guest(user)

        event.save_to_db()


def seed_users(count: int = 50):
    fake = Faker()
    usernames = {fake.first_name().lower() for _ in range(count)}
    usernames.update({"kelly", "marie", "vincent"})
    for username in usernames:
        user = UserModel(username=username,
                         password="123456789",
                         first_name=fake.first_name(),
                         last_name=fake.first_name())
        user.save_to_db()
