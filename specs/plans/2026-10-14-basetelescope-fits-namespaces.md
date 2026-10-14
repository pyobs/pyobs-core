# Apply FITS namespaces in BaseTelescope

Status: implemented on `codex/fits-header-provider-routing` (2026-10-14); PR pending.

Repos: pyobs-core

Related: [pyobs-core#971](https://github.com/pyobs/pyobs-core/issues/971).
This plan covers provider-side telescope keyword filtering only. The issue's proposed
camera `fits_header_modules` allowlist and `request_fits_headers(..., only=...)` are separate work.

## Current behavior and scope

Checked against the local source on 2026-10-14; no implementation or downstream-driver audit
has been performed for this plan.

- `BaseTelescope.get_fits_header_before()` accepts `namespaces` but ignores it. It assembles
  coordinate, site, tracking, configured, celestial and package-version cards and returns all.
- `_DummyTelescopeBase` alone inherits `FitsNamespaceMixin`. Its public header override calls
  the base without request metadata, adds `TEL-FOCU` from `self._focus`, then filters. The
  override is not wholly redundant: simply deleting it loses `TEL-FOCU`.
- The mixin consumes provider-side `fits_namespaces`, a mapping of namespace names to keyword
  lists. This is distinct from the camera's same-named setting, which is a list of requested
  namespaces. Empty/absent provider mapping passes all cards through. With a mapping, the
  result is the union of the sender's namespace and explicitly requested namespaces; unknown
  names contribute nothing, an empty list contributes nothing, and a `None` mapping value
  currently means all cards (despite the narrower annotation). Preserve these semantics.
- The helper requires `sender`, even when the provider mapping is absent. Existing direct
  `BaseTelescope` calls can omit it, so an unconditional call forwarding only `**kwargs`
  would introduce a `TypeError`.
- `request_fits_headers()` discovers every applicable before/after provider and schedules RPCs.
  Returning fewer cards does not stop discovery, requests, provider work, or timeout delays.
  It can prevent conflicting cards only when ownership mappings are configured correctly.

Non-goals: camera/provider selection, changed merge precedence, timeout changes, new namespace
semantics, changes to other provider classes, and automatically filtering arbitrary downstream
subclasses that append cards after the base public method returns. Do not close #971 on the
strength of this change: its unnecessary-request/delay problem remains.

## Implementation checklist

### 1. Add the shared mixin cooperatively

- [ ] Add `FitsNamespaceMixin` to `BaseTelescope`'s bases alongside the existing concrete
      mixins, before `ITelescope`/`IFitsHeaderBefore`; import it from `pyobs.mixins`.
- [ ] Keep the existing single `super().__init__(...)` call and forward `fits_namespaces`
      through `**kwargs` to its owning mixin. Do not explicitly initialize the mixin or add
      another copy of its state. Document the inherited provider mapping in the base docs.
- [ ] Remove the direct mixin base and import from `_DummyTelescopeBase` in the same change.
      `Module.__init__` calls `Object.__init__`, which continues through `super()` to the
      mixins; verify the concrete MRO rather than treating Module as the end of the chain.
      Confirm namespace configuration is consumed exactly once and unrelated unexpected
      kwargs still raise the existing diagnostic.

### 2. Filter the base result; retain the dummy focus contribution

- [ ] Keep the public `get_fits_header_before(namespaces=None, **kwargs)` signature and
      existing assembly. Replace its final return with `_filter_fits_namespace()` after
      static, celestial and package-version cards have all been added.
- [ ] Normalize a missing sender to `""` in a copied kwargs dictionary, retain a supplied
      sender, and forward namespaces/other kwargs. Do not change the global mixin's signature
      or inject the telescope's own name as a fictitious sender.
- [ ] Retain the dummy public override and its `TEL-FOCU` assignment, as requested. Change its
      parent call to `super().get_fits_header_before(namespaces=namespaces, **kwargs)` with the
      same normalized sender context used by its final filtering call. Keep that final filter
      so the dummy-added `TEL-FOCU` cannot bypass selection.
- [ ] Preserve card values, comments and assembly ordering. No protected assembly hook is
      needed for this scoped change.

The two filters in the dummy path are intentional and idempotent for an unchanged mapping and
identical sender/namespaces: both select the same union of keyword names. A `None` mapping value
passes every current card, so it also preserves cards added between the calls; an absent mapping
passes everything unchanged. The final dummy filter therefore selects `TEL-FOCU` correctly.
Forwarding identical context is essential: filtering the parent without namespaces/sender can
irreversibly discard base cards before the dummy's final filter. `namespaces=None` is not an
unfiltered escape hatch when a mapping is configured.

### 3. Compatibility and downstream review

- [ ] Before implementation is considered complete, inspect available telescope drivers for
      `BaseTelescope`, explicit `FitsNamespaceMixin` bases/initializers, header overrides and
      metadata forwarding.
      Record repositories/versions actually checked; this plan does not claim fleet coverage.
- [ ] Test representative legacy inheritance shapes. A subclass listing `BaseTelescope`
      before an explicit `FitsNamespaceMixin` can be redundant but valid; reversed ordering
      can become an inconsistent C3 MRO once the base owns the mixin. Remove redundant bases
      and explicit initialization where needed; verify imports/constructors before rollout.
- [ ] Public driver overrides that call `super()` must forward `namespaces` and `**kwargs`.
      Overrides adding cards afterward still need final filtering after their additions. Base-only
      filtering cannot cover their later additions. In particular,
      `FilterHeaderMixin` and `FocuserHeaderMixin` append cards after their cooperative parent
      call; composing them before `BaseTelescope` does not provide whole-header filtering.
- [ ] Document the inherited mapping and a provider YAML example in existing telescope documentation. Explain
      missing sender as an empty namespace name: no mapping means unchanged output; with a
      mapping, only explicit requested namespaces (or a configured empty-string key) match.
      A driver that now accepts an existing mapping may intentionally return fewer cards;
      audit site configurations before enabling mappings in production.

### 4. Regression coverage and validation

- [ ] Use a minimal concrete non-dummy `BaseTelescope` subclass to prove namespace support
      resides in the base, independent of dummy behavior. Cover constructor mapping propagation
      through normal construction and the config object factory.
- [ ] Cover no mapping (`None` and `{}`), with and without sender; the previous complete
      header and `FitsHeaderEntry` values/comments must survive unchanged.
- [ ] Cover sender-only selection, explicit namespace selection, their union, unknown sender
      and namespace, `namespaces=None` versus `[]`, and empty namespace keyword lists. Include
      the existing all-keywords `None` mapping value without changing its policy.
- [ ] Include static, celestial and mocked version cards in filtering assertions; ensure cards
      introduced at the end of assembly cannot bypass filtering.
- [ ] Exercise all dummy variants (RA/Dec, Alt/Az, solar): the inherited public method retains
      `TEL-FOCU` without mapping, includes it when selected, excludes it otherwise, and reflects
      a changed focus value. Verify both filtering calls use identical namespace/sender context.
- [ ] Test a legacy public override forwarding namespace/sender metadata and filtering its
      own added cards. Cover direct local calls without sender
      and a normal RPC-style call with sender and extra metadata.
- [ ] Run focused telescope/mixin tests, then repository checks: `ruff check pyobs tests`,
      `black --check pyobs tests`, `pyrefly check`, and
      `pytest tests -m "not integration and not xmpp"` using the repository environment.
      No live hardware or ejabberd is needed for the new regression cases.
- [ ] Update this plan and its index status after implementation; remove its open-plan entry
      from `specs/steering/fleet-open-items.md` once the fix lands on `develop`.

## Separate resolution of #971

The reporter's allowlist proposal controls which modules are contacted: camera configuration
`fits_header_modules`, forwarded as an optional `only` argument to `request_fits_headers()`
for both before and after requests. Its proposed defaults distinguish `None` (current broadcast)
from `[]` (no remote providers). That selection avoids their header RPCs and collection waits; capability-cache checks may still wait for background discovery.
Namespace filtering controls which cards a contacted provider returns. These mechanisms solve
different parts of the report and can coexist; no allowlist implementation is included here.

## Implementation notes (2026-10-14)

Base and dummy changes implemented; TEL-FOCU stays in the dummy. Focused core tests cover both
provider selection and namespaces, including two camera/telescope pairs and config-factory
construction. Local Alpaca/BROT inheritance shapes are valid with the shared mixin; retained
explicit driver bases preserve compatibility with older core versions. Their header overrides
need metadata forwarding fixes tracked in pyobs-alpaca #54 and pyobs-brot #87, implemented in
separate coordinated PRs. IAGVT SolarTelescope also calls the base without metadata and appends
cards without final filtering; configured ownership there needs a follow-up before enabling it.
ASCOM is legacy synchronous code and was not migrated. No hardware or XMPP runtime test.

Regression tests pass without an automatic IERS download. Broad core tests and Sphinx validation
have existing issues; the PR records the observed results rather than claiming full passage.
