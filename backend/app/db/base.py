"""
SQLAlchemy declarative base.
All ORM models inherit from `Base` so SQLAlchemy can track the schema.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass