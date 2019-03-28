import datetime
import logging
import math
import threading
from typing import Union, Tuple
import numpy as np
from astropy.io import fits
from pyobs.utils.time import Time
from pyobs.utils.fits import format_filename

from pyobs import PyObsModule
from pyobs.events import BadWeatherEvent, NewImageEvent, ExposureStatusChangedEvent
from pyobs.interfaces import ICamera, IFitsHeaderProvider, IAbortable
from pyobs.modules import timeout
from pyobs.utils.threads import ThreadWithReturnValue

log = logging.getLogger(__name__)


class CameraException(Exception):
    pass


class BaseCamera(PyObsModule, ICamera, IAbortable):
    def __init__(self, fits_headers: dict = None, centre: Tuple[float, float] = None, rotation: float = None,
                 filenames: str = '/cache/pyobs_{DATE-OBS|date}T{DATE-OBS|time}{IMAGETYP}.fits.gz', *args, **kwargs):
        """Creates a new BaseCamera.

        Args:
            fits_headers: Additional FITS headers.
            centre: (x, y) tuple of camera centre.
            rotation: Rotation east of north.
            filenames: Template for file naming.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # check
        if self.comm is None:
            log.warning('No comm module given, will not be able to signal new images!')

        # store
        self._fits_headers = fits_headers if fits_headers is not None else {}
        if 'OBSERVER' not in self._fits_headers:
            self._fits_headers['OBSERVER'] = ['pyobs', 'Name of observer']
        self._centre = centre
        self._rotation = rotation
        self._filenames = filenames

        # init camera
        self._last_image = None
        self._exposure = None
        self._camera_status = ICamera.ExposureStatus.IDLE
        self._exposures_left = 0

        # multi-threading
        self._expose_lock = threading.Lock()
        self.expose_abort = threading.Event()

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(NewImageEvent)
            self.comm.register_event(ExposureStatusChangedEvent)
            self.comm.register_event(BadWeatherEvent, self._on_bad_weather)

    def _change_exposure_status(self, status: ICamera.ExposureStatus):
        """Change exposure status and send event,

        Args:
            status: New exposure status.
        """

        # send event, if it changed
        if self._camera_status != status:
            self.comm.send_event(ExposureStatusChangedEvent(self._camera_status, status))

        # set it
        self._camera_status = status

    def get_exposure_status(self, *args, **kwargs) -> ICamera.ExposureStatus:
        """Returns the current status of the camera, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of camera.
        """
        return self._camera_status

    def get_exposure_time_left(self, *args, **kwargs) -> float:
        """Returns the remaining exposure time on the current exposure in ms.

        Returns:
            Remaining exposure time in ms.
        """

        # if we're not exposing, there is nothing left
        if self._exposure is None:
            return 0.

        # calculate difference between start of exposure and now, and return in ms
        diff = self._exposure[0] + datetime.timedelta(milliseconds=self._exposure[1]) - datetime.datetime.utcnow()
        return int(diff.total_seconds() * 1000)

    def get_exposures_left(self, *args, **kwargs) -> int:
        """Returns the remaining exposures.

        Returns:
            Remaining exposures
        """
        return self._exposures_left

    def get_exposure_progress(self, *args, **kwargs) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """

        # if we're not exposing, there is no progress
        if self._exposure is None:
            return 0.

        # calculate difference between start of exposure and now
        diff = datetime.datetime.utcnow() - self._exposure[0]

        # zero exposure time?
        if self._exposure[1] == 0. or self._camera_status == ICamera.ExposureStatus.READOUT:
            return 100.
        else:
            # return max of 100
            percentage = (diff.total_seconds() * 1000. / self._exposure[1]) * 100.
            return min(percentage, 100.)

    def _add_fits_headers(self, hdr: fits.Header):
        """Add FITS header keywords to the given FITS header.

        Args:
            hdr: FITS header to add keywords to.
        """

        # convenience function to return value of keyword
        def v(k):
            return hdr[k][0] if isinstance(k, list) or isinstance(k, tuple) else hdr[k]

        # we definitely need a DATE-OBS and IMAGETYP!!
        if 'DATE-OBS' not in hdr:
            log.warning('No DATE-OBS found in FITS header, adding NO further information!')
            return
        if 'IMAGETYP' not in hdr:
            log.warning('No IMAGETYP found in FITS header, adding NO further information!')
            return

        # get date obs
        date_obs = Time(hdr['DATE-OBS'])

        # basic stuff
        hdr['EQUINOX'] = (2000., 'Equinox of celestial coordinate system')

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

        # do we have a location?
        if self.environment and self.environment.location:
            loc = self.environment.location
            # add location of telescope
            hdr['LONGITUD'] = (loc.lon.degree, 'Longitude of the telescope [deg E]')
            hdr['LATITUDE'] = (loc.lat.degree, 'Latitude of the telescope [deg N]')

            # add local sidereal time
            # TODO: takes too long, try something different?
            # hdr['LST'] = (self.environment.lst(date_obs).to_string(unit=u.hour, sep=':'))

        # day of observation start
        if self.environment:
            hdr['DAY-OBS'] = self.environment.night_obs(date_obs).strftime('%Y-%m-%d')

        # only add all this stuff for OBJECT images
        if hdr['IMAGETYP'] in ['object', 'light']:
            # projection
            hdr['CTYPE1'] = ('RA---TAN', 'RA in tangent plane projection')
            hdr['CTYPE2'] = ('DEC--TAN', 'Dec in tangent plane projection')

            # centre pixel
            if self._centre is not None:
                hdr['DET-CPX1'] = (self._centre['x'], 'x-pixel on mechanical axis in unbinned image')
                hdr['DET-CPX2'] = (self._centre['y'], 'y-pixel on mechanical axis in unbinned image')
            else:
                log.warning('Could not calculate DET-CPX1/DET-CPX2 (centre not given in config).')

            # reference pixel in binned image
            if 'XORGSUBF' in hdr and 'YORGSUBF' in hdr and 'DET-CPX1' in hdr and 'DET-BIN1' in hdr \
                    and 'DET-CPX2' in hdr and 'DET-BIN2' in hdr:
                # offset?
                off_x = v('XORGSUBF') if 'XORGSUBF' in hdr else 0.
                off_y = v('YORGSUBF') if 'YORGSUBF' in hdr else 0.
                hdr['CRPIX1'] = ((v('DET-CPX1') - off_x) / v('DET-BIN1'), 'Reference x-pixel position in binned image')
                hdr['CRPIX2'] = ((v('DET-CPX2') - off_y) / v('DET-BIN2'), 'Reference y-pixel position in binned image')
            else:
                log.warning('Could not calculate CRPIX1/CRPIX2 '
                                '(XORGSUBF/YORGSUBF/DET-CPX1/TEL-CPX2/DET-BIN1/DET-BIN2) missing.')

            # PC matrix: rotation only, shift comes from CDELT1/2
            if self._rotation is not None:
                theta_rad = math.radians(self._rotation)
                cos_theta = math.cos(theta_rad)
                sin_theta = math.sin(theta_rad)
                hdr['PC1_1'] = (+cos_theta, 'Partial of first axis coordinate w.r.t. x')
                hdr['PC1_2'] = (-sin_theta, 'Partial of first axis coordinate w.r.t. y')
                hdr['PC2_1'] = (+sin_theta, 'Partial of second axis coordinate w.r.t. x')
                hdr['PC2_2'] = (+cos_theta, 'Partial of second axis coordinate w.r.t. y')
            else:
                log.warning('Could not calculate CD matrix (rotation or CDELT1/CDELT2 missing.')

    def _fetch_fits_headers(self, client: IFitsHeaderProvider) -> dict:
        """Fetch FITS headers from a given IFitsHeaderProvider.

        Args:
            client: A IFitsHeaderProvider to fetch headers from.

        Returns:
            New FITS header keywords.
        """
        return self.comm.execute(client, 'get_fits_headers')

    def _expose(self, exposure_time: int, open_shutter: bool, abort_event: threading.Event) -> fits.PrimaryHDU:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            exposure_time: The requested exposure time in ms.
            open_shutter: Whether or not to open the shutter.
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image.

        Raises:
            ValueError: If exposure was not successful.
        """
        raise NotImplementedError

    def __expose(self, exposure_time: int, image_type: ICamera.ImageType, broadcast: bool) -> (fits.PrimaryHDU, str):
        """Wrapper for a single exposure.

        Args:
            exposure_time: The requested exposure time in ms.
            open_shutter: Whether or not to open the shutter.
            broadcast: Whether or not the new image should be broadcasted.

        Returns:
            Tuple of the image itself and its filename.

        Raises:
            ValueError: If exposure was not successful.
        """
        if self.comm:
            # get clients that provide fits headers
            clients = self.comm.clients_with_interface(IFitsHeaderProvider)

            # create and run a threads in which the fits headers are fetched
            fits_header_threads = {}
            for client in clients:
                log.info('Requesting FITS headers from %s...', client)
                thread = ThreadWithReturnValue(target=self._fetch_fits_headers, args=(client,), name='headers_' + client)
                thread.start()
                fits_header_threads[client] = thread

        # open the shutter?
        open_shutter = image_type in [ICamera.ImageType.OBJECT, ICamera.ImageType.FLAT]

        # do the exposure
        self._exposure = (datetime.datetime.utcnow(), exposure_time)
        try:
            hdu = self._expose(exposure_time, open_shutter, abort_event=self.expose_abort)
        finally:
            # exposure was not successful (aborted?), so reset everything
            self._exposure = None

        # add image type
        hdu.header['IMAGETYP'] = image_type.value

        # add static fits headers
        for key, value in self._fits_headers.items():
            hdu.header[key] = tuple(value)

        # add more fits headers
        log.info("Adding FITS headers...")
        self._add_fits_headers(hdu.header)

        # get fits headers from other clients
        for client, thread in fits_header_threads.items():
            # join thread
            log.info('Fetching FITS headers from %s...', client)
            headers = thread.join(10)

            # still alive?
            if thread.is_alive():
                log.error('Could not receive fits headers from %s.' % client)

            # add them to fits file
            if headers:
                log.info('Adding additional FITS headers from %s...' % client)
                for key, value in headers.items():
                    # if value is not a string, it may be a list of value and comment
                    if type(value) is list:
                        # convert list to tuple
                        hdu.header[key] = tuple(value)
                    else:
                        hdu.header[key] = value

        # don't want to save?
        if self._filenames is None:
            return hdu, None

        # create a temporary filename
        filename = format_filename(hdu.header, self._filenames, self.environment)
        if filename is None:
            raise ValueError('Cannot save image.')

        # upload file
        try:
            with self.open_file(filename, 'wb') as cache:
                log.info('Uploading image to file server...')
                hdu.writeto(cache)
        except FileNotFoundError:
            raise ValueError('Could not upload image.')

        # broadcast image path
        if broadcast and self.comm:
            log.info('Broadcasting image ID...')
            self.comm.send_event(NewImageEvent(filename))

        # store new last image
        self._last_image = {'filename': filename, 'fits': hdu}

        # return image and unique
        self._exposure = None
        log.info('Finished image %s.', filename)
        return hdu, filename

    @timeout('(exposure_time+10000)*count')
    def expose(self, exposure_time: int, image_type: ICamera.ImageType, count: int = 1, broadcast: bool = True,
               *args, **kwargs) -> list:
        """Starts exposure and returns reference to image.

        Args:
            exposure_time: Exposure time in seconds.
            image_type: Type of image.
            count: Number of images to take.
            broadcast: Broadcast existence of image.

        Returns:
            List of references to the image that was taken.
        """

        # acquire lock
        log.info('Acquiring exclusive lock on camera...')
        if not self._expose_lock.acquire(blocking=False):
            raise ValueError('Could not acquire camera lock for expose().')

        # make sure that we release the lock
        try:
            # are we exposing?
            if self._camera_status != ICamera.ExposureStatus.IDLE:
                raise CameraException('Cannot start new exposure because camera is not idle.')

            # loop count
            images = []
            self._exposures_left = count
            while self._exposures_left > 0 and not self.expose_abort.is_set():
                if count > 1:
                    log.info('Taking image %d/%d...', count-self._exposures_left+1, count)

                # expose
                hdu, filename = self.__expose(exposure_time, image_type, broadcast)
                if hdu is None:
                    log.error('Could not take image.')
                else:
                    if filename is None:
                        log.warning('Image has not been saved, so cannot be retrieved by filename.')
                    else:
                        images.append(filename)

                # finished
                self._exposures_left -= 1

            # return id
            self._exposures_left = 0
            return images

        finally:
            log.info('Releasing exclusive lock on camera...')
            self._expose_lock.release()

    def _abort_exposure(self):
        """Abort the running exposure. Should be implemented by derived class.

        Raises:
            ValueError: If an error occured.
        """
        pass

    def abort(self, *args, **kwargs):
        """Aborts the current exposure and sequence.

        Returns:
            Success or not.
        """

        # set abort event
        log.info('Aborting current image and sequence...')
        self._exposures_left = 0
        self.expose_abort.set()

        # do camera-specific abort
        self._abort_exposure()

        # wait for lock and unset event
        acquired = self._expose_lock.acquire(blocking=True, timeout=5.)
        self.expose_abort.clear()
        if acquired:
            self._expose_lock.release()
        else:
            raise ValueError('Could not abort exposure.')

    def abort_sequence(self, *args, **kwargs):
        """Aborts the current sequence after current exposure.

        Returns:
            Success or not.
        """
        if self._exposures_left > 1:
            log.info('Aborting sequence of images...')
        self._exposures_left = 0

    @staticmethod
    def set_biassec_trimsec(hdr: fits.Header, left: int, top: int, width: int, height: int):
        """Calculates and sets the BIASSEC and TRIMSEC areas.

        Args:
            hdr:    FITS header (in/out)
            left:   left edge of data area
            top:    top edge of data area
            width:  width of data area
            height: height of data area
        """

        # get image area in unbinned coordinates
        img_left = hdr['XORGSUBF']
        img_top = hdr['YORGSUBF']
        img_width = hdr['NAXIS1'] * hdr['XBINNING']
        img_height = hdr['NAXIS2'] * hdr['YBINNING']

        # get intersection
        is_left = max(left, img_left)
        is_right = min(left+width, img_left+img_width)
        is_top = max(top, img_top)
        is_bottom = min(top+height, img_top+img_height)

        # for simplicity we allow prescan/overscan only in one dimension
        if (left < is_left or left+width > is_right) and (top < is_top or top+height > is_bottom):
            log.warning('BIASSEC/TRIMSEC can only be calculated with a prescan/overscan on one axis only.')
            return False

        # comments
        c1 = 'Area containing bias overscan [x1:x2,y1:y2] in binned pixels'
        c2 = 'Area containing actual image [x1:x2,y1:y2] in binned pixels'

        # rectangle empty?
        if is_right <= is_left or is_bottom <= is_top:
            # easy case, all is BIASSEC, no TRIMSEC at all
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (hdr['NAXIS1'], hdr['NAXIS2']), c1)
            return

        # we got a TRIMSEC, calculate its binned and windowd coordinates
        is_left_binned = np.floor((is_left - hdr['XORGSUBF']) / hdr['XBINNING']) + 1
        is_right_binned = np.ceil((is_right - hdr['XORGSUBF']) / hdr['XBINNING'])
        is_top_binned = np.floor((is_top - hdr['YORGSUBF']) / hdr['YBINNING']) + 1
        is_bottom_binned = np.ceil((is_bottom - hdr['YORGSUBF']) / hdr['YBINNING'])

        # set it
        hdr['TRIMSEC'] = ('[%d:%d,%d:%d]' % (is_left_binned, is_right_binned, is_top_binned, is_bottom_binned), c2)

        # now get BIASSEC -- whatever we do, we only take the first one
        # which axis?
        if img_left < left:
            right_binned = np.ceil((is_left - hdr['XORGSUBF']) / hdr['XBINNING'])
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (right_binned, hdr['NAXIS2']), c2)
        elif img_left+img_width > left+width:
            left_binned = np.floor((is_right - hdr['XORGSUBF']) / hdr['XBINNING']) + 1
            hdr['BIASSEC'] = ('[%d:%d,1:%d]' % (left_binned, hdr['NAXIS1'], hdr['NAXIS2']), c2)
        elif img_top < top:
            bottom_binned = np.ceil((is_top - hdr['YORGSUBF']) / hdr['YBINNING'])
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (hdr['NAXIS1'], bottom_binned), c2)
        elif img_top+img_height > top+height:
            top_binned = np.floor((is_bottom - hdr['YORGSUBF']) / hdr['YBINNING']) + 1
            hdr['BIASSEC'] = ('[1:%d,%d:%d]' % (hdr['NAXIS1'], top_binned, hdr['NAXIS2']), c2)

    def _on_bad_weather(self, event: BadWeatherEvent, sender: str, *args, **kwargs):
        """Abort exposure if a bad weather event occurs.

        Args:
            event: The bad weather event.
            sender: Who sent it.
        """
        log.warning('Received bad weather event, shutting down.')
        self.abort()


__all__ = ['BaseCamera', 'CameraException']
