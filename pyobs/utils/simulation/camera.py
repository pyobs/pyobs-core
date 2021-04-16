from __future__ import annotations

import glob
import numpy as np
import astropy.units as u
from astropy.time import Time
from typing import Tuple
from astropy.wcs import WCS
from astropy.io import fits
from photutils.datasets import make_gaussian_prf_sources_image
from photutils.datasets import make_noise_image

from pyobs.object import Object
from pyobs.utils.enums import ImageFormat
from pyobs.images import Image


class SimCamera(Object):
    """A simulated camera."""
    ___module__ = 'pyobs.utils.simulation'

    def __init__(self, world: 'SimWorld', image_size: Tuple[int, int] = None, pixel_size: float = 0.015,
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
        from astroquery.gaia import Gaia

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


__all__ = ['SimCamera']
