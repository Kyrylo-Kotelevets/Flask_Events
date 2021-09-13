from flask.cli import FlaskGroup

from flask_app import app, db
from flask_app.seed_db import seed_django_user, seed_users, seed_event

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.reflect()
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    seed_django_user()
    seed_users(5)
    seed_event(50)


@cli.command("drop_db")
def drop_db():
    db.drop_all()
    db.session.commit()


if __name__ == "__main__":
    cli()
