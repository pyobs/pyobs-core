import logging

from .. import Module
from ...interfaces import IAutoGuiding

log = logging.getLogger(__name__)


class DummyAutoGuiding(Module, IAutoGuiding):
    """An auto-guiding system."""
    __module__ = 'pyobs.modules.guiding'

    def __init__(self, *args, **kwargs):
        Module.__init__(self, *args, **kwargs)
        self._running = False

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        pass

    def start(self, *args, **kwargs):
        log.info('Start guiding.')
        self._running = True

    def stop(self, *args, **kwargs):
        log.info('Stop guiding.')
        self._running = False

    def is_running(self, *args, **kwargs) -> bool:
        return self._running


__all__ = ['DummyAutoGuiding']
