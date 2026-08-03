# Plan: `pyobs-gui` IAcquisition widget

Status: implemented, closed.
Repos: pyobs-gui (widget), pyobs-core (`IAcquisition` interface it consumes, already shipped)

## Shipped (pyobs-core, `develop`)

`IAcquisition` (`pyobs/interfaces/IAcquisition.py`) inherits `IRunning` and `IAbortable`:

```python
class IAcquisition(IRunning, IAbortable, metaclass=ABCMeta):
    state = AcquisitionState

    async def acquire_target(self, **kwargs: Any) -> AcquisitionResult: ...
```

`Acquisition.acquire_target()` publishes `RunningState` around the run, same pattern as
`IAutoFocus`. Per-attempt telemetry is published live via a dedicated growing state, mirroring
`AutoFocusState`:

```python
@dataclass
class AcquisitionResult:
    time: Time
    ra: Annotated[float, Unit.DEGREES]
    dec: Annotated[float, Unit.DEGREES]
    alt: Annotated[float, Unit.DEGREES]
    az: Annotated[float, Unit.DEGREES]
    offset_frame: OffsetFrame | None = None
    offset_lon: Annotated[float, Unit.DEGREES] | None = None
    offset_lat: Annotated[float, Unit.DEGREES] | None = None

@dataclass
class AcquisitionAttempt:  # AcquisitionState.attempts element
    attempt: int
    distance: Annotated[float, Unit.ARCSEC]
    offset_applied: bool
    offset_frame: OffsetFrame | None = None
    offset_lon: Annotated[float, Unit.DEGREES] | None = None
    offset_lat: Annotated[float, Unit.DEGREES] | None = None

@dataclass
class AcquisitionState:
    attempts: list[AcquisitionAttempt] = field(default_factory=list)
    result: AcquisitionResult | None = None
    time: Time = field(default_factory=Time.now)
```

Note this is `offset_frame`/`offset_lon`/`offset_lat`, not the originally-sketched
`off_ra`/`off_dec`/`off_alt`/`off_az` (see "Resolved from the original open questions" below) —
`off_ra`/`off_dec` and `off_alt`/`off_az` were mutually-exclusive duplicate field pairs, since only
one is ever populated depending on mount type; a single `offset_frame` enum + generic `lon`/`lat`
pair replaces both. `OffsetFrame` itself lives in `pyobs/utils/enums.py` (alongside `Unit`), not in
this file — it's shared with `IAutoGuiding` and `pyobs.utils.offsets`.

`offset_frame`/`offset_lon`/`offset_lat` report the telescope's **cumulative** offset (queried via
`IOffsetsRaDec`/`IOffsetsAltAz` state, through a small `Acquisition._get_offsets()` helper), fetched
after each attempt applies a correction and once more for the final result. This is deliberately
different from `IAutoGuiding`'s `GuidingState`, which reports the size of each individual correction,
not a cumulative value — see `gui-iautoguiding-widget.md` for why the two interfaces need different
semantics despite looking superficially similar.

`Acquisition._acquire()` publishes a new `AcquisitionAttempt` as soon as the distance is known
(before applying the correction, so the distance plot updates immediately), then republishes the
same attempt with `offset_frame`/`offset_lon`/`offset_lat` filled in once the correction is applied.

## Widget design (pyobs-gui) — shipped

Same visual language as the `IAutoFocus` widget, but with **two** plots side by side
(`plt.subplots(1, 2)` in a single `framePlot`):

- left (`ax`): distance-to-target (arcsec) vs. attempt number, integer x-axis ticks
  (`MaxNLocator(integer=True)`)
- right (`ax2`): 2D trajectory of the accumulated offset in whichever frame the mount supports
  (RA/Dec or Alt/Az, degrees), points connected by a line since this is a single converging run,
  with distinct "start" (red square) and "latest" (green star) markers and reference crosshairs at
  (0, 0) — this is what actually motivated moving to `offset_frame`/`offset_lon`/`offset_lat`, since
  a fixed set of four `off_*` labels couldn't drive a "show whichever pair is real" plot cleanly
- `buttonAcquire` (green) / `buttonAbort` (red), grey out via ACL (`permitted("acquire_target")`/
  `permitted("abort")`, same convention as `telescopewidget.py`/`filterwidget.py`/`modewidget.py`)
- `labelStatus` — Idle / Acquiring... / `Acquired.`
- Result group box: RA/Dec, Alt/Az, and a single offset row whose label text switches between
  "RA/Dec offset:"/"Alt/Az offset:" based on `AcquisitionResult.offset_frame`

State handling (`_on_running_state`/`_on_acquisition_state`) matches the original sketch: clear
`self._attempts`/`self._result` on the `IRunning` rising edge, otherwise just mirror
`AcquisitionState.attempts`/`.result` and re-render on every update.

## Resolved from the original open questions

- ~~`off_ra`/`off_dec` vs `off_alt`/`off_az` are mutually exclusive~~ — resolved by replacing both
  pairs with a single `offset_frame` (`OffsetFrame.RA_DEC`/`ALT_AZ`) + `offset_lon`/`offset_lat`
  pair, in both `AcquisitionResult` and `AcquisitionAttempt`. The widget picks the right axis
  labels/result-row text from `offset_frame` instead of checking which pair is non-`None`.
- ~~Should `attempts` be capped~~ — left uncapped, as expected: it's naturally bounded by
  `self._attempts` (the configured max attempt count), same reasoning as before.
