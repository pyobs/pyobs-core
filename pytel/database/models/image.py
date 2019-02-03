import logging
import math
import os
from typing import Union

from astropy.io import fits

from pytel.utils.time import Time
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Table
from sqlalchemy.orm import relationship, Session

from .base import Base
from .telescope import Telescope
from .instrument import Instrument
from .observation import Observation

log = logging.getLogger(__name__)

"""Define connections between images, mainly used for reduction."""
image_relation = Table(
    "pytel_image_relation", Base.metadata,
    Column("image_id", Integer, ForeignKey("pytel_image.id"), index=True),
    Column("parent_id", Integer, ForeignKey("pytel_image.id"), index=True)
)


class ImageType(object):
    """Available image types."""
    bias = 'bias'
    dark = 'dark'
    flat = 'flat'
    object = 'object'
    all = [bias, dark, flat, object]


class Image(Base):
    """A single image."""
    __tablename__ = 'pytel_image'

    id = Column(Integer, comment='Unique ID of image', primary_key=True)
    observation_id = Column(Integer, ForeignKey(Observation.id), comment='Link to observation', nullable=False)
    telescope_id = Column(Integer, ForeignKey(Telescope.id), comment='ID of telescope used')
    instrument_id = Column(Integer, ForeignKey(Instrument.id), comment='ID of instrument used')
    image_type = Column(String(10), comment='Image type')
    reduction_level = Column(Integer, comment='Level of reduction', default=0)
    date_obs = Column(DateTime, comment='Time exposure started', nullable=False)
    target_name = Column(String(50), comment='Name of target')
    target_x = Column(Float, comment='Target coordinates as vector, X component')
    target_y = Column(Float, comment='Target coordinates as vector, Y component')
    target_z = Column(Float, comment='Target coordinates as vector, Z component')
    tel_ra = Column(Float, comment='Telescope Right Ascension')
    tel_dec = Column(Float, comment='Telescope Declination')
    tel_alt = Column(Float, comment='Altitude of telescope at start of exposure')
    tel_az = Column(Float, comment='Azimuth of telescope at start of exposure')
    tel_focus = Column(Float, comment='Focus of telescope')
    sol_alt = Column(Float, comment='Elevation of sun above horizon in deg')
    moon_alt = Column(Float, comment='Elevation of moon above horizon in deg')
    moon_ill = Column(Float, comment='Illuminated fraction of moon surface')
    moon_sep = Column(Float, comment='Ok-sky distance of object to Moon in deg')
    exp_time = Column(Float, comment='Exposure time')
    filter = Column(String(20), comment='Filter used')
    binning = Column(String(5), comment='Binning of image')
    offset_x = Column(Integer, comment='X offset of image in unbinned pixels')
    offset_y = Column(Integer, comment='Y offset of image in unbinned pixels')
    width = Column(Integer, comment='Width of image in binned pixels')
    height = Column(Integer, comment='Height of image in binned pixels')
    data_mean = Column(Float, comment='Mean data value')
    quality = Column(Float, comment='Estimation of image quality (0..1)')
    filename = Column(String(255), comment='Name of file', unique=True, nullable=False)

    observation = relationship(Observation, back_populates='images')
    telescope = relationship(Telescope)
    instrument = relationship(Instrument)

    children = relationship("Image",
                            secondary=image_relation,
                            primaryjoin=id == image_relation.c.parent_id,
                            secondaryjoin=id == image_relation.c.image_id,
                            backref="parents")

    def delete(self, session: Session, archive_path: str):
        """Delete an image from the database and filesystem.

        Args:
            session: SQLalchemy session to use.
            archive_path: Archive path for images, i.e. where to find the images.
        """

        # delete file, if exists
        filename = os.path.join(archive_path, self.filename)
        if os.path.exists(filename):
            os.remove(filename)
        else:
            log.warning('File for Image %s does not exist and thus cannot be deleted.', self.filename)

        # delete from database
        session.delete(self)

    @property
    def binning_factors(self) -> (int, int):
        """Returns the binning factors as integer.

        Returns:
            (int, int) Binning in X and Y.
        """
        s = self.binning.split('x')
        return int(s[0]), int(s[1])

    @property
    def unbinned_size(self) -> (int, int):
        """Returns the unbinned size of this image.

        Returns:
            (int, int) Unbinned size of this image.
        """
        b = self.binning_factors
        return self.width * b[0], self.height * b[1]

    def add_fits_header(self, session, header):
        """Add properties from FITS headers.
        
        Args:
            session (Session): Session object. 
            header (Header): FITS header to take data from. 
        """
        
        from .instrument import Instrument
        from .telescope import Telescope

        # dates
        if 'DATE-OBS' in header:
            self.date_obs = Time(header['DATE-OBS']).to_datetime()
        else:
            raise ValueError('Could not find DATE-OBS in FITS header.')

        # telescope and instrument
        self.telescope = Telescope.get_by_name(session, header['TELESCOP']) if 'TELESCOP' in header else None
        self.instrument = Instrument.get_by_name(session, header['INSTRUME']) if 'INSTRUME' in header else None
        self.image_type = header['IMAGETYP'] if 'IMAGETYP' in header else None

        # binning
        if 'XBINNING' in header and 'YBINNING' in header:
            self.binning = '%dx%d' % (header['XBINNING'], header['YBINNING'])
        elif 'XBIN' in header and 'YBIN' in header:
            self.binning = '%dx%d' % (header['XBIN'], header['YBIN'])
        else:
            log.warning('Missing or invalid XBINNING and/or YBINNING in FITS header.')

        # telescope stuff
        if 'OBJRA' in header and 'OBJDEC' in header:
            self.tel_ra = header['OBJRA']
            self.tel_dec = header['OBJDEC']
            ra = math.radians(header['OBJRA'])
            dec = math.radians(header['OBJDEC'])
            self.target_x = math.cos(dec) * math.cos(ra)
            self.target_y = math.cos(dec) * math.sin(ra)
            self.target_z = math.sin(dec)
        if 'TEL-ALT' in header and 'TEL-AZ' in header:
            self.tel_alt = header['TEL-ALT']
            self.tel_az = header['TEL-AZ']
        if 'TEL-FOCU' in header:
            self.tel_focus = header['TEL-FOCU']

        # environment
        if 'SOL-ALT' in header:
            self.sol_alt = header['SOL-ALT']
        if 'MOON-ALT' in header:
            self.moon_alt = header['MOON-ALT']
        if 'MOON-ILL' in header:
            self.moon_ill = header['MOON-ILL']
        if 'MOON-SEP' in header:
            self.moon_sep = header['MOON-SEP']

        # image size and offset
        self.width = header['NAXIS1']
        self.height = header['NAXIS2']
        self.offset_x = header['XORGSUBF'] if 'XORGSUBF' in header else 0
        self.offset_y = header['YORGSUBF'] if 'YORGSUBF' in header else 0

        # other stuff
        self.target_name = header['OBJNAME'] if 'OBJNAME' in header else header['OBJECT']
        self.exp_time = header['EXPTIME']
        self.filter = header['FILTER']
        self.data_mean = header['DATAMEAN']

    @staticmethod
    def add_from_fits(filename: str, header: fits.Header, environment: 'Environment') -> Union['Image', None]:
        """Add Image from a given FITS file.

        Args:
            filename: Archive name of file to add.
            header: FITS header of file to add.
            environment: Environment to use.

        Returns:
            The new Image in the database.
        """
        from ..database import session_context
        from . import Project, Task, Night, Observation

        # don't want to raise exceptions
        with session_context() as session:
            # get night of observation
            if 'DATE-OBS' not in header:
                raise ValueError('No DATE-OBS in FITS header.')
            night_obs = environment.night_obs(Time(header['DATE-OBS']))

            # get project
            if 'PROJECT' not in header:
                log.error('No PROJECT in FITS header.')
            project = Project.get_by_name(session, header['PROJECT'])
            if project is None:
                project = Project(header['PROJECT'])
                session.add(project)

            # get task
            if 'TASK' not in header:
                log.error('No TASK in FITS header.')
            task = Task.get_by_name(session, header['TASK'])
            if task is None:
                task = Task(header['TASK'])
                session.add(task)
            task.project = project

            # get night from database
            night = session.query(Night).filter(Night.night == night_obs).first()
            if night is None:
                night = Night(night_obs)
                session.add(night)

            # get observation
            if 'OBS' not in header:
                log.error('No OBS in FITS header.')
            observation = Observation.get_by_name(session, header['OBS'])
            if observation is None:
                observation = Observation(header['OBS'])
                session.add(observation)
            observation.night = night
            observation.task = task

            # create or update image
            image = session.query(Image).filter(Image.filename == filename).first()
            if image is None:
                image = Image()
                image.filename = filename
                session.add(image)

            # load fits headers
            image.add_fits_header(session, header)

            # add image to observation
            observation.add_image(session, image, environment)

            # finished
            return image


__all__ = ['Image', 'ImageType']
