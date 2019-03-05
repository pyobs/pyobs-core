import logging
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base
from .table import GetByNameMixin


log = logging.getLogger(__name__)


class Project(Base, GetByNameMixin):
    """A project."""
    __tablename__ = 'pytel_project'

    id = Column(Integer, comment='Unique ID of project', primary_key=True)
    name = Column(String(50), comment='Name of project', unique=True)

    tasks = relationship("Task", lazy='dynamic')

    def __init__(self, name):
        self.name = name


__all__ = ['Project']
