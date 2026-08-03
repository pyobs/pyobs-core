# Plan: `pyobs-gui` IAutoGuiding widget

Status: in progress — first pass implemented and shipped; this doc now describes a follow-up
refinement.
Repos: pyobs-gui (widget), pyobs-core (`IAutoGuiding`/`ApplyOffsets` changes, partly proposed)

*Note: pyobs-core's actual interface name is `IAutoGuiding`, not `IGuiding` — used the real name
throughout.*

## Shipped (pyobs-core, `develop`)

`IAutoGuiding` (`pyobs/interfaces/IAutoGuiding.py`) combines `IStartStop` (→ `IRunning`) and
`IExposureTime`, and defines its own `GuidingState`:

```python
@dataclass
class GuidingState:
    loop_closed: bool = False
    last_offset_x: float | None = None  # pixel offset, axis 1
    last_offset_y: float | None = None  # pixel offset, axis 2
    time: Time = field(default_factory=Time.now)

class IAutoGuiding(IStartStop, IExposureTime, metaclass=ABCMeta):
    state = GuidingState
```

`BaseGuiding.start()`/`stop()` publish `RunningState`. `_set_loop_state()` (now `async`, all 6 call
sites in `_process_image()`/`_reset_guiding()` updated) is the single choke point every
closed/open-loop transition goes through, and publishes `GuidingState` on each one. Today it reads
`image.get_meta(PixelOffsets)` right after `self._apply(...)` succeeds, giving pixel-space `dx`/`dy`
— guider/camera-specific and not comparable across setups, exactly the gap flagged in the original
open questions below.

`DummyAutoGuiding` (`pyobs/modules/pointing/dummyguiding.py`) simulates this with a background loop
task publishing `RunningState`/`ExposureTimeState`/`GuidingState`, with an occasional simulated
"lost guide star" (open-loop) event. `AutoGuidingWidget` (pyobs-gui) exists with Start/Stop, a
loop-state label, an exposure-time control (`WatchedLabel` + `ModifiedDoubleSpinBox`, the
`init_modified(label).committed` pattern also used in `camerawidget.py` — not the
`valueChangedByUser` API originally sketched below, which doesn't exist), and a last-offset label.

## Problem: pixel offsets aren't physical, and the per-image correction is discarded

Pixel offset isn't a portable unit (pixel scale varies by camera/setup). The natural fix looked
like reusing `IAcquisition`'s `OffsetFrame`/`offset_lon`/`offset_lat` pattern — but that reports the
telescope's *cumulative* offset (queried from `IOffsetsRaDec`/`IOffsetsAltAz` state), which for
acquisition's short, converging run is exactly the useful "final answer." For guiding's
indefinitely-long session, the cumulative offset just shows the mount's slow overall drift, not the
size of each individual correction — not useful for "how well is guiding tracking right now."

The actual per-image correction (`dra`/`ddec` or `dalt`/`daz`, in arcsec) is already computed inside
`ApplyRaDecOffsets`/`ApplyAltAzOffsets.__call__` — but discarded, since `ApplyOffsets.__call__`
currently only returns `bool` (applied or not).

## Proposed pyobs-core change

Make `ApplyOffsets.__call__` return what it actually did, not just whether it succeeded:

```python
@dataclass
class OffsetResult:
    applied: bool
    frame: OffsetFrame | None = None
    lon: Annotated[float, Unit.DEGREES] | None = None  # matches RaDecOffsetState/AltAzOffsetState
    lat: Annotated[float, Unit.DEGREES] | None = None
```

`ApplyRaDecOffsets`/`ApplyAltAzOffsets` return `OffsetResult(applied=True, frame=OffsetFrame.RA_DEC,
lon=dra.degree, lat=ddec.degree)` (or `ALT_AZ`, `lon=dalt.degree, lat=daz.degree`) on success,
`OffsetResult(applied=False)` otherwise. `OffsetFrame` moves from `IAcquisition.py` to
`pyobs/utils/enums.py` (alongside `Unit`), since it's now shared by `IAcquisition`, `IAutoGuiding`,
and `pyobs.utils.offsets` — three unrelated subsystems.

`Acquisition` only needs `if await self._apply(...):` → `result = await self._apply(...); if
result.applied:` — it keeps using its own `_get_offsets()` helper for its own (correct, unchanged)
cumulative-offset-per-attempt tracking.

`BaseGuiding` drops `PixelOffsets` entirely from `_process_image()`'s offset-application block and
uses the result directly:

```python
result = await self._apply(image, telescope, self._location)
if result.applied:
    await self._set_loop_state(True, result.frame, result.lon, result.lat)
    log.info("Finished image.")
else:
    log.info("Could not apply offsets.")
    await self._set_loop_state(False)
```

`_set_loop_state(state, frame=None, lon=None, lat=None)` stores `self._last_offset_frame/_lon/_lat`
(replacing the pixel tuple) and publishes `GuidingState(loop_closed=state, offset_frame=...,
offset_lon=..., offset_lat=...)` — same "keep last known value when not provided" behavior as
today. `GuidingState` becomes:

```python
@dataclass
class GuidingState:
    loop_closed: bool = False
    offset_frame: OffsetFrame | None = None
    offset_lon: Annotated[float, Unit.DEGREES] | None = None
    offset_lat: Annotated[float, Unit.DEGREES] | None = None
    time: Time = field(default_factory=Time.now)
```

`DummyAutoGuiding` simulates a small RA/Dec offset in degrees (`random.gauss(0.0, 1.0/3600)`, ~1
arcsec stddev) instead of the pixel-scale simulation, publishing `offset_frame=OffsetFrame.RA_DEC`.

`GuidingStatisticsPixelOffset`'s independent per-client FITS-header RMS stats are untouched — they
read `PixelOffsets` separately, for a different purpose, and don't go through `_set_loop_state`.

## Widget design (pyobs-gui)

Guiding is continuous rather than one-shot, so unlike acquisition's single converging trajectory,
this is a live rolling window: two plots (mirroring `AcquisitionWidget`'s two-subplot layout) plus
the existing status/controls:

- `framePlot` — a `plt.subplots(1, 2)` figure:
  - left: offset magnitude (`sqrt(lon**2+lat**2)`, arcsec) vs. sample index over the last N
    corrections, integer x-axis ticks (`MaxNLocator(integer=True)`)
  - right: lon/lat scatter of the same N points, in arcsec, **not** connected by a line (unlike
    acquisition — this is an ongoing process, not a single converging run), latest point marked
    distinctly, reference crosshairs at (0, 0), axis labels driven by `offset_frame`
- `buttonStart` / `buttonStop`, enabled based on `RunningState.running`
- Status label for `loop_closed` — "Closed loop" / "Open loop" / "Stopped"
- `spinExposureTime` (`ModifiedDoubleSpinBox`) + `labelExposureTime` (`WatchedLabel`), the same
  `init_modified(label).committed.connect(...)` pattern as `camerawidget.py`'s gain/window controls
- Last offset label, in arcsec

The rolling window (`deque(maxlen=50)` of `(lon_arcsec, lat_arcsec)`) is accumulated client-side in
the widget from each `GuidingState` update — not tracked in `GuidingState` itself. Unlike
`AcquisitionState.attempts` (naturally bounded by a short, finite run), a guiding session runs
indefinitely; publishing a growing/capped history on every processed image would be wasteful
bandwidth-wise, and "how many points to show" is a display concern the widget should own, not the
wire schema.

The widget resets its rolling window on the `IRunning` rising edge (a fresh `start()`), same
convention as `AutoFocusWidget`/`AcquisitionWidget` clearing their state on a new run.

## Known bug in the shipped widget (to fix alongside this change)

`AutoGuidingWidget.__init__` initializes `self._exposure_time = 0.0`, but the `.ui` file's
`spinExposureTime` default is `0.1` (its `minimum`). `_on_exptime_state`'s dirty-check
(`self.spinExposureTime.value() == self._exposure_time`) is `0.1 == 0.0` on the very first state
update, so it's treated as "user has diverged" and the spin box is never pre-filled from live state.
Fix: initialize `self._exposure_time: float | None = None` and treat `None` as always-synced.

## Resolved from the original open questions

- ~~`_set_loop_state` currently isn't `async`~~ — done; all 6 call sites updated (mechanical change,
  all already in async context).
- ~~Whether `last_offset_x/y` (pixel offsets) is the right unit~~ — resolved above: arcsec, via
  `OffsetResult` from `ApplyOffsets`, not pixel scale or `GuidingStatisticsSkyOffset` (which isn't
  reliably populated in real guiding pipelines — only a `DummySkyOffsets` test processor sets it).
- No live RMS in `GuidingState` — still out of scope. The rolling-window plot in the widget gives an
  eyeballable sense of scatter without needing a new wire-level RMS field; still easy to add later
  if needed.
