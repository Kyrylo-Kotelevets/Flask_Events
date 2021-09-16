from typing import Optional

from flask_app import db
from flask_app.models.base import EntityModel


class ArtifactModel(db.Model, EntityModel):
    __tablename__ = 'artifact'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128), unique=True)

    # __table_args__ = (
    #     db.CheckConstraint("url LIKE '{}/books/%'".format(os.getenv("BOOKS_APP_URL")), name='valid_book_url_constraint'),
    # )

    def __repr__(self) -> str:
        """
        Converts Artifact to the string
        """
        return "<Artifact (id = {}, url = {}>".format(self.id, self.url)

    @classmethod
    def find_by_url(cls, url: str) -> Optional['ArtifactModel']:
        """Method for searching by event title

        Parameters
        ----------
        url : str
            Artifact url pattern for search

        Returns
        -------
        Optional['ArtifactModel']
            Search result, None if not exists
        """
        return cls.query.filter_by(url=url).first()
