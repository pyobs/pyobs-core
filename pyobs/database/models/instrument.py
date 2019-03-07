from sqlalchemy import Column, Integer, String

from .base import Base
from .table import GetByNameMixin


class Instrument(Base, GetByNameMixin):
    """An instrument."""
    __tablename__ = 'pyobs_instrument'

    id = Column(Integer, comment='Unique ID of instrument', primary_key=True)
    name = Column(String(30), comment='Name of instrument', unique=True, nullable=False)

    def __init__(self, name):
        """Create a new instrument with the given name.

        Args:
            name: Name for new instrument.
        """
        self.name = name


__all__ = ['Instrument']
