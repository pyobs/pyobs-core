import asyncio
import glob
import logging
from datetime import datetime
from typing import Tuple, NamedTuple, Dict, Any, Optional, TYPE_CHECKING

from pyobs.interfaces import IWindow, IBinning, ICooling, IGain
from pyobs.modules.camera.basecamera import BaseCamera
from pyobs.images import Image
from pyobs.utils.enums import ExposureStatus
from pyobs.utils import exceptions as exc

if TYPE_CHECKING:
    from pyobs.utils.simulation import SimWorld


log = logging.getLogger(__name__)


class CoolingStatus(NamedTuple):
    enabled: bool = True
    set_point: float = -10.0
    power: float = 80.0
    temperatures: Dict[str, float] = {"CCD": 0.0, "Back": 3.14}


class DummyCamera(BaseCamera, IWindow, IBinning, ICooling, IGain):
    """A dummy camera for testing."""

    __module__ = "pyobs.modules.camera"

    def __init__(
        self,
        readout_time: float = 2,
        sim: Optional[Dict[str, Any]] = None,
        world: Optional["SimWorld"] = None,
        **kwargs: Any,
    ):
        """Creates a new dummy cammera.

        Args:
            readout_time: Readout time in seconds.
            sim: Dictionary with config for image simulator.
        """
        BaseCamera.__init__(self, **kwargs)

        # add thread func
        self.add_background_task(self._cooling_thread, True)

        # store
        self._readout_time = readout_time
        self._sim = sim if sim is not None else {}
        if "images" not in self._sim:
            self._sim["images"] = None

        # simulated world
        from pyobs.utils.simulation import SimCamera, SimWorld

        self._world = self.get_object(world, SimWorld) if world is not None else self.add_child_object(SimWorld)
        self._camera: SimCamera = self._world.camera

        # init camera
        self._cooling = CoolingStatus()
        self._exposing = True
        self._gain = 10.0

        # simulator
        self._sim_images = sorted(glob.glob(self._sim["images"])) if self._sim["images"] else None

    async def _cooling_thread(self) -> None:
        while True:
            # adjust temperature
            temps = self._cooling.temperatures
            temps["CCD"] -= (self._cooling.temperatures["CCD"] - self._cooling.set_point) * 0.05

            # cooling power
            power = (60.0 - self._cooling.temperatures["CCD"]) / 70.0 * 100.0

            # create new object
            self._cooling = CoolingStatus(
                enabled=self._cooling.enabled, set_point=self._cooling.set_point, power=power, temperatures=temps
            )

            # sleep for 1 second
            await asyncio.sleep(1)

    async def get_full_frame(self, **kwargs: Any) -> Tuple[int, int, int, int]:
        """Returns full size of CCD.

        Returns:
            Tuple with left, top, width, and height set.
        """
        return self._camera.full_frame

    def _get_image(self, exp_time: float, open_shutter: bool) -> Image:
        """Actually get (i.e. simulate) the image."""

        # random image or pre-defined?
        if self._sim_images:
            filename = self._sim_images.pop(0)
            self._sim_images.append(filename)
            return Image.from_file(filename)

        else:
            image = self._camera.get_image(exp_time, open_shutter)
            return image

    async def _expose(self, exposure_time: float, open_shutter: bool, abort_event: asyncio.Event) -> Image:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            exposure_time: The requested exposure time in seconds.
            open_shutter: Whether or not to open the shutter.
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image.

        Raises:
            GrabImageError: If exposure was not successful.
        """

        # start exposure
        log.info("Starting exposure with {0:s} shutter...".format("open" if open_shutter else "closed"))
        date_obs = datetime.utcnow()
        self._exposing = True

        # request image
        loop = asyncio.get_running_loop()
        hdu_future = loop.run_in_executor(None, self._get_image, exposure_time, open_shutter)

        # wait a little
        steps = 10
        for i in range(steps):
            if abort_event.is_set() or not self._exposing:
                self._exposing = False
                await self._change_exposure_status(ExposureStatus.IDLE)
                raise InterruptedError("Exposure was aborted.")
            await asyncio.sleep(exposure_time / steps)
        self._exposing = False

        # readout
        await self._change_exposure_status(ExposureStatus.READOUT)
        await asyncio.sleep(self._readout_time)

        # get image
        image = await hdu_future

        # add headers
        image.header["EXPTIME"] = exposure_time
        image.header["DATE-OBS"] = date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        image.header["XBINNING"] = image.header["DET-BIN1"] = (self._camera.binning[0], "Binning factor used on X axis")
        image.header["YBINNING"] = image.header["DET-BIN2"] = (self._camera.binning[1], "Binning factor used on Y axis")
        image.header["XORGSUBF"] = (self._camera.window[0], "Subframe origin on X axis")
        image.header["YORGSUBF"] = (self._camera.window[1], "Subframe origin on Y axis")

        # biassec/trimsec
        self.set_biassec_trimsec(image.header, *self._camera.full_frame)

        # finished
        log.info("Exposure finished.")
        return image

    async def _abort_exposure(self) -> None:
        """Abort the running exposure. Should be implemented by derived class.

        Returns:
            Success or not.
        """
        self._exposing = False

    async def get_window(self, **kwargs: Any) -> Tuple[int, int, int, int]:
        """Returns the camera window.

        Returns:
            Tuple with left, top, width, and height set.
        """
        return self._camera.window

    async def set_window(self, left: int, top: int, width: int, height: int, **kwargs: Any) -> None:
        """Set the camera window.

        Args:
            left: X offset of window.
            top: Y offset of window.
            width: Width of window.
            height: Height of window.

        Raises:
            ValueError: If binning could not be set.
        """
        log.info("Set window to %dx%d at %d,%d.", width, height, top, left)
        self._camera.window = (left, top, width, height)

    async def get_binning(self, **kwargs: Any) -> Tuple[int, int]:
        """Returns the camera binning.

        Returns:
            Tuple with x and y.
        """
        return self._camera.binning

    async def set_binning(self, x: int, y: int, **kwargs: Any) -> None:
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        log.info("Set binning to %dx%d.", x, y)
        self._camera.binning = (x, y)

    async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
        """Enables/disables cooling and sets setpoint.

        Args:
            enabled: Enable or disable cooling.
            setpoint: Setpoint in celsius for the cooling.

        Raises:
            ValueError: If cooling could not be set.
        """

        # log
        if enabled:
            log.info("Enabling cooling with a setpoint of %.2f°C.", setpoint)
        else:
            log.info("Disabling cooling.")

        # set
        self._cooling = CoolingStatus(
            enabled=enabled, set_point=setpoint, power=self._cooling.power, temperatures=self._cooling.temperatures
        )

    async def get_cooling_status(self, **kwargs: Any) -> Tuple[bool, float, float]:
        """Returns the current status for the cooling.

        Returns:
            (tuple): Tuple containing:
                Enabled:  Whether the cooling is enabled
                SetPoint: Setpoint for the cooling in celsius.
                Power:    Current cooling power in percent or None.
        """
        return self._cooling.enabled, self._cooling.set_point, self._cooling.power

    async def get_temperatures(self, **kwargs: Any) -> Dict[str, float]:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        return self._cooling.temperatures

    def _set_config_readout_time(self, readout_time: float) -> None:
        """Set readout time."""
        self._readout_time = readout_time

    def _get_config_readout_time(self) -> float:
        """Returns readout time."""
        return self._readout_time

    async def set_gain(self, gain: float, **kwargs: Any) -> None:
        """Set the camera gain.

        Args:
            gain: New camera gain.

        Raises:
            ValueError: If gain could not be set.
        """
        self._gain = gain

    async def get_gain(self, **kwargs: Any) -> float:
        """Returns the camera binning.

        Returns:
            Current gain.
        """
        return self._gain


__all__ = ["DummyCamera"]
