# Plan: pyobs-iag50 pyobs-core 2.x migration

No GitHub issue — pyobs-iag50 is IAG-internal (GitLab, not in the `pyobs` GitHub org).
Repos: pyobs-iag50 only.

Status: in progress. Steps done so far (2026-08-23): `1.x` branch cut from the last known-good
1.x state (`f4711a8`); `develop` reset to `2.0.0.dev0` with `pyobs-core>=2.0.0.dev93,<3`
(`e42ad3f`) — see "What's already done" below for why the reset was needed. The actual code
migration below is **not yet done**.

## Problem

pyobs-iag50's `pyproject.toml` was bumped to `2.0.0.dev2` at some point, but the `pyobs-core`
dependency stayed pinned `>=1,<2` and the lockfile had actually resolved `pyobs-core==1.25.4` —
the version number claimed 2.x compatibility that was never real. Confirmed by actually running
the code against `pyobs-core==2.0.0.dev93`: the package doesn't even import.

Repo is small — two real modules, no tests, no CI:

- `pyobs_iag50/pointing.py` — `Pointing(PointingSeries)`, used in production
  (`config/iag50srv/pointing.yaml`).
- `pyobs_iag50/aligntest.py` — `AlignGridTest(Module, IAutonomous, IFitsHeaderBefore)`, used from
  `config/test/aligntest.yaml`, not exported from `pyobs_iag50/__init__.py` (only `Pointing` is).

## What's already done

- `1.x` branch (`f4711a8`): preserves the actual last-1.x-compatible state, for reference/rollback.
- `develop` reset to `2.0.0.dev0` (`e42ad3f`), `pyobs-core` pin bumped to `>=2.0.0.dev93,<3`.
  Resetting the dev counter (rather than continuing from `dev2`) marks this as the real start of
  2.x work, since the prior `dev1`/`dev2` bumps didn't correspond to verified 2.x compatibility.

## What's broken — verified against pyobs-core 2.0.0.dev93

Verified by `uv sync` + `uv run python -c "import ..."` + `uv run pyrefly check pyobs_iag50/`,
not guessed from a changelog:

1. **`aligntest.py` doesn't import**: `from pyobs.utils.grids import SphericalGrid` — no longer
   exists. The grid API was redesigned (some point after `1.25.4`) from a flat point-list class
   into a composable pipeline: `pyobs.utils.grids.grid.{Grid, RegularSphericalGrid,
   GraticuleSphericalGrid}` (`Grid` implements the iterator protocol,
   `pyobs/utils/grids/gridnode.py:43-49`) plus filter stages in
   `pyobs.utils.grids.filters.{GridFilterValue, ConvertGridToSkyCoord, ConvertGridFrame,
   RandomizeGrid, AvoidMoon, FromList}`, composed by `pyobs.utils.grids.pipeline.GridPipeline`.
   `GraticuleSphericalGrid` (`pyobs/utils/grids/grid.py:91-138`) is the *exact same* Deserno-2004
   equidistribution algorithm as the old `SphericalGrid.equidistributed` — same formula, same
   output shape (a `(lon_deg, lat_deg)` tuple per point) — just packaged as an iterator instead of
   returning a plain list.
2. **`self.proxy(...)` is no longer directly awaitable.** It now returns a `_ProxyContext`
   (`pyobs/comm/proxy.py:266-281`), meant to be used as `async with self.proxy(name, Type) as x:`.
   `await self.proxy(...)` raises (`pyrefly`: `not-async`). Three call sites in
   `aligntest.py:84-86` (telescope, cam1, cam2).
3. **`PointingSeries.__init__` now requires a `grid` argument** (`pyobs/modules/robotic/pointing.py:23-30`,
   `grid: list[Grid | GridFilter | dict[str, Any]]`, no default) — confirmed by instantiating
   `Pointing(log_file=...)`, which raises `TypeError: PointingSeries.__init__() missing 1
   required positional argument: 'grid'`. In 1.x, `alt_range`/`az_range`/`dec_range`/`exp_time`
   were apparently accepted directly by `PointingSeries` (they're in
   `config/iag50srv/pointing.yaml` today) — 2.x's `PointingSeries.__init__` no longer has those
   params at all; the equivalent must now be expressed as a `grid:` pipeline (see §2 below).
4. **Two pre-existing bugs, unrelated to 2.x but caught along the way** (`pyrefly`:
   `unused-coroutine`): `pointing.py:100,104` — `f.write(...)` inside the measurement-log loop is
   missing `await` (only line 95's initial write is awaited). Since `LocalFile.write` /
   `HttpFile`-backed VFS writes are `async def`, these two calls currently return an unawaited
   coroutine and do nothing — meaning `_process_acquisition` has likely never actually persisted
   more than the point-count line to `self._log_file`. Worth confirming against the real
   `/pyobs/pointing.poi` file in production before assuming this was silently broken all along.
5. **Non-cooperative `__init__`/`open` calls** in both files (`Module.__init__(self, ...)`,
   `PointingSeries.__init__(self, **kwargs)`, `await PointingSeries.open(self)` instead of
   `super().__init__(...)` / `await super().open()`). Same pattern the rest of the fleet was
   converted away from in `specs/plans/2026-08-18-cooperative-mixin-init.md` (10 repos, closed
   2026-08-19) — worth aligning while this code is open, even though it isn't the thing currently
   causing an exception.

## Design decisions

1. **`aligntest.py`'s grid: drain `GraticuleSphericalGrid` into a plain list, keep the existing
   post-processing.** `GridNode` implements the standard iterator protocol
   (`gridnode.py:43-49`), so `list(GraticuleSphericalGrid(n=150))` reproduces exactly what
   `SphericalGrid.equidistributed(150)` used to return — same algorithm, same tuple shape. The
   rest of `_run_thread`'s post-processing (the `+5° modulo` offset, `.sort(key=lambda x: x[0])`,
   `+= reversed(...)` for a there-and-back sweep — encoding a specific slew-minimizing visit
   order, not something to casually reinterpret) needs **no change** once `self._grid` is a plain
   list again. This is the minimal-risk option: it doesn't touch the observation-ordering logic
   at all, just re-sources the same points from the new API.
2. **`pointing.py`/`config/iag50srv/pointing.yaml`: translate `alt_range`/`az_range`/`dec_range`
   into an explicit `grid:` pipeline**, since `PointingSeries` no longer accepts those params
   directly. Composition, built from the filter primitives that exist today:
   ```yaml
   grid:
     - class: pyobs.utils.grids.GraticuleSphericalGrid
       n: 150   # TBD — point density; 150 matches aligntest.py's, not necessarily what
                # pointing.yaml's old alt/az/dec-bounded grid actually produced
     - class: pyobs.utils.grids.ConvertGridToSkyCoord
       frame: altaz
     - class: pyobs.utils.grids.GridFilterValue
       x_gte: 5      # AZ lower bound (old az_range[0])
       x_lte: 355    # AZ upper bound (old az_range[1])
       y_gte: 20     # ALT lower bound (old alt_range[0])
       y_lte: 85     # ALT upper bound (old alt_range[1])
   ```
   `dec_range` doesn't fit this chain directly — `GridFilterValue` filters whichever frame the
   point is currently in (it reads `x`/`y` generically off `.ra`/`.dec` *or* `.az`/`.alt`,
   `filters.py:134-139`), so filtering both alt/az bounds *and* a dec bound in one pass means
   either: (a) add a second `ConvertGridFrame(frame: icrs)` + `GridFilterValue(y_gte/y_lte=
   dec_range)` stage after the alt/az filter, transforming back to equatorial only to filter
   declination, or (b) decide `dec_range` was actually redundant with the alt/az bounds for this
   telescope's real horizon limits and drop it. **Needs your call, not a default I should pick
   silently** — I don't know whether `dec_range: [-85, 85]` in the current config is a real
   independent constraint or leftover boilerplate. `exp_time: 5` isn't a grid concern at all —
   check whether it's still a valid `PointingSeries`/`Pointing` kwarg in 2.x, or dead config left
   over from 1.x (grep for `exp_time` in `pyobs/modules/robotic/pointing.py` found nothing, so
   it's likely now silently ignored rather than erroring, since `**kwargs` still absorbs it).
3. **Fix the two missing `await`s in `pointing.py`** while touching the file, regardless of the
   2.x migration — they're a real correctness bug independent of the version.
4. **Convert both files to cooperative `super().__init__()`/`super().open()`** while touching
   them, matching fleet convention (§ "Non-cooperative `__init__`" above).

## Implementation

### 1. `pyobs_iag50/aligntest.py`

- [ ] Replace `from pyobs.utils.grids import SphericalGrid` with
      `from pyobs.utils.grids.grid import GraticuleSphericalGrid`.
- [ ] `self._grid = list(GraticuleSphericalGrid(n=150))` in place of
      `SphericalGrid.equidistributed(150)`; leave the offset/sort/reverse-concat lines unchanged.
- [ ] Fix the three `self.proxy(...)` call sites (`_run_thread`, lines 84-86) to
      `async with self.proxy(self._telescope, ITelescope) as telescope:` (and same for
      `cam1`/`cam2`), restructuring the rest of `_run_thread`'s body inside the `async with`
      block(s) (nested, since all three proxies are needed simultaneously).
- [ ] `Module.__init__(self, *args, **kwargs)` → `super().__init__(*args, **kwargs)`.
- [ ] Manual smoke test against `config/test/aligntest.yaml` (or a local stand-in — this module
      talks to real telescope/camera proxies, so a full run needs the actual test setup) before
      considering this file done.

### 2. `pyobs_iag50/pointing.py`

- [ ] `PointingSeries.__init__(self, **kwargs)` → `super().__init__(**kwargs)`;
      `await PointingSeries.open(self)` → `await super().open()`.
- [ ] Fix `f.write(b"%d\n" % m[0])` (line 100) and `f.write(b"%.15f\n" % v)` (line 104) to
      `await f.write(...)`.
- [ ] No code change needed for the `grid` param itself — `Pointing.__init__` already forwards
      `**kwargs` to `PointingSeries.__init__`, so once the config supplies `grid:` (§3), it flows
      through unchanged.

### 3. `config/iag50srv/pointing.yaml`

- [ ] Resolve the `dec_range`/`exp_time` open questions in decision 2 above.
- [ ] Replace `alt_range`/`az_range`/`dec_range` with the `grid:` pipeline block (decision 2),
      once the `dec_range` question is settled.
- [ ] Decide `n` (point density) — 150 is `aligntest.py`'s value, not verified as the right
      density for the production pointing series.

## Tests

No existing test suite in this repo (`find . -iname "test*"` found nothing beyond config files
named `test/`) and no CI (`.github/workflows/` doesn't exist here). Given the module talks to
real hardware proxies and there's no fixture/mock infrastructure to build on cheaply, this plan
doesn't add one — verification is manual:

- Import + instantiate both modules with representative kwargs (as done during this
  investigation) after each code fix, to catch regressions early without needing hardware.
- `config/test/aligntest.yaml` against whatever `test/` config setup exists for a dry run.
- `config/iag50srv/pointing.yaml`'s new `grid:` block: verify point count/coverage looks sane
  (e.g. a quick script iterating the configured `GridPipeline` and plotting/counting output)
  before pointing it at the real 50cm mount.

## Consequences

- **Good:** unblocks releasing pyobs-iag50 on the pyobs-core 2.x line, closing the gap flagged in
  the fleet's `specs/steering/pyobs-project-tiers.md` version policy.
- **Good:** the `aligntest.py` grid fix is genuinely low-risk — same algorithm, same output
  shape, only the sourcing API changed.
- **Neutral:** the `pointing.yaml` grid-pipeline translation is not risk-free — it's a real
  reimplementation of what `alt_range`/`az_range`/`dec_range` used to do internally, on
  production pointing-model config for a live telescope. Test the point coverage before
  deploying, not just that the module imports.
- **Trade-off:** no automated test coverage added for either module (matches the repo's existing
  state, not a regression this plan introduces) — verification stays manual/hardware-adjacent.

## Open questions — need your input before finishing §3

- Does `dec_range: [-85., 85.]` in `pointing.yaml` do real independent work today, or is it
  redundant with the alt/az horizon limits? Determines whether the new `grid:` pipeline needs a
  second ICRS-frame filter stage.
- Is `exp_time: 5` in `pointing.yaml` still consumed anywhere, or is it already-dead 1.x config?
- What point density (`n`) should the production pointing-series grid use? 150 is a borrowed
  default from `aligntest.py`, not a verified value for this use case.
