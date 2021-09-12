"""
Module Configuration
"""
from os import getenv

POSTGRES_DB = getenv("POSTGRES_DB")
APP_NAME = getenv("APP_NAME")
POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")


class Config:
    """
    Class default Configuration that all environments will default to
    """
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://"
        f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@db_{APP_NAME}:5432/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
