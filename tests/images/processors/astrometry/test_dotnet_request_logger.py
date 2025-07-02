import logging

from astropy.wcs import WCS

from pyobs.images import Image
from pyobs.images.processors.astrometry._dotnet_request_logger import _RequestLogger


def test_log_catalog_data(caplog, mock_header):
    log = logging.getLogger(__name__)

    data = {"ra": 0.0, "dec": 0.0}
    image = Image(header=mock_header)

    logger = _RequestLogger(log, image, data)

    with caplog.at_level(logging.INFO):
        logger.log_request_data()

    assert (
        caplog.records[-1].message == "Found original RA=00:00:00 (0.0000), Dec=00:00:00 (0.0000) at pixel 1.00,1.00."
    )
    assert caplog.records[-1].levelname == "INFO"


def test_log_request_result(caplog, mock_header):
    log = logging.getLogger(__name__)

    data = {"ra": 0.0, "dec": 0.0}
    image = Image(header=mock_header)

    logger = _RequestLogger(log, image, data)

    with caplog.at_level(logging.INFO):
        logger.log_request_result(WCS())

    assert caplog.records[-1].message == "Found final RA=00:08:00 (0.0000), Dec=02:00:00 (0.0000) at pixel 1.00,1.00."
    assert caplog.records[-1].levelname == "INFO"
