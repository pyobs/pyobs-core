import pytest

from pyobs.events import ExposureStatusChangedEvent, NewSpectrumEvent
from pyobs.modules.camera import DummySpectrograph


def test_fits_header_timeout_reaches_mixin():
    """BaseSpectrograph forwards fits_header_timeout to SpectrumFitsHeaderMixin via **kwargs --
    see issue #764 / PR #765. Unlike BaseCamera/BaseVideo, this path already used **kwargs
    forwarding before the fix; this test guards against a future regression."""
    spectrograph = DummySpectrograph(fits_header_timeout=1.0)
    assert spectrograph._fitsheadermixin_header_timeout == 1.0


@pytest.mark.asyncio
async def test_open_registers_sent_events():
    """BaseSpectrograph sends NewSpectrumEvent and ExposureStatusChangedEvent, so it must advertise them."""
    spectrograph = DummySpectrograph()
    await spectrograph.open()

    assert NewSpectrumEvent in spectrograph.comm._events_sent
    assert ExposureStatusChangedEvent in spectrograph.comm._events_sent

    await spectrograph.close()
