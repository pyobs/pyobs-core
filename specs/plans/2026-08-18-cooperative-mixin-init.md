# Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`

Status: proposed (Repos: pyobs-core, pyobs-alpaca, pyobs-brot, pyobs-fli, pyobs-gemini, pyobs-iagvt,
pyobs-monet, pyobs-monti, pyobs-sbig, pyobs-zwoeaf)

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

## Non-goals

- Not converting every explicit `ClassName.__init__(self, **kwargs)` call in these codebases — a
  single explicit call with no sibling calls in the same `__init__` isn't the fan-out pattern and
  doesn't need to change (most of the ~166 explicit-call sites found are this ordinary shape).
- Not touching `pyobs-dashboard-utils` or `pyobs-pilar` — out of scope per
  `object-kwarg-validation.md`'s fleet cleanup pass (`pilar` is archived; `dashboard-utils` wasn't
  cloned/investigated).

## Implementation checklist

- [ ] `pyobs-core`: convert the 14 production fan-out classes + 5 tests to cooperative `super()`
      chains; full test suite green (`pytest -m "not integration and not xmpp" --extra full`).
- [ ] `pyobs-monet` (2 classes)
- [ ] `pyobs-monti` (1 class)
- [ ] `pyobs-alpaca` (3 classes)
- [ ] `pyobs-gemini` (1 class)
- [ ] `pyobs-zwoeaf` (1 class)
- [ ] `pyobs-iagvt` (2 classes)
- [ ] `pyobs-sbig` (1 class)
- [ ] `pyobs-fli` (2 classes)
- [ ] `pyobs-brot` (1 class)
- [ ] Implement `if kwargs: raise TypeError(...)` in `Object.__init__` (`pyobs-core`), now that
      every consuming class threads kwargs cooperatively.
- [ ] Roll out / restart affected fleet modules; watch for anything this session's checks missed
      (the ~45-class import-failure bucket in `object-kwarg-validation.md` was never fully cleared
      — `pyobs_gui.GUI`, `pyobs-pilar`, `pyobs-dashboard-utils` remain genuinely unverified).
- [ ] Mark `specs/plans/2026-08-09-object-kwarg-validation.md`'s last checklist item done, update
      its `Status:` to closed.
