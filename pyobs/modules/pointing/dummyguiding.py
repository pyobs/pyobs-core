import logging
from typing import Any

from pyobs.modules import Module
from pyobs.interfaces import IAutoGuiding

log = logging.getLogger(__name__)


class DummyAutoGuiding(Module, IAutoGuiding):
    """An auto-guiding system."""
    __module__ = 'pyobs.modules.guiding'

    def __init__(self, **kwargs: Any):
        Module.__init__(self, **kwargs)
        self._running = False

    async def set_exposure_time(self, exposure_time: float, **kwargs: Any) -> None:
        pass

    async def start(self, **kwargs: Any) -> None:
        log.info('Start guiding.')
        self._running = True

    async def stop(self, **kwargs: Any) -> None:
        log.info('Stop guiding.')
        self._running = False

    async def is_running(self, **kwargs: Any) -> bool:
        return self._running


__all__ = ['DummyAutoGuiding']
