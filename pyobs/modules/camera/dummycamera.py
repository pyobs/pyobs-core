from __future__ import annotations

import asyncio
import glob
import logging
from datetime import UTC, datetime
from typing import Any, NamedTuple

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.modeling import models
from astropy.table import Table
from astropy.wcs import WCS
from numpy.typing import NDArray
from photutils.datasets import make_model_image, make_noise_image

from pyobs.images import Image
from pyobs.interfaces import (
    BinningState,
    CoolingState,
    GainState,
    IBinning,
    ICooling,
    IGain,
    IImageFormat,
    ImageFormatState,
    IPointingRaDec,
    ITemperatures,
    IWindow,
    RaDecState,
    SensorReading,
    TemperaturesState,
    WindowState,
)
from pyobs.modules.camera.basecamera import BaseCamera
from pyobs.utils.enums import ExposureStatus, ImageFormat, ImageType
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class CoolingStatus(NamedTuple):
    enabled: bool = True
    set_point: float = -10.0
    power: int = 80
    temperatures: dict[str, float] = {"CCD": 0.0, "Back": 3.14}


class DummyCamera(BaseCamera, IWindow, IBinning, ICooling, IGain, IImageFormat):
    """A dummy camera for testing."""

    __module__ = "pyobs.modules.camera"

    def __init__(
        self,
        readout_time: float = 2,
        image_size: tuple[int, int] | None = None,
        pixel_size: float = 0.015,
        focal_length: float = 5000.0,
        images: str | None = None,
        max_mag: float = 20.0,
        seeing: float = 3.0,
        telescope: str | None = None,
        **kwargs: Any,
    ):
        """Creates a new dummy camera.

        Args:
            readout_time: Readout time in seconds.
            image_size: Size of simulated image in pixels (width, height).
            pixel_size: Square pixel size in mm.
            focal_length: Focal length in mm (for plate scale calculation).
            images: Filename pattern for pre-recorded images to use instead of simulation.
            max_mag: Maximum magnitude of simulated stars.
            seeing: Seeing in arcsec FWHM.
            telescope: Name of telescope module to read pointing from (for star simulation).
        """
        BaseCamera.__init__(self, **kwargs)
        self.add_background_task(self._cooling_thread, True)

        self._readout_time = readout_time

        # image geometry
        self._full_frame: tuple[int, int, int, int] = (
            (0, 0, image_size[0], image_size[1]) if image_size is not None else (0, 0, 512, 512)
        )
        self._window = self._full_frame
        self._binning = (1, 1)
        self._pixel_size = pixel_size
        self._focal_length = focal_length
        self._max_mag = max_mag
        self._seeing = seeing

        # pre-recorded images
        self._sim_images: list[str] | None = (
            sorted(glob.glob(images)) if images and ("*" in images or "?" in images) else ([images] if images else None)
        )

        # telescope state (updated via subscribe_state)
        self._telescope_module = telescope
        self._telescope_pos: SkyCoord = SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs")

        # camera state
        self._cooling = CoolingStatus()
        self._exposing = True
        self._gain = 10.0
        self._gain_offset = 0.0
        self._image_format = ImageFormat.INT16
        self._image_type = ImageType.OBJECT

        # GAIA catalog cache
        self._catalog: Table | None = None
        self._catalog_coords: SkyCoord | None = None

    def _on_telescope_state(self, state: RaDecState) -> None:
        """Update cached telescope position from IPointingRaDec state."""
        self._telescope_pos = SkyCoord(ra=state.ra * u.deg, dec=state.dec * u.deg, frame="icrs")

    async def open(self) -> None:
        """Opens camera."""
        # publish capabilities before super().open()
        await self.comm.set_capabilities(IWindow.Capabilities(full_frame=WindowState(*self._full_frame)))
        await self.comm.set_capabilities(
            IBinning.Capabilities(binnings=[BinningState(x=i[0], y=i[1]) for i in [(1, 1), (2, 2), (3, 3)]])
        )
        await self.comm.set_capabilities(IImageFormat.Capabilities(image_formats=[ImageFormat.INT8, ImageFormat.INT16]))

        await BaseCamera.open(self)

        # subscribe to telescope pointing if given
        if self._telescope_module:
            await self.comm.subscribe_state(self._telescope_module, IPointingRaDec, self._on_telescope_state)

        # publish initial states
        await self.comm.set_state(
            ICooling,
            CoolingState(setpoint=self._cooling.set_point, power=self._cooling.power, enabled=self._cooling.enabled),
        )
        await self.comm.set_state(IGain, GainState(gain=self._gain, offset=self._gain_offset))
        await self.comm.set_state(IWindow, WindowState(*self._full_frame))
        await self.comm.set_state(IBinning, BinningState(*self._binning))
        await self.comm.set_state(IImageFormat, ImageFormatState(image_format=self._image_format))

    async def _cooling_thread(self) -> None:
        while True:
            temps = dict(self._cooling.temperatures)
            temps["CCD"] -= (temps["CCD"] - self._cooling.set_point) * 0.05
            power = (60.0 - temps["CCD"]) / 70.0 * 100.0
            self._cooling = CoolingStatus(
                enabled=self._cooling.enabled,
                set_point=self._cooling.set_point,
                power=power,
                temperatures=temps,
            )
            await self.comm.set_state(
                ICooling,
                CoolingState(setpoint=self._cooling.set_point, power=int(power), enabled=self._cooling.enabled),
            )
            await self.comm.set_state(
                ITemperatures,
                TemperaturesState(readings=[SensorReading(name=name, value=value) for name, value in temps.items()]),
            )
            await asyncio.sleep(1)

    def _sun_alt(self) -> float:
        """Returns current solar altitude in degrees, or -18 if no observer."""
        if self._observer is not None:
            return float(self.observer.sun_altaz(Time.now()).alt.degree)
        return -18.0

    def _simulate_image(self, exp_time: float, open_shutter: bool) -> NDArray[Any]:
        shape = (int(self._window[3]), int(self._window[2]))
        data = make_noise_image(shape, distribution="gaussian", mean=10, stddev=1.0)

        if exp_time > 0:
            data += make_noise_image(shape, distribution="gaussian", mean=exp_time / 1e4, stddev=exp_time / 1e5)
            if open_shutter:
                sun_alt = self._sun_alt()
                flat_counts = 30000 / np.exp(-1.28 * (4.209 + sun_alt)) * exp_time
                data += make_noise_image(shape, distribution="gaussian", mean=flat_counts, stddev=flat_counts / 10.0)
                sources = self._get_sources_table(exp_time)
                sources = sources[
                    (sources["x_mean"] > 0)
                    & (sources["x_mean"] < shape[1])
                    & (sources["y_mean"] > 0)
                    & (sources["y_mean"] < shape[0])
                ]
                model = models.Moffat2D()
                data += make_model_image(shape, model, sources, model_shape=(15, 15))

        data[data > 65535] = 65535
        return data.astype(np.uint16)

    def _create_header(self, exp_time: float, time: Time, data: NDArray[Any]) -> fits.Header:
        hdr = fits.Header()
        hdr["NAXIS1"] = data.shape[1]
        hdr["NAXIS2"] = data.shape[0]
        hdr["DATE-OBS"] = (time.isot, "Date and time of start of exposure")
        hdr["EXPTIME"] = (exp_time, "Exposure time [s]")
        hdr["XBINNING"] = hdr["DET-BIN1"] = (int(self._binning[0]), "Binning factor used on X axis")
        hdr["YBINNING"] = hdr["DET-BIN2"] = (int(self._binning[1]), "Binning factor used on Y axis")
        hdr["XORGSUBF"] = (int(self._window[0]), "Subframe origin on X axis")
        hdr["YORGSUBF"] = (int(self._window[1]), "Subframe origin on Y axis")
        hdr["TEL-FOCL"] = (self._focal_length, "Focal length [mm]")
        hdr["DET-PIXL"] = (self._pixel_size, "Size of detector pixels (square) [mm]")
        hdr["DATAMIN"] = float(np.min(data))
        hdr["DATAMAX"] = float(np.max(data))
        hdr["DATAMEAN"] = float(np.mean(data))
        return hdr

    def _get_catalog(self, fov: float) -> Table:
        if self._catalog_coords is None or self._catalog_coords.separation(self._telescope_pos) > 10.0 * u.arcmin:
            from astroquery.utils.tap import TapPlus

            ra, dec = self._telescope_pos.ra.degree, self._telescope_pos.dec.degree
            tap = TapPlus(url="https://gea.esac.esa.int/tap-server/tap")
            query = f"""
                SELECT TOP 1000
                  DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra}, {dec})) as dist,
                  ra, dec, phot_g_mean_flux, phot_g_mean_mag
                FROM gaiadr2.gaia_source
                WHERE 1 = CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {fov * 1.5}))
                  AND phot_g_mean_mag < {self._max_mag}
                ORDER BY phot_g_mean_mag ASC
            """
            job = tap.launch_job(query)
            self._catalog = job.get_results()
            self._catalog_coords = self._telescope_pos
        return self._catalog

    def _get_sources_table(self, exp_time: float) -> Table:
        tmp = 360.0 / (2.0 * np.pi) * self._pixel_size / self._focal_length
        cdelt1, cdelt2 = tmp * self._binning[0], tmp * self._binning[1]
        fov = np.max(cdelt2 * np.array(self._full_frame[2:]))
        cat = self._get_catalog(fov)

        w = WCS(naxis=2)
        w.wcs.crpix = [self._window[3] / 2.0, self._window[2] / 2.0]
        w.wcs.cdelt = np.array([-cdelt1, cdelt2])
        w.wcs.crval = [self._telescope_pos.ra.degree, self._telescope_pos.dec.degree]
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

        fwhm = self._seeing / 3600.0 / cdelt1 / 2.3548
        cat["x"], cat["y"] = w.wcs_world2pix(cat["ra"], cat["dec"], 0)

        sources = cat["x", "y", "phot_g_mean_flux", "phot_g_mean_mag"]
        sources.rename_columns(["x", "y", "phot_g_mean_flux"], ["x_mean", "y_mean", "flux"])
        sources.add_column([fwhm] * len(sources), name="x_stddev")
        sources.add_column([fwhm] * len(sources), name="y_stddev")
        sources["flux"] *= exp_time
        return sources

    def _get_image(self, exp_time: float, open_shutter: bool) -> Image:
        now = Time.now()
        if self._sim_images:
            filename = self._sim_images.pop(0)
            self._sim_images.append(filename)
            return Image.from_file(filename)
        data = self._simulate_image(exp_time, open_shutter)
        hdr = self._create_header(exp_time, now, data)
        return Image(data, header=hdr)

    async def _expose(self, exposure_time: float, open_shutter: bool, abort_event: asyncio.Event) -> Image:
        log.info("Starting exposure with %s shutter...", "open" if open_shutter else "closed")
        date_obs = datetime.now(UTC)
        self._exposing = True

        loop = asyncio.get_running_loop()
        hdu_future = loop.run_in_executor(None, self._get_image, exposure_time, open_shutter)

        steps = 10
        for _ in range(steps):
            if abort_event.is_set() or not self._exposing:
                self._exposing = False
                await self._change_exposure_status(ExposureStatus.IDLE)
                raise InterruptedError("Exposure was aborted.")
            await asyncio.sleep(exposure_time / steps)
        self._exposing = False

        await self._change_exposure_status(ExposureStatus.READOUT)
        await asyncio.sleep(self._readout_time)

        image = await hdu_future
        image.header["EXPTIME"] = exposure_time
        image.header["DATE-OBS"] = date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        image.header["XBINNING"] = image.header["DET-BIN1"] = (self._binning[0], "Binning factor used on X axis")
        image.header["YBINNING"] = image.header["DET-BIN2"] = (self._binning[1], "Binning factor used on Y axis")
        image.header["XORGSUBF"] = (self._window[0], "Subframe origin on X axis")
        image.header["YORGSUBF"] = (self._window[1], "Subframe origin on Y axis")
        self.set_biassec_trimsec(image.header, *self._full_frame)

        log.info("Exposure finished.")
        return image

    async def _abort_exposure(self) -> None:
        self._exposing = False

    async def set_window(self, left: int, top: int, width: int, height: int, **kwargs: Any) -> None:
        log.info("Set window to %dx%d at %d,%d.", width, height, top, left)
        self._window = (left, top, width, height)
        await self.comm.set_state(IWindow, WindowState(*self._window))

    async def set_binning(self, x: int, y: int, **kwargs: Any) -> None:
        log.info("Set binning to %dx%d.", x, y)
        self._binning = (x, y)
        await self.comm.set_state(IBinning, BinningState(*self._binning))

    async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
        if enabled:
            log.info("Enabling cooling with a setpoint of %.2f°C.", setpoint)
        else:
            log.info("Disabling cooling.")
        self._cooling = CoolingStatus(
            enabled=enabled,
            set_point=setpoint,
            power=self._cooling.power,
            temperatures=self._cooling.temperatures,
        )
        await self.comm.set_state(
            ICooling,
            CoolingState(setpoint=self._cooling.set_point, power=self._cooling.power, enabled=self._cooling.enabled),
        )

    async def set_gain(self, gain: float, **kwargs: Any) -> None:
        log.info("Setting gain to %.2f...", gain)
        self._gain = gain
        await self.comm.set_state(IGain, GainState(gain=self._gain, offset=self._gain_offset))

    async def set_offset(self, offset: float, **kwargs: Any) -> None:
        self._gain_offset = offset
        await self.comm.set_state(IGain, GainState(gain=self._gain, offset=self._gain_offset))

    async def set_image_format(self, fmt: ImageFormat, **kwargs: Any) -> None:
        self._image_format = fmt
        await self.comm.set_state(IImageFormat, ImageFormatState(image_format=self._image_format))

    async def _set_config_readout_time(self, readout_time: float) -> None:
        self._readout_time = readout_time

    async def _get_config_readout_time(self) -> float:
        return self._readout_time


__all__ = ["DummyCamera"]
