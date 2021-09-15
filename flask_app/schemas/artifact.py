"""
Module with Artifact Schema
"""

from typing import Dict

from marshmallow import post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from flask_app.models.artifact import ArtifactModel


class ArtifactSchema(SQLAlchemyAutoSchema):
    """
    Artifact Schema
    """
    class Meta:
        """
        Connecting Schema with the Artifact Model
        """
        ordered = True
        model = ArtifactModel
        fields = ("id", "url",)
        dump_only = ("id", "url",)

    @post_load
    def make_artifact(self, data: Dict, **kwargs) -> ArtifactModel:
        """
        Method for returning ArtifactModel
        """
        return ArtifactModel(**data)


artifact_schema = ArtifactSchema()
artifact_list_schema = ArtifactSchema(many=True)
