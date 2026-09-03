# Plan: FITS header audit follow-through (#872)

Status: proposed

Repos: pyobs-core, pyobs-qhyccd, pyobs-sbig, pyobs-asi, pyobs-fli, pyobs-flipro, pyobs-aravis,
pyobs-tis, pyobs-zwoeaf, pyobs-zaber, pyobs-alpaca, pyobs-brot, pyobs-gemini, pyobs-iagvt,
pyobs-monet, pyobs-monti

## Background

Follow-up to #872 (itself a follow-up to #739). #872 asked for a fleet-wide audit of modules
implementing `IFitsHeaderBefore`/`IFitsHeaderAfter` — and modules that plausibly should but
don't — for config/runtime state that a data user (WCS solving, calibration, troubleshooting a
frame after the fact) would want in the header but currently doesn't get. The audit is done
(four parallel passes: pyobs-core, camera drivers, mount/dome/focuser drivers, IAG-internal +
weather); this plan is the resulting checklist, reviewed and trimmed by Tim. Two items verified
and dropped during review because `INSTRUME` is set via each site's static `fits_headers:` YAML
block (`pyobs.mixins.fitsheader.FitsHeaderMixin`), not driver code — confirmed against every
deployed camera config in the fleet (iag50, monet, monti); no other proposed keyword collides
with an existing static config entry anywhere in the fleet.

Repo list answers #872's open question 1 (survey approach): read off
`specs/steering/pyobs-project-tiers.md`'s fleet definition rather than re-deriving it. Answers
question 2 (where the list lives): here, as a plan — not a design doc, and not split into
per-module issues, since the checklist below already IS the per-item tracker.

## Approach

**pyobs-core lands first.** Every driver repo already tracks pyobs-core's major version
(`specs/steering/pyobs-project-tiers.md`'s version policy) and pulls it as a real dependency, so
there's no reason to stage driver-repo work ahead of a pyobs-core release/dev-tag it can pin to.
Two of the pyobs-core items are also prerequisites, not just "land first for convenience":

- The new `FilterHeaderMixin`/`FocuserHeaderMixin` (item 1.3 below) are what pyobs-zwoeaf,
  pyobs-alpaca's focuser, and pyobs-brot's focus-offset gap actually adopt — those driver items
  are written against the mixin's existence, not against hand-rolled `get_fits_header_before`.
- `pyobs-gemini`'s dead `GEM-TEMP` is a **bug**, not a coverage gap (every frame gets a null
  value because the driver call that would populate it is commented out) — fix it as a small
  standalone PR, independent of and before the header-coverage work in that repo, so it doesn't
  get lost inside a larger diff.

Camera-driver items (section 2) and the IAG-internal items (section 4) don't depend on the new
mixins at all — they're direct `get_fits_header_before`/`_after` edits in each repo and can start
as soon as each repo bumps its pyobs-core floor to whatever dev tag ships section 1.

## 1. pyobs-core

- [x] `pyobs/modules/camera/basecamera.py: BaseCamera` — write `FLIPX`/`FLIPY` (bool, from
      `_flip_x`/`_flip_y`) and `FLIPDONE` (bool, whether `apply_meridian_flip()` actually flipped
      this frame)
- [x] `pyobs/modules/camera/dummycamera.py: DummyCamera` — write `GAIN`/`GAINOFST` from
      `_gain`/`_gain_offset` (`IGain` state) — this is the reference driver every real camera
      driver pattern-matches against
- [x] Add `FilterHeaderMixin`/`FocuserHeaderMixin` to `pyobs/mixins/fitsheader.py`, alongside the
      existing `FitsHeaderMixin`/`ImageFitsHeaderMixin` — cooperative mixins (same multi-
      inheritance style as the rest of the file) that implement `get_fits_header_before` by
      reading the module's own last-published `IFilters`/`IFocuser` state and emitting `FILTER` /
      `FOCUS`+`FOCOFF`, merging with `super().get_fits_header_before()` so they stack with other
      mixins (needed for combo devices, e.g. `pyobs-gemini`'s `GeminiFocuserRotator`, which is
      both focuser and rotator)
  - [ ] Retrofit `pyobs-fli/pyobs_fli/flifilterwheel.py: FliFilterWheel` to use
        `FilterHeaderMixin`, dropping its current duplicated manual `get_fits_header_before`
        (tracks `self._current_filter` twice: once for `comm.set_state`, once for the header) —
        deferred to section 2 (pyobs-fli), out of pyobs-core's own repo
- [x] `pyobs/modules/telescope/basetelescope.py: BaseTelescope` — write `TRACKMOD`/`TRACKOBJ`
      (tracking mode + tracked body/elements name, when non-sidereal)
- [x] `pyobs/modules/pointing/_baseguiding.py: BaseGuiding` — write `AGOFF-FR`/`AGOFFLON`/
      `AGOFFLAT` (last applied guiding correction — already tracked, just not in the header)
- [x] `pyobs/modules/weather/weather.py: Weather` — write `WSGOOD` (the good/bad verdict itself,
      not just raw sensor values)

**Implementation note (2026-09-03):** all six items above done on `develop`, working tree only
(not committed/pushed — awaiting go-ahead). `ruff check`, `black --check`, `pyrefly check` all
clean on the changed files; full non-integration suite (`pytest -q -m "not integration and not
xmpp"`) passes, 1910 passed / 25 skipped / 1 xfailed, no regressions. No new tests added — none of
the touched header-building code paths had existing unit coverage to extend (`test_basecamera.py`
has no flip/meridian assertions today), and adding a test harness for it was judged out of scope
for a straight header-field addition; flagged as a possible follow-up, not done speculatively.
`FilterHeaderMixin`/`FocuserHeaderMixin` reads state via `Comm.get_own_state()`, degrades to no-op
(returns just whatever it chained from `super()`) if the module hasn't published `IFilters`/
`IFocuser` state yet or has no `comm` at all — safe for a device that hasn't finished `open()`.

**Release note (2026-09-03):** committed (`10ef9d1f`, `14d062de`), pushed, and released as
pyobs-core **v2.6.0** via `do-python-release -v minor` (tagged, `develop`→`main` PR merged, `main`
merged back into `develop`). Pin-bumped `pyobs-core>=2.6.0,<3` (+ `uv lock`) in the four repos
whose plan items below actually consume the new mixins — pyobs-fli, pyobs-zwoeaf, pyobs-alpaca,
pyobs-brot — since those are the only ones with a structural dependency on 2.6.0 right now; the
other 11 plan repos' header additions are self-contained and get their pin bumped when their own
section starts. `pyobs-fli`'s push surfaced a pre-existing, unrelated GitHub Dependabot alert (45
vulnerabilities: 29 high, 14 moderate, 2 low) on that repo's default branch — flagged to Tim, not
addressed here.

### Bug fix, opportunistic (pyobs-gemini, do before that repo's coverage item below)

- [ ] `pyobs-gemini/pyobs_gemini/gemini.py: GeminiFocuserRotator` — `_update_status` has the
      `self._T` assignment commented out (`# TODO: find out`, ~line 203); wire it back to the
      already-working `self._driver.get_temperature()` call so `GEM-TEMP` stops being written as
      permanently null

## 2. Cameras (independent of the mixin work; needs pyobs-core dev tag from section 1)

- [ ] `pyobs-qhyccd/pyobs_qhyccd/qhyccdcamera.py: QHYCCDCamera` — `GAIN`, `OFFSET`
- [ ] `pyobs-sbig/src/pyobs_sbig/sbigcamera.py: SbigCamera` — `DET-COOL` (cooler power, already
      polled)
- [ ] `pyobs-asi/pyobs_asi/asicamera.py: AsiCamera` — `OFFSET` (`ASI_OFFSET`)
- [ ] `pyobs-asi/pyobs_asi/asicamera.py: AsiCoolCamera` — `DET-COOL`/`DET-TSET`
- [ ] `pyobs-fli/pyobs_fli/flicamera.py: FliCamera` — `DET-ID` (serial number, already fetched at
      `open()`, currently only logged)
- [ ] `pyobs-fli/pyobs_fli/flicamera.py: FliCamera` and
      `pyobs-flipro/pyobs_flipro/fliprocamera.py: FliProCamera` — `DET-TBAS` (base-plate
      temperature, already polled into `ITemperatures`)
- [ ] `pyobs-aravis/pyobs_aravis/araviscamera.py: AravisCamera` — `INSTRUME` (device id),
      `GAIN`/`TRIGMODE` where present in the connect-time GenICam `settings` dict (this driver
      currently writes no per-frame headers at all beyond the inherited mixin)
- [ ] `pyobs-tis/pyobs_tis/tiscamera.py: TisCamera` — `INSTRUME` (serial), `VIDFMT`/`VIDFPS`

## 3. Mounts, domes, focusers (needs pyobs-core dev tag; focuser items build on the new mixin)

- [ ] `pyobs-zwoeaf/src/pyobs_zwoeaf/eaffocuser.py: EAFFocuser` — adopt `FocuserHeaderMixin`
      (`FOCUS`/`FOCOFF`); add `FOC-TEMP` (live temperature, already polled every 10s) and
      `FOC-BLSH` (`backlash` config)
- [ ] `pyobs-zaber/pyobs_zaber/zabermodeselector.py: ZaberModeSelector` — `INSMODE` (current mode,
      already tracked/published via `IMode`)
- [ ] `pyobs-alpaca/pyobs_alpaca/dome.py: AlpacaDome` and
      `pyobs-brot/pyobs_brot/brotdome.py: BrotDome` — `DOMESHUT` (shutter open/closed; both
      currently inherit only `BaseDome`'s `ROOF-AZ`)
- [ ] `pyobs-alpaca/pyobs_alpaca/focuser.py: AlpacaFocuser` — adopt `FocuserHeaderMixin` for the
      `FOCOFF` gap (currently writes only raw `TEL-FOCU`)
- [ ] `pyobs-brot/pyobs_brot/brottelescope.py: BrotBaseTelescope` (+ `BrotRaDecTelescope`/
      `BrotAltAzTelescope`) — `FOCOFF` (focus offset, already tracked/published via `IFocuser`
      state); `PNTHAOF`/`PNTDCOF` (or `PNTAZOF`/`PNTALOF`) for the applied pointing-model
      correction, distinct from the already-written `HAOFF`/`DECOFF` user offsets; `TEMP-<NAME>`
      per configured `ITemperatures` sensor (this interface is state-only fleet-wide today, never
      reaches any header)

## 4. IAG-internal (independent of pyobs-core mixin work; can start any time)

- [ ] `pyobs-iagvt/pyobs_iagvt/modules/ldp.py: LDP` — implement `IFitsHeaderBefore`:
      `HIERARCH LDP DICHROIC`/`PRIMARY`/`ADDITIONAL` (beam-path selection, currently `IMode`-only)
- [ ] `pyobs-iagvt/pyobs_iagvt/modules/led.py: LED` (Iodine cell + FP etalon control) — implement
      `IFitsHeaderBefore`: `HIERARCH CAL IODINE`/`FP`
- [ ] `pyobs-iagvt/pyobs_iagvt/modules/gregorycamera.py: GregoryCamera` — `FLATCORR`/`CROPIMG`/
      `NAVGSTK` (runtime `IConfig` toggles that directly change delivered pixel data)
- [ ] `pyobs-iagvt/pyobs_iagvt/modules/fibercamera.py: FiberCamera` — `FIBERSEL` (human-readable
      fiberhole selection; currently only the derived pixel position is written)
- [ ] `pyobs-iagvt/pyobs_iagvt/modules/solartelescope.py: SolarTelescope` —
      `HIERARCH TEL CALOFFAZ`/`CALOFFALT` (fixed siderostat-to-sun-center calibration offset)
- [ ] `pyobs-iagvt/pyobs_iagvt/modules/sungrid.py: SunGrid` — `HIERARCH GRID OFFALT`/`OFFAZ`
      (per-exposure grid offset; sibling module `pyobs-iag50`'s `AlignGridTest` already does this
      for its own purpose)
- [ ] `pyobs-monet/pyobs_monet/frontendsouth.py: FrontendSouth` and
      `pyobs-monet/pyobs_monet/frontendcamerasouthfli.py: FrontendCameraSouth` — `INSTMODE`
      (instrument mode name, phot/spec; currently only the derived `FOCL-RED` is written)
- [ ] `pyobs-monti/src/pyobs_monti/montitelescope.py: MontiTelescope` — `PNTMODEL` (pointing-model
      file/version loaded from the `pointing` config param) and
      `HIERARCH PNT MODEL HAOFF`/`DECOFF` (model-derived correction terms, distinct from the
      already-written manual `HAOFF`/`DECOFF`) — this is the exact "mount pointing model version"
      example from #872's own problem statement

## Consequences

- Every driver in the fleet ends up with richer, more consistent FITS headers with no per-repo
  guesswork about keyword naming — the two new core mixins fix the root cause behind several of
  the focuser gaps (no shared convention existed, so each driver either invented its own or
  skipped it).
- `FLIPX`/`FLIPY`/`FLIPDONE`, `TRACKMOD`/`TRACKOBJ`, and `WSGOOD` are pure additions on top of
  existing tracked state — no behavior change, no migration risk.
- The `FilterHeaderMixin`/`FocuserHeaderMixin` retrofit changes `FliFilterWheel`'s header values
  from hand-maintained to mixin-derived — same output, less duplicated state.
- `pyobs-gemini`'s `GEM-TEMP` fix changes real header content (null → an actual reading) for every
  frame that repo produces from here on; worth a release note in that repo.
- Exact FITS keyword names above are proposals, not final — match each repo's existing 8-char/
  `HIERARCH` convention at implementation time rather than copying these verbatim if a repo's
  local style differs.
