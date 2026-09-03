# Fleet open items: open issues and plans across the pyobs fleet

Status: standing snapshot — checked on 2026-09-03 (issues re-queried; #831/#832 landed on
`develop` via PR #840/#842 so dropped per the maintenance rule below, though both GitHub issues
stay open pending release to `main`; observation-portal-keycloak-auth plan dropped, implemented
and deployed for MONET as of 2026-09-03; full fleet-wide re-check same day: pyobs-portal#141 and
pyobs-weather#35 closed, pyobs-core#871 and pyobs-web-admin#89 (new repo in this table) opened,
pyobs-portal's `2026-09-02-instrument-capability-estimate-duration-endpoint.md` added; pyobs-core#849
closed — fix landed on `develop` `f95da2c6` 2026-09-01, issue itself just hadn't been closed;
pyobs-core#861 closed same day — fixed in pyobs-web-client, landed on its `develop` `7fa5061`).

Fleet-wide view of what's open across the pyobs project fleet (see
`specs/steering/pyobs-project-tiers.md` for the fleet definition). This is a **derived view**, not
a source of truth:

- **Open issues**: GitHub is authoritative — re-query with `gh issue list --repo pyobs/<repo>
  --state open`.
- **Open plans**: each repo's own `specs/plans/index.md` (or `specs/index.md` for repos that keep
  their plans there) is authoritative; this doc links the docs and copies their one-line status.

**Maintenance rule: update this file whenever you open/close an issue or change a plan's status —
and remove items outright once their fix has landed on `develop` (even if the GitHub issue stays
open pending a release to `main`), never annotate them.** Only open items live here.

Repos: the whole pyobs fleet.

## Open issues (13, checked 2026-09-03)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#871](https://github.com/pyobs/pyobs-core/issues/871) | `Comm`: `unregister_event()` doesn't cancel already-scheduled handler tasks (stale-widget race) | pyobs-gui `DataDisplayWidget._on_new_data` hits a `libshiboken` already-deleted-object error when a widget is torn down before its scheduled event-dispatch task runs; caught/logged, not fatal, but a real dispatch-ordering bug in `comm.py`'s `_send_event_to_module()`/`unregister_event()` |
| pyobs-core | [#866](https://github.com/pyobs/pyobs-core/issues/866) | `Module._on_module_opened` fan-out is unthrottled, saturates event loop with enough peers | confirmed twice (iag50 module-join timeouts, pyobs-gui `monet` GUI-freeze) — see `specs/steering/module-opened-fanout-stalls-event-loop.md` |
| pyobs-core | [#863](https://github.com/pyobs/pyobs-core/issues/863) | Colors in web projects, especially plots: theme-aware chart colors and user-defined colors that work in both themes | *enhancement* — follow-up to #861 (now closed/implemented) |
| pyobs-core | [#846](https://github.com/pyobs/pyobs-core/issues/846) | `DarkBiasScript`: inherit archive/site from the caller instead of per-task config (like pipeline steps) | *enhancement, on hold* — mirror pyobs-pipeline's `_with_default_archive()` caller-level inheritance instead of requiring `archive`/`site` on every task with `match_science_exptimes=True` (follow-up to #831). Confirmed no existing caller-level slot holds archive+site (checked `TaskRunner`, `Object`'s location/observer, `LcoObservationArchive`'s site) — a real new injection point, not a wiring gap. Same redundancy also exists in `pyobs/robotic/utils/skyflats/priorities/archive.py`. Not required at the moment (Repos: pyobs-core, pyobs-portal, pyobs-pipeline) |
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-core | [#739](https://github.com/pyobs/pyobs-core/issues/739) | Record installed pyobs package versions in FITS headers | *enhancement* — per-package version keywords; approach undecided |
| pyobs-core | [#858](https://github.com/pyobs/pyobs-core/issues/858) | Use live telescope position for scheduler's first-task slew-distance estimate | *enhancement* — follow-up to the (now-implemented) instrument-capability-duration-estimates plan; solvable now for `OnDemandScheduler`'s first placed task only (one pre-fetched live position), not the harder mid-schedule/portal-UI cases |
| pyobs-core | [#859](https://github.com/pyobs/pyobs-core/issues/859) | Track last-scheduled-task position through `OnDemandScheduler` for slew-distance estimates beyond the first task | *enhancement* — follow-up to #858; needs "last scheduled task's target" state threaded through `OnDemandScheduler`'s greedy recursion, careful of `check_for_better_task`/`can_postpone_task`'s out-of-order yields |
| pyobs-brot | [#61](https://github.com/pyobs/pyobs-brot/issues/61) | `set_offsets_altaz` times out (120s) repeatedly during autoguiding on MONET South | *bug, assigned: thusser* — three consecutive settle-wait timeouts during a 2026-08-24 autoguiding run on monets1m2; needs mount-side telemetry/drive-fault investigation |
| pyobs-portal | [#143](https://github.com/pyobs/pyobs-portal/issues/143) | Dashboard schedule timeline shows local browser time instead of UTC | `dashboard.js`'s `observationItem()` builds timeline items with plain `new Date(...)`, no UTC override; tooltip already uses `toUTCString()` |
| pyobs-archive | [#57](https://github.com/pyobs/pyobs-archive/issues/57) | Consider a Keycloak-role-synced archive-admin flag (deferred from #56) | |
| pyobs-weather | [#6](https://github.com/pyobs/pyobs-weather/issues/6) | Historic data | *enhancement* |
| pyobs-web-admin | [#89](https://github.com/pyobs/pyobs-web-admin/issues/89) | Flag running modules as needing restart after their config file changes | new repo in this table. Config drift (on-disk vs. loaded-at-startup) isn't tracked; should probably reuse the UI pattern of the existing package-version "restart-outdated" mechanism (`stale_packages()`/`restart_module()`) |

## Open plans

### pyobs-core `specs/plans/`

- [2026-07-27-gui-widget-plugins-and-packaging.md](../plans/2026-07-27-gui-widget-plugins-and-packaging.md) —
  *draft* (pyobs-gui). Widget plugin mechanism + `pyside6-deploy` packaging; loading mechanism
  decided + spiked, widget-selection mechanism still open.
- [2026-07-29-gui-telescopewidget-layout.md](../plans/2026-07-29-gui-telescopewidget-layout.md) —
  *proposed* (pyobs-gui). `TelescopeWidget` width-floor investigation with candidate fixes.
- [2026-08-23-iag50-pyobs-core-2x-migration.md](../plans/2026-08-23-iag50-pyobs-core-2x-migration.md) —
  *in progress* (pyobs-iag50, IAG-internal). `1.x` branch cut, `develop` reset to
  `2.0.0.dev0`/`pyobs-core>=2.0.0.dev93`; actual code migration (grid-API rewrite, `self.proxy()`
  async-context-manager change, missing-await fixes) not yet done, three open questions need
  Tim's input.

### Design docs still *proposed*

- [gui-standalone-binary.md](../design/gui-standalone-binary.md) — umbrella for the compiled
  pyobs-gui binary; login pieces done, widget plugin/selection + real plugin smoke test still open.
- [interface_versioning.md](../design/interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...) (#819). Sanity-checked against `develop` 2026-08-28 (MRO/diamond,
  registration, discovery, wire round-trip all verified); gaps recorded before a plan; no plan yet.

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-portal** — [2026-09-02-instrument-capability-estimate-duration-endpoint.md](../../pyobs-portal/specs/plans/2026-09-02-instrument-capability-estimate-duration-endpoint.md) —
  this repo's half of `2026-09-01-instrument-capability-duration-estimates.md` (pyobs-core side,
  now implemented/closed): a TTL-cached `get_instrument_capabilities()` helper feeding
  `schema.py`'s `estimate_duration/`, plus a `last_instrument_update/` marker for pyobs-core's
  `PortalTaskArchive` to poll (*proposed*, no issue yet; Repos: pyobs-portal, pyobs-core)
- **pyobs-gui** — [2026-09-01-gui-video-widget-split.md](../../pyobs-gui/specs/2026-09-01-gui-video-widget-split.md) —
  split `VideoWidget` into a main widget + paired sidebar widget, D6 follow-up to the (now landed,
  see pyobs-gui's own `specs/index.md`) main-vs-sidebar-widgets plan (#150) (*draft, unblocked*)
- **pyobs-web-client** — [acl-aware-shell-forms](../../pyobs-web-client/specs/plans/acl-aware-shell-forms.md) —
  ACL-aware Shell forms (*proposed*)
- **pyobs-web-client** — [auxiliary-interface-widgets](../../pyobs-web-client/specs/plans/auxiliary-interface-widgets.md) —
  auxiliary interface widgets (attach-or-standalone) (*proposed*)
- **pyobs-web-client** — [idatasequence](../../pyobs-web-client/specs/plans/idatasequence.md) —
  `IDataSequence` support ("grab N images") (*proposed*)
- **pyobs-web-client** — [rpc-fault-call-id](../../pyobs-web-client/specs/plans/rpc-fault-call-id.md) —
  surface `call_id` on RPC faults (*proposed*)
- **pyobs-web-client** — [struct-typed-command-params](../../pyobs-web-client/specs/plans/struct-typed-command-params.md) —
  `struct<Name>`-typed command params (*blocked on upstream*)
- **pyobs-web-client** — [telescope-page](../../pyobs-web-client/specs/plans/telescope-page.md) —
  telescope page for `ITelescope` modules (*proposed*)
- **pyobs-web-client** — [vfs-token-auth](../../pyobs-web-client/specs/plans/vfs-token-auth.md) —
  VFS endpoint auth (Basic Auth → Bearer token) (*proposed, unblocked — the pyobs-core release
  it depended on has shipped*)
