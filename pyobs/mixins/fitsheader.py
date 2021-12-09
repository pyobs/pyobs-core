from __future__ import annotations
import logging
import math
import os
from collections import Coroutine
from typing import Union, Dict, Any, Tuple, Optional, List, cast
import astropy.units as u
from astropy.io import fits

from pyobs.comm import TimeoutException, InvocationException, RemoteException
from pyobs.images import Image
from pyobs.interfaces import IFitsHeaderBefore, IFitsHeaderAfter
from pyobs.modules import Module
from pyobs.utils.fits import format_filename
from pyobs.utils.parallel import Future
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FitsHeaderMixin:
    """Helper methods for all modules that implement IImageGrabber."""
    __module__ = 'pyobs.mixins'

    def __init__(self, fits_namespaces: Optional[List[str]] = None, fits_headers: Optional[Dict[str, Any]] = None,
                 filenames: str = '/cache/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits', **kwargs: Any):
        """Initialise the mixin.

        Args:
            fits_namespaces: List of namespaces for FITS headers that this camera should request.
            fits_headers: Additional FITS headers.
            filename: Filename pattern for FITS images.
        """
        module = cast(Module, self)

        # store
        self._fitsheadermixin_fits_namespaces = fits_namespaces
        self._fitsheadermixin_filename_pattern = filenames
        self._fitsheadermixin_fits_headers = fits_headers if fits_headers is not None else {}
        if 'OBSERVER' not in self._fitsheadermixin_fits_headers:
            self._fitsheadermixin_fits_headers['OBSERVER'] = ['pyobs', 'Name of observer']

        # night exposure number
        self._fitsheadermixin_cache = '/pyobs/modules/%s/cache.yaml' % module.name()
        self._fitsheadermixin_frame_num = 0

    async def request_fits_headers(self, before: bool = True) -> Dict[str, Coroutine]:
        """Request FITS headers from other modules.

        Returns:
            Futures from all modules.
        """

        # init
        futures: Dict[str, Coroutine] = {}

        # we can only do this with a comm module
        module = cast(Module, self)
        if module.comm:
            # get clients that provide fits headers
            clients = await module.comm.clients_with_interface(IFitsHeaderBefore if before else IFitsHeaderAfter)

            # create and run a threads in which the fits headers are fetched
            proxy: Union[IFitsHeaderBefore, IFitsHeaderAfter]
            for client in clients:
                log.debug('Requesting FITS headers from %s...', client)
                if before:
                    proxy = await module.proxy(client, IFitsHeaderBefore)
                    futures[client] = proxy.get_fits_header_before(self._fitsheadermixin_fits_namespaces)
                else:
                    proxy = await module.proxy(client, IFitsHeaderAfter)
                    futures[client] = proxy.get_fits_header_after(self._fitsheadermixin_fits_namespaces)

        # finished
        return futures

    async def add_requested_fits_headers(self, image: Union[Image, fits.PrimaryHDU],
                                        futures: Dict[str, Coroutine]) -> None:
        """Add requested FITS headers to header of given image.

        Args:
            image: Image with header to add to.
            futures: Futures to get headers from. 
        """

        # get fits headers from other clients
        for client, future in futures.items():
            # join thread
            log.info('Fetching FITS headers from %s...', client)
            try:
                headers = await future
            except TimeoutException:
                log.warning('Fetching FITS headers from %s timed out.', client)
                continue
            except InvocationException as e:
                log.warning('Could not fetch FITS headers from %s: %s.', client, e.get_message())
                continue
            except RemoteException as e:
                log.warning('Could not fetch FITS headers from %s: %s.', client, e.get_message())
                continue

            # add them to fits file
            if headers:
                log.debug('Adding additional FITS headers from %s...' % client)
                for key, value in headers.items():
                    # if value is not a string, it may be a list of value and comment
                    if isinstance(value, list) and not isinstance(value, str):
                        # convert list to tuple
                        image.header[key] = tuple(value)
                    else:
                        image.header[key] = value

    async def add_fits_headers(self, image: Union[Image, fits.PrimaryHDU]) -> None:
        """Add requested FITS headers to header of given image.

        Args:
            image: Image with header to add to.
        """

        # add HDU name
        image.header['EXTNAME'] = 'SCI'

        # add static fits headers
        for key, value in self._fitsheadermixin_fits_headers.items():
            image.header[key] = tuple(value)

        # add more fits headers
        self._fitsheadermixin_add_fits_headers(image)
        await self._fitsheadermixin_add_framenum(image)

    def _fitsheadermixin_add_fits_headers(self, image: Union[Image, fits.PrimaryHDU]) -> None:
        """Add FITS header keywords to the given FITS header.

        Args:
            image: Image with header to add to.
        """
        module = cast(Module, self)

        # get header
        hdr = image.header

        # we definitely need a DATE-OBS and IMAGETYP!!
        if 'DATE-OBS' not in hdr:
            log.warning('No DATE-OBS found in FITS header, adding NO further information!')
            return

        # get date obs
        date_obs = Time(hdr['DATE-OBS'])

        # UT1-UTC
        hdr['UT1_UTC'] = (float(date_obs.delta_ut1_utc), 'UT1-UTC')

        # basic stuff
        hdr['EQUINOX'] = (2000., 'Equinox of celestial coordinate system')

        # do we have a location?
        if module.location is not None:
            loc = module.location
            # add location of telescope
            hdr['LONGITUD'] = (float(loc.lon.degree), 'Longitude of the telescope [deg E]')
            hdr['LATITUDE'] = (float(loc.lat.degree), 'Latitude of the telescope [deg N]')
            hdr['HEIGHT'] = (float(loc.height.value), 'Altitude of the telescope [m]')

            # add local sidereal time
            if module.observer is not None:
                lst = module.observer.local_sidereal_time(date_obs)
                hdr['LST'] = (lst.to_string(unit=u.hour, sep=':'), 'Local sidereal time')

        # date of night this observation is in
        hdr['DAY-OBS'] = (date_obs.night_obs(module.observer).strftime('%Y-%m-%d'), 'Night of observation')

    async def _fitsheadermixin_add_framenum(self, image: Union[Image, fits.PrimaryHDU]) -> None:
        """Add FRAMENUM keyword to header

        Args:
            image: Image with header to add to.
        """
        module = cast(Module, self)

        # get header
        hdr = image.header

        # get night from header
        night = hdr['DAY-OBS']

        # increase night exp
        self._fitsheadermixin_frame_num += 1

        # do we have a cache?
        if self._fitsheadermixin_cache is not None:
            # try to load it
            try:
                # load cache
                cache = await module.vfs.read_yaml(self._fitsheadermixin_cache)

                # get new number
                if cache is not None and 'framenum' in cache:
                    self._fitsheadermixin_frame_num = cache['framenum'] + 1

                # if nights differ, reset count
                if cache is not None and 'night' in cache and night != cache['night']:
                    self._fitsheadermixin_frame_num = 1

            except (FileNotFoundError, ValueError):
                pass

            # write file
            try:
                await module.vfs.write_yaml({'night': night, 'framenum': self._fitsheadermixin_frame_num},
                                            self._fitsheadermixin_cache)
            except (FileNotFoundError, ValueError):
                log.warning('Could not write camera cache file.')

        # set it
        hdr['FRAMENUM'] = self._fitsheadermixin_frame_num

    def format_filename(self, image: Union[Image, fits.PrimaryHDU]) -> Optional[str]:
        """Format filename according to given pattern and store in header of image.

        Args:
            image: Image with header to add to.
        """

        # no pattern?
        if self._fitsheadermixin_filename_pattern is None:
            return None

        # create a temporary filename
        filename = format_filename(image.header, self._fitsheadermixin_filename_pattern)
        if filename is None: 
            return None
        
        # set it
        image.header['ORIGNAME'] = (os.path.basename(filename), 'The original file name')
        image.header['FNAME'] = (os.path.basename(filename), 'FITS file file name')
        return filename


class ImageFitsHeaderMixin(FitsHeaderMixin):
    """Helper methods for all modules that need FITS headers for an image."""
    __module__ = 'pyobs.mixins'

    def __init__(self, centre: Optional[Tuple[float, float]] = None, rotation: float = 0., **kwargs: Any):
        """Initialise the mixin.

        Args:
            fits_namespaces: List of namespaces for FITS headers that this camera should request.
            fits_headers: Additional FITS headers.
            centre: (x, y) tuple of camera centre.
            rotation: Rotation east of north.
            filename: Filename pattern for FITS images.
        """
        FitsHeaderMixin.__init__(self, **kwargs)

        # store
        self._fitsheadermixin_centre = centre
        self._fitsheadermixin_rotation = rotation

    @property
    def rotation(self) -> float:
        return self._fitsheadermixin_rotation

    @property
    def centre(self) -> Optional[Tuple[float, float]]:
        return self._fitsheadermixin_centre

    def _fitsheadermixin_add_fits_headers(self, image: Union[Image, fits.PrimaryHDU]) -> None:
        """Add FITS header keywords to the given FITS header.

        Args:
            image: Image with header to add to.
        """

        # parent method
        FitsHeaderMixin._fitsheadermixin_add_fits_headers(self, image)

        # get header
        hdr = image.header

        # convenience function to return value of keyword
        def v(k: str) -> Any:
            return hdr[k][0] if isinstance(k, list) or isinstance(k, tuple) else hdr[k]

        # set CRVAL1/2 from RA/Dec
        if 'TEL-RA' in hdr and 'TEL-DEC' in hdr:
            hdr['CRVAL1'] = hdr['TEL-RA']
            hdr['CRVAL2'] = hdr['TEL-DEC']

        # pixel size in world coordinates
        if 'DET-PIXL' in hdr and 'TEL-FOCL' in hdr and 'DET-BIN1' in hdr and 'DET-BIN2' in hdr:
            tmp = 360. / (2. * math.pi) * v('DET-PIXL') / v('TEL-FOCL')
            hdr['CDELT1'] = (-tmp * v('DET-BIN1'), 'Coordinate increment on x-axis [deg/px]')
            hdr['CDELT2'] = (+tmp * v('DET-BIN2'), 'Coordinate increment on y-axis [deg/px]')
            hdr['CUNIT1'] = ('deg', 'Units of CRVAL1, CDELT1')
            hdr['CUNIT2'] = ('deg', 'Units of CRVAL2, CDELT2')
            hdr['WCSAXES'] = (2, 'Number of WCS axes')
        else:
            log.warning('Could not calculate CDELT1/CDELT2 (DET-PIXL/TEL-FOCL/DET-BIN1/DET-BIN2 missing).')

        # centre pixel
        if self._fitsheadermixin_centre is not None:
            hdr['DET-CPX1'] = (self._fitsheadermixin_centre[0], 'x-pixel on mechanical axis in unbinned image')
            hdr['DET-CPX2'] = (self._fitsheadermixin_centre[1], 'y-pixel on mechanical axis in unbinned image')
        else:
            log.warning('Could not calculate DET-CPX1/DET-CPX2 (centre not given in config).')

        # reference pixel in binned image
        if 'DET-CPX1' in hdr and 'DET-BIN1' in hdr and 'DET-CPX2' in hdr and 'DET-BIN2' in hdr:
            # offset?
            off_x, off_y = 0, 0
            if 'XORGSUBF' in hdr and 'YORGSUBF' in hdr:
                off_x = v('XORGSUBF') if 'XORGSUBF' in hdr else 0.
                off_y = v('YORGSUBF') if 'YORGSUBF' in hdr else 0.
            hdr['CRPIX1'] = ((v('DET-CPX1') - off_x) / v('DET-BIN1'), 'Reference x-pixel position in binned image')
            hdr['CRPIX2'] = ((v('DET-CPX2') - off_y) / v('DET-BIN2'), 'Reference y-pixel position in binned image')
        else:
            log.warning('Could not calculate CRPIX1/CRPIX2 '
                            '(XORGSUBF/YORGSUBF/DET-CPX1/TEL-CPX2/DET-BIN1/DET-BIN2) missing.')
        # only add all this stuff for OBJECT images
        if 'IMAGETYP' not in hdr or hdr['IMAGETYP'] not in ['dark', 'bias']:
            # projection
            hdr['CTYPE1'] = ('RA---TAN', 'RA in tangent plane projection')
            hdr['CTYPE2'] = ('DEC--TAN', 'Dec in tangent plane projection')

            # PC matrix: rotation only, shift comes from CDELT1/2
            if self._fitsheadermixin_rotation is not None:
                theta_rad = math.radians(self._fitsheadermixin_rotation)
                cos_theta = math.cos(theta_rad)
                sin_theta = math.sin(theta_rad)
                hdr['PC1_1'] = (+cos_theta, 'Partial of first axis coordinate w.r.t. x')
                hdr['PC1_2'] = (-sin_theta, 'Partial of first axis coordinate w.r.t. y')
                hdr['PC2_1'] = (+sin_theta, 'Partial of second axis coordinate w.r.t. x')
                hdr['PC2_2'] = (+cos_theta, 'Partial of second axis coordinate w.r.t. y')
            else:
                log.warning('Could not calculate CD matrix (rotation or CDELT1/CDELT2 missing.')


class SpectrumFitsHeaderMixin(FitsHeaderMixin):
    """Helper methods for all modules that need FITS headers for an image."""
    __module__ = 'pyobs.mixins'
    pass


__all__ = ['FitsHeaderMixin', 'ImageFitsHeaderMixin', 'SpectrumFitsHeaderMixin']
