from __future__ import annotations

import glob
import threading
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from typing import Union, Tuple, List
import random
from astropy.wcs import WCS
from astropy.io import fits
from astroquery.gaia import Gaia
from photutils.datasets import make_gaussian_prf_sources_image
from photutils.datasets import make_noise_image

from pyobs.interfaces import IMotion
from pyobs.object import create_object, Object
from pyobs.utils.enums import ImageFormat, MotionStatus
from pyobs.images import Image


class SimTelescope(Object):
    """A simulated telescope on an equitorial mount."""
    def __init__(self, world: SimWorld, position: Tuple[float, float] = None, offsets: Tuple[float, float] = None,
                 pointing_offset: Tuple[float, float] = None, move_accuracy: float = 2.,
                 speed: float = 20., focus: float = 50, filters: List[str] = None, filter: str = 'clear',
                 drift: Tuple[float, float] = None, focal_length: float = 5000., *args, **kwargs):
        """Initializes new telescope.

        Args:
            world: World object.
            position: RA/Dec tuple with position of telescope in degrees.
            offsets: RA/Dec offsets of telescope in arcsecs.
            pointing_offset: Pointing offset in RA/Dec in arcsecs.
            move_accuracy: Accuracy of movements in RA/Dec, i.e. random error after any movement [arcsec].
            speed: Speed of telescope in deg/sec.
            focus: Telescope focus.
            filters: List of filters.
            filter: Current filter.
            drift: RA/Dec drift of telescope in arcsec/sec.
            focal_length: Focal length of telescope in mm.
        """
        Object.__init__(self, *args, **kwargs)

        # store
        self.world = world
        self.status = MotionStatus.IDLE
        self.status_callback = None

        # init
        self._position = SkyCoord(0. * u.deg, 0. * u.deg, frame='icrs') if position is None else \
            SkyCoord(position[0] * u.deg, position[1] * u.deg, frame='icrs')
        self._offsets = (0., 0.) if offsets is None else offsets
        self.pointing_offset = (20., 2.) if pointing_offset is None else pointing_offset
        self.move_accuracy = (1, 1) if move_accuracy is None else move_accuracy
        self.speed = speed     # telescope speed in deg/sec
        self.focus = focus
        self.filters = ['clear', 'B', 'V', 'R'] if filters is None else filters
        self.filter = filter
        self.drift = (0.01, 0.0001) if drift is None else drift     # arcsec/sec in RA/Dec
        self.focal_length = focal_length

        # private stuff
        self._drift = (0., 0.)
        self._dest_coords = None

        # locks
        self._pos_lock = threading.RLock()

        # threads
        self._add_thread_func(self._move_thread)

    @property
    def position(self):
        return self._position

    @property
    def offsets(self):
        return self._offsets

    def _change_motion_status(self, status: MotionStatus):
        """Change the current motion status.

        Args:
            status: New motion status
        """

        # call callback
        if self.status_callback is not None and status != self.status:
            self.status_callback(status)

        # set it
        self.status = status

    @property
    def real_pos(self):
        # calculate offsets
        dra = (self._offsets[0] * u.deg + self._drift[0] * u.arcsec) / np.cos(np.radians(self._position.dec.degree))
        ddec = self._offsets[1] * u.deg + self._drift[1] * u.arcsec

        # return position
        with self._pos_lock:
            return SkyCoord(ra=self._position.ra + dra,
                            dec=self._position.dec + ddec,
                            frame='icrs')

    def move_ra_dec(self, coords):
        """Move telescope to given RA/Dec position.

        Args:
            coords: Destination coordinates.
        """

        # change status
        self._change_motion_status(MotionStatus.SLEWING)

        # calculate random RA/Dec offsets
        acc = self.move_accuracy / 3600.
        ra = random.gauss(coords.ra.degree, acc / np.cos(np.radians(coords.dec.degree))) * u.deg
        dec = random.gauss(coords.dec.degree, acc) * u.deg

        # set coordinates
        self._dest_coords = SkyCoord(ra=ra, dec=dec, frame='icrs')

    def set_offsets(self, dra, ddec):
        """Move RA/Dec offsets.

        Args:
            dra: RA offset [deg]
            ddec: Dec offset [deg]
        """

        # calculate random RA/Dec offsets
        acc = self.move_accuracy / 3600.
        ra, dec = random.gauss(dra, acc), random.gauss(ddec, acc)

        # set offsets
        self._offsets = (ra, dec)

    def _move_thread(self):
        """Move the telescope over time."""

        # run until closed
        while not self.closing.is_set():

            # do we have destination coordinates?
            if self._dest_coords is not None:
                # calculate moving vector
                vra = (self._dest_coords.ra.degree - self._position.ra.degree) * \
                      np.cos(np.radians(self._position.dec.degree))
                vdec = self._dest_coords.dec.degree - self._position.dec.degree

                # get direction
                length = np.sqrt(vra**2 + vdec**2)

                # do we reach target?
                if length < self.speed:
                    # set it
                    with self._pos_lock:
                        # set position and reset destination
                        self._change_motion_status(MotionStatus.TRACKING)
                        self._position = self._dest_coords
                        self._dest_coords = None

                        # set some random drift around the pointing error
                        self._drift = (random.gauss(self.pointing_offset[0], self.pointing_offset[0] / 10.),
                                       random.gauss(self.pointing_offset[1], self.pointing_offset[1] / 10.))

                else:
                    # norm vector and get movement
                    dra = vra / length * self.speed / np.cos(np.radians(self._position.dec.degree)) * u.deg
                    ddec = vdec / length * self.speed * u.deg

                    # apply it
                    with self._pos_lock:
                        self._change_motion_status(MotionStatus.SLEWING)
                        self._position = SkyCoord(ra=self._position.ra + dra,
                                                  dec=self._position.dec + ddec,
                                                  frame='icrs')

            else:
                # no movement, just drift
                # calculate constant drift
                drift_ra = random.gauss(self.drift[0], self.drift[0] / 10.)
                drift_dec = random.gauss(self.drift[1], self.drift[1] / 10.)

                # and apply it
                with self._pos_lock:
                    self._drift = (self._drift[0] + drift_ra, self._drift[1] + drift_dec)

            # sleep a second
            self.closing.wait(1)


class SimCamera(Object):
    """A simulated camera."""
    def __init__(self, world: SimWorld, image_size: Tuple[int, int] = None, pixel_size: float = 0.015,
                 images: str = None, *args, **kwargs):
        """Inits a new camera.

        Args:
            world: World to use.
            image_size: Size of image.
            pixel_size: Square pixel size in mm.
            images: Filename pattern (e.g. /path/to/*.fits) for files to return instead of simulated images.
        """
        Object.__init__(self, *args, **kwargs)

        # store
        self.world = world
        self.telescope = world.telescope
        self.full_frame = tuple([0, 0] + list(image_size)) if image_size is not None else (0, 0, 512, 512)
        self.window = self.full_frame
        self.binning = (1, 1)
        self.pixel_size = pixel_size
        self.image_format = ImageFormat.INT16
        self.images = [] if images is None else sorted(glob.glob(images)) \
            if '*' in images or '?' in images else [images]

        # private stuff
        self._catalog = None
        self._catalog_coords = None

    def get_image(self, exp_time: float, open_shutter: bool) -> Image:
        """Simulate an image.

        Args:
            exp_time: Exposure time in seconds.
            open_shutter: Whether the shutter is opened.

        Returns:
            numpy array with image.
        """

        # get now
        now = Time.now()

        # simulate or what?
        if self.images:
            # take image from list
            filename = self.images.pop(0)
            data = fits.getdata(filename)
            self.images.append(filename)

        else:
            # simulate
            data = self._simulate_image(exp_time, open_shutter)

        # create header
        hdr = self._create_header(exp_time, open_shutter, now, data)

        # return it
        return Image(data, header=hdr)

    def _simulate_image(self, exp_time: float, open_shutter: bool) -> Image:
        """Simulate an image.

        Args:
            exp_time: Exposure time in seconds.
            open_shutter: Whether the shutter is opened.

        Returns:
            numpy array with image.
        """

        # get shape for image
        shape = (int(self.window[3]), int(self.window[2]))

        # create image with Gaussian noise for BIAS
        data = make_noise_image(shape, distribution='gaussian', mean=1e3, stddev=100.)

        # add DARK
        if exp_time > 0:
            data += make_noise_image(shape, distribution='gaussian', mean=exp_time / 1e4, stddev=exp_time / 1e5)

            # add stars and stuff
            if open_shutter:
                # get solar altitude
                sun_alt = self.world.sun_alt

                # get mean flatfield counts
                flat_counts = 30000 / np.exp(-1.28 * (4.209 + sun_alt)) * exp_time

                # create flat
                data += make_noise_image(shape, distribution='gaussian', mean=flat_counts, stddev=flat_counts / 10.)

                # get catalog with sources
                sources = self._get_sources_table(exp_time)

                # create image
                data += make_gaussian_prf_sources_image(shape, sources)

        # saturate
        data[data > 65535] = 65535

        # finished
        return data.astype(np.uint16)

    def _create_header(self, exp_time: float, open_shutter: float, time: Time, data: np.ndarray):
        # create header
        hdr = fits.Header()
        hdr['NAXIS1'] = data.shape[1]
        hdr['NAXIS2'] = data.shape[0]

        # set values
        hdr['DATE-OBS'] = (time.isot, 'Date and time of start of exposure')
        hdr['EXPTIME'] = (exp_time, 'Exposure time [s]')

        # binning
        hdr['XBINNING'] = hdr['DET-BIN1'] = (int(self.binning[0]), 'Binning factor used on X axis')
        hdr['YBINNING'] = hdr['DET-BIN2'] = (int(self.binning[1]), 'Binning factor used on Y axis')

        # window
        hdr['XORGSUBF'] = (int(self.window[0]), 'Subframe origin on X axis')
        hdr['YORGSUBF'] = (int(self.window[1]), 'Subframe origin on Y axis')

        # statistics
        hdr['DATAMIN'] = (float(np.min(data)), 'Minimum data value')
        hdr['DATAMAX'] = (float(np.max(data)), 'Maximum data value')
        hdr['DATAMEAN'] = (float(np.mean(data)), 'Mean data value')

        # hardware
        hdr['TEL-FOCL'] = (self.telescope.focal_length, "Focal length [mm]")
        hdr['DET-PIXL'] = (self.pixel_size, "Size of detector pixels (square) [mm]")

        # finished
        return hdr

    def _get_catalog(self):
        """Returns GAIA catalog for current telescope coordinates."""

        # get catalog
        if self._catalog_coords is None or self._catalog_coords.separation(self.telescope.real_pos) > 10. * u.arcmin:
            self._catalog = Gaia.query_object_async(coordinate=self.telescope.real_pos, radius=1. * u.deg)
        return self._catalog

    def _get_sources_table(self, exp_time: float):
        """Create sources table."""

        # get catalog
        cat = self._get_catalog()

        # calculate cdelt1/2
        tmp = 360. / (2. * np.pi) * self.pixel_size / self.telescope.focal_length
        cdelt1, cdelt2 = tmp * self.binning[0], tmp * self.binning[1]

        # create WCS
        w = WCS(naxis=2)
        w.wcs.crpix = [self.window[3] / 2., self.window[2] / 2.]
        w.wcs.cdelt = np.array([-cdelt1, cdelt2])
        w.wcs.crval = [self.telescope.real_pos.ra.degree, self.telescope.real_pos.dec.degree]
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

        # set fwhm to 2" in pixels
        fwhm = 2. / 3600. / cdelt1

        # convert world to pixel coordinates
        cat['x'], cat['y'] = w.wcs_world2pix(cat['ra'], cat['dec'], 0)

        # get columns
        sources = cat['x', 'y', 'phot_g_mean_flux']
        sources.rename_columns(['x', 'y', 'phot_g_mean_flux'], ['x_0', 'y_0', 'amplitude'])
        sources.add_column([fwhm] * len(sources), name='sigma')
        sources['amplitude'] *= exp_time

        # finished
        return sources


class SimWorld(Object):
    """A simulated world."""

    def __init__(self, time: Union[Time, str] = None,
                 telescope: Union[SimTelescope, dict] = None, camera: Union[SimCamera, dict] = None,
                 *args, **kwargs):
        """Initializes a new simulated world.

        Args:
            time: Time at start of simulation.
            telescope: Telescope to use.
            camera: Camera to use.
            observer: Observer to use.
            *args:
            **kwargs:
        """
        Object.__init__(self, *args, **kwargs)

        # get start time
        if time is None:
            time = Time.now()
        elif isinstance(time, str):
            time = Time(time)

        # calculate time offset
        self.time_offset = time - Time.now()

        # get telescope
        if telescope is None:
            self.telescope = SimTelescope(world=self)
        elif isinstance(telescope, SimTelescope):
            self.telescope = telescope
        elif isinstance(telescope, dict):
            self.telescope = create_object(telescope, world=self)
        else:
            raise ValueError('Invalid telescope.')

        # get camera
        if camera is None:
            self.camera = SimCamera(world=self)
        elif isinstance(camera, SimCamera):
            self.camera = camera
        elif isinstance(camera, dict):
            self.camera = create_object(camera, world=self)
        else:
            raise ValueError('Invalid camera.')

    def open(self):
        """Open module."""
        Object.open(self)

        # open telescope
        if hasattr(self.telescope, 'open'):
            self.telescope.open()

        # open camera
        if hasattr(self.telescope, 'open'):
            self.camera.open()

    def close(self):
        """Close module."""
        Object.close(self)

        # close telescope
        if hasattr(self.telescope, 'close'):
            self.telescope.close()

        # close camera
        if hasattr(self.camera, 'close'):
            self.camera.close()

    @property
    def time(self) -> Time:
        """Returns current time in simulation."""
        return Time.now() + self.time_offset

    @property
    def sun_alt(self) -> float:
        """Returns current solar altitude."""
        return float(self.observer.sun_altaz(self.time).alt.degree)


__all__ = ['SimTelescope', 'SimCamera', 'SimWorld']
