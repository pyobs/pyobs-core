from typing import List, Tuple

import numpy as np
from scipy.optimize import curve_fit


def fit_hyperbola(x_arr: List[float], y_arr: List[float], y_err: List[float]) -> Tuple[float, float]:
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
    coeffs, cov = curve_fit(
        lambda xx, aa, bb, cc: bb * np.sqrt((xx - cc) ** 2 / aa**2 + 1.0), x_arr, y_arr, sigma=y_err, p0=p0
    )

    # return result
    return coeffs[2], cov[2][2]
