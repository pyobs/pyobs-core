import pytest
from astropy.table import QTable

from pyobs.images.meta.exptime import ExpTime
from pyobs.images.processors.detection import DaophotSourceDetection, SourceDetection
from pyobs.images.processors.exptime import StarExpTimeEstimator
from pyobs.images import Image


@pytest.fixture()
def mock_table() -> QTable:
    table = QTable()
    table['peak'] = [2500, 2000, 40, 30]
    table['x'] = [30, 25, 80, 90]
    table['y'] = [10, 40, 25, 60]

    return table


class MockSourceDetection(SourceDetection):
    async def __call__(self, image: Image) -> Image:
        return image


@pytest.mark.asyncio
async def test_full_wout_satu_header(mock_table):
    source_detection = MockSourceDetection()
    mock_image = Image(catalog=mock_table)

    mock_image.header["EXPTIME"] = 1.0

    estimator = StarExpTimeEstimator(source_detection, saturated=0.1, bias=0.0)

    exp_time = await estimator._calc_exp_time(mock_image)

    assert exp_time == 2.0


@pytest.mark.asyncio
async def test_full_with_satu_header(mock_table):
    source_detection = MockSourceDetection()
    mock_image = Image(catalog=mock_table)

    mock_image.header["EXPTIME"] = 1.0
    mock_image.header["DET-SATU"] = 48000.0
    mock_image.header["DET-GAIN"] = 2.0

    estimator = StarExpTimeEstimator(source_detection, saturated=0.1, bias=0.0)

    exp_time = await estimator._calc_exp_time(mock_image)

    assert exp_time == 2400/2000

