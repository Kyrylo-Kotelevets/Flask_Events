from flask_app import db
from flask_app.models.base import BaseModel


class ArtifactModel(db.Model, BaseModel):
    __tablename__ = 'artifact'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128), nullable=False, unique=True)

    # __table_args__ = (
    #     db.CheckConstraint("url LIKE '{}/books/%'".format(os.getenv("BOOKS_APP_URL")), name='valid_book_url_constraint'),
    # )

    def __str__(self):
        return self.url

    @classmethod
    def find_by_url(cls, url):
        return cls.query.filter_by(url=url).first()
