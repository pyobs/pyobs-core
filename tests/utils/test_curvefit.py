from __future__ import annotations

import numpy as np

from pyobs.utils.curvefit import fit_hyperbola

# ── fit_hyperbola ─────────────────────────────────────────────────────────────


def make_hyperbola(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """Generate clean hyperbola data: b * sqrt((x-c)^2/a^2 + 1)."""
    return b * np.sqrt((x - c) ** 2 / a**2 + 1.0)


def test_fit_hyperbola_recovers_minimum() -> None:
    """fit_hyperbola recovers the minimum position of a clean hyperbola."""
    x = np.linspace(1.0, 3.0, 20)
    true_min = 2.0
    y = make_hyperbola(x, a=0.5, b=0.3, c=true_min)
    err = np.ones_like(x) * 0.01

    result, _ = fit_hyperbola(x.tolist(), y.tolist(), err.tolist())
    assert abs(result - true_min) < 0.01


def test_fit_hyperbola_returns_tuple() -> None:
    """fit_hyperbola returns (minimum, variance)."""
    x = np.linspace(1.0, 3.0, 10)
    y = make_hyperbola(x, a=0.5, b=0.3, c=2.0)
    err = np.ones_like(x) * 0.01

    result = fit_hyperbola(x.tolist(), y.tolist(), err.tolist())
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_fit_hyperbola_variance_is_non_negative() -> None:
    """Variance from covariance matrix is non-negative."""
    x = np.linspace(0.5, 3.5, 15)
    y = make_hyperbola(x, a=0.8, b=0.5, c=2.0)
    err = np.ones_like(x) * 0.01

    _, variance = fit_hyperbola(x.tolist(), y.tolist(), err.tolist())
    assert variance >= 0.0


def test_fit_hyperbola_with_noise() -> None:
    """fit_hyperbola works with noisy data within reasonable tolerance."""
    rng = np.random.default_rng(42)
    x = np.linspace(1.0, 3.0, 20)
    true_min = 2.0
    y = make_hyperbola(x, a=0.5, b=0.3, c=true_min) + rng.normal(0, 0.005, len(x))
    err = np.ones_like(x) * 0.005

    result, _ = fit_hyperbola(x.tolist(), y.tolist(), err.tolist())
    assert abs(result - true_min) < 0.05


def test_fit_hyperbola_minimum_at_different_positions() -> None:
    """fit_hyperbola works for different minimum positions."""
    err = [0.01] * 20
    for true_min in [1.5, 2.0, 2.5, 3.0]:
        x = np.linspace(1.0, 4.0, 20)
        y = make_hyperbola(x, a=0.5, b=0.3, c=true_min)
        result, _ = fit_hyperbola(x.tolist(), y.tolist(), err)
        assert abs(result - true_min) < 0.01, f"Failed for true_min={true_min}"
