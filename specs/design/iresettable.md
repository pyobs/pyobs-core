# `IResettable`: reset a device to its defaults

Status: implemented (2026-09-27). Plan:
[`2026-09-27-data-pipeline-stack-reset.md`](../plans/2026-09-27-data-pipeline-stack-reset.md).

Repos: pyobs-core (interface, base classes, `Module.startup()`, robotic scripts), driver plugins
(pyobs-asi, pyobs-fli, pyobs-flipro, pyobs-qhyccd, pyobs-sbig, pyobs-aravis, pyobs-tis,
pyobs-v4l, pyobs-iagvt, pyobs-monet: inherit it via the base classes, may extend `reset()` and
`full_reset()`).

Related: [`idatapipeline.md`](idatapipeline.md), [`idatastack.md`](idatastack.md).

## Problem

Camera settings in pyobs are set-then-grab: `set_exposure_time()`, `set_image_type()`,
`set_binning()`, `set_window()` store a value, and the next `grab_data()` uses it. Every setting
persists until someone changes it. A caller only overwrites the settings it knows about, so it
inherits everything else from whoever used the device before.

This was tolerable as long as all settings were ones every script sets anyway. It stops being
tolerable with `IDataPipeline` ([`idatapipeline.md`](idatapipeline.md)): a pipeline replaces the
raw data, so a pipeline left behind by an earlier user silently destroys raw frames for a script
that has never heard of pipelines (e.g. `DarkBias` taking darks through a leftover `median`
pipeline).

Operating assumption, stated explicitly because this design depends on it: **only one operator
(a person at the GUI, or the mastermind) drives a device at any time.** Two concurrent callers
are already a recipe for disaster with the existing setters, and this design does not try to fix
that. Nothing in pyobs enforces the rule; it is operational policy.

## Decision

A new, small interface. Callers call `reset()` first, then set only what they know about.

```python
class IResettable(Interface, metaclass=ABCMeta):
    """The module can reset itself to its defaults, per-acquisition settings only or completely."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def reset(self, **kwargs: Any) -> None:
        """Reset all per-acquisition settings to their defaults.

        Per-acquisition settings are the ones that only affect the next grab: exposure time,
        image type, binning, window, data pipeline, and driver-specific ones like gain. Settings
        that move hardware or change its thermal state (cooling setpoint, filter, focus, ...)
        are never touched.

        Raises:
            DeviceBusyError: If the device is currently exposing, or running a sequence or stack.
        """
        ...

    @abstractmethod
    async def full_reset(self, **kwargs: Any) -> None:
        """Reset the device completely to its configured defaults, hardware included.

        Does everything reset() does, plus hardware settings: cooling (enabled and setpoint
        from the module config) and any other driver-specific hardware state.

        Raises:
            DeviceBusyError: If the device is currently exposing, or running a sequence or stack.
        """
        ...
```

No state, no capabilities. The individual settings already publish their own state through
their setters, and `reset()` goes through those setters, so every affected state gets pushed
for free.

### Two levels: `reset()` and `full_reset()`

`reset()` runs at the start of every script, in `Imaging` once per instrument
config, so dozens of times a night. It must not touch hardware state:
- **Cooling:** an operator raising the setpoint on a warm night (the camera can't hold -20 °C)
  would be undone by the next task, and the temperature would never settle. Every setpoint
  change also costs settling time before frames are usable.
- **Filter:** an integrated filter wheel would move to its default and straight back to the
  filter the script sets, on every config.

`full_reset()` is the explicit "put everything back" call for a person or a start-of-night
routine, e.g. after the camera was warmed up during the day. It's rare and deliberate, so
hardware moves and settling time are acceptable there.

Both methods are in the interface from the start. Adding `full_reset()` later would mean
changing an existing interface, the case [`interface_versioning.md`](interface_versioning.md)
(#819) hasn't settled yet. Now it costs nothing, since nobody implements `IResettable` yet.

`Module.startup()` calls `full_reset()` (see below). Drivers move "apply configured hardware
settings" (e.g. enable cooling at the configured setpoint) out of `open()` into their
`full_reset()` override, so there is exactly one code path that puts the device into its
configured state, and it runs on every startup. `open()` keeps what must happen there:
connecting to the hardware, starting background tasks, publishing initial state.

### Why a separate interface and not a method on `IData`

- An abstract method on `IData` would break every existing `IData` implementor, including ones
  that don't inherit from a pyobs-core base class (e.g. pyobs-iagvt's
  `SunCamera(Module, ICamera, ...)`,
  `/home/husser/code/pyobs/pyobs-iagvt/pyobs_iagvt/modules/suncamera.py`).
- A concrete method on `IData` would let such implementors claim a reset they don't do.
- As a separate interface, callers use `safe_proxy(camera, IResettable)` and skip the call when
  it isn't there, the same pattern the robotic scripts already use for `IBinning`/`IWindow`.

No interface version bump is needed anywhere. Nothing existing changes signature
(see [`interface_versioning.md`](interface_versioning.md)).

### What "default" means

The value the module starts with. For the base classes, that is what `__init__` currently
hard-codes, plus the configured default pipeline:

| Setting | Default | Where |
|---|---|---|
| exposure time | `0.0` | `BaseCamera.__init__` (`self._exposure_time`) |
| image type | `ImageType.OBJECT` | `BaseCamera.__init__`, `BaseVideo.__init__` |
| binning | `1x1`, if the camera implements `IBinning` and `1x1` is in its `BinningCapabilities.binnings` (or the list is empty/unavailable) | `BaseCamera.reset()` |
| window | full frame from the module's own `WindowCapabilities`, if it implements `IWindow` and `full_frame_width > 0` | `BaseCamera.reset()` |
| data pipeline | `default_pipeline` from YAML (usually `None`) | `DataPipelineMixin` |
| gain, offset, image format, driver extras | none generic; drivers override `reset()` | driver |
| cooling (enabled, setpoint) | configured values, **`full_reset()` only** | driver overrides `full_reset()` |
| other hardware state | configured values, **`full_reset()` only** | driver overrides `full_reset()` |

No new config options for exposure time or image type. If an observatory needs a different
default, that's a later, separate change.

### Called automatically at startup

`Module.startup()` (`pyobs/modules/module.py:368`) calls `full_reset()` after the full `open()`
chain and before the transition to `ModuleState.READY`:

```python
await self.open()
if isinstance(self, IResettable):
    try:
        await self.full_reset()
    except Exception:
        log.exception("Could not reset module %s to its defaults during startup.", self.name)
# ... existing missing_published_state() check ...
await self.set_state(ModuleState.READY)
```

Why `startup()` and not `open()`: drivers call `BaseCamera.open()` first and only connect their
hardware afterwards (e.g. `FliCamera.open()`,
`/home/husser/code/pyobs/pyobs-fli/pyobs_fli/flicamera.py:49`; `QHYCCDCamera.open()`,
`/home/husser/code/pyobs/pyobs-qhyccd/pyobs_qhyccd/qhyccdcamera.py:136`). A reset inside
the base `open()` would call `set_window()` before a driver exists. `startup()` runs after
every subclass's `open()` and before any non-whitelisted RPC is accepted.

A failure is logged, not raised: a module whose hardware refuses one setting should still come
up, the same way the missing-state check right below it logs and continues.

**Behavior change for drivers that migrate:** today an exception from cooling setup in `open()`
aborts the module's startup. Once that setup lives in `full_reset()`, the same failure is only
logged and the module reaches `READY` with cooling off. That's intended (a camera without
cooling can still take biases, and the log error is visible), but each driver migration should
be a conscious decision, not a mechanical move.

Callers that use `open()` directly instead of `startup()` (some tests) don't get the reset.
That is intended. Tests of a migrated driver that relied on `open()` applying hardware settings
have to call `full_reset()` themselves.

## Base-class behavior

### `BaseCamera.reset()`

Order matters: binning before window (window coordinates can depend on binning, and
`Imaging._setup_instrument_config()` uses the same order).

1. If `self._camera_status != ExposureStatus.IDLE` or a sequence or stack is running: raise
   `exc.DeviceBusyError`.
2. `await self.set_exposure_time(0.0)`
3. `await self.set_image_type(ImageType.OBJECT)`
4. If `isinstance(self, IBinning)`: read `self.comm.get_own_capabilities(IBinning)`. If it is
   `None`, has an empty `binnings` list, or contains `Binning(1, 1)`: `await self.set_binning(1, 1)`.
   Otherwise log a warning and skip.
5. If `isinstance(self, IWindow)`: read `self.comm.get_own_capabilities(IWindow)`. If it is not
   `None` and `full_frame_width > 0` and `full_frame_height > 0`:
   `await self.set_window(full_frame_x, full_frame_y, full_frame_width, full_frame_height)`.
   Otherwise log a warning and skip.
6. `await self.set_pipeline(self._default_pipeline)` (from `DataPipelineMixin`).

Note: the base `Comm.get_own_capabilities()` returns `None` (`pyobs/comm/comm.py:606`), only
real comm implementations return values. The skip paths above are therefore normal in tests.

### `BaseVideo.reset()`

1. Busy if a stack request is pending (see [`idatastack.md`](idatastack.md)): raise
   `exc.DeviceBusyError`. Pending single `grab_data()` requests don't count, `BaseVideo` serves
   those concurrently anyway.
2. `await self.set_image_type(ImageType.OBJECT)`
3. `await self.set_pipeline(self._default_pipeline)`

`BaseVideo` doesn't own an exposure time (drivers like `AravisCamera` and `DummyVideo` implement
`IExposureTime` themselves), so there's nothing to reset there. Drivers that want it override.

### `BaseSpectrograph.reset()`

Busy check only (`self._spectrograph_status != ExposureStatus.IDLE` or a sequence running).
`BaseSpectrograph` has no settings of its own. Implementing `IResettable` there gives drivers a
hook (e.g. pyobs-iagvt's `FTS` could reset its scan mode) and gives callers one uniform call.

### `full_reset()` in the base classes

`BaseCamera`, `BaseVideo` and `BaseSpectrograph` implement `full_reset()` as just
`await self.reset(**kwargs)`. The base classes can't reset cooling generically: `ICooling` only
has `set_cooling(enabled, setpoint)`, and each driver keeps its configured setpoint in its own
attribute (`FliCamera` in `self._temp_setpoint`, `AsiCoolCamera` takes `setpoint` in its own
`__init__`), so the base class doesn't know the default.

### Drivers

Drivers with extra per-acquisition settings override `reset()` and call the base first:

```python
async def reset(self, **kwargs: Any) -> None:
    await BaseCamera.reset(self, **kwargs)
    await self.set_gain(self._default_gain)
```

Drivers with hardware state override `full_reset()`, calling their own `reset()` first (not
`BaseCamera.full_reset()`, which would just call `reset()` a second time):

```python
async def full_reset(self, **kwargs: Any) -> None:
    await self.reset(**kwargs)
    await self.set_cooling(True, self._default_setpoint)
```

Until a driver does that, its extra settings (e.g. gain on `QHYCCDCamera`, `AsiCamera`) are
*not* reset, and `full_reset()` does nothing more than `reset()`, even though the driver
advertises `IResettable`. Unmigrated drivers keep applying their hardware settings in `open()`,
so startup behaves exactly as today. A driver that overrides `full_reset()` but also still
applies the same settings in `open()` just applies them twice at startup, which is harmless but
should be cleaned up. This is a known, accepted gap. The plan lists the affected drivers as
follow-ups rather than blocking on them.

`DummyCamera` gets a `full_reset()` override that restores its initial cooling
(`CoolingStatus()` defaults: enabled, -10 °C), so both the base path and an override are covered
by tests.

Follow-up issues opened 2026-09-27 against [pyobs-core 2.11.0](https://github.com/pyobs/pyobs-core/releases/tag/v2.11.0)
(see `specs/plans/2026-09-27-data-pipeline-stack-reset.md`, phase 7/8, for the survey and drafts).
All implemented and pushed to `develop` 2026-09-28; none of the issues have been closed yet.

- pyobs-asi: https://github.com/pyobs/pyobs-asi/issues/43 -- done, `5550ff8`
- pyobs-fli: https://github.com/pyobs/pyobs-fli/issues/99 -- done, `49d8feb`
- pyobs-flipro: https://github.com/pyobs/pyobs-flipro/issues/49 -- done, `98d38cd`
- pyobs-qhyccd: https://github.com/pyobs/pyobs-qhyccd/issues/78 -- done, `31c5b75`. The issue text's
  "needs a default policy" framing turned out to be wrong -- `open()` already hardcoded gain=10/
  offset=140 before reading them back, the survey just missed those two lines. Fixed by making
  them `default_gain`/`default_offset` constructor options instead of a new design question; issue
  text is now stale and should be corrected or closed.
- pyobs-sbig: https://github.com/pyobs/pyobs-sbig/issues/87 -- done, `e73dae3`
- pyobs-aravis: https://github.com/pyobs/pyobs-aravis/issues/52 -- done, `f855158`
- pyobs-iagvt (GWDG GitLab): https://gitlab.gwdg.de/iagvt/pyobs-iagvt/-/work_items/33 -- done,
  `1f0587a`. The exposure-time gap (item 3, shared with `GregoryCamera`) still needs the
  `pyobs-aravis>=2.0.0` pin bumped to a release containing `f855158` before it actually takes
  effect -- the fix is inherited automatically once that happens, no further code change needed.
- pyobs-monet (GWDG GitLab): https://gitlab.gwdg.de/monet/pyobs-monet/-/work_items/17 -- done,
  `01b03f3`

## Callers

The robotic scripts that configure a camera call `reset()` first, before any `set_*()`:

```python
async with self.comm.safe_proxy(self.camera, IResettable) as camera:
    if camera:
        await camera.reset()
```

Scripts, not helpers: `reset()` goes where a task *starts* configuring the camera, never into
helper objects that run inside a task that has already configured it (e.g.
`pyobs/robotic/utils/exptime/stellarexptime.py`, `pyobs/robotic/utils/skyflats/flatfielder.py`).
A reset there would wipe the calling script's own settings. The exact list is in the plan.

Nothing in pyobs-core calls `full_reset()` yet. Intended callers, as follow-ups: a "full reset"
button in pyobs-gui, and possibly the mastermind at the start of the night.

## Not in scope

- Enforcing the single-operator rule. Worth its own ADR or steering note, since this design and
  the existing set-then-grab model both depend on it.
- Configurable defaults for exposure time and image type.
- GUI "reset" and "full reset" buttons (pyobs-gui). Easy to add later.
- Calling `full_reset()` from the mastermind at the start of the night.
- Driver `full_reset()` overrides and moving hardware setup out of `open()` (cooling etc.),
  except `DummyCamera`.
