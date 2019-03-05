import logging
from enum import Enum
from typing import Union

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Session

from .base import Base
from .night import Night
from .table import GetByNameMixin

log = logging.getLogger(__name__)


class Observation(Base, GetByNameMixin):
    """A observation, i.e. a collection of images."""
    __tablename__ = 'pytel_observation'

    id = Column(Integer, comment='Unique ID of observation', primary_key=True)
    night_id = Column(Integer, ForeignKey(Night.id), comment='ID of night')
    name = Column(String(30), comment='Name of observation', unique=True, nullable=False)
    task_name = Column(Integer, comment='Name of task')
    project_name = Column(Integer, comment='Name of project')
    start_time = Column(DateTime, comment='Date and time of start of observation')

    night = relationship(Night, back_populates='observations')
    images = relationship("Image", lazy='dynamic')
    task = relationship("Task", foreign_keys=[task_name], primaryjoin='Observation.task_name == Task.name')
    project = relationship("Project", foreign_keys=[project_name],
                           primaryjoin='Observation.project_name == Project.name')

    def __init__(self, name: str):
        self.name = name

    def add_image(self, session: Session, image: 'Image', environment: 'Environment'):
        """Add a new image to this observation.

        Args:
            session: SQLalchemy session to use.
            image: Image to add.
            environment: Environment to use.
        """

        # set observation
        image.observation = self

        # update observation start time
        if not self.start_time or image.date_obs < self.start_time:
            # set start time
            self.start_time = image.date_obs

            # get beginning of night
            night_obs = environment.night_obs(self.start_time)

            # get night
            night = session.query(Night).filter(Night.night == night_obs).first()
            if not night:
                night = Night(night_obs)
                session.add(night)

            # reset night and set it
            night.reduced = 0
            self.night = night

    def _images(self, session: Session, image_types: Union[list, str, Enum], reduction_level: int) -> list:
        """Return list of (un)reduced images of given type in this observation.

        Args:
            session: SQLAlchemy session to query data from.
            image_types: Single string or ImageType or list of them.
            reduction_level: Reduction level.

        Returns:
             List of images.
        """

        # image types to list
        if not hasattr(image_types, '__iter__') or isinstance(image_types, str):
            image_types = [image_types]

        # return list of reduced images
        from .image import Image
        return self.images.filter(Image.image_type.in_(image_types)).filter(Image.reduction_level == reduction_level)

    def raw_images(self, session: Session, image_types: Union[list, str, Enum]) -> list:
        """Return list of raw images of given type in this observation.

        Args:
            session: SQLAlchemy session to query data from.
            image_types: Single string or ImageType or list of them.

        Returns:
             List of raw images.
        """
        return self._images(session, image_types, reduction_level=0)

    def reduced_images(self, session: Session, image_types: Union[list, str, Enum]) -> list:
        """Return list of reduced images of given type in this observation.

        Args:
            session: SQLAlchemy session to query data from.
            image_types: Single string or ImageType or list of them.

        Returns:
             List of reduced images.
        """
        return self._images(session, image_types, reduction_level=1)


__all__ = ['Observation']
