import pytest
from astropy.io import fits
import numpy as np
import threading

from pyobs.comm.dummy import DummyComm
from pyobs.environment import Environment
from pyobs.modules.camera import BaseCamera


def test_open_close():
    """Test basic open/close of BaseCamera."""

    # create camera, open and close it
    camera = BaseCamera(comm=DummyComm())
    camera.open()
    camera.close()


def test_remaining():
    """Test the methods for remaining exposure time and progress."""

    # open camera
    camera = BaseCamera(comm=DummyComm())
    camera.open()

    # no exposure, so both should be zero
    assert 0 == camera.get_exposure_time_left()
    assert 0 == camera.get_exposure_progress()

    # more tests will be done with DummyCamera

    # close camera
    camera.close()


def test_add_fits_headers():
    """Check adding FITS headers. Only check for existence, only for some we check actual value."""

    # create comm and environment
    comm = DummyComm()
    environment = Environment(timezone='utc',
                              location={'longitude': 20.810808, 'latitude': -32.375823, 'elevation': 1798.})

    # open camera
    centre = {'x': 100, 'y': 100}
    rotation = 42
    camera = BaseCamera(centre=centre, rotation=rotation, comm=comm, environment=environment)
    camera.open()

    # try empty header
    hdr = fits.Header()
    camera._add_fits_headers(hdr)
    assert 0 == len(hdr)

    # add DATE-OBS and IMAGETYP
    hdr['DATE-OBS'] = '2019-01-31T03:00:00.000'
    hdr['IMAGETYP'] = 'object'
    camera._add_fits_headers(hdr)

    # now we should get some values
    assert 2000 == hdr['EQUINOX']
    assert '2019-01-30' == hdr['DAY-OBS']
    assert environment.location.lon.degree == hdr['LONGITUD']
    assert environment.location.lat.degree == hdr['LATITUDE']
    assert 'RA---TAN' == hdr['CTYPE1']
    assert 'DEC--TAN' == hdr['CTYPE2']
    assert centre['x'] == hdr['DET-CPX1']
    assert centre['y'] == hdr['DET-CPX2']
    assert 'PC1_1' in hdr
    assert 'PC2_1' in hdr
    assert 'PC1_2' in hdr
    assert 'PC2_2' in hdr

    # add pixel size, focus and binning
    hdr['DET-PIXL'] = 0.015
    hdr['TEL-FOCL'] = 8400.0
    hdr['DET-BIN1'] = 1
    hdr['DET-BIN2'] = 1
    camera._add_fits_headers(hdr)

    # some WCS stuff
    assert 'CDELT1' in hdr
    assert 'CDELT2' in hdr
    assert 'deg' == hdr['CUNIT1']
    assert 'deg' == hdr['CUNIT2']
    assert 2 == hdr['WCSAXES']

    # windowing
    hdr['XORGSUBF'] = 0
    hdr['YORGSUBF'] = 0
    camera._add_fits_headers(hdr)

    # now we should have reference pixels
    assert 'CRPIX1' in hdr
    assert 'CRPIX2' in hdr

    # close camera
    camera.close()


class DummyCam(BaseCamera):
    """Test implementation of BaseCamera for text_expose()."""

    def __init__(self, *args, **kwargs):
        BaseCamera.__init__(self, *args, **kwargs)
        self.status_during_expose = None

    def _expose(self, exposure_time: int, open_shutter: bool, abort_event: threading.Event) -> fits.ImageHDU:
        # store current status
        self.status_during_expose = self.get_exposure_status()

        # wait for exposure
        abort_event.wait(exposure_time / 1000.)

        # raise exception, if aborted
        if abort_event.is_set():
            raise ValueError('Exposure was aborted.')

        # return image
        return fits.ImageHDU(np.zeros((100, 100)))


def test_expose():
    """Do a dummy exposure."""

    # create comm and environment
    comm = DummyComm()
    environment = Environment(timezone='utc',
                              location={'longitude': 20.810808, 'latitude': -32.375823, 'elevation': 1798.})

    # open camera
    camera = DummyCam(filenames=None, comm=comm, environment=environment)
    camera.open()

    # status must be idle
    assert 'idle' == camera.get_exposure_status()

    # expose
    camera.expose(exposure_time=0, image_type='object')
    assert 'exposing' == camera.status_during_expose

    # status must be idle again
    assert 'idle' == camera.get_exposure_status()

    # close camera
    camera.close()


def test_abort():
    """Do a dummy exposure."""

    # create comm and environment
    comm = DummyComm()
    environment = Environment(timezone='utc',
                              location={'longitude': 20.810808, 'latitude': -32.375823, 'elevation': 1798.})

    # open camera
    camera = DummyCam(filenames=None, comm=comm, environment=environment)
    camera.open()

    def expose():
        with pytest.raises(ValueError):
            camera.expose(exposure_time=1000, image_type='object')

    # expose
    thread = threading.Thread(target=expose)
    thread.start()

    # abort
    camera.abort()

    # thread should be closed
    assert False == thread.is_alive()

    # close camera
    camera.close()


def test_trimsec():
    # create camera, no need for opening it
    camera = DummyCam()

    # define full frame
    full = {'left': 50, 'width': 100, 'top': 0, 'height': 100}

    # image covering the whole data area
    hdr = fits.Header({
        'NAXIS1': 100,
        'NAXIS2': 100,
        'XORGSUBF': 50,
        'YORGSUBF': 0,
        'XBINNING': 1,
        'YBINNING': 1
    })
    camera.set_biassec_trimsec(hdr, **full)
    assert 'BIASSEC' not in hdr
    assert '[1:100,1:100]' == hdr['TRIMSEC']

    # image covering the whole bias area
    hdr = fits.Header({
        'NAXIS1': 50,
        'NAXIS2': 100,
        'XORGSUBF': 0,
        'YORGSUBF': 0,
        'XBINNING': 1,
        'YBINNING': 1
    })
    camera.set_biassec_trimsec(hdr, **full)
    assert '[1:50,1:100]' == hdr['BIASSEC']
    assert 'TRIMSEC' not in hdr

    # half in both
    hdr = fits.Header({
        'NAXIS1': 50,
        'NAXIS2': 100,
        'XORGSUBF': 25,
        'YORGSUBF': 0,
        'XBINNING': 1,
        'YBINNING': 1
    })
    camera.set_biassec_trimsec(hdr, **full)
    assert '[1:25,1:100]' == hdr['BIASSEC']
    assert '[26:50,1:100]' == hdr['TRIMSEC']

    # same with binning
    hdr = fits.Header({
        'NAXIS1': 40,
        'NAXIS2': 50,
        'XORGSUBF': 10,
        'YORGSUBF': 0,
        'XBINNING': 2,
        'YBINNING': 2
    })
    camera.set_biassec_trimsec(hdr, **full)
    assert '[1:20,1:50]' == hdr['BIASSEC']
    assert '[21:40,1:50]' == hdr['TRIMSEC']
