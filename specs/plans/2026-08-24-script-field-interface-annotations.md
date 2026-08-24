# Plan: Tag `Script` module-name fields with required `pyobs.interfaces` via `Annotated`

Status: implemented, PR open. Tracks github.com/pyobs/pyobs-core#808 (requested by
pyobs/pyobs-robotic-backend#98). PR #809 opened and approved, not yet merged.

## Problem

Module-name fields on `Script` subclasses (`ImagingScript.camera`, `.telescope`, etc.) are plain
`str`/`str | None`, with no machine-readable signal for which `pyobs.interfaces` interface the
referenced module must implement. That requirement exists only implicitly, in each script's
`run()`/`can_run()` code, as literal interface classes passed to
`self.comm.proxy(...)`/`has_proxy(...)`/`safe_proxy(...)`.

pyobs-robotic-backend wants to render these fields as dropdowns of the modules actually configured
on a site, filtered to only those implementing the right interface. Doing that today would need a
hand-maintained table in pyobs-robotic-backend duplicating what's already implicit in this repo's
`run()` code, with no way to detect drift when a script's interface requirements change here.

## Approach

Tag each module-name field with the interface(s) it requires via `typing.Annotated`, using the
real interface class(es) as metadata:

```python
camera: Annotated[str, ICamera]
telescope: Annotated[str | None, ITelescope] = None
```

Confirmed against pydantic 2.13.4 (what this repo's lockfile resolves to; `pyproject.toml` pins
`>=2.12.5`): arbitrary classes placed in
`Annotated` are accepted without validation and preserved in `FieldInfo.metadata`
(`cls.model_fields["camera"].metadata`) for a consumer to introspect. This changes nothing about
validation or runtime behavior — fields keep behaving exactly as plain `str`/`str | None` today.
No JSON Schema / dropdown / UI concerns belong in this repo; that's entirely
pyobs-robotic-backend's job downstream of this metadata.

## Tagging rule (resolves the issue's "open question")

Include an interface in a field's `Annotated` tag only if the field is passed as the `obj_type` to
an actual `self.comm.proxy()` / `safe_proxy()` / `has_proxy()` call somewhere in that class.

Two categories are excluded even though they show up when grepping for interface names near a
field:

1. **`get_state(X)` calls on an already-typed proxy.** E.g. `ImagingScript.can_run` does
   `safe_proxy(self.telescope, ITelescope)` and then `telescope.get_state(IReady)` on that same
   object — `IReady` here is a cached-state read, not a requirement that the module implement
   `IReady` as a proxy type (the code already handles `ready_state is None` gracefully). It's also
   structurally redundant: `ITelescope → IMotion → IReady`, so anything already required to
   implement `ITelescope` implements `IReady` by inheritance anyway.
2. **An interface already implied by another interface in the same field's tag**, via the
   interface's own Python inheritance — even if that interface *was* reached through a genuine
   `proxy()`/`safe_proxy()` call. E.g. `AutoFocusScript.run()` does
   `safe_proxy(self.telescope, IMotion)` for `stop_motion()`, a real proxy call — but `ITelescope`
   is already required on that same field and `ITelescope → IMotion`, so tagging `IMotion`
   separately adds no filtering information.

This is **not** a blanket "drop anything reachable via `get_state`" rule — `PointingScript.telescope`
does `self.comm.proxy(self.telescope, IReady)` as a genuine, separate proxy call (not
`get_state()` on an already-`IPointingAltAz`-typed object), and `IPointingAltAz` does not inherit
`IReady`, so that one is a real, non-redundant requirement and stays tagged.

## Corrected field audit

Re-auditing every `run()`/`can_run()` against the rule above turned up four discrepancies against
the issue's own table — two omissions on `ImagingScript`, and two more (`SkyFlatsScript.flatfield`,
`SelectorScript.selector`) found while re-verifying the other fields with the same method. All four
are fields where the issue's table listed a real "must implement" interface as absent, which would
have under-tagged the field relative to what the code actually requires.

| Class | Field | Tag | Note |
|---|---|---|---|
| `ImagingScript` | `camera` | `Annotated[str, ICamera, IBinning, IWindow, IExposureTime, IImageType]` | Issue table only had `ICamera`; `_setup_instrument_config` also `safe_proxy`s `camera` as `IBinning`/`IWindow`/`IExposureTime`/`IImageType` (same pattern `DarkBiasScript.camera` already gets credit for) |
| `ImagingScript` | `telescope` | `Annotated[str \| None, ITelescope, IPointingRaDec] = None` | Issue table had `ITelescope, IReady`; `IReady` dropped (get_state-only + implied by `ITelescope`); `IPointingRaDec` added — `_start_move_radec` does `comm.proxy(self.telescope, IPointingRaDec)`, a hard requirement the table missed entirely |
| `ImagingScript` | `filters` | `Annotated[str \| None, IFilters] = None` | same interface as issue table, converted to `Annotated` for consistency with the rest of the class |
| `ImagingScript` | `autoguider` | `Annotated[str \| None, IAutoGuiding] = None` | same, converted for consistency |
| `ImagingScript` | `acquisition` | `Annotated[str \| None, IAcquisition] = None` | same, converted for consistency |
| `DarkBiasScript` | `camera` | `Annotated[str, IData, IBinning, IWindow, IExposureTime, IImageType]` | unchanged, matches issue |
| `PointingScript` | `telescope` | `Annotated[str, IPointingAltAz, IReady]` | unchanged — `IReady` here is a genuine separate `proxy()` call, not redundant (see tagging rule) |
| `AutoFocusScript` | `telescope` | `Annotated[str, ITelescope, IPointingRaDec] = "telescope"` | Issue table had `ITelescope, IReady, IPointingRaDec, IMotion`; `IReady` dropped (get_state-only), `IMotion` dropped (implied by `ITelescope` even though reached via a real `safe_proxy` call — see rule's second category) |
| `AutoFocusScript` | `autofocus` | `Annotated[str, IAutoFocus] = "autofocus"` | unchanged |
| `SkyFlatsScript` | `roof` | `Annotated[str, IRoof]` | `IReady` dropped (get_state-only + implied by `IRoof → IMotion → IReady`) |
| `SkyFlatsScript` | `telescope` | `Annotated[str, ITelescope]` | `IReady` dropped, same reason |
| `SkyFlatsScript` | `flatfield` | `Annotated[str, IBinning, IFilters, IFlatField]` | Issue table only had `IFlatField`; `run()` also does `proxy(self.flatfield, IBinning)` (hard) and `safe_proxy(self.flatfield, IFilters)` — both missed |
| `SelectorScript` | `mode` | *not tagged* | Not a module-name field — it's a mode-name string passed to `selector.set_mode(self.mode)`, never used as a `comm.proxy` target. The issue's table incorrectly grouped it with `selector` under `IMode` |
| `SelectorScript` | `selector` | `Annotated[str, IMode, IMotion]` | Issue table only had `IMode`; `can_run` also does `proxy(self.selector, IMotion)` for `wait_for_state(IMotion, ...)` — a hard requirement the table missed (`IMode` does not inherit `IMotion`, so both are needed) |

`CallModuleScript.module`/`.interface` (`robotic/scripts/utils/callmodule.py`) stays excluded per
the issue — `.interface` is a dynamic FQCN string chosen by the caller, not a fixed interface.

## Implementation checklist

- [x] `pyobs/robotic/scripts/imaging/imaging.py` — tagged all five module-name fields (`camera`,
      `telescope`, `filters`, `autoguider`, `acquisition`) with `Annotated`, including
      `filters`/`autoguider`/`acquisition` for consistency even though each is single-interface and
      unchanged from the issue's table
- [x] `pyobs/robotic/scripts/calibration/darkbias.py` — tagged `camera`
- [x] `pyobs/robotic/scripts/calibration/pointing.py` — tagged `telescope`
- [x] `pyobs/robotic/scripts/imaging/autofocus.py` — tagged `telescope`, `autofocus`
- [x] `pyobs/robotic/scripts/calibration/skyflats.py` — tagged `roof`, `telescope`, `flatfield`
- [x] `pyobs/robotic/scripts/control/selector.py` — tagged `selector` only, `mode` left as plain `str`
- [x] Added `tests/robotic/scripts/test_field_interface_annotations.py` — 9 tests asserting the
      exact `Annotated` metadata for every tagged field across all 6 script classes
- [x] `pyrefly check` clean on all changed files
- [x] Confirmed no runtime/validation behavior changed: full non-integration suite passes (1585
      passed, 1 pre-existing unrelated failure confirmed identical on `develop`)
- [x] Posted the corrected audit table as a comment on #808 before implementing:
      github.com/pyobs/pyobs-core/issues/808#issuecomment-5394604012
- [x] PR #809 opened, reviewed (approved) — not yet merged
