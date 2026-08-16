from pyobs.modules.camera import DummySpectrograph


def test_fits_header_timeout_reaches_mixin():
    """BaseSpectrograph forwards fits_header_timeout to SpectrumFitsHeaderMixin via **kwargs --
    see issue #764 / PR #765. Unlike BaseCamera/BaseVideo, this path already used **kwargs
    forwarding before the fix; this test guards against a future regression."""
    spectrograph = DummySpectrograph(fits_header_timeout=1.0)
    assert spectrograph._fitsheadermixin_header_timeout == 1.0
