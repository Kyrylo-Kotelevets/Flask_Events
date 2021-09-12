# from sqlalchemy import exc
from flask_app import db


class BaseModel:
    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_by_id(cls, iid: int):
        return cls.query.filter_by(id=iid).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        # try:
        #     db.session.add(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        # try:
        #     db.session.delete(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()

    def as_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

