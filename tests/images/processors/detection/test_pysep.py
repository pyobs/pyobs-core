import pytest

from pyobs.images.processors.detection import SepSourceDetection


def test_init_default():
    detector = SepSourceDetection()
    assert detector.threshold == 1.5
    assert detector.minarea == 5
    assert detector.deblend_nthresh == 32
    assert detector.deblend_cont == 0.005
    assert detector.clean is True
    assert detector.clean_param == 1.0


def test_init():
    threshold = 1.0
    minarea = 4
    deblend_nthresh = 30
    deblend_cont = 0.001
    clean = False
    clean_param = .5

    detector = SepSourceDetection(threshold, minarea, deblend_nthresh, deblend_cont, clean, clean_param)
    assert detector.threshold == threshold
    assert detector.minarea == minarea
    assert detector.deblend_nthresh == deblend_nthresh
    assert detector.deblend_cont == deblend_cont
    assert detector.clean is clean
    assert detector.clean_param == clean_param


@pytest.mark.asyncio
async def test_full(gaussian_sources_image):
    detector = SepSourceDetection()
    output_image = await detector(gaussian_sources_image)

    assert len(output_image.catalog) == 4
    assert (list(output_image.catalog.keys()) ==
            ["x",
                "y",
                "peak",
                "flux",
                "fwhm",
                "a",
                "b",
                "theta",
                "ellipticity",
                "tnpix",
                "kronrad",
                "fluxrad25",
                "fluxrad50",
                "fluxrad75",
                "xwin",
                "ywin",])
