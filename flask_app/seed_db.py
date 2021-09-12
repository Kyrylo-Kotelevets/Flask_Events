from faker import Faker

from flask_app import db
from flask_app.models.event import EventModel
from flask_app.models.user import UserModel
from sqlalchemy.sql.expression import func
from random import randint


def seed_event(count: int = 10):
    fake = Faker()
    for _ in range(count):
        event = EventModel(title=" ".join(fake.words(randint(1, 5))),
                           summary=fake.text()[:128],
                           dt_start=fake.date_between(start_date='-1y', end_date='today'),
                           dt_end=fake.date_between(start_date='today', end_date='+1y'),
                           owner=UserModel.query.order_by(func.random()).first())

        for user in UserModel.query.order_by(func.random()).limit(randint(1, 3)):
            event.guests.append(user)

        for user in UserModel.query.order_by(func.random()).limit(randint(1, 3)):
            event.participants.append(user)

        event.save_to_db()


def seed_users(count: int = 5):
    fake = Faker()
    for _ in range(count):
        user = UserModel(username=fake.word().lower(),
                         password="123456789",
                         first_name=fake.first_name(),
                         last_name=fake.first_name())
        user.save_to_db()


def seed_django_user():
    db.session.add(UserModel(username="wenom"))
    db.session.commit()
