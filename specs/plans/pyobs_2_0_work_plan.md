# Plan: pyobs 2.0 rollout

Status: nearly done. Phases 0-8 below are historical record (all ✅ complete) — see
`specs/design/pyobs_2_0_wire_protocol.md` for the design those phases implemented. What's
actually still open is the short list right below; that's the live part of this plan.

## Remaining open items

- [ ] **Delete `IRunning.is_running()` from `IRunning` and its ~10 implementers.**
  `RunningState` was added and is pushed via `comm.set_state(IRunning, RunningState(...))`
  everywhere, but `is_running()` itself was never removed from the interface
  (`pyobs/interfaces/IRunning.py:25`) or from any implementer (`acquisition.py`,
  `_baseguiding.py`, `dummyacquisition.py`, `dummyguiding.py`, `focusseries.py`,
  `dummyautofocus.py`, etc.) — both the RPC method and the pushed state exist side by side
  for the same boolean, the exact duplication this migration was meant to remove. Found
  during the `get_*` → State survey; see `specs/design/pyobs_2_0_wire_protocol.md`'s
  appendix.
- [ ] **`pyobsd` should default to systemd (journal) logging instead of per-module file
  logging.** Today `pyobsd` (`pyobs/cli/pyobsd.py`) spawns each module with
  `--log-file <log_path>/<module>.log` and manages PID/log files itself, duplicating what
  the systemd journal already does (stdout/stderr capture, rotation, `journalctl` querying)
  when run under systemd. Direction: default to stdout/stderr (or
  `systemd.journal.JournalHandler`) under systemd, file logging becomes opt-in. Not yet
  designed in detail — no decision on deprecating `log_path`/`--log-file`, or on the
  transition for non-systemd (sysvinit) installs.
- [ ] **Warn when a module's configured `name` doesn't match its XMPP JID.**
  `Module.__init__` (`pyobs/modules/module.py`) defaults `name` to the JID's user part but
  doesn't enforce agreement if a config sets `name` explicitly — a silent footgun, since
  logging/GUIs display `name` while `proxy()`/config references address by JID. Direction:
  on startup, once the JID is known, compare and log a warning (not a hard error, since a
  friendly display name may be intentional) on mismatch. Not yet designed in detail — no
  decision on whether the check belongs in `Module.open()` or `Comm`, or whether `label`
  should be checked too.

## Phase-by-phase record

## Work Plan

Ordered by dependency, not by section order above — several things only make sense once something earlier exists. Each phase names what it unblocks.

### Phase 0 — Foundations

✅ **Done, including event-feature versioning.** Nothing here is interesting on its own, but everything later depends on it existing first.

- ✅ `Interface.version`/`Event.version` (lowercase `version`, default `1`) — wired into state (`urn:pyobs:state:{name}:{version}`) and capabilities (`urn:pyobs:capabilities:{name}:{version}`) namespaces. **Interface features: done.** `add_feature` publishes `urn:pyobs:interface:{name}:{version}`, and `_get_interfaces`'s parsing filters to only the versioned form, so `.version` mismatches now actually exclude the interface from a resolved proxy instead of resolving silently — see the mixed-version-fleet diagnostic above. **Event features: done too** — `add_feature(f"urn:pyobs:event:{ev.__name__}:{ev.version}")` publishes the versioned form (`9c19e512`), replacing the old pre-2.0 unversioned `pyobs:event:{name}`. See [Versioning](#versioning).
- ✅ `Comm.proxy()`/`Object.proxy()`/`Comm.safe_proxy()` converted to the `async with`-only `_ProxyContext`, `ProxyType`/`_ProxyContext` consolidated into `proxy.py`, `has_proxy()` added. Migration complete: no `await self.proxy(...)` call sites remain in `pyobs-core`. `cache_proxies` removed.
- ✅ ~~All six project enums converting `Enum` → `StrEnum`~~ Already true today — nothing to do here. This is what the wire-vocabulary's `enum(Name)` design assumes. See [Type Vocabulary](#type-vocabulary).
- ✅ `Unit(StrEnum)` added to `pyobs/utils/enums.py` with `to_astropy()`. All applicable interface signatures annotated with `Annotated[float, Unit.X]`. See [Units](#units).

### Phase 1 — Walking skeleton: prove State end-to-end on one interface

✅ **Done.** `ICooling` was the pilot as planned, and the pattern proved out — since generalized to 23 of ~26 State-bearing interfaces (Phase 3).

- ✅ The three `Comm` abstract methods (`set_state`, `subscribe_state`, `unsubscribe_state`) exist and are implemented for XMPP: PubSub publish/subscribe with "deliver the last item immediately" semantics, unsubscribe. See [`Comm`: three new abstract methods](#comm-three-new-abstract-methods).
- ✅ `Proxy.update_state`/`get_state(interface)`/`wait_for_state(interface)` (named `get_state`, not the bare `.state(...)` originally sketched), the auto-subscribe loop in `Comm._get_client`, and `_state_subscriptions` tracking + teardown in `_client_disconnected` are all implemented. See [`Proxy`](#proxy-state-hidden-behind-update_state-and-a-state-method) and [Lifecycle](#lifecycle-piggyback-on-existing-proxy-eviction-no-new-proxy-api).
- ✅ disco#info extended with versioned namespaces and state schema blocks; the dataclass ↔ XML auto-generation utility lives in `pyobs/comm/xmpp/serializer.py`, shared with RPC (Phase 1.5).

✅ **Validation and integration testing — implemented, mechanism differs slightly from the sketch below.** `.github/workflows/pytest-integration.yml` exists, triggered on release publish exactly as planned. Rather than an inline GitHub Actions `services:` block, it starts ejabberd via `docker compose -f tests/xmpp/docker-compose.yml up -d` and polls `docker compose ... ps` for a healthy container before running tests — same effect (a live ejabberd for `tests/integration/`), different mechanism (compose file instead of the native `services:` key). The original sketch is left below for the reasoning; the compose file itself is the source of truth for the actual container config.

```yaml
# original sketch -- actual implementation uses tests/xmpp/docker-compose.yml instead
services:
  ejabberd:
    image: ejabberd/ejabberd
    ports:
      - 5222:5222
    env:
      EJABBERD_DOMAIN: localhost
      EJABBERD_ADMIN: admin
      EJABBERD_ADMINPASS: testpassword
    options: >-
      --health-cmd "ejabberdctl status"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 12
```



### Phase 1.5 — RPC payload encoding 2.0

✅ **Mostly done.**

**Landed:**
- ✅ `pyobs/comm/xmpp/serializer.py` — shared `value_to_xml`/`xml_to_value` core used by both state and RPC. Handles the full vocabulary: `bool`, `int`, `float`, `str`, `StrEnum`, `nil`, `list`, `tuple`, `dict`, dataclasses, `Annotated`/`Optional` unwrapping, ejabberd namespace-strip on round-trip. `_dataclass_to_xml`/`_xml_to_dataclass` delegate to `value_to_xml`/`xml_to_value` per field — cleaner than the document sketched.
- ✅ `pyobs/comm/xmpp/rpc.py` — `RPC` class using `urn:pyobs:rpc:1`: `params_to_xml`/`xml_to_params` for arguments, `return_to_xml`/`xml_to_return` reading `return_annotation`, `fault_to_xml`/`xml_to_fault` for typed exception reconstruction. XEP-0009 envelope (`jabber:iq:rpc`) unchanged; `urn:pyobs:rpc:1` scopes only `<value>` content.
- ✅ **`get_*` removal has gone much further than "still pending."** This isn't an intermediate step anymore for most interfaces — `ICooling.get_cooling`, `IWindow.get_full_frame`, `IModule.get_label`/`get_version`, `IMultiFiber.get_fiber_count`, `IVideo.get_video`, `IConfig.get_config_caps`, `IFocusModel.get_optimal_focus`, `IWeather.get_weather_status`/`is_weather_good`/`get_current_weather` and others are gone outright, not returning `State` as a transition shape. Only 4 `get_*`-prefixed abstract methods remain across all interfaces: `IConfig.get_config_value` (RPC by design), `IFitsHeaderBefore`/`After.get_fits_header_*` (RPC by design), and `IWeather.get_sensor_value` (RPC by design — a live per-station HTTP call, kept deliberately rather than folded into `IWeather.state`). The `IWindow.get_full_frame` vs. Discovery discrepancy this section used to flag is moot: the method isn't there to be inconsistent anymore.

✅ **Nothing pending** — this section is fully resolved now:
- ✅ `ConfigValue = bool | int | float | str` — applied.
- ✅ `WeatherSensors.RAIN`'s unit is resolved: `SENSOR_UNITS[RAIN] = "bool"` in `pyobs/modules/weather/weather.py`, documenting the 0/1-flag-as-float interpretation — see [Units](#units).

### Phase 2 — Audit and design pass (no implementation yet)

✅ **Done.**

- ✅ ~~Systematic survey of every `get_*` method across all interfaces for State-read candidacy.~~ Done — see the [get_* to State Survey](#appendix-get_-to-state-survey). All 47 methods settled: 34 `State`, 8 `Discovery`, 2 `Presence`, 4 `RPC`.
- ✅ ~~Design (not yet implement) the State dataclasses resolving the six genuinely-undocumented-`Any` interfaces.~~ Design done and now fully implemented — see the [State dataclass catalogue](#appendix-state-and-capability-dataclass-catalogue). `IAutoFocus` and `IWeather` both closed (Phase 3).
- ✅ ~~Design the tagged-union approach for `IConfig.get_config_value`/`set_config_value` separately.~~ `ConfigValue = bool | int | float | str` — applied.
- ✅ ~~Design the named dataclasses for all 19 tuple-returning methods (`RaDec`, `AltAz`, `Binning`, `Window`, and the rest).~~ Done and implemented — only 3 of the 19 remain (see [Type Vocabulary](#type-vocabulary)).

### Phase 2.5 — Discovery and Presence

✅ **Done.** These 8 methods were blocking the `get_*` removal sweep at the end of Phase 3 — done, and the sweep proceeded (see Phase 1.5/3).

**Design decisions (as implemented):**

- ✅ **`set_presence` is automatic, not explicit** — confirmed: `Module`'s `ModuleState` transitions call `Comm.set_presence` without module authors needing to call it themselves.
- ✅ **Discovery goes into the XEP-0030 disco#info handler, not a dedicated IQ handler** — `XmppComm._get_disco_info` is registered as the `xep_0030` node handler for `get_info`, exactly as decided.
- ✅ **Both Discovery and Presence implemented together.**

**Discovery (7, was 8 in the original list — `ILatLon.get_latlon` no longer exists) — all now `capabilities =`, published in disco#info `<capability>`, `get_*` method removed:**

| Method | Interface | Value | Status |
|---|---|---|---|
| `get_label()` | `IModule` | Human-readable module name | ✅ removed, `ModuleCapabilities` |
| `get_version()` | `IModule` | Software version string | ✅ removed, `ModuleCapabilities` |
| `get_fiber_count()` | `IMultiFiber` | Number of fibers (fixed hardware) | ✅ removed, `MultiFiberCapabilities` |
| `get_full_frame()` | `IWindow` | Full CCD dimensions | ✅ removed, `WindowCapabilities` |
| `get_config_caps()` | `IConfig` | Which config keys exist and are readable/writable | ✅ removed, `ConfigCapabilities` |
| `get_video()` | `IVideo` | Stream URL/path | ✅ removed, `VideoCapabilities` |

The `<capability>` element pattern designed in [Capabilities / Discovery](#1-capabilities--discovery) is implemented as described — one `<capability name="..." type="...">value</capability>` element per item, published inline in the module's disco#info response, no PubSub, no subscription. `Interface.capabilities: ClassVar[type | None] = None`, `Proxy.get_capabilities(interface)` reads a dict populated synchronously from disco#info during `_get_client`. Capabilities coverage on `develop` is actually broader than this table: `IFilters`, `IImageFormat`, `IMode`, and `IBinning` also declare `capabilities =` now (e.g. `FiltersCapabilities`, `ImageFormatCapabilities`) — additions beyond what this document originally catalogued.

**Presence (2) — module lifecycle, maps onto XMPP presence stanzas:**

| Method | Interface | Value | Status |
|---|---|---|---|
| `get_state()` | `IModule` | `ModuleState`: closed/ready/error/local | ✅ removed, `get_client_state()`/presence |
| `get_error_string()` | `IModule` | Current error message if state is error | ✅ removed, rides as `<status>` text |

✅ Implemented exactly as this section speculated it should be designed: `XmppComm._set_presence` maps `ModuleState.READY`→no `<show>`, `ERROR`→`dnd`, `LOCAL`→`away`, `CLOSED`→handled by disconnect; `error_string` rides as XMPP `<status>` text when `ERROR`.

### Phase 3 — Bulk rollout

✅ **Done**, including event schema publication.

- ✅ Tuple-returning methods converted to dataclasses — 18 of 19 done; the 1 remaining (`IFlatField.flat_field`) is a genuine RPC action result, out of scope for removal.
- ✅ Add `State` to every interface identified in Phase 2's `get_*` survey: **done for all ~26**. `IAutoFocus`, `IFocusModel`, and `IWeather` were the last three — all closed now.
- ✅ disco#info and PubSub state publishing extended to every interface now carrying a `State`.
- ✅ `urn:pyobs:event:Name:{version}` schemas for events: event disco#info features are versioned and an event schema block (`_event_schema_to_xml` in `serializer.py`) is emitted in disco#info (`9c19e512`) — see [Events](#4-events--unchanged-at-the-api-level) and [Versioning](#versioning).

### Phase 4 — Other backends and Presence

✅ Done. `utils/types.py` and the old XML-RPC cast pipeline deleted.

- ✅ Local backend: `LocalComm` already implements `_set_state`, `_subscribe_state`, `_set_capabilities`, `_set_presence` as simple in-memory operations, matching this design.

### Phase 5 — `pyobs-gui`

✅ **Done, checked against `../pyobs-gui` on this pass.** Every widget (`coolingwidget.py`, `filterwidget.py`, `temperatureswidget.py`, `camerawidget.py`, `focuswidget.py`, `modewidget.py`, `roofwidget.py`, `videowidget.py`, `telescopewidget.py`, `spectrographwidget.py`) now consumes `comm.subscribe_state(...)`/`comm.get_capabilities(...)`/`comm.get_interfaces(...)` and `statuswidget.py` uses `comm.subscribe_presence(...)` — the reactive 2.0 model this phase called for, not `get_*` polling.

✅ **The one former stale call site is fixed:** `compassmovewidget.py:45,56,62` now calls `p.wait_for_state(IPointingAltAz, ...)`, `p.wait_for_state(IOffsetsAltAz, ...)`, `p.wait_for_state(IOffsetsRaDec, ...)` — no more `get_altaz()`/`get_offsets_altaz()`/`get_offsets_radec()` RPC calls against the removed `get_*` methods.

### Phase 6 — External official `pyobs-*` hardware modules

✅ **Done.** Checked this pass — all 11 repos available locally (parallel to `pyobs-core`), each audited for `comm.set_state(...)` calls on every state-bearing interface it implements, and for leftover `get_*` methods that would indicate a module never migrated. All 11 are now fully migrated: 9 needed no changes, and the 2 that initially weren't (`pyobs-aravis`, `pyobs-v4l`) shared one root cause that turned out to be a `pyobs-core` bug — fixed upstream in this pass, not a per-module migration gap (see below). Note the table below has 11 rows, not the "13" the count previously (and wrongly) claimed — corrected.

| Repo | Hardware | Status |
|---|---|---|
| `pyobs-alpaca` | ASCOM Alpaca wrapper | ✅ Fully migrated — `IFocuser`, `IPointingRaDec`, `IPointingAltAz` (via `IDome`), `IOffsetsRaDec`, `IReady`, `IMotion` all publish via `set_state` |
| `pyobs-aravis` | Aravis webcams | ✅ Fully migrated — `IExposureTime` migrated directly; `IImageType` (inherited via `BaseVideo`) fixed upstream in `pyobs-core`, see below |
| `pyobs-asi` | ZWO ASI cameras | ✅ Fully migrated — `IWindow`, `IBinning`, `IImageFormat`, `IGain`, `ITemperatures`, `ICooling` |
| `pyobs-brot` | BROTlib telescopes | ✅ Fully migrated — `IPointingRaDec`, `IPointingAltAz`, `IOffsetsRaDec`, `IOffsetsAltAz`, `IFocuser`, `ITemperatures`, `IReady` |
| `pyobs-fli` | FLI cameras | ✅ Fully migrated — `IWindow`, `IBinning`, `ICooling`, `ITemperatures`, `IFilters`, `IReady` |
| `pyobs-flipro` | FLIPRO cameras | ✅ Fully migrated — `IWindow`, `IBinning`, `ICooling`, `ITemperatures` |
| `pyobs-qhyccd` | QHYCCD cameras | ✅ Fully migrated — `ICooling`, `IWindow`, `IBinning`, `IGain`, `ITemperatures` (cosmetic-only gap: `ITemperatures` state is published but the class doesn't formally list it as a base) |
| `pyobs-sbig` | SBIG cameras | ✅ Fully migrated — `IWindow`, `IBinning`, `ICooling`, `ITemperatures`, `IFilters` |
| `pyobs-v4l` | V4L webcams | ✅ Fully migrated — its only state-bearing interface, `IImageType` (via `BaseVideo`), fixed upstream in `pyobs-core` alongside `pyobs-aravis`, see below |
| `pyobs-zaber` | Zaber motors | ✅ Fully migrated — `IMode`, `IMotion` (repo has one module, a mode selector; no focuser/filter-wheel module exists here despite what this table used to imply) |
| `pyobs-zwoeaf` | ZWO EAF focus motor | ✅ Fully migrated — `IFocuser`, `ITemperatures` |

No leftover `get_cooling`/`get_window`/`get_binning`/`get_gain`/`get_focus`/`get_radec`/`get_altaz`/etc. methods were found standing in as the sole way to read state in any of the 11 repos — where old `get_*` methods appear at all, they're either unrelated (`get_fits_header_before`) or low-level driver accessors, not interface overrides.

**The `pyobs-aravis`/`pyobs-v4l` gap was a real `pyobs-core` bug, found by checking these two repos: `BaseVideo.set_image_type` only did `self._image_type = image_type` and never called `self.comm.set_state(IImageType, ImageTypeState(...))`, unlike its sibling `BaseCamera.set_image_type` (`pyobs/modules/camera/basecamera.py:142-150`), which does exactly that.** Any module built on `BaseVideo` instead of `BaseCamera` — `pyobs-aravis` and `pyobs-v4l` — silently never published `IImageType` state. ✅ **Fixed**: `BaseVideo` (`pyobs/modules/camera/basevideo.py`) now publishes the initial `IImageType` state in `open()` and republishes it in `set_image_type()`, mirroring `BaseCamera` exactly. Resolves both external repos at once; no change needed on their side.

Out of scope for this phase (infrastructure, services, UIs handled in other phases): `pyobs-core`, `pyobs-gui`, `pyobs-web-admin`, `pyobs-robotic-backend`, `pyobs-weather`, `pyobs-task-editor`, `pyobs-archive`, `pyobs-astrometry`, `pyobs-allsky-cloudcover`, `pyobs-tui`, `pyobs-launcher`, `pyobs-web`, `pyobs.github.io`.

**Two of these checked directly and confirmed genuinely not applicable, not just unchecked:** `pyobs-robotic-backend` (pinned `pyobs-core>=1.53.0`, `1.53.0` actually installed) and `pyobs-task-editor` (pinned `>=1.46.0`, `1.49.1` actually installed) — neither has ever been bumped for 2.0, but neither needs to be for this redesign specifically. Both import exclusively from `pyobs.robotic.*` (`Task`, `TaskData`, `Script`, `ObservationState`, scheduler/constraints/merits/targets) — the scheduling subsystem — with zero references anywhere in either codebase to `pyobs.interfaces`, `pyobs.comm`, `Proxy`, or XMPP, i.e. none of the state/capabilities/RPC-2.0/versioning machinery this document covers. Every symbol they import still resolves on current `develop`. The rest of the out-of-scope list above (`pyobs-web-admin`, `pyobs-weather`, `pyobs-archive`, `pyobs-astrometry`, `pyobs-allsky-cloudcover`, `pyobs-tui`, `pyobs-launcher`, `pyobs-web`, `pyobs.github.io`) remains unchecked, not confirmed either way.

### Phase 7 — `pyobs-web-client` catch-up

✅ **Done — checked this pass against `../pyobs-web-client`'s own `DEVELOPMENT.md` and code, not just assumed.** It's substantially further along than "status unknown, early-stage" implied: the whole port to the 2.0 wire protocol was designed, implemented, and verified end-to-end against a live ejabberd server with a real `pyobs-core` module, across multiple commits (`2d1fa73` "Port to pyobs-core 2.0 wire protocol, drop generated interfaces` through `7e602db`).

- ✅ **Live disco#info feature-matching fixed** — `useXmpp.ts` matches `urn:pyobs:interface:`/`urn:pyobs:event:` (versioned), not the old bare prefixes; confirmed live at `src/composables/useXmpp.ts:118-124,142,198`.
- ✅ **`generate-interfaces.py`'s build-time extraction retired, not just optionally** — `scripts/generate-interfaces.{py,sh}` and the generated `src/pyobs-interfaces.ts` are deleted from the repo entirely. Interface/event/state/capability schemas are fetched live from disco#info on every connect (`pyobs-codec.ts`'s schema-less decode + schema-driven encode), so there's no local `../pyobs-core` checkout dependency and mixed-version fleets "just work" per-module — a stronger outcome than this document's original "optionally retire" framing anticipated.
- ✅ **Enum dropdowns implemented** — `enum(Name)`-typed RPC params render as a real `<select>` populated from the schema's own `<types>` block, verified live (`IImageFormat.set_image_format` in the verification log below).
- ✅ **A genuine cross-repo bug found and fixed on both sides during this work, worth recording:** the web client's hand-rolled RPC value serializer omitted the required `urn:pyobs:rpc:1` xmlns on the value wrapper, which `pyobs-core`'s `xml_to_params` used to silently treat as `None` instead of raising — surfacing downstream as a confusing `ValueError: No parameter name given.` from `get_config_value` that looked like a server bug from a real, non-empty client value. Fixed on the client side (`pyobs-web-client@456773c`) and hardened on the `pyobs-core` side to raise a clear `ValueError` at the RPC boundary instead of silently substituting `None` (`d170fd5e`, already on `develop`).
- ✅ **One small `pyobs-core`-side cleanup surfaced and fixed:** `xmppcomm.py`'s `_capability_type`/`_CAPABILITY_NS` were dead code — a scalar `<capability name="..." type="...">value</capability>` form from an earlier, module-wide capabilities design (`a362655d`) that got fully superseded by the current per-interface, versioned, dataclass-based one (`bd663d87`) without the old helper being cleaned up. The real `_get_disco_info` path serializes capabilities via `_dataclass_to_xml(..., tag="capabilities")`, and the old helper wasn't even compatible with the current `dict[type, Any]` capabilities storage — removed.

### Phase 8 — Access Control (ACLs)

✅ **Implemented**, see [Access Control (ACLs)](#access-control-acls). Two pre-existing latent bugs in the XMPP client-side error path were found and fixed while making the `forbidden` condition actually round-trip end-to-end (verified against a live ejabberd server, not just unit-tested) — see the note below the checklist.

- ✅ `exc.ForbiddenError(RemoteError)` added to `pyobs/utils/exceptions.py`, carrying `sender` and `method`, matching the existing `RemoteError`/`InvocationError` family.
- ✅ Optional `acl:` config block parsed on `Module` construction (sibling of the existing `comm:` block), stored as `_acl_allow`/`_acl_deny`/`_acl_mode`; either `allow: dict[str, list[str] | str]` or `deny: list[str]`, mutually exclusive — rejects config that sets both — plus an optional `mode: enforce | log` (default `enforce`). Absent block means fully open, matching every other additive default in this document.
- ✅ ACL check inserted in `Module.execute()`, right after `func, signature, type_hints = self._methods[method]` and before binding — denies if `allow` is set and `sender` isn't listed for `method`, or if `deny` is set and `sender` appears in it. `mode == "enforce"` raises `exc.ForbiddenError`; `mode == "log"` logs a warning and lets the call proceed.
- ✅ In `rpc.py`'s inbound exception handling, `exc.ForbiddenError` is special-cased to reply with the XMPP IQ `forbidden` condition instead of a Jabber-RPC `<fault>` (via a new `forbidden()` wrapper on the vendored `xep_0009` plugin, alongside the existing `item_not_found()`/`send_fault()` wrappers).
- ✅ `LocalComm` needed no change — confirmed directly: `ForbiddenError` just propagates as a normal Python exception since the call is in-process.
- ✅ Unit tests: `Module.execute()` denies/allows correctly for `allow` (`"*"`, explicit method lists, no-`acl:`-block) and for `deny` (listed caller blocked, all others and all methods still permitted), in both `enforce` and `log` mode (`log` mode never raises, and produces a log record on what would have been denied) — `tests/modules/test/standalone.py`. Integration test over real ejabberd verifying the `forbidden` IQ round-trips into `exc.RemoteError` client-side, for both `allow` and `deny` (denied and non-denied caller in each) — `tests/integration/test_xmpp_acl.py`.
- ✅ Decided: per-module opt-in only, no global default-deny switch — see [Design](#design).
- ✅ `IModule.get_permitted_methods() -> list[str]` added and implemented in `Module`, resolving the caller's own `sender` against the target's `acl:` block (every method name if no block or if `mode == "log"`) — see [Finding out proactively](#design). Exempt from the ACL check in `Module.execute()` itself, the same way the existing `ModuleState.ERROR` check already special-cases `IModule` methods.
- ✅ `acl:` config key (both `allow` and `deny` forms, plus `mode`) documented alongside `comm:` in `docs/source/overview.rst`.
- ✅ Interface-name sugar (originally a [Follow-up](#follow-ups-not-required-for-v1)) implemented too: an `allow` entry may name an interface as shorthand for all of that interface's own methods — see the [Follow-ups](#follow-ups-not-required-for-v1) entry for how it's implemented.

**Two real, pre-existing bugs surfaced by actually exercising the `forbidden` condition end-to-end over a live ejabberd server, not by this design's own new code:**

- `pyobs/comm/xmpp/xep_0009/rpc.py`'s `XEP_0009` override defined `_handle_error` (leading underscore) as a no-op, but the base `slixmpp` plugin's `_handle_method_call` calls `self.handle_error(iq)` (no underscore) for any incoming `type="error"` IQ that still carries an `rpc_query` payload (exactly what `_forbidden()`/`_item_not_found()` produce, since both echo the original query back via `set_payload`). The names never matched, so this branch always raised `AttributeError` internally (logged by `slixmpp`, not raised to caller) instead of firing `jabber_rpc_error` — dating back to the original `pytel`→`pyobs` rename commit, never exercised because "nothing today can be forbidden" until now. Fixed: renamed to `handle_error` and made it fire `self.xmpp.event("jabber_rpc_error", iq)`, mirroring the base class's own other branch.
- Even with that fixed, `_on_jabber_rpc_error` (and the `_futures`-dict-based condition-to-message mapping it contains, written for exactly this purpose) turned out to be **unreachable in practice** for the `RPC.call()` path specifically: `XEP_0009.call()` does `await iq.send()`, and `slixmpp`'s own `Iq.send()` registers its own one-shot stanza-id-matched handler that resolves (or raises `IqError` on) the awaited future *before* control ever returns to the caller — so `XmppComm.execute()`'s `except slixmpp.exceptions.IqError` already unwinds the call with a generic `"Could not call {method} on {client}."` `RemoteError` first, regardless of what `_on_jabber_rpc_error` does with the same stanza. Fixed at the reachable point instead: `XmppComm.execute()` now inspects `e.iq["error"]["condition"]` and raises a `RemoteError` mentioning "Forbidden to invoke ..." specifically for `condition == "forbidden"`. (`_on_jabber_rpc_error`'s dict-based mapping remains in place and is now at least reachable for the `jabber_rpc_error` event itself, but is not what the caller of `RPC.call()` actually observes — a genuine pre-existing duplication this pass didn't attempt to unwind further, since doing so was not required to make Phase 8 work.)

**One more pre-existing bug, unrelated to XMPP, found while extending the `tests/modules/test/standalone.py` coverage for this phase:** `test_background_task` asserted `module._message_func in module._background_tasks` — but `_background_tasks` is a `list[tuple[BackgroundTask, bool]]`, so a bound method can never equal one of its tuples and the assertion could never actually fail on a regression. Confirmed pre-existing (reproduced against the commit this session started from, before any Phase 8 work). Fixed to check the wrapped function on each `BackgroundTask` instead: `any(task._func == module._message_func for task, _ in module._background_tasks)`.

