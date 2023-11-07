import pytest
from astropy.table import QTable

from pyobs.images import Image
from pyobs.images.processors.detection import DaophotSourceDetection


def test_init_default():
    detector = DaophotSourceDetection()

    assert detector.fwhm == 3.0
    assert detector.threshold == 4.0
    assert detector.bkg_sigma == 3.0
    assert detector.bkg_box_size == (50, 50)
    assert detector.bkg_filter_size == (3, 3)


def test_init():
    fwhm = 1.0
    threshold = 5.0
    bkg_sigma = 4.0
    bkg_box_size = (60, 60)
    bkg_filter_size = (4, 4)

    detector = DaophotSourceDetection(fwhm, threshold, bkg_sigma, bkg_box_size, bkg_filter_size)

    assert detector.fwhm == fwhm
    assert detector.threshold == threshold
    assert detector.bkg_sigma == bkg_sigma
    assert detector.bkg_box_size == bkg_box_size
    assert detector.bkg_filter_size == bkg_filter_size


@pytest.mark.asyncio
async def test_invalid_image():
    detector = DaophotSourceDetection()
    image = Image()

    assert image == await detector(image)


@pytest.fixture()
def gaussian_sources_image() -> Image:
    from photutils.datasets import make_gaussian_prf_sources_image, make_noise_image
    shape = (100, 100)

    table = QTable()
    table['amplitude'] = [50, 70, 150, 210]
    table['x_0'] = [30, 25, 80, 90]
    table['y_0'] = [10, 40, 25, 60]
    table['sigma'] = [1.4, 3.1, 3., 2.1]

    data = make_gaussian_prf_sources_image(shape, table)
    noise = make_noise_image(shape, distribution='gaussian', mean=5., stddev=2.)

    return Image(data + noise, catalog=table)


@pytest.mark.asyncio
async def test_source_detection(gaussian_sources_image):
    detector = DaophotSourceDetection()
    output_image = await detector(gaussian_sources_image)

    assert len(output_image.catalog) == 4
