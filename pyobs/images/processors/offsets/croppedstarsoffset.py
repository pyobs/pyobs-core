import logging
import numpy as np
from scipy import signal, optimize
from astropy.table import Table, Column

from pyobs.utils.pid import PID
from . import Offsets
from ..photometry import SepPhotometry
from ... import Image

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class CroppedStarsOffset(Offsets):
    """An auto-guiding system based on comparing complete 2D images that are created by finding all clear sources in the image
    and setting the rest of the image to zero."""

    def __init__(
            self,
            max_expected_offset_in_arcsec=4,
            min_required_sources_in_image=1,
            min_pixels_above_threshold_per_source=3,
            *args,
            **kwargs,
    ):
        """Initializes a new auto guiding system."""
        log.info("Initializing CroppedStarsOffset")
        self.max_expected_offset_in_arcsec = max_expected_offset_in_arcsec
        self.max_expected_offset_in_pixels = None
        self.min_pixels_above_threshold_per_source = min_pixels_above_threshold_per_source

        self._ref_cropped_stars_image = None

        self.min_required_sources_in_image = min_required_sources_in_image

        self._pid_ra = None
        self._pid_dec = None

    def reset(self):
        """Resets guiding."""
        log.info("Reset auto-guiding.")
        self._ref_cropped_stars_image = None

    def find_pixel_offset(self, image: Image) -> (float, float):
        """Processes an image and return x/y pixel offset to reference.

        Args:
            image: Image to process.

        Returns:
            x/y pixel offset to reference.

        Raises:
            ValueError if offset could not be found.
        """

        self.max_expected_offset_in_pixels = (
                self.max_expected_offset_in_arcsec / image.pixel_scale
        )
        # no reference image?
        if self._ref_cropped_stars_image is None:
            log.info("Initialising auto-guiding with new image...")

            # initialize reference image
            try:
                self._ref_cropped_stars_image = self.get_cropped_stars_image(image)
            except ValueError as e:
                log.warning(
                    f"Could not initialize reference image info due to exception '{e}'. Resetting..."
                )
                self.reset()
                return None, None

            self._init_pid()
            return 0, 0

        # process it
        log.info("Perform auto-guiding on new image...")
        dx, dy = self.calculate_offset(image)
        return dx, dy

    def get_cropped_stars_image(self, image: Image) -> np.ndarray:
        # extract sources
        sep = SepPhotometry()
        sources = sep.find_stars(image)
        sources = self.convert_from_fits_to_numpy_index_convention(sources)

        sources = self.remove_sources_close_to_border(
            sources,
            image.data.shape,
            min_distance_from_border_in_pixels=self.max_expected_offset_in_pixels,
        )
        sources = self.remove_bad_sources(sources)

        self.check_if_enough_sources_in_image(sources)
        log.info(f"Found {len(sources)} source(s) in image.")

        # build image with stars cut out in circles of radius FWHM_factor_for_radius * FWHM of stars
        cropped_stars_image = np.zeros(image.data.shape)
        FWHM_factor_for_radius = 1.5
        xs = np.arange(image.data.shape[0])
        ys = np.arange(image.data.shape[1])
        X, Y = np.meshgrid(ys, xs)
        for source in sources:
            radius2 = (FWHM_factor_for_radius * source["fwhm"]) ** 2
            within_radius_mask = (X - source["x"]) ** 2 + (
                    Y - source["y"]
            ) ** 2 < radius2
            cropped_stars_image[within_radius_mask] = (
                    image.data[within_radius_mask] - source["background"]
            )

        cropped_stars_image[cropped_stars_image <= 0] = 0

        return cropped_stars_image

    @staticmethod
    def convert_from_fits_to_numpy_index_convention(sources: Table) -> Table:
        sources["x"] -= 1
        sources["y"] -= 1
        sources["xmin"] -= 1
        sources["xmax"] -= 1
        sources["ymin"] -= 1
        sources["ymax"] -= 1
        sources["xpeak"] -= 1
        sources["ypeak"] -= 1
        return sources

    def remove_sources_close_to_border(self, sources: Table, image_shape: tuple,
                                       min_distance_from_border_in_pixels) -> Table:
        """Remove table rows from sources when closer than min_distance_from_border_in_pixels from border of image."""
        width, height = image_shape

        def min_distance_from_border(source):
            # minimum across x and y of distances to border
            return np.min(
                np.array(
                    (
                        (width / 2 - np.abs(source["y"] - width / 2)),
                        (height / 2 - np.abs(source["x"] - height / 2)),
                    )
                ),
                axis=0,
            )

        sources.add_column(
            Column(
                name="min_distance_from_border",
                data=min_distance_from_border(sources),
            )
        )
        sources.sort("min_distance_from_border")

        sources_result = sources[
            np.where(
                sources["min_distance_from_border"]
                > min_distance_from_border_in_pixels * 2
            )
        ]
        return sources_result

    def remove_bad_sources(self, sources: Table, MAX_ELLIPTICITY=0.4,
                           MIN_FACTOR_ABOVE_LOCAL_BACKGROUND: float = 1.5) -> Table:

        # remove small sources
        sources = sources[np.where(sources['tnpix'] >= self.min_pixels_above_threshold_per_source)]

        # remove large sources
        tnpix_median = np.median(sources["tnpix"])
        tnpix_std = np.std(sources["tnpix"])
        sources = sources[
            np.where(
                sources["tnpix"] <= tnpix_median + 2 * tnpix_std,
            )
        ]

        # remove highly elliptic sources
        sources.sort("ellipticity")
        sources = sources[np.where(sources["ellipticity"] <= MAX_ELLIPTICITY)]

        # remove saturated
        sources = sources[np.where(sources["peak"] + sources["background"] < 6e5)]

        # remove sources with background <= 0
        sources = sources[np.where(sources["background"] > 0)]
        # remove sources with low contrast to background
        sources = sources[
            np.where(
                (sources["peak"] + sources["background"]) / sources["background"]
                > MIN_FACTOR_ABOVE_LOCAL_BACKGROUND
            )
        ]
        return sources

    def check_if_enough_sources_in_image(self, sources: Table, N_stars=0):
        n_required_sources = max(self.min_required_sources_in_image, N_stars)
        if len(sources) < n_required_sources:
            raise ValueError(
                f"Only {len(sources)} source(s) in image, but at least {n_required_sources} required."
            )

    def calculate_offset(self,current_image: Image) -> tuple:
        # create images cropped around stars
        current_cropped_star_image = self.get_cropped_stars_image(current_image)
        try:
            corr = self.calculate_correlation(
                current_cropped_star_image,
                self._ref_cropped_stars_image,
                max_expected_offset=self.max_expected_offset_in_pixels,
            )

            offset = self.calculate_offset_from_2d_correlation(corr)
        except Exception as e:
            log.warning(str(e))
            return None, None

        return offset

    @staticmethod
    def gauss2d(x, a, b, x0, y0, sigma_x, sigma_y):
        return a + b * np.exp(
            -((x[0] - x0) ** 2) / (2 * sigma_x ** 2)
            - (x[1] - y0) ** 2 / (2 * sigma_y ** 2)
        )

    def calculate_correlation(self, im1: np.ndarray, im2: np.ndarray, max_expected_offset) -> np.ndarray:

        # maximal expected offsets to be tried.
        # (if-condition so that max_expected_offset is included in the last offset to be tried)
        max_expected_offsets = [
            offset for offset in [4, 8, 16, 32] if offset / 2 <= max_expected_offset
        ]

        for max_expected_offset in max_expected_offsets:
            # multiply by four to have space for fit on all sides
            # add one because correlation has central pixel, which corresponds to no shift
            correlation_size = int(4 * max_expected_offset) + 1
            padding_size = correlation_size // 2

            cropped_im1, cropped_im2 = (
                im1,
                im2,
            )  # self.crop_images_to_enforce_time_limit(im1, im2, correlation_size)

            # pad with zeros to allow use of 'valid' mode in correlation
            cropped_im1_padded = self.pad_with_zeros(cropped_im1, padding_size)

            corr = signal.correlate2d(cropped_im1_padded, cropped_im2, mode="valid")
            try:
                self.check_if_correlation_max_is_close_to_border(corr)
                break  # if max is contained
            except:
                # try next max_expected_offset
                pass
        else:  # nobreak
            # non of the max_expected_offsets passed the check_if_correlation_max_is_close_to_border()
            raise Exception(
                f"Maximum of correlation not properly identified within "
                f"max_expected_offset = {max_expected_offsets[-1]}."
            )

        log.info(
            f"Calculated correlation with max_expected_offset = {max_expected_offset}."
        )
        return corr

    def crop_images_to_enforce_time_limit(self, cropped_im1: np.ndarray, cropped_im2: np.ndarray,
                                          correlation_size: int) -> (np.ndarray, np.ndarray):
        """Calculate cropping of images to allow calculation of correlation in less than max_allowed_time"""

        max_allowed_time = 1  # TODO: find optimal value
        multiplications_per_sec = (
                140 ** 4
        )  # TODO: find out for machine where this will be running on

        corr_pixels = correlation_size ** 2
        image_pixels = np.prod(np.array(cropped_im1.shape))
        expected_time = image_pixels * corr_pixels / multiplications_per_sec

        if expected_time > max_allowed_time:
            over_time_ratio = expected_time / max_allowed_time
            reduce_factor = 1 - 1 / np.sqrt(over_time_ratio)

            reduce_image_width_by_pixels = (
                    int(reduce_factor * (cropped_im1.shape[0])) // 2 * 2
            )  # make even
            reduce_image_height_by_pixels = (
                    int(reduce_factor * (cropped_im1.shape[1])) // 2 * 2
            )  # make even

            cropped_im1 = cropped_im1[
                          reduce_image_width_by_pixels // 2: -reduce_image_width_by_pixels // 2,
                          reduce_image_height_by_pixels
                          // 2: -reduce_image_height_by_pixels
                                // 2,
                          ]
            log.info(
                f"Cropping images from {cropped_im2.shape} to {cropped_im1.shape} to enforce time limit on correlation."
            )
            cropped_im2 = cropped_im2[
                          reduce_image_width_by_pixels // 2: -reduce_image_width_by_pixels // 2,
                          reduce_image_height_by_pixels
                          // 2: -reduce_image_height_by_pixels
                                // 2,
                          ]

        return cropped_im1, cropped_im2

    def pad_with_zeros(sellf, cropped_im1: np.ndarray, padding_size: int) -> np.ndarray:
        cropped_im1_padded = np.zeros(
            (
                cropped_im1.shape[0] + 2 * padding_size,
                cropped_im1.shape[1] + 2 * padding_size,
            )
        )
        cropped_im1_padded[
        padding_size:-padding_size, padding_size:-padding_size
        ] = cropped_im1
        return cropped_im1_padded

    def calculate_offset_from_2d_correlation(self, corr):
        """Fit 2d correlation data with a 2d gaussian + constant offset.
        raise CorrelationMaxCloseToBorderError if the correlation maximum is not well separated from border."""
        # calc positions corresponding to the values in the correlation
        xs = np.arange(-corr.shape[0] / 2, corr.shape[0] / 2) + 0.5
        ys = np.arange(-corr.shape[1] / 2, corr.shape[1] / 2) + 0.5
        X, Y = np.meshgrid(xs, ys)

        # format data as needed by R^2 -> R curve_fit
        xdata = np.vstack((X.ravel(), Y.ravel()))
        ydata = corr.ravel()

        # initial parameter values
        a = np.min(corr)
        b = np.max(corr) - a
        # use max pixel as initial value for x0, y0
        max_index = np.array(np.unravel_index(np.argmax(corr), corr.shape))
        x0, y0 = X[tuple(max_index)], Y[tuple(max_index)]
        self.check_if_correlation_max_is_close_to_border(corr)

        # estimate width of correlation peak as radius of area with values above half maximum
        half_max = np.max(corr - a) / 2 + a
        greater_than_half_max_area = np.sum(corr >= half_max)
        sigma_x = np.sqrt(greater_than_half_max_area / np.pi)
        sigma_y = sigma_x

        # initial values for fit
        p0 = [a, b, x0, y0, sigma_x, sigma_y]
        bounds = (
            [a - 1, -np.inf, x0 - 2 * sigma_x, y0 - 2 * sigma_y, 1e-3, 1e-3],
            [a + 1, np.inf, x0 + 2 * sigma_x, y0 + 2 * sigma_y, corr.shape[0], corr.shape[1]],
        )

        # restrict part of correlation that is going to be used for fit
        # only use data that clearly belong to peak to avoid border effects
        mask_value_above_background = ydata > 0  # a + .1*b
        mask_circle_around_peak = (X.ravel() - x0) ** 2 + (Y.ravel() - y0) ** 2 < (
                (2 * sigma_x) ** 2 + (2 * sigma_y) ** 2
        )
        mask = np.logical_and(mask_value_above_background, mask_circle_around_peak)
        ydata_restricted = ydata[mask]
        xdata_restricted = xdata[:, mask]

        try:
            popt, pcov = optimize.curve_fit(
                self.gauss2d,
                xdata_restricted,
                ydata_restricted,
                p0,
                bounds=bounds,
                maxfev=int(1e5),
                ftol=1e-12,
                # verbose=2
            )
        except Exception as e:
            # if fit fails return max pixel
            log.info(e)
            log.info("Returning pixel position with maximal value in correlation.")
            offset = np.unravel_index(np.argmax(corr), corr.shape)
            return offset

        return (popt[2], popt[3])

    def check_if_correlation_max_is_close_to_border(self, corr):
        corr_size = corr.shape[0]

        xs = np.arange(-corr.shape[0] / 2, corr.shape[0] / 2) + 0.5
        ys = np.arange(-corr.shape[1] / 2, corr.shape[1] / 2) + 0.5

        X, Y = np.meshgrid(xs, ys)

        max_index = np.array(np.unravel_index(np.argmax(corr), corr.shape))
        x0, y0 = X[tuple(max_index)], Y[tuple(max_index)]

        if (
                x0 < -corr_size / 4
                or x0 > corr_size / 4
                or y0 < -corr_size / 4
                or y0 > corr_size / 4
        ):
            raise CorrelationMaxCloseToBorderError(
                "Maximum of correlation is outside center half of axes. "
                "This means that either the given image data is bad, or the offset is larger than expected."
            )

    def _init_pid(self):
        # init pids
        Kp = 0.2
        Ki = 0.16
        Kd = 0.83

        # reset
        self._pid_ra = PID(Kp, Ki, Kd)
        self._pid_dec = PID(Kp, Ki, Kd)


__all__ = ["CroppedStarsOffset"]
