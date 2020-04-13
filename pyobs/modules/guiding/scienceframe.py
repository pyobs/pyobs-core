import logging
import threading
from typing import Union

from pyobs import PyObsModule, get_object
from pyobs.events import NewImageEvent
from pyobs.interfaces import ITelescope, IAutoGuiding, IFitsHeaderProvider
from pyobs.mixins import TableStorageMixin
from pyobs.utils.guiding.base import BaseGuider
from pyobs.utils.images import Image


log = logging.getLogger(__name__)


class ScienceFrameAutoGuider(PyObsModule, TableStorageMixin, IAutoGuiding, IFitsHeaderProvider):
    """An auto-guiding system based on comparing collapsed images along the x&y axes with a reference image."""

    def __init__(self, camera: str, telescope: Union[str, ITelescope], guider: Union[dict, BaseGuider],
                 log_file: str = None, *args, **kwargs):
        """Initializes a new science frame auto guiding system.

        Args:
            camera: Camera to use.
            telescope: Telescope to use.
            guider: Auto-guider to use
            log_file
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store
        self._camera = camera
        self._telescope = telescope
        self._enabled = False

        # create auto-guiding system
        self._guider: BaseGuider = get_object(guider, BaseGuider)

        # add thread func
        self._add_thread_func(self._auto_guiding, True)

        # variables
        self._next_image: Image = None
        self._lock = threading.Lock()

        # columns for storage
        storage_columns = {
            'datetime': str,
            'ra': float,
            'dec': float,
            'alt': float,
            'az': float,
            'off_ra': float,
            'off_dec': float,
            'off_alt': float,
            'off_az': float
        }

        # init table storage and load measurements
        TableStorageMixin.__init__(self, filename=log_file, columns=storage_columns, reload_always=True)

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # check telescope
        try:
            self.proxy(self._telescope, ITelescope)
        except ValueError:
            log.warning('Given telescope does not exist or is not of correct type at the moment.')

        # subscribe to channel with new images
        log.info('Subscribing to new image events...')
        self.comm.register_event(NewImageEvent, self.add_image)

    def set_exposure_time(self, exp_time: int):
        """Set the exposure time for the auto-guider.

        Args:
            exp_time: Exposure time in ms.
        """
        raise NotImplementedError

    def start(self, *args, **kwargs):
        """Starts/resets auto-guiding."""
        self._guider.reset()
        self._enabled = True

    def stop(self, *args, **kwargs):
        """Stops auto-guiding."""
        self._guider.reset()
        self._enabled = False

    def is_running(self, *args, **kwargs) -> bool:
        """Whether auto-guiding is running.

        Returns:
            Auto-guiding is running.
        """
        return self._enabled

    def add_image(self, event: NewImageEvent, sender: str, *args, **kwargs):
        """Processes an image asynchronously, returns immediately.

        Args:
            event: Event for new image.
            sender: Name of sender.
        """

        # did it come from correct camera and are we enabled?
        if sender != self._camera or not self._enabled:
            return
        log.info('Received new image.')

        # download image
        image = self.vfs.download_fits_image(event.filename)

        # we only accept OBJECT images
        if image.header['IMAGETYP'] != 'object':
            return

        # store filename as next image to process
        with self._lock:
            # do we have a filename in here already?
            if self._next_image:
                log.warning('Last image still being processed by auto-guiding, skipping new one.')
                return

            # store it
            self._next_image = image

    def _auto_guiding(self):
        """the thread function for processing the images"""

        # run until closed
        while not self.closing.is_set():
            # get next image to process
            with self._lock:
                image = self._next_image

            # got one?
            if image:
                try:
                    # get telescope
                    telescope: ITelescope = self.proxy(self._telescope, ITelescope)

                    # process it
                    self._guider(image, telescope, self.location)

                except Exception as e:
                    log.error('An exception occured: %s', e)

                # image finished
                with self._lock:
                    self._next_image = None

            # wait for next image
            self.closing.wait(0.1)

    def get_fits_headers(self, namespaces: list = None, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # state
        state = 'GUIDING_CLOSED_LOOP' if self._guider.is_loop_closed() else 'GUIDING_OPEN_LOOP'

        # return header
        return {
            'AGSTATE': state
        }


__all__ = ['ScienceFrameAutoGuider']
