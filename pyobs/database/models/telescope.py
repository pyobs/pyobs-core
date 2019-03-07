from sqlalchemy import Column, Integer, String

from .base import Base
from .table import GetByNameMixin


class Telescope(Base, GetByNameMixin):
    """A telescope."""
    __tablename__ = 'pyobs_telescope'

    id = Column(Integer, comment='Unique ID of telescope', primary_key=True)
    name = Column(String(20), comment='Name of telescope', unique=False, nullable=False)

    def __init__(self, name):
        self.name = name


__all__ = ['Telescope']
