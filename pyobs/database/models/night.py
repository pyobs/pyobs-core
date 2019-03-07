from sqlalchemy import Column, Integer, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base
from .table import GetByNameMixin


class Night(Base, GetByNameMixin):
    """A single night."""
    __tablename__ = 'pyobs_night'

    id = Column(Integer, comment='Unique ID of night', primary_key=True)
    night = Column(Date, comment='Date at beginning  of night', unique=True, nullable=False)
    observations = relationship("Observation")

    def __init__(self, night: datetime = None):
        """Create a new Night for the given date.

        Args:
            night: Date of night.
        """

        self.night = night


__all__ = ['Night']
