import logging
from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base
from .project import Project


log = logging.getLogger(__name__)


class Task(Base):
    """A single task in the database."""
    __tablename__ = 'pytel_task'

    id = Column(Integer, comment='Unique ID of task', primary_key=True)
    name = Column(String(50), comment='Name of task.')
    project_id = Column(Integer, ForeignKey(Project.id), comment='Project this tasks belongs to')

    project = relationship(Project, back_populates='tasks')
    UniqueConstraint('name', 'project_id')


__all__ = ['Task']
