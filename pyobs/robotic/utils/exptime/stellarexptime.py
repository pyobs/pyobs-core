from __future__ import annotations

import logging

import numpy as np
from astropy.modeling import fitting, models

from pyobs.interfaces import ICamera, IExposureTime, IImageType, IWindow
from pyobs.utils.enums import ImageType

from .exptime import ExposureTimeProvider

log = logging.getLogger(__name__)


class StellarExposureTimeProvider(ExposureTimeProvider):
    """Determines exposure time by finding a star near the image centre
    and adjusting the exposure to reach a given peak ADU value.

    Takes a short bias-subtracted test exposure, fits a 2D Gaussian to
    the brightest source within the search radius, and scales the exposure
    time so the fitted peak matches ``target_peak``. Repeats up to
    ``max_iterations`` times until the result converges.
    """

    camera: str
    """Name of the camera module to use."""

    target_peak: float = 30000.0
    """Desired peak ADU value of the star (after bias subtraction)."""

    search_radius: int = 200
    """Search radius in pixels from image centre."""

    max_iterations: int = 3
    """Maximum number of test exposures to take."""

    convergence_threshold: float = 0.05
    """Stop iterating when the estimated peak is within this fraction of target_peak."""

    default_exposure_time: float = 1.0
    """Initial test exposure time and fallback if no star is found."""

    async def __call__(self) -> float:
        """Determine the optimal exposure time.

        Returns:
            Optimal exposure time in seconds.
        """
        camera = await self.comm.proxy(self.camera, ICamera)
        camera_exptime = await self.comm.proxy(self.camera, IExposureTime)
        camera_imagetype = await self.comm.proxy(self.camera, IImageType)
        camera_window = await self.comm.proxy(self.camera, IWindow)

        # store original settings to restore afterward
        orig_exptime = await camera_exptime.get_exposure_time()
        orig_window = await camera_window.get_window()

        exptime = self.default_exposure_time

        try:
            # take bias once before all iterations
            log.info("Taking bias frame...")
            await camera_exptime.set_exposure_time(0.0)
            await camera_imagetype.set_image_type(ImageType.BIAS)
            bias_filename = await camera.grab_data(broadcast=False)
            bias_img = await self.vfs.read_image(bias_filename)

            for iteration in range(self.max_iterations):
                log.info("Iteration %d/%d, exptime=%.2fs", iteration + 1, self.max_iterations, exptime)

                # take test exposure
                log.info("Taking test exposure...")
                await camera_exptime.set_exposure_time(exptime)
                await camera_imagetype.set_image_type(ImageType.OBJECT)
                sci_filename = await camera.grab_data(broadcast=False)
                sci_img = await self.vfs.read_image(sci_filename)

                # subtract bias
                data = sci_img.data.astype(float) - bias_img.data.astype(float)

                # find brightest pixel within search radius of centre
                peak, cx, cy = self._find_star(data)

                if peak is None:
                    log.warning("No star found, keeping exptime=%.2fs", exptime)
                    return exptime

                log.info("Found star at (%d, %d) with peak=%.1f ADU", cx, cy, peak)

                # scale exposure time linearly
                ratio = self.target_peak / peak
                new_exptime = exptime * ratio
                log.info("Scaling exptime %.2fs -> %.2fs (ratio=%.3f)", exptime, new_exptime, ratio)

                exptime = new_exptime

                # check convergence
                if abs(ratio - 1.0) < self.convergence_threshold:
                    log.info("Converged at %.2fs", exptime)
                    break

        finally:
            # restore original settings
            await camera_exptime.set_exposure_time(orig_exptime)
            await camera_window.set_window(*orig_window)
            await camera_imagetype.set_image_type(ImageType.OBJECT)

        return exptime

    def _find_star(self, data: np.ndarray) -> tuple[float | None, int, int]:
        """Find the brightest star near the image centre by fitting a 2D Gaussian.

        Args:
            data: Bias-subtracted image data as 2D numpy array.

        Returns:
            Tuple of (fitted_peak, col, row), or (None, 0, 0) if no star found.
        """
        height, width = data.shape
        cy_centre, cx_centre = height // 2, width // 2

        # crop search region around centre
        y0 = max(0, cy_centre - self.search_radius)
        y1 = min(height, cy_centre + self.search_radius)
        x0 = max(0, cx_centre - self.search_radius)
        x1 = min(width, cx_centre + self.search_radius)
        region = data[y0:y1, x0:x1]

        if region.size == 0:
            return None, 0, 0

        # find peak in region
        flat_idx = np.argmax(region)
        ry, rx = np.unravel_index(flat_idx, region.shape)

        # fit 2D Gaussian around peak
        fit_half = 10
        fy0 = max(0, ry - fit_half)
        fy1 = min(region.shape[0], ry + fit_half)
        fx0 = max(0, rx - fit_half)
        fx1 = min(region.shape[1], rx + fit_half)
        stamp = region[fy0:fy1, fx0:fx1]

        try:
            y_grid, x_grid = np.mgrid[0 : stamp.shape[0], 0 : stamp.shape[1]]
            amplitude = float(np.max(stamp) - np.median(stamp))
            g_init = models.Gaussian2D(
                amplitude=amplitude,
                x_mean=stamp.shape[1] / 2,
                y_mean=stamp.shape[0] / 2,
                x_stddev=2.0,
                y_stddev=2.0,
            )
            fitter = fitting.LevMarLSQFitter()
            g_fit = fitter(g_init, x_grid, y_grid, stamp - np.median(stamp))
            peak = float(g_fit.amplitude) + float(np.median(stamp))
            col: int = int(x0) + int(fx0) + int(g_fit.x_mean)
            row: int = int(y0) + int(fy0) + int(g_fit.y_mean)
        except Exception:
            # fallback to raw peak if fitting fails
            peak = float(np.max(region))
            col = int(x0 + rx)
            row = int(y0 + ry)

        if peak <= 0:
            return None, 0, 0

        return peak, col, row


__all__ = ["StellarExposureTimeProvider"]
