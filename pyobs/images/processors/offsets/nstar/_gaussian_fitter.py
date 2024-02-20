import logging
from typing import Tuple, Any

import numpy as np
from scipy import optimize
from scipy.optimize import OptimizeWarning

log = logging.getLogger(__name__)


class GaussianFitter(object):

    @staticmethod
    def offsets_from_corr(corr: np.ndarray[float]) -> Tuple[float, float]:
        """Fit 2d correlation data with a 2d gaussian + constant offset.
        raise CorrelationMaxCloseToBorderError if the correlation maximum is not well separated from border."""

        xdata_restricted, ydata_restricted, p0, bounds = GaussianFitter._init_fit(corr)

        try:
            fit_result, _ = optimize.curve_fit(GaussianFitter._gauss2d, xdata_restricted, ydata_restricted, p0, bounds=bounds)
        except (ValueError, RuntimeError, OptimizeWarning):

            log.info("Returning pixel position with maximal value in correlation.")
            return p0[2], p0[3]

        GaussianFitter._check_fit_quality(xdata_restricted, ydata_restricted, fit_result)

        return fit_result[2], fit_result[3]

    @staticmethod
    def _init_fit(corr: np.ndarray[float]) -> tuple[
        np.ndarray[Any, np.dtype[Any]], np.ndarray[Any, np.dtype[float]], tuple[float, float, float, float, float, float], tuple[
            tuple[float, float, float, float, int, int], tuple[float, float, float, float, float, float]]]:
        # get x,y positions array corresponding to the independent variable values of the correlation
        x, y = GaussianFitter._corr_grid(corr)

        # gaussian peak position (estimate from maximum pixel position in correlation)
        max_index = np.array(np.unravel_index(np.argmax(corr), corr.shape))
        peak_x, peak_y = x[tuple(max_index)], y[tuple(max_index)]

        # check if maximum of correlation is too close to border
        GaussianFitter._check_peak_border_distance(corr, peak_x, peak_y)

        # estimate initial parameter values
        # constant offset of 2d gaussian
        background = np.min(corr)

        # height of 2d gaussian
        peak_height = np.max(corr) - background

        # estimate width of 2d gaussian as radius of area with values above half maximum
        half_max = np.max(corr - background) / 2 + background

        # sum over binary array
        greater_than_half_max_area = np.sum(corr >= half_max)
        sigma_x = np.sqrt(greater_than_half_max_area / np.pi)
        sigma_y = sigma_x

        # initial value list
        p0 = (background, peak_height, peak_x, peak_y, sigma_x, sigma_y)
        bounds = (
            (-np.inf, -np.inf, peak_x - sigma_x, peak_y - sigma_y, 0, 0),
            (np.inf, np.inf, peak_x + sigma_x, peak_y + sigma_y, np.inf, np.inf),
        )

        # shape data as needed by R^2 -> R scipy curve_fit
        xdata = np.vstack((x.ravel(), y.ravel()))
        ydata = corr.ravel()

        # only use data points that clearly belong to peak to avoid border effects
        # mask_value_above_background = ydata > -1e5  # a + .1*b
        mask_circle_around_peak = (x.ravel() - peak_x) ** 2 + (y.ravel() - peak_y) ** 2 < 4 * (
                sigma_x ** 2 + sigma_y ** 2) / 2
        mask = mask_circle_around_peak
        ydata_restricted = ydata[mask]
        xdata_restricted = xdata[:, mask]

        return xdata_restricted, ydata_restricted, p0, bounds

    @staticmethod
    def _corr_grid(corr: np.ndarray[float]) -> np.ndarray[float]:
        """Create x/y grid for given 2D correlation."""
        xs = np.arange(-corr.shape[0] / 2, corr.shape[0] / 2) + 0.5
        ys = np.arange(-corr.shape[1] / 2, corr.shape[1] / 2) + 0.5
        return np.meshgrid(xs, ys)

    @staticmethod
    def _check_peak_border_distance(corr: np.ndarray[float], peak_x: float, peak_y: float) -> None:
        """Check whether maximum of correlation is too close to border."""

        corr_size = corr.shape[0]

        if peak_x < -corr_size / 4 or peak_x > corr_size / 4 or peak_y < -corr_size / 4 or peak_y > corr_size / 4:
            raise Exception(
                "Maximum of correlation is outside center half of axes. "
                "This means that either the given image data is bad, or the offset is larger than expected."
            )

    @staticmethod
    def _gauss2d(
            x: np.ndarray[float], a: float, b: float, x0: float, y0: float, sigma_x: float, sigma_y: float
    ) -> np.ndarray[float]:
        """2D Gaussian function."""
        return a + b * np.exp(-((x[0] - x0) ** 2) / (2 * sigma_x ** 2) - (x[1] - y0) ** 2 / (2 * sigma_y ** 2))

    @staticmethod
    def _check_fit_quality(xdata_restricted: np.ndarray[float], ydata_restricted: np.ndarray[float],
                           popt: Tuple[float, float, float, float, float, float]) -> None:
        median_squared_relative_residue_threshold = 1e-1
        fit_ydata_restricted = GaussianFitter._gauss2d(xdata_restricted, *popt)
        square_rel_res = np.square((fit_ydata_restricted - ydata_restricted) / fit_ydata_restricted)
        median_squared_rel_res = np.median(np.square(square_rel_res))

        if median_squared_rel_res > median_squared_relative_residue_threshold:
            raise Exception(
                f"Bad fit with median squared relative residue = {median_squared_rel_res}"
                f" vs allowed value of {median_squared_relative_residue_threshold}"
            )