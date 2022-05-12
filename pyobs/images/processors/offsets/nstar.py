import logging
from typing import Tuple, List, Union, Dict, Any, Optional
import numpy as np
from numpy.typing import NDArray
from scipy import signal, optimize
from astropy.nddata import NDData
from astropy.table import Table, Column
import photutils

from pyobs.images import Image, ImageProcessor
from pyobs.mixins.pipeline import PipelineMixin
from .offsets import Offsets

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class NStarOffsets(Offsets, PipelineMixin):
    """An offset-calculation method based on comparing 2D images of the surroundings of a variable number of stars."""

    def __init__(
        self,
        num_stars: int = 10,
        max_offset: float = 4.0,
        min_pixels: int = 3,
        min_sources: int = 1,
        pipeline: Optional[List[Union[Dict[str, Any], ImageProcessor]]] = None,
        **kwargs: Any,
    ):
        """Initializes a new auto guiding system.

        Requires pyobs.images.processors.detection.SepSourceDetection and
        pyobs.images.processors.photometry.SepPhotometry to be run on the image beforehand.

        Args:
            num_stars: maximum number of stars to use to calculate offset from boxes around them
            max_offset: the maximal expected offset in arc seconds. Determines the size of boxes
                around stars.
            min_pixels: minimum required number of pixels above threshold for source to be
                used for offset calculation.
            min_sources: Minimum required number of sources in image.
            pipeline: Pipeline to be used for first image in series.
        """
        Offsets.__init__(self, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # store
        self.num_stars = num_stars
        self.max_offset = max_offset
        self.min_pixels = min_pixels
        self.min_sources = min_sources
        self.ref_boxes: List[Any] = []

    def reset(self) -> None:
        """Resets guiding."""
        log.info("Reset auto-guiding.")
        self.ref_boxes = []

    def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        # no reference image?
        if self.ref_boxes is None:
            log.info("Initialising nstar auto-guiding with new image...")
            star_box_size = max(5, self._get_box_size(self.max_offset, image.pixel_scale))
            log.info(f"Choosing box size of {star_box_size} pixels.")

            # initialize reference image information
            try:
                # get boxes
                self.ref_boxes = self._boxes_from_ref(image, star_box_size)

                # reset and finish
                image.meta["offsets"] = (0, 0)
                return image

            except ValueError as e:
                # didn't work
                log.warning(f"Could not initialize reference image info due to exception '{e}'. Resetting...")
                self.reset()
                if "offsets" in image.meta:
                    del image.meta["offsets"]
                self.offset = None, None
                return image

        # process it
        log.info("Perform auto-guiding on new image...")
        offsets = self._calculate_offsets(image)
        if offsets[0] is not None:
            image.meta["offsets"] = offsets
        return image

    @staticmethod
    def _get_box_size(max_expected_offset_in_arcsec, pixel_scale) -> int:
        # multiply by 4 to give enough space for fit of correlation around the peak on all sides
        return int(4 * max_expected_offset_in_arcsec / pixel_scale if pixel_scale else 20)

    async def _boxes_from_ref(self, image: Image, star_box_size: int) -> List:
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

        # run pipeline on 1st image
        img = await self.run_pipeline(image)

        # check data and catalog
        if img.data is None:
            raise ValueError("No data found in image.")
        if img.catalog is None:
            raise ValueError("No catalog found in image.")

        # do photometry and get catalog
        sources = self._fits2numpy(img.catalog)

        # filter sources
        sources = self.remove_sources_close_to_border(sources, img.data.shape, star_box_size // 2 + 1)
        sources = self.remove_bad_sources(sources)
        self._check_sources_count(sources)
        selected_sources = self._select_brightest_sources(self.num_stars, sources)

        # extract boxes
        return photutils.psf.extract_stars(
            NDData(img.data.astype(float)), selected_sources, size=star_box_size
        ).all_stars

    @staticmethod
    def _fits2numpy(sources: Table) -> Table:
        """Convert from FITS to numpy conventions for pixel coordinates."""
        for k in ["x", "y", "xmin", "xmax", "ymin", "ymax", "xpeak", "ypeak"]:
            if k in sources:
                sources[k] -= 1
        return sources

    @staticmethod
    def remove_sources_close_to_border(sources: Table, image_shape: tuple, min_dist) -> Table:
        """Remove table rows from sources when source is closer than given distance from border of image.

        Args:
            sources: Input table.
            image_shape: Shape of image.
            min_dist: Minimum distance from border in pixels.

        Returns:
            Filtered table.
        ."""

        # get shape
        width, height = image_shape

        def min_distance_from_border(source) -> None:
            # calculate the minimum distance of source to any image border (across x and y)
            return min(width / 2 - np.abs(source["y"] - width / 2), height / 2 - np.abs(source["x"] - height / 2))

        sources.add_column(Column(name="min_dist", data=min_distance_from_border(sources)))
        sources.sort("min_dist")

        sources_result = sources[np.where(sources["min_dist"] > min_dist)]
        return sources_result

    def remove_bad_sources(
        self, sources: Table, max_ellipticity: float = 0.4, min_bkg_factor: float = 1.5, saturation: int = 50000
    ) -> Table:
        """Remove bad sources from table.

        Args:
            sources: Input table.
            max_ellipticity: Maximum ellipticity.
            min_bkg_factor: Minimum factor above local background.
            saturation: Saturation level.

        Returns:
            Filtered table.
        """

        # remove saturated sources
        sources = sources[sources["peak"] < saturation]

        # remove small sources
        sources = sources[np.where(sources["tnpix"] >= self.min_pixels)]

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
        sources = sources[np.where((sources["peak"] + sources["background"]) / sources["background"] > min_bkg_factor)]
        return sources

    @staticmethod
    def _select_brightest_sources(num_stars: int, sources: Table) -> Table:
        """Select N brightest sources from table.

        Args:
            num_stars: Maximum number of stars to select.
            sources: Source table.

        Returns:
            New table containing N brightest sources.
        """

        # sort by flux.
        sources.sort("flux")
        sources.reverse()

        # extract
        if 0 < num_stars < len(sources):
            sources = sources[:num_stars]
        return sources

    def _check_sources_count(self, sources: Table) -> None:
        """Check if enough sources in table.

        Args:
            sources: astropy table of sources to check.

        Returns:
            None

        Raises:
            ValueError if not at least self.min_sources in sources table

        """
        n_required_sources = self.min_sources
        if len(sources) < n_required_sources:
            raise ValueError(f"Only {len(sources)} source(s) in image, but at least {n_required_sources} required.")

    def _calculate_offsets(self, image: Image) -> Tuple[Optional[float], Optional[float]]:
        """Calculate offsets of given image to ref image for every star.

        Args:
            image: Image to calculate offset for.

        Returns:
            Offset tuple.
        """

        # data?
        if image.data is None:
            return None, None

        # calculate offset for each star
        offsets = []
        for box in self.ref_boxes:
            # get box dimensions
            box_ymin, box_ymax = box.origin[1], box.origin[1] + box.data.shape[0]
            box_xmin, box_xmax = box.origin[0], box.origin[0] + box.data.shape[1]

            # extract box image
            current_boxed_image = image.data[box_ymin:box_ymax, box_xmin:box_xmax].astype(float)

            # correlate
            corr = signal.correlate2d(current_boxed_image, box.data, mode="same", boundary="wrap")

            try:
                offset = self._offsets_from_corr(corr)
                offsets.append(offset)
            except Exception as e:
                log.info(f"Exception '{e}' caught. Ignoring this star.")
                pass

        if len(offsets) == 0:
            log.info(f"All {self.num_stars} fits on boxed star correlations failed.")
            return None, None
        offsets_np = np.array(offsets)
        return float(np.mean(offsets_np[:, 0])), float(np.mean(offsets_np[:, 1]))

    @staticmethod
    def _gauss2d(
        x: NDArray[float], a: float, b: float, x0: float, y0: float, sigma_x: float, sigma_y: float
    ) -> NDArray[float]:
        """2D Gaussian function."""
        return a + b * np.exp(-((x[0] - x0) ** 2) / (2 * sigma_x**2) - (x[1] - y0) ** 2 / (2 * sigma_y**2))

    def _offsets_from_corr(self, corr: NDArray[float]) -> Tuple[float, float]:
        """Fit 2d correlation data with a 2d gaussian + constant offset.
        raise CorrelationMaxCloseToBorderError if the correlation maximum is not well separated from border."""

        # check if maximum of correlation is too close to border
        self._check_corr_border(corr)

        # get x,y positions array corresponding to the independent variable values of the correlation
        x, y = NStarOffsets._corr_grid(corr)

        # shape data as needed by R^2 -> R scipy curve_fit
        xdata = np.vstack((x.ravel(), y.ravel()))
        ydata = corr.ravel()

        # estimate initial parameter values
        # constant offset of 2d gaussian
        a = np.min(corr)

        # height of 2d gaussian
        b = np.max(corr) - a

        # gaussian peak position (estimate from maximum pixel position in correlation)
        max_index = np.array(np.unravel_index(np.argmax(corr), corr.shape))
        x0, y0 = x[tuple(max_index)], y[tuple(max_index)]

        # estimate width of 2d gaussian as radius of area with values above half maximum
        half_max = np.max(corr - a) / 2 + a

        # sum over binary array
        greater_than_half_max_area = np.sum(corr >= half_max)
        sigma_x = np.sqrt(greater_than_half_max_area / np.pi)
        sigma_y = sigma_x

        # initial value list
        p0 = [a, b, x0, y0, sigma_x, sigma_y]
        bounds = (
            [-np.inf, -np.inf, x0 - sigma_x, y0 - sigma_y, 0, 0],
            [np.inf, np.inf, x0 + sigma_x, y0 + sigma_y, np.inf, np.inf],
        )

        # only use data points that clearly belong to peak to avoid border effects
        # mask_value_above_background = ydata > -1e5  # a + .1*b
        mask_circle_around_peak = (x.ravel() - x0) ** 2 + (y.ravel() - y0) ** 2 < 4 * (sigma_x**2 + sigma_y**2) / 2
        mask = mask_circle_around_peak
        ydata_restricted = ydata[mask]
        xdata_restricted = xdata[:, mask]

        # do fit
        try:
            popt, pcov = optimize.curve_fit(self._gauss2d, xdata_restricted, ydata_restricted, p0, bounds=bounds)
        except Exception as e:
            # if fit fails return max pixel
            log.info("Returning pixel position with maximal value in correlation.")
            idx = np.unravel_index(np.argmax(corr), corr.shape)
            return float(idx[0]), float(idx[1])

        # check quality of fit
        median_squared_relative_residue_threshold = 1e-1
        fit_ydata_restricted = self._gauss2d(xdata_restricted, *popt)
        square_rel_res = np.square((fit_ydata_restricted - ydata_restricted) / fit_ydata_restricted)
        median_squared_rel_res = np.median(np.square(square_rel_res))

        if median_squared_rel_res > median_squared_relative_residue_threshold:
            raise Exception(
                f"Bad fit with median squared relative residue = {median_squared_rel_res}"
                f" vs allowed value of {median_squared_relative_residue_threshold}"
            )

        return popt[2], popt[3]

    @staticmethod
    def _corr_grid(corr: NDArray[float]) -> NDArray[float]:
        """Create x/y grid for given 2D correlation."""
        xs = np.arange(-corr.shape[0] / 2, corr.shape[0] / 2) + 0.5
        ys = np.arange(-corr.shape[1] / 2, corr.shape[1] / 2) + 0.5
        return np.meshgrid(xs, ys)

    @staticmethod
    def _check_corr_border(corr: NDArray[float]) -> None:
        """Check whether maximum of correlation is too close to border."""

        corr_size = corr.shape[0]
        x, y = NStarOffsets._corr_grid(corr)

        max_index = np.array(np.unravel_index(np.argmax(corr), corr.shape))
        x0, y0 = x[tuple(max_index)], y[tuple(max_index)]

        if x0 < -corr_size / 4 or x0 > corr_size / 4 or y0 < -corr_size / 4 or y0 > corr_size / 4:
            raise CorrelationMaxCloseToBorderError(
                "Maximum of correlation is outside center half of axes. "
                "This means that either the given image data is bad, or the offset is larger than expected."
            )


__all__ = ["NStarOffsets"]
