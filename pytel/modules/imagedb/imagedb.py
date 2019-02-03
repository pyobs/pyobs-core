import logging
from typing import Union
import os
from astropy.io import fits
from pytel.utils.time import Time
from sqlalchemy.orm import Query
from pytel.utils.fits import format_filename
from sqlalchemy import func

from pytel import PytelModule
from pytel.database import session_context, Image, Observation, Night, Telescope, Instrument
from pytel.interfaces import IImageDB
from pytel.modules import timeout

log = logging.getLogger(__name__)


class ImageDB(PytelModule, IImageDB):
    """An image database."""

    def __init__(self, pattern: str = '{telescope}/{night}/raw/{filename}',
                 raw_path: str = 'raw', calibration_path: str = 'calib', reduced_path: str = 'reduced',
                 vfs_root: str = '/archive', *args, **kwargs):
        """Create a new image database.

        Args:
            pattern: Filename pattern for new images.
            raw_path: Sub-folder for raw files.
            calibration_path: Sub-folder for calibration files.
            reduced_path: Sub-folder for reduced files.
            vfs_root: The VFS root to store images in.
        """
        PytelModule.__init__(self, *args, **kwargs)
        
        # store
        self._pattern = pattern
        self._raw_path = raw_path
        self._calibration_path = calibration_path
        self._reduced_path = reduced_path
        self._vfs_root = vfs_root

    @timeout(60000)
    def add_image(self, filename: str, *args, **kwargs) -> Union[str, None]:
        """Add a new image to the database.

        Args:
            filename (str): Filename at file cache of new image.

        Returns:
            (str) Archive filename
        """

        # download image
        log.info('Downloading image from %s...', filename)
        try:
            with self.open_file(filename, 'rb', compression=False) as f:
                tmp = fits.open(f)
                hdu = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
                tmp.close()
        except FileNotFoundError:
            log.error('Could not download image.')
            return None

        # add image
        return self._add_image(os.path.basename(filename), hdu)

    def _add_image(self, filename: str, hdu) -> Union[str, None]:
        """Actually add image to database.

        Args:
            filename:  Filename of image.
            hdu: HDU of image to store.

        Returns:
            Archive filename
        """

        # open a session
        with session_context() as session:
            # find observation
            if 'OBS' not in hdu.header:
                log.error('Could not find observation name OBS in FITS header.')
                return None
            observation_name = hdu.header['OBS']

            # find or create observation
            log.info('Searching for observation  %s...', observation_name)
            observation = session.query(Observation).filter(Observation.name == observation_name).first()
            if observation is None:
                log.info('Creating new observation...')

                # get night of observation
                if 'DATE-OBS' not in hdu.header:
                    log.warning('Could not fetch DATE-OBS, skipping...')
                    return None
                night_obs = self.environment.night_obs(Time(hdu.header['DATE-OBS']))

                # get task name
                if 'TASK' not in hdu.header:
                    log.warning('Could not fetch name of task, skipping...')
                    return None
                task_name = hdu.header['TASK']

                # get night from database
                night = session.query(Night).filter(Night.night == night_obs).first()
                if night is None:
                    night = Night(night_obs)
                    session.add(night)
                    session.flush()

                # add observation
                observation = Observation()
                observation.name = observation_name
                observation.night = night
                observation.task_name = task_name
                session.add(observation)
                session.flush()

            # create new filename?
            if self._pattern:
                archive_filename = format_filename(hdu.header, self._pattern, self.environment, filename=filename)
            else:
                archive_filename = filename

            # create new image from FITS file
            image = Image.add_from_fits(session, filename, self.environment)

            # add to db
            log.info('Storing new image in database...')
            session.add(image)
            observation.add_image(session, image, self.environment)

            # set new filename root
            archive_filename = os.path.join(self._vfs_root, archive_filename)

            # write file
            log.info('Writing file to disk as %s...', archive_filename)
            try:
                with self.open_file(archive_filename, 'wb') as f:
                    hdu.writeto(f, overwrite=True)
            except FileNotFoundError:
                log.error('Could not write FITS file.')
                return None

            # finished
            log.info('Finished.')
            return archive_filename

    @timeout(10000)
    def get_image_headers(self, filename: str, *args, **kwargs) -> list:
        """Returns a list of (keyword, value, comment) tuples containing FITS headers of given image.

        Args:
            filename (str): Name of file.

        Returns:
            list: List of (keyword value, comment) tuples containing FITS headers of given image.
        """

        # download image
        log.info('Downloading image from %s...', filename)
        try:
            with self.open_file(os.path.join(self._vfs_root, filename), 'rb') as f:
                hdu = fits.open(f)
                data = [(c.keyword, c.value, c.comment) for c in hdu[0].header.cards]
                hdu.close()
                return data
        except FileNotFoundError:
            log.error('Could not download image.')
            return []

    @staticmethod
    def _filter_observations(query: Query,
                             name: str = None, telescope: str = None, instrument: str = None,
                             night_start: str = None, night_end: str = None,
                             task: str = None, *args, **kwargs) -> Query:
        """Apply filter to query depending on given parameters

        Args:
            query (Query): Query to apply
            name (str): Name of observation.
            telescope (str): Name of telescope.
            instrument (str): Name of instrument.
            night_start (str): Only return observations in or after this night
            night_end (str): Only return observations in or before this night
            task (str): Only observations for the given task

        Returns:
            (Query) New query.
        """

        # joins & co
        query = query \
            .join(Night, Observation.night_id == Night.id) \
            .join(Image, Observation.id == Image.observation_id) \
            .join(Telescope, Telescope.id == Image.telescope_id) \
            .join(Instrument, Instrument.id == Image.instrument_id) \
            .filter(Image.reduction_level == 0) \
            .distinct()

        # name?
        if name is not None:
            query = query.filter(Observation.name.like(name))

        # telescope?
        if telescope is not None:
            query = query.filter(Telescope.name == telescope)

        # instrument?
        if instrument is not None:
            query = query.filter(Instrument.name == instrument)

        # night?
        if night_start is not None:
            query = query.filter(Night.night >= Time(night_start).to_datetime())
        if night_end is not None:
            query = query.filter(Night.night <= Time(night_end).to_datetime())

        # task?
        if task is not None:
            query = query.filter(Observation.task_name.like(task))

        # finished
        return query

    @timeout(10000)
    def count_observations(self, name: str = None, telescope: str = None, instrument: str = None,
                           night_start: str = None, night_end: str = None,
                           task: str = None, *args, **kwargs) -> int:
        """Returns the number of observations that match the given criteria.

        Args:
            name: Name of observation.
            telescope: Name of telescope.
            instrument: Name of instrument.
            night_start: Only return observations in or after this night
            night_end: Only return observations in or before this night
            task: Only observations for the given task

        Returns:
            (int) Number of observations that match the criteria
        """

        # open a session
        with session_context() as session:
            # base query
            query = session.query(func.count(Observation.id.distinct()))

            # apply filters
            query = self._filter_observations(query, name=name, telescope=telescope, instrument=instrument,
                                              night_start=night_start, night_end=night_end, task=task)

            # get count
            return query.first()[0]

    @timeout(10000)
    def find_observations(self, name: str = None, telescope: str = None, instrument: str = None,
                          night_start: str = None, night_end: str = None,
                          task: str = None,
                          offset: int = 0, limit: int = 100, order_by: str = 'name', order_asc: bool = True,
                          include_details: bool = False, *args, **kwargs) -> list:
        """Returns a list of observations that match the given criteria.

        Args:
            name: Name of observation.
            telescope: Name of telescope.
            instrument: Name of instrument.
            night_start: Only return observations in or after this night
            night_end: Only return observations in or before this night
            task: Only observations for the given task
            offset (int): Return observations with this number and following
            limit: Only return up to this number of observations.
            order_by: Column to sort by.
            order_asc: Sort in ascending order.
            include_details: Return full details for each observation

        Returns:
            (list) List of observation names or full details
        """

        # open a session
        with session_context() as session:
            # basic query
            query = session.query(Observation.id, Observation.name, Observation.task_name, Observation.start_time,
                                  func.date_format(Observation.start_time, '%Y-%m-%d %H:%I:%S').label('start_time'),
                                  Observation.reduced,
                                  func.date_format(Night.night, '%Y-%m-%d %H:%I:%S').label('night'),
                                  func.count(Image.id).label('image_count'),
                                  func.group_concat(Telescope.name.distinct()).label('telescopes'),
                                  func.group_concat(Image.target_name.distinct()).label('target_names')) \

            # apply filters
            query = self._filter_observations(query, name=name, telescope=telescope, instrument=instrument,
                                              night_start=night_start, night_end=night_end, task=task)

            # group by obs id
            query = query.group_by(Observation.id)

            # order
            if not hasattr(Observation, order_by):
                order_by = 'start_time'
            if order_asc:
                query = query.order_by(getattr(Observation, order_by).asc())
            else:
                query = query.order_by(getattr(Observation, order_by).desc())

            # offset and limit
            query = query.offset(offset).limit(limit)

            # get all observations
            observations = query.all()

            # no details? then just return name columns...
            if not include_details:
                return [o.name for o in observations]

            # convert to dict and split group_concat values
            full = [dict(zip(row.keys(), row)) for row in query.all()]
            for obs in full:
                obs['telescopes'] = obs['telescopes'].split(',')
                obs['target_names'] = obs['target_names'].split(',')

            # return full details
            return full

    def _filter_images(self, query: Query,
                       filename: str = None, image_type: str = None, task: str = None, observation: str = None,
                       reduction_level: int = None, date_start: str = None, date_end: str = None,
                       telescope: str = None, instrument: str = None, binning: str = None, filter: str = None,
                       exp_time: float = None, target_name: str = None, coordinates: str = None,
                       search_radius: float = None, *args, **kwargs) -> Query:
        """Apply filter to query depending on given parameters

        Args:

            query (Query): Query to apply
            filename: Filename of image
            image_type: Type of image
            task: Name of task
            observation: Observation to return images for
            reduction_level: Status of reduction
            date_start: Only return observations after this datetime
            date_end: Only return observations before this datetime
            telescope: Name of telescope
            instrument: Name of instrument
            binning: Image binning
            filter: Filter used
            exp_time (float): Exposure time
            target_name: Name of target
            coordinates: RA & Dec coordinated
            search_radius (float): Radius for cone search

        Returns:
            (Query) New query.
        """

        # joins & co
        query = query \
            .join(Observation, Observation.id == Image.observation_id) \
            .join(Telescope, Telescope.id == Image.telescope_id) \
            .join(Instrument, Instrument.id == Image.instrument_id) \
            .distinct()

        # filename?
        if filename is not None:
            query = query.filter(Image.filename == filename)

        # image type
        if image_type is not None:
            query = query.filter(Image.image_type == image_type)

        # task?
        if task is not None:
            query = query.filter(Observation.task_name.like(task))

        # observation?
        if observation is not None:
            query = query.filter(Observation.name.like(observation))

        # reduction status
        if reduction_level is not None:
            query = query.filter(Image.reduction_level == reduction_level)

        # date?
        if date_start is not None:
            query = query.filter(Image.date_obs >= Time(date_start).to_datetime())
        if date_end is not None:
            query = query.filter(Image.date_obs <= Time(date_end).to_datetime())

        # telescope?
        if telescope is not None:
            query = query.filter(Telescope.name == telescope)

        # instrument?
        if instrument is not None:
            query = query.filter(Instrument.name == instrument)

        # binning?
        if binning is not None:
            query = query.filter(Image.binning == binning)

        # filter?
        if filter is not None:
            query = query.filter(Image.filter == filter)

        # exp time?
        if exp_time is not None:
            query = query.filter(Image.exp_time == exp_time)

        # target?
        if target_name is not None:
            query = query.filter(Image.target_name.like(target_name))

        # return it
        return query

    @timeout(10000)
    def count_images(self, filename: str = None, image_type: str = None, task: str = None, observation: str = None,
                     reduction_level: int = None, date_start: str = None, date_end: str = None,
                     telescope: str = None, instrument: str = None, binning: str = None, filter: str = None,
                     exp_time: float = None, target_name: str = None, coordinates: str = None,
                     search_radius: float = None, *args, **kwargs) -> int:
        """Returns the number of images that match the given criteria.

        Args:
            filename: Filename of image
            image_type: Type of image
            task: Name of task
            observation: Observation to return images for
            reduction_level: Status of reduction
            date_start: Only return observations after this datetime
            date_end: Only return observations before this datetime
            telescope: Name of telescope
            instrument: Name of instrument
            binning: Image binning
            filter: Filter used
            exp_time (float): Exposure time
            target_name: Name of target
            coordinates: RA & Dec coordinated
            search_radius (float): Radius for cone search

        Returns:
            Number of images that match the criteria
        """

        # open a session
        with session_context() as session:
            # base query
            query = session.query(func.count(Image.id.distinct()))

            # apply filters
            query = self._filter_images(query,
                                        filename=filename, image_type=image_type, task=task, observation=observation,
                                        reduction_level=reduction_level, date_start=date_start, date_end=date_end,
                                        telescope=telescope, instrument=instrument, binning=binning, filter=filter,
                                        exp_time=exp_time, target_name=target_name, coordinates=coordinates,
                                        search_radius=search_radius)

            # get count
            return query.first()[0]

    @timeout(10000)
    def find_images(self, filename: str = None, image_type: str = None, task: str = None, observation: str = None,
                    reduction_level: int = None, date_start: str = None, date_end: str = None,
                    telescope: str = None, instrument: str = None, binning: str = None, filter: str = None,
                    exp_time: float = None, target_name: str = None, coordinates: str = None,
                    search_radius: float = None,
                    offset: int = 0, limit: int = 100, order_by: str = 'filename', order_asc: bool = True,
                    include_details: bool = False, *args, **kwargs) -> list:
        """Returns a list of images that match the given criteria.

        Args:
            filename: Filename of image
            image_type: Type of image
            task: Name of task
            observation: Observation to return images for
            reduction_level: Status of reduction
            date_start: Only return observations after this datetime
            date_end: Only return observations before this datetime
            telescope: Name of telescope
            instrument: Name of instrument
            binning: Image binning
            filter: Filter used
            exp_time (float): Exposure time
            target_name: Name of target
            coordinates: RA & Dec coordinated
            search_radius (float): Radius for cone search
            offset: Return images with this number and following
            limit: Only return up to this number of images.
            order_by: Column to sort by.
            order_asc: Sort in ascending order.
            include_details: Return full details for each image.

        Returns:
            List of image names or full details
        """

        # open a session
        with session_context() as session:
            # base query
            query = session.query(Image.filename, func.concat(self._vfs_root).label('scheme'),
                                  Image.image_type, Image.binning, Image.filter,
                                  Image.exp_time, Image.target_name,
                                  func.date_format(Image.date_obs, '%Y-%m-%d %H:%I:%S').label('date_obs'),
                                  Observation.name.label('observation'), Telescope.name.label('telescope'))

            # apply filters
            query = self._filter_images(query,
                                        filename=filename, image_type=image_type, task=task, observation=observation,
                                        reduction_level=reduction_level, date_start=date_start, date_end=date_end,
                                        telescope=telescope, instrument=instrument, binning=binning, filter=filter,
                                        exp_time=exp_time, target_name=target_name, coordinates=coordinates,
                                        search_radius=search_radius)

            # order
            if not hasattr(Image, order_by):
                order_by = 'filename'
            if order_asc:
                query = query.order_by(getattr(Image, order_by).asc())
            else:
                query = query.order_by(getattr(Image, order_by).desc())

            # offset and limit
            query = query.offset(offset).limit(limit)

            # get all images
            images = query.all()

            # details or no details?
            if include_details:
                return [dict(zip(row.keys(), row)) for row in query.all()]
            else:
                return [o.filename for o in images]

    def get_telescopes(self, *args, **kwargs) -> list:
        """Returns the list of telescopes in the database.

        Returns:
            List of telescope names.
        """
        # open a session
        with session_context() as session:
            # base query
            query = session.query(Telescope.name).order_by(Telescope.id.asc())

            # return them
            return [t[0] for t in query.all()]

    def get_instruments(self, *args, **kwargs) -> list:
        """Returns the list of instruments in the database.

        Returns:
            List of instrument names.
        """
        # open a session
        with session_context() as session:
            # base query
            query = session.query(Instrument.name).order_by(Instrument.id.asc())

            # return them
            return [i[0] for i in query.all()]


__all__ = ['ImageDB']
