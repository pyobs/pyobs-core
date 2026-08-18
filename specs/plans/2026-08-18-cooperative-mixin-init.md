# Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`

Status: step 1/10 (`pyobs-core`) implemented, PR #776 open (not yet merged). (Repos: pyobs-core,
pyobs-alpaca, pyobs-brot, pyobs-fli, pyobs-gemini, pyobs-iagvt, pyobs-monet, pyobs-monti, pyobs-sbig,
pyobs-zwoeaf)

Related: `specs/plans/2026-08-09-object-kwarg-validation.md` — where this was discovered. That
plan's last open item ("implement warn/raise enforcement at `Object.__init__`") is superseded by
this plan: a first raise attempt found the mixin fan-out pattern below blocks it outright (59 test
failures), documented in that plan's "Raise attempt (2026-08-18)" section. This plan does the
prerequisite work; that plan's Status gets closed once this one lands the actual `raise`.

## Problem

Several classes across pyobs-core and its driver repos compose multiple mixins by calling each
one's `__init__` explicitly and separately, all handed the *same* original `**kwargs`, instead of a
cooperative `super().__init__(**kwargs)` chain:

```python
class BaseTelescope(WeatherAwareMixin, MotionStatusMixin, WaitForMotionMixin, ..., Module):
    def __init__(self, fits_headers=None, min_altitude=10, wait_for_dome=None, **kwargs):
        Module.__init__(self, **kwargs)              # reaches Object.__init__ FIRST
        ...
        WeatherAwareMixin.__init__(self, **kwargs)    # claims motion_status_interfaces etc. LATER
        MotionStatusMixin.__init__(self, **kwargs)
        WaitForMotionMixin.__init__(self, ...)
```

`Module.__init__(self, **kwargs)` runs *first*, while keys the later sibling calls will still claim
(e.g. `motion_status_interfaces`) are sitting unclaimed in `kwargs`. That call forwards straight to
`Object.__init__`, where those keys look exactly like unrecognized leftovers — even though they're
about to be legitimately consumed a few lines later in the same method. A `raise` at
`Object.__init__`-time is structurally too early for this shape: it can't know a sibling mixin
called *after* it will still claim the key.

**Scale, confirmed via an AST scan across every local `pyobs-*` repo** (`__init__` methods making 2+
distinct explicit `ClassName.__init__(self, ...)` calls): **28 production classes across 10 repos**
— 14 in `pyobs-core` (plus 5 test files using the same pattern), 14 more spread across 9 driver
repos (`pyobs-alpaca` ×3, `pyobs-fli` ×2, `pyobs-iagvt` ×2, `pyobs-monet` ×2, `pyobs-brot`/
`pyobs-gemini`/`pyobs-monti`/`pyobs-sbig`/`pyobs-zwoeaf` ×1 each). `MotionStatusMixin` is the most
common one involved (~13 of 28) — any device with discrete motion states (filter wheels, focusers,
mounts, domes, roofs) mixes it in.

**Confirmed order dependencies, all pointing the same direction** (checked every pyobs-core mixin's
`__init__` body for what it reads/calls): `WeatherAwareMixin`/`FollowMixin` call
`self.add_background_task(...)` (needs `Object.__init__`'s `self._background_tasks`);
`PipelineMixin` calls `self.add_child_object(...)` (needs `self._child_objects`); `FitsHeaderMixin`
reads `self.name` → `self.comm.name` (needs `self._comm`). All four need `Object`/`Module` to have
already run — none need the opposite. `WaitForMotionMixin`, `CameraSettingsMixin`,
`FitsNamespaceMixin` are self-contained, no dependency either way. No conflicting dependency found
in `pyobs-core`; each driver repo needs the same check before assuming it's equally clean.

## Decision

**Fix the fan-out pattern itself (convert to cooperative `super()` chains), not a static
MRO-signature-union check bolted onto `create_object` instead.** The alternative — check a config's
keys against the union of every `__init__` signature (plus AST-detected dynamic `kwargs.pop()`/
`kwargs["x"]` accesses) across the target class's full MRO, once, centrally, without touching any
mixin — was seriously considered: it's contained entirely inside `pyobs-core`, touches none of the 9
driver repos, and is much lower short-term risk.

Rejected anyway: it doesn't fix anything, it builds a smarter external detector that tolerates a
contract violation. It's a heuristic — AST-sniffing for dynamic kwargs access can be fooled by
anything even slightly more exotic than a literal string-keyed access (confirmed one real instance
of this exact blind spot this session: `pyobs_iagvt.modules.FiberCamera`'s
`rotation_correction_coefficients`, consumed via `if "x" in kwargs: ... del kwargs["x"]`, invisible
to plain `inspect.signature`). A cooperative `super()` chain makes `Object.__init__`'s own invariant
*true by construction* — by the time kwargs reaches it, everything really has been claimed, no
guessing, and every *future* mixin added to any of these repos gets checked correctly for free.

Accepted tradeoff: this touches 28 classes across 10 repos, including live-hardware drivers, not
just `pyobs-core`. Mitigated by rolling out repo-by-repo, safest first, each in its own `feature/*`
branch with a full test-suite gate before merging — see checklist.

## Approach

- Convert each affected class's explicit fan-out (`SiblingMixin.__init__(self, **kwargs)` called
  multiple times) to a cooperative chain: each class in the hierarchy declares its own named
  params, ends with `super().__init__(**kwargs)`, and the *composing* class's own `__init__` calls
  `super().__init__(**kwargs)` exactly once instead of naming each mixin.
- Requires checking/fixing base-class listing order per class — cooperative `super()` walks
  `type(self).__mro__`, and MRO order is base-class *listing* order (leftmost runs first). Every
  order dependency found in `pyobs-core` needs `Module`/`Object` to run first; confirm the same
  holds before converting each driver-repo class (don't assume it transfers without checking).
- Case-by-case exceptions: `WaitForMotionMixin`'s constructor currently takes *derived* values
  (`wait_for_modules=[wait_for_dome]`, fixed `wait_for_timeout`/`wait_for_states`), not values
  forwarded straight from config — needs its own per-class judgment call, not a mechanical
  find-and-replace of `ClassName.__init__(self, **kwargs)` → `super().__init__(**kwargs)`.
- Only after every repo below is converted: implement `if kwargs: raise TypeError(f"{type(self).
  __name__}() got unexpected keyword argument(s): {...}")` in `Object.__init__` (the exact change
  attempted and reverted in `object-kwarg-validation.md`), and roll it out.

## Rollout order (proposed, safest first — confirm before starting, not confirmed operational
knowledge)

1. **`pyobs-core`** (14 production classes + 5 tests) — foundation, must be first regardless of
   ordering logic below; nothing else can be verified against a fixed base until this lands.
2. **`pyobs-monet`**'s 2 instances (`frontendcamerasouthfli.py`, `frontendsouth.py`) — the
   `FrontendCameraSouth` class they define is confirmed unreferenced by any current fleet config
   (see `object-kwarg-validation.md`'s fleet cleanup pass) — zero live-hardware risk, good early
   real-world case despite not exercising any actual site.
3. **`pyobs-monti`** (1) — `south/monti`'s checked-in config already doesn't match
   `MontiTelescope`'s current signature at all (found and deliberately deferred in
   `object-kwarg-validation.md`); likely low-risk, possibly already inactive — confirm.
4. **`pyobs-alpaca`** (3) — not referenced by any of the four fleets checked this session
   (`pyobs-monet`/`-iagvt`/`-iag50`/`-polaris`); unclear current deployment — confirm before
   assuming this is actually low-risk just because it wasn't in scope so far.
5. **`pyobs-gemini`** (1) — single piggyback (secondary-instrument) site.
6. **`pyobs-zwoeaf`** (1) — only known use found this session is `south/monti` (deprioritized
   above); confirm no other active site uses it before treating as equally low-risk.
7. **`pyobs-iagvt`** (2) — `ldp.py`/`led.py`, auxiliary devices, not the primary solar-telescope
   pointing itself.
8. **`pyobs-sbig`** (1) — actively used cameras (`iag50`, `monet`).
9. **`pyobs-fli`** (2) — actively used cameras across multiple `monet` sites, core imaging.
10. **`pyobs-brot`** (1) — highest stakes: telescope/dome/roof control at multiple active sites
    (`monet` north+south, `iag50`) — last, most critical, most to lose if something's missed.

## Critical finding (2026-08-18): PR #776's blast radius isn't scoped by rollout order

The "safest repo first" ordering above assumes each repo's own risk is independent — that
converting `pyobs-monet` before `pyobs-fli` only matters for `pyobs-monet`'s *own* classes. That's
wrong. The moment `Object`/`Module`/`BaseCamera` in `pyobs-core` became cooperative (PR #776), any
**unconverted** fan-out class *anywhere downstream* that threads a foreign (sibling-only) kwarg
through the same `**kwargs` dict to one of those now-cooperative bases breaks — regardless of
whether that repo's own conversion PR has landed yet. Order of the fan-out's own explicit calls
doesn't matter either: every sibling call receives the *same* unfiltered dict, so whichever one
reaches `Module`/`Object` first carries the foreign key all the way to `object.__init__()`, which
raises. Confirmed with a minimal repro (`BaseCamera.__init__(self, **kwargs)` called before a
`FliBaseMixin`-shaped stub that owns a `port` kwarg → `TypeError: object.__init__() takes exactly
one argument`).

Re-ran the original AST fan-out scan fresh (found the same 14 non-core classes as before, across
`pyobs-alpaca`(3)/`pyobs-brot`(1)/`pyobs-fli`(2)/`pyobs-gemini`(1)/`pyobs-monet`(2)/`pyobs-monti`(1)/
`pyobs-sbig`(1)/`pyobs-zwoeaf`(1)/`pyobs-iagvt`(2)) and cross-referenced every one against real
configs in `pyobs-monet`, `pyobs-iagvt`, `pyobs-iag50`, `pyobs-polaris`. **8 of 14 are live** today:
`FliFilterWheel`, `FliCamera`, `GeminiFocuserRotator`, `SbigFilterCamera`, `EAFFocuser`, `LDP`, `LED`
(`FrontendCameraSouth` remains commented-out/dead, confirmed again). Of those 8, checking each
live config's actual keys against which sibling declares them found **two that will concretely
crash on the next `pyobs-core` bump, not just carry latent risk**:

- `pyobs_fli.FliFilterWheel` at `pyobs-monet/config/{north/fli,south/frontend}/filterwheel.yaml` —
  both set `dev_path`, a `FliBaseMixin`-only kwarg; `Module.__init__` (called first) leaks it to
  `object.__init__()` before `FliBaseMixin.__init__` (called second) ever sees it.
- `pyobs_gemini.GeminiFocuserRotator` at `pyobs-monet/config/south/piggyback/gemini.yaml` — sets
  `fits_namespaces`, a `FitsNamespaceMixin`-only kwarg; same shape, `Module.__init__` at line 53 runs
  long before `FitsNamespaceMixin.__init__` at line 114.

The other 6 live classes' *current* configs happen not to set any sibling-only kwarg, so they
won't break today, but carry the identical latent risk on the next config change.

**Action taken:** pulled `pyobs-fli` and `pyobs-gemini` forward, ahead of their step 9/5 slots —
see their sections below. Holding off on merging PR #776 until this is resolved was considered but
not required, since `pyobs-core`'s `develop` doesn't auto-propagate to fleet installs; the real
gate is "don't bump a live repo's `pyobs-core` pin past PR #776 until that repo's own fan-out
classes are converted," which now applies to `pyobs-fli`/`pyobs-gemini` (done) and still applies to
`pyobs-alpaca`/`pyobs-brot`/`pyobs-monti`/`pyobs-sbig`/`pyobs-zwoeaf`/`pyobs-iagvt` (not done yet;
none of their *current* configs concretely break, but don't treat that as a guarantee — re-check
before any of those repos' `pyobs-core` pin gets bumped past #776).

## Step 2 (`pyobs-fli`) — implemented

Reordered bases in `FliCamera` (`BaseCamera` first, was `FliBaseMixin` first) and `FliFilterWheel`
(`Module` first, was `FliBaseMixin` first) — both need `Object`/`Module` to run before
`FliBaseMixin.__init__`'s `self.add_background_task(...)` call. Added
`super().__init__(**kwargs)` to the end of `FliBaseMixin.__init__` (it never forwarded before).
Collapsed both classes' fan-out to a single `super().__init__(dev_type=..., **kwargs)` call
(`FliFilterWheel` also threads `motion_status_interfaces=["IFilters"]`, a derived value like
`BaseTelescope`'s `WaitForMotionMixin` case). Verified: 20/20 tests pass, ruff/black/pyrefly clean,
and both previously-crashing live configs (`filterwheel.yaml` x2) plus `morisot.yaml` (`FliCamera`)
and `pyobs-monet`'s `FliBonnShutter` (subclass of `FliCamera`, live at `fli230.yaml`) all construct
correctly against the fixed `pyobs-core` branch.

## Step 3 (`pyobs-gemini`) — implemented

Reordered `GeminiFocuserRotator`'s bases to put `Module` first (was `FitsNamespaceMixin` first).
Moved the single `super().__init__(*args, motion_status_interfaces=["IFocuser", "IRotation"],
**kwargs)` call to the top of `__init__`, ahead of this class's own attribute setup (matches the
`BaseTelescope` precedent from step 1) — removed the two now-redundant trailing
`FitsNamespaceMixin.__init__`/`MotionStatusMixin.__init__` calls. Verified: 17/17 tests pass,
ruff/black/pyrefly clean, and the live `gemini.yaml` config constructs correctly with
`fits_namespaces` and `motion_status_interfaces` both landing on the right attributes.

## Step 4 (`pyobs-monet`) — implemented

Both flagged classes are dead code (`FrontendCameraSouth` commented out in
`config/south/frontend/fli230.yaml`; `FrontendSouth` unreferenced anywhere), so zero live risk
either way. `FrontendCameraSouth`'s bases were reordered (`FliBonnShutter` first, was
`MotionStatusMixin` first — `FliBonnShutter` is the only path to `Module`/`Object`).
`FrontendSouth`'s bases were already correctly ordered (`Module` first). Both collapsed to a single
`super().__init__(**kwargs)` call. Note: the old `FrontendCameraSouth` code called
`MotionStatusMixin.__init__(self)` with **zero** kwargs, not even `**kwargs` — always defaulting
`motion_status_interfaces` to `None`. The cooperative version just lets it flow through `**kwargs`
naturally instead (in practice identical, since no caller has ever set it).

No test suite exists for these modules (`pyobs-monet` has no `pytest`/`ruff`/`pyrefly` dev
dependencies at all, unlike the driver repos) — verified instead by directly constructing both
classes with representative kwargs and calling `motion_status()` on each, confirming
`MotionStatusMixin.__init__` actually ran (would raise `AttributeError` otherwise, same failure
mode found in `pyobs-fli`/`pyobs-gemini`'s review). `black --line-length 120` clean.

## Step 5 (`pyobs-monti`) — implemented

`MontiTelescope`'s bases were already correctly ordered (`BaseTelescope` first, `FitsNamespaceMixin`
last), but its `__init__` still called both explicitly: `BaseTelescope.__init__(self, **kwargs,
motion_status_interfaces=["ITelescope"])` first, then `FitsNamespaceMixin.__init__(self, **kwargs)`
again at the end. Collapsed to a single `super().__init__(motion_status_interfaces=["ITelescope"],
**kwargs)` call at the top, moved ahead of this class's own attribute setup (matches the
`BaseTelescope` precedent). Verified: `black` clean; constructed directly (with a stub
`_set_tracking_rate` and mocked serial I/O, see below) — `fits_namespaces` lands correctly and
`motion_status()` returns `UNKNOWN` instead of raising.

**A third, distinct failure mode found here, worth generalizing:** because `BaseTelescope` was
already correctly ordered *before* `FitsNamespaceMixin` in the base list, `BaseTelescope`'s own
(now-cooperative) `super()` chain — triggered by the *first* explicit call — already reached
`FitsNamespaceMixin` correctly on its own. The *second*, redundant explicit
`FitsNamespaceMixin.__init__(self, **kwargs)` call wasn't needed to reach the mixin at all; it was
dead weight from the pre-cooperative world. Confirmed via a minimal repro
(`Module.__init__(self, comm=None)` then `FitsNamespaceMixin.__init__(self, comm=None)`, i.e. only
kwargs that are legitimately declared and fully consumed on the *first* call) that this redundant
second call **still raises** `TypeError: object.__init__() takes exactly one argument` — because
`**kwargs` unpacking at a call site never mutates the caller's dict, so the second call re-threads
the *same already-consumed* kwargs to a chain that's now cooperative all the way to
`object.__init__()`. This is a stricter trap than the sibling-leak pattern found in
`pyobs-fli`/`pyobs-gemini`: it doesn't require a genuinely foreign kwarg at all, just *any* redundant
second explicit call to a mixin whose `__init__` the first call's cooperative chain already reached.
Live relevance: `pyobs-monti/config/telescope.yaml` sets only ordinary `BaseTelescope`-level kwargs
(`fits_headers`, `comm`, no `fits_namespaces`) — under the *old* two-call code this construction
would still have failed against a cooperative `pyobs-core`, for exactly this reason.

Also found and worked around, not fixed (pre-existing, unrelated to this conversion):
`pyobs-monti`'s `pyproject.toml` pins `pyobs-core==1.32.1` (the old 1.x line) while its actual source
imports 2.x-era paths (`pyobs.modules.telescope.basetelescope.BaseTelescope`,
`pyobs.mixins.FitsNamespaceMixin`) — confirms this repo's dependency metadata has been stale for a
while, consistent with the "possibly already inactive" note from the original rollout plan. Verified
against current `pyobs-core` (not `1.32.1`) with `--no-deps` to bypass the stale pin.
`MontiTelescope` is also currently missing `_set_tracking_rate`, an abstract method `ITelescope` has
since grown — unrelated to kwarg threading, not fixed here (out of scope), worked around in
verification with a throwaway stub subclass.

## Non-goals

- Not converting every explicit `ClassName.__init__(self, **kwargs)` call in these codebases — a
  single explicit call with no sibling calls in the same `__init__` isn't the fan-out pattern and
  doesn't need to change (most of the ~166 explicit-call sites found are this ordinary shape).
- Not touching `pyobs-dashboard-utils` or `pyobs-pilar` — out of scope per
  `object-kwarg-validation.md`'s fleet cleanup pass (`pilar` is archived; `dashboard-utils` wasn't
  cloned/investigated).

## Step 1 (`pyobs-core`) — implemented, PR #776

Converted all 14 production classes + 3 test doubles (the other 2 flagged test files,
`test_pipeline_archive.py`/`test_pipeline_on_error.py`, turned out already-passing despite the old
pattern — not touched). Reordered bases in `BaseRoof`, `BaseTelescope`, `DummyMode` (`Module` first).

**Two extra fixes needed beyond the mechanical conversion, found via actually running things, not
just reading code:**

- `FitsHeaderMixin`'s cache-path attribute was computed eagerly at `__init__` time from
  `module.name` — but `module.name` needs `Module` to have *finished* its own setup
  (`self._device_name = self.comm.name`), and a cooperative chain can now reach a later mixin
  *during* an earlier class's single `super().__init__()` call, before that class's own post-`super()`
  code runs. Fixed by making the cache path a lazy property instead. This is a structurally different
  problem than the fan-out one — it's not about *whether* a mixin's kwargs get claimed, it's about
  *sequencing side effects* relative to a cooperative chain that now runs the entire rest of the MRO
  atomically inside one `super()` call. Worth watching for in the remaining 9 repos: any mixin that
  reads live `Module`/`Object` state (not just its own constructor kwargs) during `__init__`.
- `PipelineMixin`'s `archive` default-injection (`_with_default_archive`) unconditionally injected
  `archive` into every step's config if a pipeline-level default was set, relying on steps that
  don't want it to silently drop it — exactly the pattern this whole effort removes. Fixed to check
  the step's declared signature first (same shape later reused for `Scheduler`'s
  `observation_archive`, see below).

**Verified the double-init risk is actually closed, not just "tests still pass":** before the fix,
`BaseCamera`-family classes were silently calling `ImageFitsHeaderMixin.__init__` *twice* per
construction (once via the new cooperative chain, once via the class's own leftover explicit call) —
harmless there only because the second call happened to run last with the correct values, overwriting
the first's wrong ones. Counted actual call counts with a monkey-patched `__init__` to confirm exactly
one call post-fix, not just correct final attribute values (see PR #776 description).

**Real bugs found via a full fleet-config construction check** (not caught by the unit test suite at
all — these code paths have no test coverage): `Scheduler` passed `auto_update=False` to
`ObservationArchive`/`LcoObservationArchive` (never declared, silently dropped, zero effect for this
class's entire history) and `observation_archive` to every `TaskScheduler` implementation (only
`OnDemandScheduler` declares it). Both fixed in `pyobs-core`; the fleet YAML side of this
(`BasePointing`'s docstring falsely promised `log_file`/`log_absolute`, actually only real on the
nested `apply:` object) is fixed in companion commits to `pyobs-monet`/`pyobs-iag50` directly (not a
PR — those repos push straight to `develop`, per this session's established pattern).

**Confirms the approach works end-to-end**, not just in theory: full suite green (1490 passed),
ruff/black/pyrefly clean, and 799 real fleet config files across 4 repos still construct (the 2 real
bugs above were the only new failures, both fixed). Take this as evidence for the remaining 9 repos,
not a guarantee — each one still needs its own order-dependency check and, ideally, its own
construction check against real configs where fleet configs exist to check against.

## Implementation checklist

- [ ] `pyobs-core`: convert the 14 production fan-out classes + 5 tests to cooperative `super()`
      chains; full test suite green (`pytest -m "not integration and not xmpp" --extra full`).
      PR #776 (open, reviewed — one real regression found and fixed, see review thread — not yet
      merged; merging this is what unblocks pyobs-fli #84 and pyobs-gemini #19 below).
- [ ] `pyobs-fli` (2 classes) — pulled forward, live-breaking (see critical finding above); PR #84
      open, reviewed, regression test added and independently re-verified by reviewer. Blocked on
      pyobs-core #776 merging + bumping this repo's `pyobs-core` pin to a release containing it.
- [ ] `pyobs-gemini` (1 class) — pulled forward, live-breaking (see critical finding above); PR #19
      open, reviewed, regression test added. Same block as pyobs-fli: needs #776 merged + this
      repo's `pyobs-core` pin bumped.
- [ ] `pyobs-monet` (2 classes) — dead code (`FrontendCameraSouth`/`FrontendSouth` unreferenced),
      zero urgency; MR !54 (GitLab) open and reviewed — correct, blocked on pyobs-core #776 +
      pyobs-fli #84 merging first (this class chain depends on `FliBonnShutter`/`FliCamera`).
- [ ] `pyobs-monti` (1 class) — live (`config/telescope.yaml`); fixed, regression test added, MR !1
      (GitLab, `gitlab.gwdg.de/monet/pyobs-monti`) open and reviewed — approved, blocked purely on
      pyobs-core #776 merging first (same as pyobs-fli/pyobs-gemini). `_set_tracking_rate`
      abstract-method gap and stale `pyobs-core==1.32.1` pin are pre-existing, out of scope here.
- [ ] `pyobs-alpaca` (3 classes)
- [ ] `pyobs-zwoeaf` (1 class)
- [ ] `pyobs-iagvt` (2 classes) — `LDP`/`LED` are live but current configs don't trigger the bug;
      re-check before this repo's `pyobs-core` pin moves past #776.
- [ ] `pyobs-sbig` (1 class) — `SbigFilterCamera` is live but current configs don't trigger the bug;
      re-check before this repo's `pyobs-core` pin moves past #776.
- [ ] `pyobs-brot` (1 class)
- [ ] Implement `if kwargs: raise TypeError(...)` in `Object.__init__` (`pyobs-core`), now that
      every consuming class threads kwargs cooperatively.
- [ ] Roll out / restart affected fleet modules; watch for anything this session's checks missed
      (the ~45-class import-failure bucket in `object-kwarg-validation.md` was never fully cleared
      — `pyobs_gui.GUI`, `pyobs-pilar`, `pyobs-dashboard-utils` remain genuinely unverified).
- [ ] Mark `specs/plans/2026-08-09-object-kwarg-validation.md`'s last checklist item done, update
      its `Status:` to closed.
