# Fleet open items: open issues and plans across the pyobs fleet

Status: standing snapshot — checked on 2026-08-21.

Fleet-wide view of what's open across the pyobs project fleet (see
`specs/steering/pyobs-project-tiers.md` for the fleet definition). This is a **derived view**, not
a source of truth:

- **Open issues**: GitHub is authoritative — re-query with `gh issue list --repo pyobs/<repo>
  --state open`.
- **Open plans**: each repo's own `specs/plans/index.md` (or `specs/index.md` for repos that keep
  their plans there) is authoritative; this doc links the docs and copies their one-line status.

**Maintenance rule: update this file whenever you open/close an issue or change a plan's status —
and remove closed items outright, never annotate them.** Only open items live here.

Repos: the whole pyobs fleet.

## Open issues (7, checked 2026-08-21)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#769](https://github.com/pyobs/pyobs-core/issues/769) | Dedupe per-frame header/JSON build in `BaseVideo` raw_handler | flagged in #766 review; N raw clients ⇒ N× header build/serialization/copy per frame |
| pyobs-core | [#767](https://github.com/pyobs/pyobs-core/issues/767) | `FitsHeaderMixin` only catches `RemoteError` | a peer's malformed response (non-`IqError`/`IqTimeout`) crashes the whole exposure |
| pyobs-core | [#739](https://github.com/pyobs/pyobs-core/issues/739) | Record installed pyobs package versions in FITS headers | *enhancement* — per-package version keywords; approach undecided |
| pyobs-robotic-backend | [#81](https://github.com/pyobs/pyobs-robotic-backend/issues/81) | Full script builder for the task editor | *enhancement* |
| pyobs-robotic-backend | [#82](https://github.com/pyobs/pyobs-robotic-backend/issues/82) | Connect to pyobs-archive to link observations to their data directly | *enhancement* |
| pyobs-archive | [#42](https://github.com/pyobs/pyobs-archive/issues/42) | Show only images the logged-in user has access to | needs connection to pyobs-robotic-backend |
| pyobs-weather | [#6](https://github.com/pyobs/pyobs-weather/issues/6) | Historic data | *enhancement* |

## Open plans

### pyobs-core `specs/plans/`

- [2026-07-27-gui-widget-plugins-and-packaging.md](../plans/2026-07-27-gui-widget-plugins-and-packaging.md) —
  *draft* (pyobs-gui). Widget plugin mechanism + `pyside6-deploy` packaging; loading mechanism
  decided + spiked, widget-selection mechanism still open.
- [2026-07-29-gui-telescopewidget-layout.md](../plans/2026-07-29-gui-telescopewidget-layout.md) —
  *proposed* (pyobs-gui). `TelescopeWidget` width-floor investigation with candidate fixes.
- [2026-08-19-archive-project-access-control.md](../plans/2026-08-19-archive-project-access-control.md) —
  *planned* (pyobs-archive, pyobs-robotic-backend). Show only frames the logged-in user has
  access to; core/pipeline angle of pyobs-archive#42 (mastermind writes `PROJECT` FITS keyword).
- [2026-08-20-imagewatcher-event-loop-blocking.md](../plans/2026-08-20-imagewatcher-event-loop-blocking.md) —
  *proposed* (pyobs-monet). Stop `ImageWatcher._worker`'s FITS parse and `LocalFile` I/O from
  blocking the event loop (MONET South incident, 2026-08-20).
- [2026-08-21-basevideo-http-token-auth.md](../plans/2026-08-21-basevideo-http-token-auth.md) —
  *proposed* (pyobs-core, pyobs-gui). Shared-token auth + browser login page for `BaseVideo`'s
  HTTP endpoints (design: `specs/design/basevideo-http-auth.md`).
- [2026-08-21-keycloak-idp-hint-login.md](../plans/2026-08-21-keycloak-idp-hint-login.md) —
  *proposed* (pyobs-auth, pyobs-archive, pyobs-robotic-backend, pyobs-web-admin). One-click IdP
  login via `kc_idp_hint` (dual login buttons).

### Design docs still *proposed*

- [gui-standalone-binary.md](../design/gui-standalone-binary.md) — umbrella for the compiled
  pyobs-gui binary; login pieces done, widget plugin/selection + real plugin smoke test still open.
- [basevideo-http-auth.md](../design/basevideo-http-auth.md) — shared-token auth with a browser
  login page for `BaseVideo`'s HTTP endpoints (pyobs-core, pyobs-gui); implementation tracked in
  plan `2026-08-21-basevideo-http-token-auth.md`.

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-archive** — [2026-08-20-archive-project-access-control](../../pyobs-archive/specs/plans/2026-08-20-archive-project-access-control.md) —
  project-based access control for frames, archive side of pyobs-archive#42 (*planned*)
- **pyobs-robotic-backend** — [2026-08-20-connect-pyobs-archive](../../pyobs-robotic-backend/specs/plans/2026-08-20-connect-pyobs-archive.md) —
  observations → archived-frame links, backend side of #82 (*planned*; on PR #85, not yet on
  `develop`)
- **pyobs-robotic-backend** — [2026-08-20-script-builder](../../pyobs-robotic-backend/specs/plans/2026-08-20-script-builder.md) —
  full schema-driven script builder for the task editor, #81 (*planned*; on PR #85, not yet on
  `develop`)
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
  VFS endpoint auth (Basic Auth → Bearer token) (*proposed*)

## Open decisions

- **ADR 0013** (rename pyobs-robotic-backend → `pyobs-schedule`) — *proposed*: `pyobs-schedule` is
  the recommendation, pending team confirmation; the rename itself (repo/package/Docker
  image/Keycloak client, in lockstep) has not been executed. See
  [0013-renaming-pyobs-robotic-backend.md](../adrs/0013-renaming-pyobs-robotic-backend.md).
