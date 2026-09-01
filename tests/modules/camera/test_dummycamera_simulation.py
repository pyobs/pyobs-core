import numpy as np
from astropy.modeling import models
from astropy.table import Table

from pyobs.modules.camera import DummyCamera


def _camera_with_fake_catalog(seeing: float = 3.0, flux: float = 1e6) -> DummyCamera:
    """A DummyCamera whose _get_catalog() returns a single fixed star at (ra, dec) = (0, 0)
    instead of querying the Gaia TAP service. _telescope_pos defaults to (0, 0) too, so the
    star lands at the WCS reference pixel (image center for a square image_size)."""
    camera = DummyCamera(image_size=(200, 200), seeing=seeing)
    fake_catalog = Table({"ra": [0.0], "dec": [0.0], "phot_g_mean_flux": [flux], "phot_g_mean_mag": [8.0]})
    camera._get_catalog = lambda fov: fake_catalog  # type: ignore[method-assign]
    return camera


def test_get_sources_table_maps_amplitude_not_just_position():
    """Regression for #838: Moffat2D's params_map only mapped x_0/y_0, so amplitude silently
    stayed at astropy's default of 1 -- every simulated star was invisible under the noise
    floor. _get_sources_table() must supply an amplitude column derived from flux."""
    camera = _camera_with_fake_catalog()

    sources, gamma = camera._get_sources_table(exp_time=1.0)

    assert "amplitude" in sources.colnames
    assert sources["amplitude"][0] > 0
    # amplitude is a peak value derived from (already exptime-scaled) flux via the Moffat2D
    # profile's own volume -- not a raw copy of flux.
    assert sources["amplitude"][0] != sources["flux"][0]
    assert gamma > 0


def test_get_sources_table_gamma_matches_configured_seeing():
    """gamma must be derived from self._seeing at the camera's actual plate scale, not left at
    Moffat2D's default width -- otherwise every star renders with the wrong profile shape
    regardless of the seeing configured on the camera."""
    seeing_arcsec = 3.0
    camera = _camera_with_fake_catalog(seeing=seeing_arcsec)

    _, gamma = camera._get_sources_table(exp_time=1.0)

    cdelt1 = 360.0 / (2.0 * np.pi) * camera._pixel_size / camera._focal_length * camera._binning[0]
    expected_fwhm_pix = seeing_arcsec / 3600.0 / cdelt1

    model = models.Moffat2D(gamma=gamma, alpha=camera._MOFFAT_ALPHA)
    assert model.fwhm == expected_fwhm_pix


def test_simulate_image_renders_visible_star():
    """End-to-end regression for #838: a simulated exposure must actually contain a star well
    above the background/read noise, not just a uniform noise field."""
    camera = _camera_with_fake_catalog(flux=1e6)

    data = camera._simulate_image(exp_time=5.0, open_shutter=True)

    background = np.median(data)
    assert data.max() > background + 500
