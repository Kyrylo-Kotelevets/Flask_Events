# from sqlalchemy import exc
from flask_app import db


class RelationshipModel:
    """
    Class with base functions for m2m models
    """
    @classmethod
    def find_all(cls):
        """
        Returns all objects
        """
        return cls.query.all()

    def save_to_db(self):
        """
        Saves object to database
        """
        db.session.add(self)
        db.session.commit()
        # try:
        #     db.session.add(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()

    def delete_from_db(self):
        """
        Delete object from database
        """
        db.session.delete(self)
        db.session.commit()
        # try:
        #     db.session.delete(self)
        #     db.session.commit()
        # except exc.IntegrityError:
        #     db.session.rollback()


class EntityModel(RelationshipModel):
    """
    Class with base functions for entity models
    """
    @classmethod
    def find_by_id(cls, iid: int):
        """
        Returns object by id
        """
        return cls.query.filter_by(id=iid).first()

    def as_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
