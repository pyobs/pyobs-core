import logging
from typing import Tuple, List
import numpy as np
from scipy import signal, optimize
from astropy.nddata import NDData
from astropy.table import Table, Column
import photutils

from pyobs.images import Image
from pyobs.images.processors.detection import SepSourceDetection
from pyobs.images.processors.photometry import SepPhotometry
from . import Offsets
from ..misc.removebackground import RemoveBackground

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class NStarOffsets(Offsets):
    """An auto-guiding system based on comparing 2D images of the surroundings of variable number of stars."""

    def __init__(self, num_stars: int = 10, max_expected_offset_in_arcsec: float = 4.,
                 min_pixels_above_threshold_per_source: int = 3, min_required_sources_in_image: int = 1,
                 *args, **kwargs):
        """Initializes a new auto guiding system.

        Args:
            num_stars: maximum number of stars to use to calculate offset from boxes around them
            max_expected_offset_in_arcsec: the maximal expected offset in arc seconds. Determines the size of boxes
                around stars.
            min_pixels_above_threshold_per_source: minimum required number of pixels above threshold for source to be
                used for offset calculation.
        """
        Offsets.__init__(self, *args, **kwargs)

        # store
        self.num_stars = num_stars
        self.max_expected_offset_in_arcsec = max_expected_offset_in_arcsec
        self.min_pixels_above_threshold_per_source = min_pixels_above_threshold_per_source
        self.min_required_sources_in_image = min_required_sources_in_image
        self.star_box_size = None
        self.ref_boxes = None

    def reset(self):
        """Resets guiding."""
        log.info("Reset auto-guiding.")
        self.ref_boxes = None

    def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        # remove background
        image = RemoveBackground()(image)

        # no reference image?
        if self.ref_boxes is None:
            log.info("Initialising auto-guiding with new image...")
            self.star_box_size = max(
                5,
                self.get_star_box_size_from_max_expected_offset(
                    self.max_expected_offset_in_arcsec, image.pixel_scale
                ),
            )
            log.info(f"Choosing star_box_size={self.star_box_size}")

            # initialize reference image information: dimensions & position of boxes, box images
            try:
                self.ref_boxes = self._create_star_boxes_from_ref_image(image)
            except ValueError as e:
                log.warning(f"Could not initialize reference image info due to exception '{e}'. Resetting...")
                self.reset()
                self.offset = None, None
                return image

            self.offset = 0, 0
            return image

        # process it
        log.info("Perform auto-guiding on new image...")
        self.offset = self.calculate_offset(image)
        return image

    @staticmethod
    def get_star_box_size_from_max_expected_offset(max_expected_offset_in_arcsec, pixel_scale):
        # multiply by 4 to give enough space for fit of correlation around the peak on all sides
        return int(4 * max_expected_offset_in_arcsec / pixel_scale if pixel_scale else 20)

    def _create_star_boxes_from_ref_image(self, image: Image) -> List:
        """Calculate the boxes around self.N_stars best sources in the image.

        Args:
             image: Image to process

        Returns:
            2-tuple with
                list of dimensions of boxes in "numpy" order: [0'th axis min, 0'th axis max, 1st axis min, 1st axis max]
                list of images of those boxes

        Raises:
            ValueError if not at least max(self.min_required_sources_in_image, self.N_stars) in filtered list of sources
        """

        # do photometry and get catalog
        detection = SepSourceDetection()
        photometry = SepPhotometry()
        sources = self.convert_from_fits_to_numpy_index_convention(photometry(detection(image)).catalog)

        # filter sources
        sources = self.remove_sources_close_to_border(
            sources, image.data.shape, self.star_box_size // 2 + 1
        )
        sources = self.remove_bad_sources(sources)
        self.check_if_enough_sources_in_image(sources)
        selected_sources = self.select_top_n_brightest_sources(self.num_stars, sources)

        # extract boxes
        return photutils.psf.extract_stars(NDData(image.data), selected_sources, size=self.star_box_size).all_stars

    @staticmethod
    def convert_from_fits_to_numpy_index_convention(sources: Table) -> Table:
        for k in ['x', 'y', 'xmin', 'xmax', 'ymin', 'ymax', 'xpeak', 'ypeak']:
            if k in sources:
                sources[k] -= 1
        return sources

    @staticmethod
    def remove_sources_close_to_border(sources: Table, image_shape: tuple,
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

        sources.add_column(Column(name="min_distance_from_border", data=min_distance_from_border(sources)))
        sources.sort("min_distance_from_border")

        sources_result = sources[np.where(sources["min_distance_from_border"] > min_distance_from_border_in_pixels)]
        return sources_result

    def remove_bad_sources(self, sources: Table, max_ellipticity=0.4,
                           min_factor_above_local_background: float = 1.5) -> Table:

        # remove small sources
        sources = sources[np.where(sources['tnpix'] >= self.min_pixels_above_threshold_per_source)]

        # remove large sources
        tnpix_median = np.median(sources["tnpix"])
        tnpix_std = np.std(sources["tnpix"])
        sources = sources[np.where(sources["tnpix"] <= tnpix_median + 2 * tnpix_std)]

        # remove highly elliptic sources
        sources.sort("ellipticity")
        sources = sources[np.where(sources["ellipticity"] <= max_ellipticity)]

        # remove sources with background <= 0
        sources = sources[np.where(sources["background"] > 0)]

        # remove sources with low contrast to background
        sources = sources[
            np.where(
                (sources["peak"] + sources["background"]) / sources["background"] > min_factor_above_local_background
            )
        ]
        return sources

    @staticmethod
    def select_top_n_brightest_sources(num_stars: int, sources: Table):
        sources.sort("flux")
        sources.reverse()
        if 0 < num_stars < len(sources):
            sources = sources[:num_stars]
        return sources

    def check_if_enough_sources_in_image(self, sources: Table):
        """Check if enough sources in table.

        Args:
            sources: astropy table of sources to check.

        Returns:
            None

        Raises:
            ValueError if not at least max(self.min_required_sources_in_image, self.N_stars) in sources

        """
        n_required_sources = self.min_required_sources_in_image
        if len(sources) < n_required_sources:
            raise ValueError(f"Only {len(sources)} source(s) in image, but at least {n_required_sources} required.")

    def calculate_offset(self, current_image: Image) -> Tuple:
        print('calc', self.ref_boxes)
        # calculate offset for each star
        offsets = []
        for box in self.ref_boxes:
            # get box dimensions
            box_ymin, box_ymax = box.origin[1], box.origin[1] + box.data.shape[0]
            box_xmin, box_xmax = box.origin[0], box.origin[0] + box.data.shape[1]

            # extract box
            current_boxed_image = current_image.data[box_ymin:box_ymax, box_xmin:box_xmax]

            # correlate
            corr = signal.correlate2d(current_boxed_image, box.data, mode="same", boundary="wrap")

            try:
                offset = self.calculate_offset_from_2d_correlation(corr)
                offsets.append(offset)
            except Exception as e:
                log.info(f"Exception '{e}' caught. Ignoring this star.")
                pass

        if len(offsets) == 0:
            log.info(f"All {self.num_stars} fits on boxed star correlations failed.")
            return None, None
        offsets = np.array(offsets)

        offset = np.mean(offsets[:, 0]), np.mean(offsets[:, 1])

        return offset

    @staticmethod
    def gauss2d(x, a, b, x0, y0, sigma_x, sigma_y):
        return a + b * np.exp(-((x[0] - x0) ** 2) / (2 * sigma_x ** 2) - (x[1] - y0) ** 2 / (2 * sigma_y ** 2))

    def calculate_offset_from_2d_correlation(self, corr) -> Tuple[float, float]:
        """Fit 2d correlation data with a 2d gaussian + constant offset.
        raise CorrelationMaxCloseToBorderError if the correlation maximum is not well separated from border."""
        # calc positions corresponding to the values in the correlation
        xs = np.arange(-corr.shape[0] / 2, corr.shape[0] / 2) + 0.5
        ys = np.arange(-corr.shape[1] / 2, corr.shape[1] / 2) + 0.5
        x, y = np.meshgrid(xs, ys)

        # format data as needed by R^2 -> R curve_fit
        xdata = np.vstack((x.ravel(), y.ravel()))
        ydata = corr.ravel()

        # initial parameter values
        a = np.min(corr)
        b = np.max(corr) - a
        # use max pixel as initial value for x0, y0
        max_index = np.array(np.unravel_index(np.argmax(corr), corr.shape))
        x0, y0 = x[tuple(max_index)], y[tuple(max_index)]
        self.check_if_correlation_max_is_close_to_border(corr)

        # estimate width of correlation peak as radius of area with values above half maximum
        half_max = np.max(corr - a) / 2 + a
        greater_than_half_max_area = np.sum(corr >= half_max)
        sigma_x = np.sqrt(greater_than_half_max_area / np.pi)
        sigma_y = sigma_x

        p0 = [a, b, x0, y0, sigma_x, sigma_y]
        bounds = (
            [-np.inf, -np.inf, x0 - sigma_x, y0 - sigma_y, 0, 0],
            [np.inf, np.inf, x0 + sigma_x, y0 + sigma_y, np.inf, np.inf],
        )
        # only use data that clearly belong to peak to avoid border effects
        mask_value_above_background = ydata > -1e5  # a + .1*b
        mask_circle_around_peak = (x.ravel() - x0) ** 2 + (y.ravel() - y0) ** 2 < 4 * (
                sigma_x ** 2 + sigma_y ** 2
        ) / 2
        mask = np.logical_and(mask_value_above_background, mask_circle_around_peak)
        ydata_restricted = ydata[mask]
        xdata_restricted = xdata[:, mask]

        try:
            popt, pcov = optimize.curve_fit(self.gauss2d, xdata_restricted, ydata_restricted, p0,
                                            bounds=bounds, maxfev=int(1e5), ftol=1e-12)
        except Exception as e:
            # if fit fails return max pixel
            log.info(e)
            log.info("Returning pixel position with maximal value in correlation.")
            return tuple(np.unravel_index(np.argmax(corr), corr.shape))

        #median_squared_relative_residue_threshold = 1e-2
        median_squared_relative_residue_threshold = 1e-1
        fit_ydata_restricted = self.gauss2d(xdata_restricted, *popt)
        square_rel_res = np.square(
            (fit_ydata_restricted - ydata_restricted) / fit_ydata_restricted
        )
        median_squared_rel_res = np.median(np.square(square_rel_res))

        if median_squared_rel_res > median_squared_relative_residue_threshold:
            raise Exception(
                f"Bad fit with median squared relative residue = {median_squared_rel_res}"
                f" vs allowed value of {median_squared_relative_residue_threshold}"
            )

        return popt[2], popt[3]

    @staticmethod
    def check_if_correlation_max_is_close_to_border(corr):
        corr_size = corr.shape[0]

        xs = np.arange(-corr.shape[0] / 2, corr.shape[0] / 2) + 0.5
        ys = np.arange(-corr.shape[1] / 2, corr.shape[1] / 2) + 0.5
        x, y = np.meshgrid(xs, ys)

        max_index = np.array(np.unravel_index(np.argmax(corr), corr.shape))
        x0, y0 = x[tuple(max_index)], y[tuple(max_index)]

        if x0 < -corr_size / 4 or x0 > corr_size / 4 or y0 < -corr_size / 4 or y0 > corr_size / 4:
            raise CorrelationMaxCloseToBorderError(
                "Maximum of correlation is outside center half of axes. "
                "This means that either the given image data is bad, or the offset is larger than expected."
            )


__all__ = ["NStarOffsets"]
