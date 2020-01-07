import logging
import threading

from pyobs.interfaces import ICamera, IMotion, ICameraBinning, ICameraWindow, IRoof, ITelescope, IFilters
from pyobs.robotic.scripts import Script
from pyobs.utils.threads import Future


log = logging.getLogger(__name__)


class LcoDefaultScript(Script):
    """Default script for LCO configs."""

    def __init__(self, config: dict, roof: IRoof, telescope: ITelescope, camera: ICamera, filters: IFilters,
                 instruments: dict, *args, **kwargs):
        """Initialize a new LCO default script.

        Args:
            config: Config to run
            roof: Roof to use
            telescope: Telescope to use
            camera: Camera to use
            filters: Filter wheel to use
            instruments: Instruments description from portal
        """
        Script.__init__(self, *args, **kwargs)

        # store
        self.config = config
        self.roof = roof
        self.telescope = telescope
        self.camera = camera
        self.filters = filters
        self.instruments = instruments

        # get image type
        self.image_type = ICamera.ImageType.OBJECT
        if config['type'] == 'BIAS':
            self.image_type = ICamera.ImageType.BIAS
        elif config['type'] == 'DARK':
            self.image_type = ICamera.ImageType.DARK

    def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if script can run now
        """

        # we need an open roof and a working telescope for OBJECT exposures
        if self.image_type == ICamera.ImageType.OBJECT:
            if not self.roof.is_ready().wait() or not self.telescope.is_ready().wait():
                return False

        # seems alright
        return True

    def run(self, abort_event: threading.Event):
        """Run script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """

        # got a target?
        target = self.config['target']
        track = None
        if target['ra'] is not None and target['dec'] is not None:
            log.info('Moving to target %s...', target['name'])
            track = self.telescope.track_radec(target['ra'], target['dec'])

        # total exposure time in this config
        self.exptime_done = 0

        # get instrument info
        instrument_type = self.config['instrument_type'].lower()
        instrument = self.instruments[instrument_type]

        # loop instrument configs
        for ic in self.config['instrument_configs']:
            self._check_abort(abort_event)

            # get readout mode
            for readout_mode in instrument['modes']['readout']['modes']:
                if readout_mode['code'] == ic['mode']:
                    break
            else:
                # could not find readout mode
                raise ValueError('Could not find readout mode %s.' % ic['mode'])
            log.info('Using readout mode "%s"...' % readout_mode['name'])

            # set filter
            set_filter = None
            if 'optical_elements' in ic and 'filter' in ic['optical_elements']:
                log.info('Setting filter to %s...', ic['optical_elements']['filter'])
                set_filter = self.filters.set_filter(ic['optical_elements']['filter'])

            # wait for tracking and filter
            Future.wait_all([track, set_filter])

            # set binning and window
            if isinstance(self.camera, ICameraBinning):
                binning = readout_mode['params']['binning']
                log.info('Set binning to %dx%d...', binning, binning)
                self.camera.set_binning(binning, binning).wait()
            if isinstance(self.camera, ICameraWindow):
                full_frame = self.camera.get_full_frame().wait()
                self.camera.set_window(*full_frame).wait()

            # loop images
            for exp in range(ic['exposure_count']):
                self._check_abort(abort_event)

                # do exposures
                log.info('Exposing %s image %d/%d for %.2fs...',
                         self.config['type'], exp + 1, ic['exposure_count'], ic['exposure_time'])
                self.camera.expose(int(ic['exposure_time'] * 1000), self.image_type).wait()
                self.exptime_done += ic['exposure_time']

    def get_fits_headers(self, namespaces: list = None) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # init header
        hdr = {}

        # which image type?
        if self.image_type == ICamera.ImageType.OBJECT:
            # add object name
            hdr['OBJECT'] = self.config['target']['name'], 'Name of target'

        # return
        return hdr


__all__ = ['LcoDefaultScript']
