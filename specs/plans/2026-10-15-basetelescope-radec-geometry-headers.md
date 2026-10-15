# Geometry FITS headers for RA/Dec-only telescopes

Status: implemented; PR pending (2026-10-15)

Repos: pyobs-core

Issue: [pyobs-core#973](https://github.com/pyobs/pyobs-core/issues/973).

## Problem and evidence

`BaseTelescope` currently requires `IPointingAltAz` before calculating horizontal
coordinates in both `get_fits_header_before()` and `_update_celestial_headers()`.
The calculation actually uses `_position_radec`, the observer and the current time;
it does not call the telescope's Alt/Az pointing methods. Consequently a telescope
implementing only `IPointingRaDec` loses `TEL-ALT`, `TEL-AZ`, `TEL-ZD`, `AIRMASS`,
`MOONDIST` and `SUNDIST` despite having all the necessary inputs.

The reporter reproduced the issue in v2.15.0. A local reproduction on 2026-10-15
against the current v2.18.0 source also confirmed it: identical RA/Dec, observer
and fixed time produce none of these six cards with a minimal RA/Dec-only
subclass, and all six after adding `IPointingAltAz`. Both runs supplied the same
protected position property and invoked the celestial refresh before requesting
headers; local source inspection confirms the two interface guards.

`_update_celestial_headers()` also publishes `AltAzState`. That publication still
belongs only to modules implementing `IPointingAltAz`: deriving a coordinate for
metadata does not add a pointing interface or advertise a new capability.

## Intended behavior and boundaries

For a telescope with a known RA/Dec position and an observer, derive the four
horizontal-coordinate cards during the existing before-exposure header request,
and the two separation cards during the existing celestial refresh, regardless
of whether the telescope implements `IPointingAltAz`.

Keep the existing coordinate frames, degree units, comments, `secz` airmass
calculation, static-header precedence and final namespace filtering. Preserve
the current `IPointingRaDec` requirement for `TEL-RA`/`TEL-DEC` and sexagesimal
`RA`/`DEC`. Geometry eligibility itself follows the available `_position_radec`
and observer, so a subclass providing that protected property need not acquire
another interface merely to calculate geometry.

Keep the current celestial cache and refresh cadence: `MOONDIST`/`SUNDIST` become
available after a successful refresh, not synchronously on the first header
request. Do not add network calls, change startup timing, or call a driver's
pointing RPC to obtain information already exposed by `_position_radec`.
Non-finite-coordinate policy, below-horizon airmass policy and cache freshness
on a runtime observer removal are separate concerns; preserve existing behavior
rather than silently redefining it in this fix.

## Implementation checklist

- [x] In `pyobs/modules/telescope/basetelescope.py`, snapshot `_position_radec`
      once per calculation method. Construct the ICRS coordinate when that
      position exists; use position plus observer as the horizontal transform
      preconditions, independent of `IPointingAltAz`.
- [x] In `get_fits_header_before()`, separate the geometry coordinate from the
      interface check controlling equatorial header emission. Preserve the
      finite-value guard on the sexagesimal formatters. Leave header assembly
      ordering and the final `_filter_fits_namespace()` call intact.
- [x] In `_update_celestial_headers()`, compute `tel_altaz` when position is
      available after the existing observer guard. Put the `IPointingAltAz`
      check specifically around `comm.set_state(IPointingAltAz, AltAzState(...))`,
      alongside the existing comm-availability check. Keep publication behavior
      for actual Alt/Az telescopes unchanged.
- [x] Continue computing `MOONALT`, `MOONFRAC` and `SUNALT` with an observer even
      when telescope position is unknown. Only add separation cards when the
      target transform exists. Preserve the full cache replacement on a successful
      refresh, which removes prior separations if position becomes unknown.
- [x] Keep these small changes local to `BaseTelescope`; no public API, schema,
      driver inheritance or dependency change is needed. A shared coordinate
      helper is optional only if it simplifies both methods without widening scope.

## Regression coverage and verification

Add `tests/modules/telescope/test_geometry_headers.py` with a minimal concrete
`BaseTelescope` + `IPointingRaDec` subclass, implementing the required abstract
methods without hardware access. Do not derive this regression fixture from
`DummyRaDecTelescope`: its `_DummyTelescopeBase` also implements `IPointingAltAz`.
Assert the fixture is not an `IPointingAltAz` instance. Add a companion subclass
with the Alt/Az interface for parity and publication checks.

- [x] Freeze `Time.now()`, set a fixed observer/site and an above-horizon RA/Dec
      position, and call `_update_celestial_headers()` directly before requesting
      headers. Disable automatic IERS downloads in the test fixture so the test
      is deterministic and offline; do not run the sleeping background worker.
- [x] Assert all six geometry cards exist for the RA/Dec-only telescope and
      match the Alt/Az companion for identical inputs. Check numerical values
      against the fixed observer's Astropy/Astroplan transforms and separations
      with appropriate floating-point tolerances, including `TEL-ZD = 90 - TEL-ALT`
      and the existing `secz` definition of `AIRMASS`. Check `FitsHeaderEntry`
      values/comments and existing equatorial/site cards remain compatible.
- [x] With a mocked comm, assert no `IPointingAltAz` state is published by the
      RA/Dec-only fixture; assert the companion publishes matching `AltAzState`.
      Also cover absent comm: geometry still works without publication.
- [x] Cover unknown position with an observer: omit the six target geometry
      cards, retain observer-only lunar/solar cards, and do not publish Alt/Az
      state. Refresh once with a position and again without it to prove old
      separation cards do not survive that successful refresh.
- [x] Cover absent observer from initialization with a known position: preserve
      equatorial cards, omit all observer-dependent geometry, and avoid state
      publication or exceptions. Avoid the existing dummy factory's automatic
      observer substitution when setting up this case.
- [x] Check a subclass supplying `_position_radec` without a pointing interface
      can derive geometry without gaining equatorial cards or Alt/Az publication.
- [x] On the RA/Dec-only fixture, exercise default unfiltered output and a
      configured namespace mapping selecting only some of the new cards. Check
      sender/requested-namespace selection and exclusion of unselected geometry;
      retain the existing namespace regression suite.
- [x] Run focused telescope tests, then repository checks in the development
      environment: `ruff check pyobs tests`, `black --check pyobs tests`,
      `pyrefly check`, and `pytest tests -m "not integration and not xmpp"`.
      Record failures or unavailable dependencies without claiming a clean run.
- [x] Update this plan and its index after implementation, and reference #973
      in the change description. Hardware and live XMPP are unnecessary for this
      deterministic regression; deployment remains a separate operational step.

## Acceptance and open questions

The fix is complete when the RA/Dec-only regression exposes the same six derived
cards as its Alt/Az companion, with identical inputs and namespace context, while
only the companion publishes Alt/Az state. Missing-input behavior and existing
Alt/Az telescope behavior remain covered.

No blocking product questions remain. The plan deliberately retains the cached
timing of lunar/solar separations and the existing numerical policies; changing
those would require separate requirements rather than expanding #973.

## Implementation verification (2026-10-15)

The two calculation paths now snapshot the position and derive geometry without
requiring a pointing interface. Equatorial cards retain their RA/Dec interface
guard, and Alt/Az state publication retains its Alt/Az interface guard.

Eleven new regression cases cover fixed-time values, state publication with and
without comm, missing position and observer, stale separation removal, namespace
filtering and static-header precedence. The tests live in a separate focused
file alongside the existing base telescope tests. All 69 telescope tests pass.
Ruff, Pyrefly and `black --check --workers 1 pyobs tests` pass (760 files).

Initial sandboxed runs stalled in existing executor tests; both suites completed
outside the sandbox. The full non-integration suite passed: 2,492 passed, 26
skipped, 102 deselected and one expected failure (9 warnings).
