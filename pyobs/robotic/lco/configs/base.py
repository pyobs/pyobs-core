import threading

from pyobs.interfaces import IRoof, ITelescope, ICamera, IFilters


class LcoBaseConfig:
    def __init__(self, config: dict, roof: IRoof, telescope: ITelescope, camera: ICamera, filters: IFilters):
        self.config = config
        self.roof = roof
        self.telescope = telescope
        self.camera = camera
        self.filters = filters

        # get image type
        self.image_type = ICamera.ImageType.OBJECT
        if config['type'] == 'BIAS':
            self.image_type = ICamera.ImageType.BIAS
        elif config['type'] == 'DARK':
            self.image_type = ICamera.ImageType.DARK

    def can_run(self) -> bool:
        """Whether this config can currently run."""
        return False

    def __call__(self, abort_event: threading.Event) -> int:
        """Run configuration.

        Args:
            abort_event: Event to abort run.

        Returns:
            Total exposure time in ms.
        """
        raise NotImplementedError


__all__ = ['LcoBaseConfig']
