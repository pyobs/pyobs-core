"""Regression tests for pyobs/pyobs-core#808: module-name fields on Script subclasses are
tagged via typing.Annotated with the pyobs.interfaces classes a proxy for that field must
implement, so pyobs-robotic-backend can read FieldInfo.metadata to build interface-filtered
module dropdowns."""

from __future__ import annotations

from pyobs.interfaces import (
    IAcquisition,
    IAutoFocus,
    IAutoGuiding,
    IBinning,
    ICamera,
    IData,
    IExposureTime,
    IFilters,
    IFlatField,
    IImageType,
    IMode,
    IMotion,
    IPointingAltAz,
    IPointingRaDec,
    IReady,
    IRoof,
    ITelescope,
    IWindow,
)
from pyobs.robotic.scripts.calibration.darkbias import DarkBiasScript
from pyobs.robotic.scripts.calibration.pointing import PointingScript
from pyobs.robotic.scripts.calibration.skyflats import SkyFlatsScript
from pyobs.robotic.scripts.control.selector import SelectorScript
from pyobs.robotic.scripts.imaging.autofocus import AutoFocusScript
from pyobs.robotic.scripts.imaging.imaging import ImagingScript


def _metadata(cls: type, field: str) -> list[object]:
    return list(cls.model_fields[field].metadata)


def test_imaging_script_camera_tagged_with_all_required_interfaces() -> None:
    assert _metadata(ImagingScript, "camera") == [ICamera, IBinning, IWindow, IExposureTime, IImageType]


def test_imaging_script_telescope_tagged_without_redundant_iready() -> None:
    assert _metadata(ImagingScript, "telescope") == [ITelescope, IPointingRaDec]


def test_imaging_script_single_interface_fields() -> None:
    assert _metadata(ImagingScript, "filters") == [IFilters]
    assert _metadata(ImagingScript, "autoguider") == [IAutoGuiding]
    assert _metadata(ImagingScript, "acquisition") == [IAcquisition]


def test_darkbias_script_camera_tagged_with_all_required_interfaces() -> None:
    assert _metadata(DarkBiasScript, "camera") == [IData, IBinning, IWindow, IExposureTime, IImageType]


def test_pointing_script_telescope_keeps_iready() -> None:
    # unlike the get_state()-only cases, PointingScript does a genuine separate
    # comm.proxy(self.telescope, IReady) call, and IPointingAltAz does not imply IReady
    assert _metadata(PointingScript, "telescope") == [IPointingAltAz, IReady]


def test_autofocus_script_telescope_tagged_without_redundant_interfaces() -> None:
    assert _metadata(AutoFocusScript, "telescope") == [ITelescope, IPointingRaDec]


def test_autofocus_script_autofocus_field() -> None:
    assert _metadata(AutoFocusScript, "autofocus") == [IAutoFocus]


def test_skyflats_script_fields_tagged_without_redundant_iready() -> None:
    assert _metadata(SkyFlatsScript, "roof") == [IRoof]
    assert _metadata(SkyFlatsScript, "telescope") == [ITelescope]
    assert _metadata(SkyFlatsScript, "flatfield") == [IBinning, IFilters, IFlatField]


def test_selector_script_selector_tagged_mode_untagged() -> None:
    # `mode` is a mode-name string passed to set_mode(), not a module reference - never tagged
    assert _metadata(SelectorScript, "selector") == [IMode, IMotion]
    assert _metadata(SelectorScript, "mode") == []
