import logging
from sqlalchemy import Column, Integer, Float
from sqlalchemy.orm import relationship

from .base import Base


log = logging.getLogger(__name__)


class Project(Base):
    """A project."""
    __tablename__ = 'pytel_project'

    id = Column(Integer, comment='Unique ID of project', primary_key=True)
    priority = Column(Float, comment='Priority of task', default=0)

    tasks = relationship("Task", lazy='dynamic')


__all__ = ['Project']
