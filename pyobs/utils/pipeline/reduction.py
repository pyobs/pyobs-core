from __future__ import annotations

import logging
import os
import os.path
from typing import Any

from pyobs.images import Image
from pyobs.object import get_object
from pyobs.robotic.utils.archive import Archive, FrameInfo
from pyobs.utils.enums import ImageType
from pyobs.utils.fits import FilenameFormatter

from .pipeline import Pipeline
from .progress import MasterCalibCreated, ProgressCallback, ScienceFrameProcessed
from .reduction_base import ReductionBase

log = logging.getLogger(__name__)


FILENAME = "{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-{IMAGETYP}-{XBINNING}x{YBINNING}{FILTER|filter}.fits"


class Reduction(ReductionBase):
    def __init__(
        self,
        archive: dict[str, Any] | Archive,
        pipeline: dict[str, Any] | Pipeline,
        filenames_calib: str = FILENAME,
        min_flats: int = 10,
        output: str | dict[str, Any] | Archive | None = None,
        create_calibs: bool = True,
        calib_science: bool = True,
        progress_callback: ProgressCallback | None = None,
    ):
        """Creates a Reduction object for reducing a given observation period.

        Args:
            archive: Archive to fetch raw and calibration frames from. Also the output
                destination, unless output is set.
            pipeline: Science pipeline.
            filenames_calib: Filename pattern for master calibration files.
            min_flats: Minimum number of raw frames to create flat field.
            output: Where to write results. A string is a local directory path; a dict or
                Archive is an output archive. If not set, results are written back to archive.
            create_calibs: If False, no calibration files are created for night.
            calib_science: If False, no science frames are calibrated.
            progress_callback: See ReductionBase.
        """
        super().__init__(archive=archive, pipeline=pipeline, min_flats=min_flats, progress_callback=progress_callback)

        self._store_local: str | None = output if isinstance(output, str) else None
        self._output_archive = (
            self._archive if output is None or isinstance(output, str) else get_object(output, Archive)
        )
        self._create_calibs = create_calibs
        self._calib_science = calib_science

        # make sure the local output directory exists
        if self._store_local:
            os.makedirs(self._store_local, exist_ok=True)

        # default filename patterns
        self._fmt_calib = FilenameFormatter(filenames_calib)

        # populated by _count_science_frames() at the start of __call__, consumed by _calib_data()
        # so science frames are only listed from the archive once per combination, not twice
        self._science_frame_cache: dict[tuple[str, str, str], list[FrameInfo]] = {}
        self._frames_done = 0
        self._frames_total = 0

    async def _create_master_calib(
        self, night: str, instrument: str, image_type: ImageType, binning: str, filter_name: str | None = None
    ) -> Image | None:
        # get frames
        infos = await self._archive.list_frames(
            night=night,
            image_type=image_type,
            filter_name=filter_name,
            instrument=instrument,
            binning=binning,
            rlevel=0,
        )

        # log it
        fltr = "" if filter_name is None else " in " + filter_name
        log.info("Found %d %s %s frames%s from instrument %s.", len(infos), binning, image_type, fltr, instrument)

        # if too few, we're finished
        if len(infos) < 3:
            if len(infos) > 0:
                log.warning("Too few (%d) frames found, skipping...", len(infos))
            return None

        # download frames
        images = await self._archive.download_frames(infos)
        if len(images) < 3:
            log.warning("Too few (%d) frames found, skipping...", len(infos))
            return None

        # create master
        calib: Image | None = None
        if image_type == ImageType.BIAS:
            # BIAS are easy, just combine
            calib = await self._pipeline.create_master_bias(images)
            if calib is None:
                log.warning("Could not create master bias.")
                return None

            # store in cache
            self._master_frames[ImageType.BIAS, instrument, binning, None] = calib

        elif image_type == ImageType.DARK:
            # for DARKs, we first need a BIAS
            bias = await self._find_master(night, ImageType.BIAS, instrument, binning, None)
            if bias is None:
                log.error("Could not find BIAS frame, skipping...")
                return None

            # combine
            calib = await self._pipeline.create_master_dark(images, bias=bias)
            if calib is None:
                log.warning("Could not create master dark.")
                return None

            # store in cache
            self._master_frames[ImageType.DARK, instrument, binning, None] = calib

        elif image_type == ImageType.SKYFLAT:
            # got enough frames?
            if len(images) < self._min_flats:
                log.warning("Not enough flat fields found for combining.")
                return None

            # for SKYFLATs, we first need a BIAS
            bias = await self._find_master(night, ImageType.BIAS, instrument, binning, None)
            if bias is None:
                log.error("Could not find BIAS frame, skipping...")
                return None

            # combine
            calib = await self._pipeline.create_master_flat(images, bias=bias)
            if calib is None:
                log.warning("Could not create master flat.")
                return None

            # store in cache
            self._master_frames[ImageType.SKYFLAT, instrument, binning, filter_name] = calib

        else:
            raise ValueError("Invalid image type")

        # filename
        calib.format_filename(self._fmt_calib)

        # save/upload
        if self._store_local:
            path = os.path.join(self._store_local, calib.header["FNAME"])
            log.info("Storing master calibration frame as %s...", path)
            calib.writeto(path, overwrite=True)
        else:
            log.info("Uploading master calibration frame as %s...", calib.header["FNAME"])
            await self._output_archive.upload_frames([calib])

        self._report_progress(
            MasterCalibCreated(
                image_type=image_type,
                instrument=instrument,
                binning=binning,
                filter_name=filter_name,
                filename=calib.header["FNAME"],
            )
        )

        # finished
        return calib

    async def _count_science_frames(self, night: str, options: dict[str, list[Any]]) -> int:
        """Pre-pass: list (not download) OBJECT frames for every instrument/binning/filter
        combination once, caching the results so _calib_data() doesn't have to list them
        again, and return the total count across the whole night for progress reporting."""
        total = 0
        for instrument in options["instruments"]:
            for binning in options["binnings"]:
                for filter_name in options["filters"]:
                    infos = await self._archive.list_frames(
                        night=night,
                        instrument=instrument,
                        image_type=ImageType.OBJECT,
                        binning=binning,
                        filter_name=filter_name,
                        rlevel=0,
                    )
                    self._science_frame_cache[instrument, binning, filter_name] = infos
                    total += len(infos)
        return total

    async def _calib_data(self, night: str, instrument: str, binning: str, filter_name: str) -> None:
        infos = self._science_frame_cache.get((instrument, binning, filter_name), [])
        total = len(infos)
        if total == 0:
            return
        log.info("Calibrating %d OBJECT frames...", total)

        # run all science frames
        for i, info in enumerate(infos, 1):
            log.info("(%d/%d) Calibrating file %s...", i, total, info.filename)

            try:
                # download frame
                images = await self._archive.download_frames([info])
                image = images[0]

                # calibrate
                calibrated = await self._pipeline.calibrate(image)

                # save/upload
                if self._store_local:
                    path = os.path.join(self._store_local, calibrated.header["FNAME"])
                    log.info("(%d/%d) Storing calibrated images as %s...", i, total, path)
                    calibrated.writeto(path, overwrite=True)
                else:
                    log.info("(%d/%d) Uploading calibrated images as %s...", i, total, calibrated.header["FNAME"])
                    await self._output_archive.upload_frames([calibrated])

                self._frames_done += 1
                self._report_progress(
                    ScienceFrameProcessed(
                        index=self._frames_done, total=self._frames_total, filename=info.filename, status="ok"
                    )
                )

            except Exception as e:
                log.exception("(%d/%d) Error processing image %s.", i, total, info.filename)
                self._frames_done += 1
                self._report_progress(
                    ScienceFrameProcessed(
                        index=self._frames_done,
                        total=self._frames_total,
                        filename=info.filename,
                        status="error",
                        error=str(e),
                    )
                )

    async def __call__(self, site: str, night: str) -> None:
        """Reduces all data im this night."""

        # get options
        log.info("Retrieving configurations for site %s at night %s...", site, night)
        options = await self._archive.list_options(night=night, site=site)
        log.info(
            "Got data for %d instruments, %d binnings, and %d filters.",
            len(options["instruments"]),
            len(options["binnings"]),
            len(options["filters"]),
        )

        # pre-pass: know the total science-frame count up front for progress reporting, and
        # cache the per-combination frame lists so _calib_data() doesn't list them again
        if self._calib_science:
            self._frames_total = await self._count_science_frames(night, options)

        # loop instruments
        for instrument in options["instruments"]:
            log.info("Reducing data for instrument %s...", instrument)

            # loop binnings
            for binning in options["binnings"]:
                # create bias and dark
                if self._create_calibs:
                    try:
                        await self._create_master_calib(night, instrument, ImageType.BIAS, binning)
                    except Exception:
                        log.exception("Error creating master bias for instrument %s, binning %s.", instrument, binning)
                    try:
                        await self._create_master_calib(night, instrument, ImageType.DARK, binning)
                    except Exception:
                        log.exception("Error creating master dark for instrument %s, binning %s.", instrument, binning)

                # loop filters
                for filter_name in options["filters"]:
                    # create flat
                    if self._create_calibs:
                        try:
                            await self._create_master_calib(night, instrument, ImageType.SKYFLAT, binning, filter_name)
                        except Exception:
                            log.exception(
                                "Error creating master flat for instrument %s, binning %s, filter %s.",
                                instrument,
                                binning,
                                filter_name,
                            )

                    # calibrate science data
                    if self._calib_science:
                        await self._calib_data(night, instrument, binning, filter_name)


__all__ = ["Reduction"]
