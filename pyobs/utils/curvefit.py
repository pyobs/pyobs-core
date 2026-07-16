from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit


def fit_hyperbola(x_arr: list[float], y_arr: list[float], y_err: list[float]) -> tuple[float, float]:
    """Fit a hyperbola

    Args:
        x_arr: X data
        y_arr: Y data
        y_err: Y errors

    Returns:
        Minimum of hyperbola and its uncertainty
    """

    # initial guess
    ic = np.argmin(y_arr)
    ix = np.argmax(y_arr)
    b = y_arr[ic]
    c = x_arr[ic]
    x = x_arr[ix]
    slope = np.abs((y_arr[ic] - y_arr[ix]) / (c - x))
    a = b / slope

    # init
    p0 = [a, b, c]

    # fit
    #
    # absolute_sigma=True is required here: without it, curve_fit treats y_err as only
    # relative weights and rescales the returned covariance matrix so that the fit's
    # reduced chi-square equals 1. That makes the reported variance reflect how well the
    # hyperbola shape matches this particular focus run rather than the actual per-point
    # measurement uncertainty passed in via y_err, which silently miscalibrates every
    # downstream error estimate.
    coeffs, cov = curve_fit(
        lambda xx, aa, bb, cc: bb * np.sqrt((xx - cc) ** 2 / aa**2 + 1.0),
        x_arr,
        y_arr,
        sigma=y_err,
        p0=p0,
        absolute_sigma=True,
    )

    # return result
    return coeffs[2], cov[2][2]
