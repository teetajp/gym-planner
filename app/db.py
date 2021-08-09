""" Handles database connections """
import os

from flask import g

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        # Connect to PostgreSQL database
        engine = create_engine(os.getenv("DATABASE_URL"))
        g.db = scoped_session(sessionmaker(bind=engine))

    return g.db


def close_db():
    """If this request connected to the database,
    close the connection."""
    db = g.pop("db", None)

    if db is not None:
        db.remove()
