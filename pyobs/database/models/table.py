from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session


class GetByNameMixin:
    """A simple mixin class that adds get_by_name method to class."""

    @classmethod
    def get_by_name(cls, session: Session, name: str) -> Any:
        """Fetch an object from the table with the given name.

        Args:
            session: SQLalchemy session to use.
            name: Name of object to fetch.

        Returns:
            An object with the given name or None.
        """

        # query
        result = session.query(cls).filter(func.lower(cls.name) == name.lower()).all()
        if len(result) != 1:
            return None

        # object
        return result[0]


__all__ = ['GetByNameMixin']
