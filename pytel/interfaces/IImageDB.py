"""
------------------------------------------------------------------------------------------------------------------------
                                                             __         __
                                              ____   __  __ / /_ ___   / /
                                             / __ \ / / / // __// _ \ / /
                                            / /_/ // /_/ // /_ /  __// /
                                           / .___/ \__, / \__/ \___//_/
                                          /_/     /____/

                                  pytel - A Python package for robotic telescopes.

------------------------------------------------------------------------------------------------------------------------

Interface for a long-term image archival solution.


Copyright:
    Tim-Oliver Husser <thusser@uni-goettingen.de>


Changelog:
    2017-06-01  Started documentation

"""

from enum import Enum
from astropy.coordinates import SkyCoord, Angle
#from astropy.time import Time, TimeDelta
from pytel.utils.time import Time
from astropy.time import TimeDelta

from .interface import *


class IImageDB(Interface):
    class ImageType(Enum):
        BIAS = 'bias'
        DARK = 'dark'
        FLAT = 'flat'
        OBJECT = 'object'

    class QueryDict(str, Enum):
        BINNING = '$BINNING'
        FILTER = '$FILTER'
        PROGRAM = '$PROGRAM'
        TARGET = '$TARGET'
        USER = '$USER'

        @classmethod
        def has_value(cls, value):
            return any(value == item.value for item in cls)

    class IImageDBError(Exception):
        pass

    def add_image(self, filename: str, *args, **kwargs) ->str:
        """Add a new image to the database.

        Args:
            filename (str): Filename at file cache of new image.

        Returns:
            (str) Archive filename

        Raises:
            FileNotFoundError: If file could not be found.
        """
        raise NotImplementedError

    def get_image_headers(self, filename: str, *args, **kwargs) -> list:
        """Returns a list of (keyword, value, comment) tuples containing FITS headers of given image.

        Args:
            filename (str): Name of file.

        Returns:
            list: List of (keyword value, comment) tuples containing FITS headers of given image.
        """
        raise NotImplementedError

    def count_observations(self, name: str = None, telescope: str = None, instrument: str = None,
                           night_start: str = None, night_end: str = None,
                           task: str = None, user: str = None, *args, **kwargs) -> int:
        """Returns the number of observations that match the given criteria.

        Args:
            name (str): Name of observation.
            telescope (str): Name of telescope.
            instrument (str): Name of instrument.
            night_start (str): Only return observations in or after this night
            night_end (str): Only return observations in or before this night
            task (str): Only observations for the given task
            user (str) Only observations for the given user

        Returns:
            (int) Number of observations that match the criteria
        """
        raise NotImplementedError
    
    def find_observations(self, name: str = None, telescope: str = None, instrument: str = None,
                          night_start: str = None, night_end: str = None,
                          task: str = None, user: str = None,
                          offset: int = 0, limit: int = 100, order_by: str = 'name', order_asc: bool = True,
                          include_details: bool = False, *args, **kwargs) -> list:
        """Returns a list of observations that match the given criteria.

        Args:
            name (str): Name of observation.
            telescope (str): Name of telescope.
            instrument (str): Name of instrument.
            night_start (str): Only return observations in or after this night
            night_end (str): Only return observations in or before this night
            task (str): Only observations for the given task
            user (str) Only observations for the given user
            offset (int): Return observations with this number and following
            limit (int): Only return up to this number of observations.
            order_by (str): Column to sort by.
            order_asc (bool): Sort in ascending order.
            include_details (str): Return full details for each observation

        Returns:
            (list) List of observation names or full details
        """
        raise NotImplementedError

    def count_images(self, filename: str = None, image_type: str = None, task: str = None, observation: str = None,
                     reduction_level: int = None, date_start: str = None, date_end: str = None,
                     telescope: str = None, instrument: str = None, binning: str = None, filter: str = None,
                     exp_time: float = None, target_name: str = None, coordinates: str = None,
                     search_radius: float = None, *args, **kwargs) -> int:
        """Returns the number of images that match the given criteria.

        Args:
            filename (str): Filename of image
            image_type (str): Type of image
            task (str): Name of task
            observation (str): Observation to return images for
            reduction_level (int): Status of reduction
            date_start (str): Only return observations after this datetime
            date_end (str): Only return observations before this datetime
            telescope (str): Name of telescope
            instrument (str): Name of instrument
            binning (str): Image binning
            filter (str): Filter used
            exp_time (float): Exposure time
            target_name (str): Name of target
            coordinates (str): RA & Dec coordinated
            search_radius (float): Radius for cone search

        Returns:
            (int) Number of images that match the criteria
        """
        raise NotImplementedError

    def find_images(self, filename: str = None, image_type: str = None, task: str = None, observation: str = None,
                    reduction_level: int = None, date_start: str = None, date_end: str = None,
                    telescope: str = None, instrument: str = None, binning: str = None, filter: str = None,
                    exp_time: float = None, target_name: str = None, coordinates: str = None,
                    search_radius: float = None,
                    offset: int = 0, limit: int = 100, order_by: str = 'name', order_asc: bool = True,
                    include_details: bool = False, *args, **kwargs) -> list:
        """Returns a list of images that match the given criteria.

        Args:
            filename (str): Filename of image
            image_type (str): Type of image
            task (str): Name of task
            observation (str): Observation to return images for
            reduction_level (int): Status of reduction
            date_start (str): Only return observations after this datetime
            date_end (str): Only return observations before this datetime
            telescope (str): Name of telescope
            instrument (str): Name of instrument
            binning (str): Image binning
            filter (str): Filter used
            exp_time (float): Exposure time
            target_name (str): Name of target
            coordinates (str): RA & Dec coordinated
            search_radius (float): Radius for cone search
            offset (int): Return images with this number and following
            limit (int): Only return up to this number of images.
            order_by (str): Column to sort by.
            order_asc (bool): Sort in ascending order.
            include_details (str): Return full details for each image.

        Returns:
            (list) List of image names or full details
        """
        raise NotImplementedError

    def get_telescopes(self, *args, **kwargs) -> list:
        """Returns the list of telescopes in the database.

        Returns:
            (list) List of telescope names.
        """
        raise NotImplementedError

    def get_instruments(self, *args, **kwargs) -> list:
        """Returns the list of instruments in the database.

        Returns:
            (list) List of instrument names.
        """
        raise NotImplementedError


__all__ = ['IImageDB']
