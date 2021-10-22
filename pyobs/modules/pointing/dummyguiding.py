import logging
from typing import Any

from .. import Module
from ...interfaces import IAutoGuiding

log = logging.getLogger(__name__)


class DummyAutoGuiding(Module, IAutoGuiding):
    """An auto-guiding system."""
    __module__ = 'pyobs.modules.guiding'

    def __init__(self, **kwargs: Any):
        Module.__init__(self, **kwargs)
        self._running = False

    def set_exposure_time(self, exposure_time: float, **kwargs: Any):
        pass

    def start(self, **kwargs: Any):
        log.info('Start guiding.')
        self._running = True

    def stop(self, **kwargs: Any):
        log.info('Stop guiding.')
        self._running = False

    def is_running(self, **kwargs: Any) -> bool:
        return self._running


__all__ = ['DummyAutoGuiding']
