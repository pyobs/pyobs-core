# Select remote FITS header providers for each camera

Status: implemented on `codex/fits-header-provider-routing` (2026-10-14); PR pending.

Repos: pyobs-core

Issue: [pyobs-core#971](https://github.com/pyobs/pyobs-core/issues/971).
Related but independent: [BaseTelescope namespace filtering](2026-10-14-basetelescope-fits-namespaces.md).

## Scope and current behavior

Checked against local source on 2026-10-14. This is a plan; no implementation or deployment
verification has been performed.

`pyobs/mixins/fitsheader.py` discovers providers for `IFitsHeaderBefore` or `IFitsHeaderAfter`,
opens their proxies, and starts a header task for each. Collection merges cards in the futures
dictionary's insertion order, so later providers overwrite duplicate cards. It waits under one
shared collection deadline (`fits_header_timeout`, default 15 seconds), cancels pending tasks,
and logs/skips failed responses. An unrelated provider can therefore contribute conflicting
cards or occupy the collection deadline.

Add an optional consumer-side `fits_header_modules` setting to `FitsHeaderMixin`, and an
optional `only` selection to its module-level `request_fits_headers()` helper. The selection
controls contacted header providers. Namespace filtering controls cards returned by a contacted
provider; both mechanisms can be used together. The telescope namespace plan is not a dependency.

## Contract

| Camera configuration | Providers requested |
|---|---|
| Setting omitted or `fits_header_modules: null` | All discovered providers for the requested phase, preserving current behavior |
| `fits_header_modules: []` | None; return an empty task dictionary without discovery or proxy work |
| Nonempty list of names | Intersection of those names and the phase's discovered providers, minus `exclude` |

Names are exact communication client names, as returned by `Comm.clients_with_interface()`;
for XMPP these are the local parts exposed by `XmppComm.clients`, not full JIDs, labels, class
names, namespace names, or wildcard patterns. Use the site's real names.

- Apply the same configured selection to before and after requests. A selected provider that
  implements only one interface contributes only in that phase.
- Missing/offline names and names not advertising the phase's interface contribute nothing.
  Do not introduce mandatory-provider validation, a new failure, or per-frame warnings.
  Already-discovered peers that disappear during proxy acquisition retain existing behavior;
  do not broaden exception handling in this change.
- Selection is a membership filter, not a priority list. Preserve discovery order and current
  merge precedence among selected providers. Duplicate names in the configured list do not
  schedule duplicate requests. Do not add sorting or redefine discovery's ordering contract.
- `exclude` wins over `only`. With no communication object, return `{}` as before.
- Local/static camera headers and computed image metadata remain enabled even with `[]`.
  Timeout and error handling for selected providers remain unchanged.

### Discovery limitation

Keep `clients_with_interface()` as the discovery boundary for nonempty/default selection and
filter its result before proxy acquisition. `Comm.clients_with_interface()` currently walks
connected clients and awaits `_supports_interface()`; backend interface discovery can therefore
still inspect an unselected peer. This change eliminates its header proxy/RPC/task and header
collection wait, but does not promise to eliminate all discovery latency. The empty selection
can bypass discovery entirely. Changing the communication discovery API or probing configured
names directly would expand scope and potentially change interface-version/error semantics;
leave that for separately evidenced discovery work.

## Implementation checklist

### 1. Shared helper

- [ ] Append `only: Iterable[str] | None = None` after the existing `exclude` parameter in
      `request_fits_headers()`; preserve all existing positional arguments and default behavior.
      Document the `None`/empty distinction and exclusion precedence.
- [ ] Materialize a supplied `only` iterable once as a set, preserving `None` separately.
      Return `{}` immediately for an explicitly empty set. Materialize `exclude` once as a
      set as well: repeated membership checks on a generator must not consume it differently
      for successive discovered clients.
- [ ] After interface discovery, skip any client excluded or absent from a non-None selection,
      before the debug request log, proxy context, or task creation. Iterate the discovered
      list, never the set, so allowlist order does not change existing duplicate-card precedence.
- [ ] Keep the before/after interface and method dispatch, namespaces argument, returned
      futures shape, and `add_requested_fits_headers()` collection behavior unchanged.

### 2. Configuration ownership and propagation

- [ ] Add `fits_header_modules: list[str] | None = None` to `FitsHeaderMixin.__init__` after
      existing explicit parameters and before `**kwargs`. Document it and store a defensive
      list copy when supplied, preserving `None` and `[]` distinctly.
- [ ] Have `FitsHeaderMixin.request_fits_headers(before=...)` pass the setting as `only=...`
      for both phase values. Keep one owner of this state and the existing cooperative
      `super().__init__(**kwargs)` chain.
- [ ] Verify normal object-factory/YAML configuration reaches the mixin through `BaseCamera`,
      `BaseVideo`, `BaseSpectrograph`, and their concrete dummy classes. These constructors
      already forward `**kwargs`; do not duplicate the parameter/state in every driver.
- [ ] Keep this a startup constructor setting, consistent with `fits_namespaces` and
      `fits_header_timeout`. No new `IStructuredConfig` schema, runtime getter/setter, or GUI
      control is needed. `Module._get_config_caps()` only exposes fields with config accessor
      methods; merely adding a constructor argument does not make it runtime-editable.

### 3. Call paths and compatibility

- [ ] Check `BaseCamera`'s normal and counted-sequence before/after request paths: both use
      the mixin method and must receive the setting without per-path selection logic.
- [ ] Check `BaseSpectrograph`'s before/after paths likewise. Check `BaseVideo`'s existing grab
      and stack request paths, which currently request before headers only; apply selection
      there without inventing a new after-header phase for video.
- [ ] Preserve the standalone helper caller in `modules/pointing/guidingsource.py`:
      `RawStreamSource` supplies its own `exclude` and keeps default broadcast selection.
      Its requests belong to the guider, not the camera's mixin configuration; do not silently
      inherit the camera allowlist or add guider configuration in this patch.
- [ ] Search remaining helper/mixin call sites during implementation to catch new paths added
      since this plan. Existing third-party calls without `only` remain compatible; no wire
      interface or provider-driver change is required.

### 4. User documentation

- [ ] Document the option and default in the mixin constructor and request helper docstrings.
      Add a short selection section to `docs/source/modules/pyobs.modules.camera.rst`, with
      startup configuration examples and the discovery limitation.
- [ ] Include an illustrative camera configuration fragment:

      ```yaml
      class: pyobs.modules.camera.DummyCamera
      fits_header_modules:
        - telescope
        - mastermind
        - filterwheel
        - focuser
      ```

      Explain that these names must match configured modules, and only providers implementing
      the requested interface contribute. Include the mastermind when its observation/task
      cards are wanted, and filter/focuser providers when their cards are wanted. Show
      `fits_header_modules: null` for default broadcast and `fits_header_modules: []` for no
      remote headers. Do not edit live site examples to assume these names exist there.
- [ ] Explain that selection does not resolve duplicate cards from two intentionally selected
      providers. Namespace ownership/configuration remains relevant; link the separate plan
      in development documentation, without presenting it as shipped behavior.

### 5. Meaningful regression tests

Extend `tests/mixins/test_fitsheader.py` and relevant camera/config construction tests.

- [ ] Parameterize before/after helper tests over `None`, empty, and nonempty selection. For
      omitted/None, retain the current full request set; for empty, assert discovery and proxy
      factories are not called; for nonempty, assert only matching providers are proxied and
      awaited through the correct interface/method.
- [ ] Verify requested namespaces are forwarded unchanged to selected providers, and selection
      does not depend on the namespace names.
- [ ] Cover unknown names, different before/after discovery results, duplicate allowlist names,
      no comm, and overlapping `exclude`/`only`. Assert list order does not override discovery
      order. Use generators for both helper iterables with a client ordering that would expose
      destructive membership consumption.
- [ ] Prove an unselected provider's proxy factory is never entered (make it fail if touched).
      Collect a selected immediate response and confirm no unselected task exists to delay it;
      do not rely on a fragile elapsed-time threshold. Retain existing shared-timeout/cancellation
      tests to verify selected slow providers still use the current deadline.
- [ ] Construct concrete dummy camera/video/spectrograph classes through normal config/object
      creation with omitted, null, empty and explicit selections. Assert the mixin's requests
      honor each value, including both phases where existing paths use them.
- [ ] Cover a representative image acquisition with selected providers: expected cards survive,
      an unselected provider cannot overwrite them, and `[]` still produces local/static camera
      headers. Preserve existing merge-order behavior for duplicate cards from selected peers.
- [ ] Keep the standalone helper's existing `exclude` caller behavior covered without requiring
      camera configuration. Await/drain all created tasks in async tests.

### 6. Validation and completion

- [ ] Run focused FITS-header and touched camera/config tests, then repository checks using its
      environment: `ruff check pyobs tests`, `black --check pyobs tests`, `pyrefly check`, and
      `pytest tests -m "not integration and not xmpp"`. Build affected Sphinx docs with warnings
      as errors where dependencies are available. No real hardware or ejabberd is needed for
      the new selection tests.
- [ ] Review the diff for changes to timeouts, merge precedence, interface discovery, or provider
      namespace semantics; none are intended beyond materializing exclusion iterables safely.
- [ ] Mark this plan/index implemented after the work lands; remove its fleet open-plan entry
      on landing to `develop`. Link the implementation to #971, describing both the eliminated
      header RPCs and the remaining discovery limitation accurately.

## Implementation notes (2026-10-14)

Selection implemented in the shared helper and mixin, with defensive configuration copying and
one-time iterable materialization. Tests cover both phases, default/empty selections, exclusions,
generators, discovery order, config-factory camera/video/spectrograph construction, and two
camera/telescope pairs. Local headers remain active; discovery API and collection timeout are
unchanged. Focused core tests pass; broader validation limitations are recorded in the PR.
