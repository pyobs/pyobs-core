import logging
from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base
from .project import Project
from .table import GetByNameMixin


log = logging.getLogger(__name__)


class Task(Base, GetByNameMixin):
    """A single task in the database."""
    __tablename__ = 'pytel_task'

    id = Column(Integer, comment='Unique ID of task', primary_key=True)
    name = Column(String(50), comment='Name of task.', unique=True)
    project_id = Column(Integer, ForeignKey(Project.id), comment='Project this tasks belongs to')

    project = relationship(Project, back_populates='tasks')
    #observations = relationship("Observation", lazy='dynamic')
    UniqueConstraint('name', 'project_id')

    def __init__(self, name):
        self.name = name


__all__ = ['Task']
