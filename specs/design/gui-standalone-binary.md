# Design: `pyobs-gui` as a standalone binary

Status: rejected 2026-09-14 — the real `pyside6-deploy`/Nuitka build (see "Real app build" in
`specs/plans/2026-07-27-gui-widget-plugins-and-packaging.md`) came out several GB, which Tim
judged not worth shipping/distributing to a non-technical remote observer (the whole point of a
one-file download). Kept here, not deleted, since two of the three underlying pieces
(`gui-interactive-login.md`, `gui-login-window.md`) already shipped and stand on their own merit
independent of this goal — see "What still stands" below.

Repos: pyobs-core (login-deferral piece), pyobs-gui (login window, plugin loading, packaging)

## Goal

A non-technical remote observer downloads one file, double-clicks it, and gets a working `pyobs`
control GUI — no Python installation, no hand-edited YAML config, no per-site rebuild. This is the
umbrella doc for that goal; it doesn't implement anything itself, it ties together three pieces of
work that each solve one part of the problem and links out to their own plan docs.

## Why three separate pieces

Each blocks on a different, mostly-independent technical constraint:

1. **There's no interactive path today.** `pyobs_gui.GUI` is a `pyobs.modules.Module` like any
   other, so it's launched through `pyobs.application.Application`, which requires a YAML config
   file naming the module class plus XMPP credentials *before the process can do anything at all*.
   A shipped binary still needs a hand-edited YAML sitting next to it. Splits into:
   - **pyobs-core side** — `specs/plans/gui-interactive-login.md` (drafted, not yet implemented):
     defer `Application`'s module construction so an async login dialog can run *after* the event
     loop starts but *before* the module (and its XMPP connection) is built.
   - **pyobs-gui side** — `specs/plans/gui-login-window.md` (new): the actual login window UI
     (saved accounts, JID/host/port entry, opt-in keychain password storage), built on top of the
     pyobs-core mechanism above.
2. **Custom widgets are genuinely dynamic code, which conflicts with static compilation — and
   deciding which one to use is a second, separate problem from loading it.** `pyobs-gui` supports
   per-deployment custom widgets via YAML (`widgets: [{module: guiding, widget: {class:
   mypackage.GuidingWidget}}]`), resolved through pyobs-core's `create_object()` →
   `get_class_from_string()` → a plain `__import__()` on whatever dotted path the config names —
   completely arbitrary from the compiler's point of view. `pyside6-deploy`/Nuitka can only bundle
   what they can see by static analysis of the app's own import graph, so a naively compiled binary
   would only ever support the built-in widget set (`DEFAULT_WIDGETS` in `mainwindow.py`), not
   arbitrary per-site custom ones. Explicitly **not** acceptable here: recompiling a separate binary
   per deployment defeats the entire point of shipping one binary. But that YAML block also decides
   *which* widget to use for which module — and per the "no config on the user side" goal above,
   that decision can't keep living in a local file either, which is a second, still-unsettled
   question distinct from "how do we load the code once we know what to load." Both are covered by
   `specs/plans/gui-widget-plugins-and-packaging.md` (new) — the loading mechanism is decided
   (external plugin directory on `sys.path`); the selection mechanism is deliberately postponed,
   with the considered options recorded there.

## How the pieces depend on each other

```
gui-interactive-login.md (pyobs-core: defer Application's module construction)
        │
        ▼
gui-login-window.md (pyobs-gui: actual login window UI)
        │
        │   (independent — doesn't depend on login, only on packaging)
        │
gui-widget-plugins-and-packaging.md (pyobs-gui: sys.path plugin dirs + pyside6-deploy pipeline)
        │
        ▼
   a real, distributable, one-binary-fits-all-sites pyobs-gui
```

The login-flow pair and the plugin/packaging plan are independent of each other and can land in
either order or in parallel — a compiled binary is equally blocked on "no way to enter credentials"
and "no way to load a site's custom widgets" regardless of which gets fixed first. Both are
required before "ship one binary" is actually true end to end.

## Non-goals (for this doc and, unless a sub-plan says otherwise, for all three)

- Any specific installer/distribution mechanism (GitHub Releases, auto-update, code signing) —
  once a binary can be produced at all, distributing it is a separate, later concern.
- Cross-platform parity guarantees. `pyside6-deploy`/Nuitka support Windows/macOS/Linux, but nothing
  here assumes all three are in scope for v1 — whichever platform(s) the first real deployment
  needs drives that, not this doc.
- Rewriting `pyobs-gui` in a different toolkit/language (QML, Electron) to sidestep these problems
  — `pyobs-gui/DEV_qml_evaluation.md` already looked at this direction and shelved it; this doc
  assumes we're keeping PySide6/Widgets.

## Status of the pieces

| Piece | Doc | Status |
|---|---|---|
| Defer `Application`'s module construction | `gui-interactive-login.md` | implemented, closed |
| Login window UI | `gui-login-window.md` | implemented, closed |
| Widget loading mechanism | `gui-widget-plugins-and-packaging.md` | abandoned — moot without a compiled binary to load plugins into |
| Widget selection mechanism | `gui-widget-plugins-and-packaging.md` | abandoned, same reason |
| `pyside6-deploy` packaging pipeline | `gui-widget-plugins-and-packaging.md` | abandoned — the real build that proved it worked is also what surfaced the several-GB size that killed the goal |

## What still stands

The login-deferral/login-window pair (`gui-interactive-login.md`, `gui-login-window.md`) doesn't
depend on shipping a compiled binary — it's a real UX improvement to `pyobs-gui` on its own
(saved accounts, no hand-edited YAML) regardless of how the app is distributed. Both already
shipped and stay shipped; only the packaging/plugin-loading piece (and the "one download, no
Python install" framing this doc was written around) is off the table.
