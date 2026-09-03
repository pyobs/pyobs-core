"""Planning-time instrument capability data sourced from pyobs-portal's `instruments` app.

Plain data models mirroring the shape `InstrumentSerializer` emits
(`pyobs_portal/instruments/serializers.py`) -- no Django import, this module only ever
deserializes the JSON the portal API already returns. Hand-entered planning data only, never a
live query against `ICamera`/`IBinning`/etc.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from pyobs.utils.serialization import BaseModel


class Filter(BaseModel):
    """A single filter position in a filter wheel."""

    name: str
    position: int | None = None
    updated_at: str | None = None


class BinningOption(BaseModel):
    """Readout time for one binning mode of a camera."""

    x: int
    y: int
    readout_time_s: float | None = None
    updated_at: str | None = None


class FilterWheelCapability(BaseModel):
    """Planning-time capability data for one filter wheel.

    `module_name` is nullable -- not every filter wheel is its own addressable module (some
    cameras expose filter selection through the camera module itself), per pyobs-portal#142.
    """

    name: str = ""
    module_name: str | None = None
    filter_change_time_s: float | None = None
    updated_at: str | None = None
    filters: list[Filter] = Field(default_factory=list)


class CameraCapability(BaseModel):
    """Planning-time capability data for one camera, keyed by `module_name`."""

    module_name: str
    code: str
    pixel_size_um: float | None = None
    sensor_width_px: int | None = None
    sensor_height_px: int | None = None
    roi_min_width_px: int | None = None
    roi_min_height_px: int | None = None
    roi_step_px: int | None = None
    exposure_time_min_s: float | None = None
    exposure_time_max_s: float | None = None
    image_types: list[str] = Field(default_factory=list)
    updated_at: str | None = None
    binnings: list[BinningOption] = Field(default_factory=list)
    filter_wheels: list[FilterWheelCapability] = Field(default_factory=list)


# First-pass placeholder distance for slew-duration estimates -- there's no "current pointing"
# concept at estimate time, only a real slew *rate*, so this stands in for the actual
# destination-minus-start-position distance a real estimate would need. See
# specs/plans/2026-09-01-instrument-capability-duration-estimates.md's "Representative slew/rotate
# distance" note; pyobs-core#858/#859 track replacing this with a real distance.
#
# A default, not a hardcoded constant inside estimate_slew_time_s() below: #858/#859's real
# distances will likely differ per script (a flat-field PointingScript slew and an
# ImagingScript/AutoFocusScript target slew aren't the same kind of move), and this keeps that
# future per-caller distance a parameter on the estimate rather than a policy decision baked into
# what's meant to stay a pure mirror of the portal's data.
DEFAULT_SLEW_DISTANCE_DEG = 90.0


class TelescopeCapability(BaseModel):
    """Planning-time capability data for one telescope, keyed by `module_name`."""

    module_name: str
    aperture_mm: float | None = None
    focal_length_mm: float | None = None
    mount_type: str = ""
    slew_rate_deg_per_s: float | None = None
    updated_at: str | None = None

    def estimate_slew_time_s(self, distance_deg: float = DEFAULT_SLEW_DISTANCE_DEG) -> float | None:
        """First-pass slew-duration estimate: `distance_deg` divided by the real slew rate. None
        if `slew_rate_deg_per_s` isn't declared (or isn't positive) -- callers fall back to their
        own flat constant in that case, same as when no capability data exists at all.

        `distance_deg` defaults to `DEFAULT_SLEW_DISTANCE_DEG`, the same first-pass placeholder
        every caller uses today; a caller can pass its own once #858/#859 give it a real,
        script-specific distance instead of this shared guess.
        """
        if self.slew_rate_deg_per_s is None or self.slew_rate_deg_per_s <= 0:
            return None
        return distance_deg / self.slew_rate_deg_per_s


class DomeCapability(BaseModel):
    """Planning-time capability data for one dome, keyed by `module_name`."""

    module_name: str
    rotate_rate_deg_per_s: float | None = None
    updated_at: str | None = None


class Instrument(BaseModel):
    """One telescope + dome + camera(s) grouping, as returned by `GET /api/instruments/`.

    Purely an organizational grouping on the portal side -- it carries no module identity of its
    own; each device below carries its own `module_name`. `InstrumentCapabilities` is what
    flattens these into the module-name-keyed lookups scripts actually use.
    """

    display_name: str = ""
    notes: str = ""
    updated_at: str | None = None
    cameras: list[CameraCapability] = Field(default_factory=list)
    telescope: TelescopeCapability | None = None
    dome: DomeCapability | None = None


class InstrumentCapabilities:
    """Module-name-keyed view over a `GET /api/instruments/` response.

    Scripts only ever need one device's capability row (by the module name they already
    reference, e.g. `ImagingScript.camera`), never "the instrument" as a concept -- this flattens
    the nested portal response into direct lookups once at parse time instead of every script
    walking `instruments` and searching nested lists.
    """

    def __init__(self, instruments: list[Instrument]):
        self.instruments = instruments
        self._cameras: dict[str, CameraCapability] = {}
        self._cameras_by_code: dict[str, CameraCapability] = {}
        self._telescopes: dict[str, TelescopeCapability] = {}
        self._domes: dict[str, DomeCapability] = {}
        self._filter_wheels: dict[str, FilterWheelCapability] = {}

        for instrument in instruments:
            for camera in instrument.cameras:
                self._cameras[camera.module_name] = camera
                self._cameras_by_code[camera.code] = camera
                for wheel in camera.filter_wheels:
                    if wheel.module_name is not None:
                        self._filter_wheels[wheel.module_name] = wheel
            if instrument.telescope is not None:
                self._telescopes[instrument.telescope.module_name] = instrument.telescope
            if instrument.dome is not None:
                self._domes[instrument.dome.module_name] = instrument.dome

    @classmethod
    def from_api_response(cls, data: list[dict[str, Any]]) -> InstrumentCapabilities:
        """Parse `GET /api/instruments/`'s `results` list (already unwrapped by the caller)."""
        return cls([Instrument.model_validate(item) for item in data])

    def camera(self, module_name: str) -> CameraCapability | None:
        """The `CameraCapability` whose own `module_name` matches, or None."""
        return self._cameras.get(module_name)

    def by_camera_code(self, code: str) -> CameraCapability | None:
        """The `CameraCapability` with this fleet-wide physical camera code, or None."""
        return self._cameras_by_code.get(code)

    def telescope(self, module_name: str) -> TelescopeCapability | None:
        """The `TelescopeCapability` whose own `module_name` matches, or None."""
        return self._telescopes.get(module_name)

    def dome(self, module_name: str) -> DomeCapability | None:
        """The `DomeCapability` whose own `module_name` matches, or None."""
        return self._domes.get(module_name)

    def filter_wheel(self, module_name: str) -> FilterWheelCapability | None:
        """The `FilterWheelCapability` whose own `module_name` matches, or None."""
        return self._filter_wheels.get(module_name)


__all__ = [
    "DEFAULT_SLEW_DISTANCE_DEG",
    "Filter",
    "BinningOption",
    "FilterWheelCapability",
    "CameraCapability",
    "TelescopeCapability",
    "DomeCapability",
    "Instrument",
    "InstrumentCapabilities",
]
