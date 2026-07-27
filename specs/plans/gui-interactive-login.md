# Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction

Status: draft
Repos: pyobs-core (this plan's scope — see Non-goals), pyobs-gui (follow-on, depends on this)
See `specs/design/gui-standalone-binary.md` for the bigger picture this is one piece of, and
`specs/plans/gui-login-window.md` for the pyobs-gui-side follow-on this unblocks.

## Problem

Motivation: distributing `pyobs-gui` as a compiled standalone binary (`pyside6-deploy`/Nuitka) so
non-technical remote observers can "just run it." Compiling the binary alone doesn't get there —
`pyobs_gui.GUI` (`pyobs_gui/gui.py:14`) is a `pyobs.modules.Module` like any other, so it's launched
through `pyobs.application.Application`, which requires a YAML config file naming the module class
plus a `comm:` block with the XMPP JID/password/server *before the process can do anything at all*
(`Application.__init__`, `pyobs/application.py:56-204`). A shipped binary still needs a hand-edited
YAML file with credentials sitting next to it — there's no interactive path today. `pyobs-polaris`
(a separate, from-scratch C++/QML client for the same XMPP protocol) solves this with
`qml/LoginWindow.qml`: a saved-accounts login window shown immediately on launch, with JID,
optional host/port override, and an opt-in "store password in system keychain" checkbox — `Connect`
never implicitly saves anything.

This plan is the **pyobs-core side only**: what `Application` needs to change to make a
login-dialog-first flow possible at all. The `pyobs-gui`-side login window itself is a separate,
follow-on piece of work in that repo (see "Out of scope" below) and depends on this.

### Why this isn't already possible

It looked at first like it might not need any core change — `Module`/`Object` already support
fully programmatic construction with no YAML involved: `Object.__init__`'s `comm`/`vfs` params each
accept either a config dict *or* an already-constructed instance (`pyobs/object.py:244-245`,
resolved at `object.py:328-336` for `comm`, `object.py:280-283` for `vfs`), and both fall back to a
sane default (`DummyComm()`, a local `VirtualFileSystem()`) when omitted entirely. So in principle,
`GUI(comm=XmppComm(jid=..., password=...))` works fine as plain Python with no config file.

The actual blocker is `Application` itself, which is the only thing that provides the shared
lifecycle machinery worth reusing (logging setup, the IERS-offline env var handling, signal
handlers, and critically `_main()`'s `startup()` → `main()` → `close()` orchestration with graceful
shutdown on `SIGTERM`/`SIGINT`, `application.py:206-271`). `Application.__init__` does config
loading and `self._module = get_object(cfg, Module)` (`application.py:161-185`) **synchronously,
before `run()` ever starts the event loop** — there is no point in that sequence where async code
(e.g. `await` on a Qt dialog's "submit" signal via `qasync`) can run. A login dialog needs to show
*after* the event loop exists but *before* the module is constructed — a sequencing `Application`
doesn't support today.

## Goals

1. Let a module class be constructed **after** the event loop starts, from an async factory,
   instead of requiring it to already exist by the time `Application.__init__` returns.
2. Reuse all of `Application`'s existing lifecycle code (`run()`, `_main()`, `_signal_handler()`,
   logging/warnings setup) unchanged for both the existing config-file path and the new
   deferred-construction path — this is additive, not a rewrite.
3. Keep the existing config-file-driven `Application(config="...")` path (used by every other
   module in the fleet) working byte-for-byte identically. No behavior change for anyone not
   opting into the new path.

## Non-goals

- The actual login/settings dialog UI (QML or QWidgets, saved-accounts list, keychain password
  storage) — that's `pyobs-gui`-side work, follow-on to this plan, not part of it.
- Changing how `vfs`/`observer`/`location` are configured — v1 of the interactive flow only needs
  to solve `comm` (the XMPP connection details); those already default sanely with no config at all
  (`object.py:280-283`, `object.py:311-321`) and can stay YAML/default-driven if ever needed.
- Packaging/compiling itself (`pyside6-deploy`, Nuitka, installers) — separate concern, not blocked
  by or part of this plan; see `specs/plans/gui-widget-plugins-and-packaging.md`.
- Any change to `MultiModule`, which has its own separate construction path
  (`pyobs/modules/module.py:862-894`) not touched here.

## Design

Add a second, alternate way to build an `Application` that skips config-file parsing entirely and
instead defers module construction to an async factory supplied by the caller:

```python
class Application:
    def __init__(
        self,
        config: str | None = None,
        module_factory: Callable[[], Awaitable[Module]] | None = None,
        loop_module_class: type[Module] | None = None,
        ...
    ):
        ...
```

- Exactly one of `config` / `module_factory` must be given (mirrors the existing "exactly one of
  X/Y" validation pattern already used elsewhere in this codebase, e.g.
  `pyobs/modules/flatfield/scheduler.py`'s `sources`/`interval` check before this cleanup pass).
- `config` path: entirely unchanged from today — parse YAML, `get_object(cfg, Module)`, done
  synchronously in `__init__`, exactly as now.
- `module_factory` path: `__init__` does *not* construct `self._module` at all. It still needs a
  module class to pick the event loop from (`new_event_loop()`, `application.py:172-181`) — pass
  `loop_module_class` explicitly instead of discovering it from a parsed config's `class:` key,
  since the caller already knows which module it's about to build (`GUI`, hardcoded, in
  `pyobs-gui`'s case). `self._module` stays unset (`Module | None`) until `_main()` resolves it.
- `_main()` (`application.py:241-271`) gets one change: if `self._module` isn't set yet, resolve it
  first —
  ```python
  if self._module is None:
      self._module = await self._module_factory()
  ```
  as the first line inside the existing `try` block. This runs *inside* the running event loop, so
  the factory can `await` a Qt dialog's submit signal (via `qasync`) for as long as it needs —
  seconds or hours, doesn't matter, nothing else is blocked. Everything after
  (`await self._module.startup()`, `await self._module.main()`, the `finally` close) is unchanged.
- Null-safety: `self._module` can now legitimately be `None` for a window of time (while the login
  dialog is up). Audit and guard the two places that currently assume it's always set:
  - `_signal_handler()` (`application.py:230-239`) — calls `self._module.quit()` unconditionally;
    needs a `None` check (e.g. just close the Qt app / stop the loop directly if no module exists
    yet).
  - `_main()`'s `finally` block (`application.py:258-271`) — already has `if self._module is not
    None:` before closing it, so this one's already safe; keep as reference for the pattern.
- `GuiApplication` (`application.py:274-297`) is a separate, older mechanism (wraps the *existing*
  config-file path with a log-window, `pyobs/utils/modulegui.py`) — not touched by this plan, not
  reused by `pyobs-gui`'s new flow, which needs its own `QApplication`/`qasync` loop already created
  by `GUI.new_event_loop()` (`pyobs_gui/gui.py:50-53`), not a second one.

## Non-goals for the factory's contract

The factory itself is 100% `pyobs-gui`-side code (build a `LoginWindow`, wait for `Connect`,
construct `XmppComm(jid=..., password=..., server=...)`, then `GUI(comm=that_comm, ...)`) — this
plan only needs `Application` to be able to call *some* `Callable[[], Awaitable[Module]]` at the
right point in the lifecycle; it has no opinion on what's inside it.

## Implementation checklist

- [ ] `Application.__init__`: add `module_factory` and `loop_module_class` params; validate
      exactly one of `config`/`module_factory` is given.
- [ ] Guard the existing config-parsing block (`application.py:161-204`, including the name-mismatch
      warning at `195-204`, which is meaningless without a config file) behind `if config is not
      None:`.
- [ ] Event-loop creation (`application.py:170-181`): when `module_factory` is given, use
      `loop_module_class` directly instead of the config-derived `klass`/child-module scan.
- [ ] Store `self._module: Module | None = None` and `self._module_factory` when in factory mode.
- [ ] `_main()`: resolve `self._module` from the factory as the first step inside `try`, if not
      already set.
- [ ] `_signal_handler()`: guard `self._module.quit()` for the `self._module is None` case.
- [ ] Tests: config-file path unchanged (existing coverage should still pass as-is); new tests for
      factory-mode construction, the exactly-one-of validation, and signal handling before the
      factory has resolved.
- [ ] Update this doc's `Status:` to `implemented` once landed, per `CLAUDE.md`'s convention for
      `specs/design/` (this file lives in `specs/plans/` per the checklist convention, but keep the
      same status-update habit).

## Open questions

- Does `loop_module_class` need to be a full class, or would passing an already-bound
  `new_event_loop` classmethod/callable be cleaner? Leaning toward the class, since
  `Application` already does `klass.new_event_loop()` for the config path and this keeps both
  paths symmetric.
- Should `module_factory` be allowed to raise/cancel (e.g. user closes the login window without
  connecting) and have `Application` shut down cleanly in that case, rather than only supporting
  "eventually resolves"? Needs an answer before `pyobs-gui` can implement "Cancel" or window-close
  on the login dialog. Current lean: yes, `_main()`'s existing `except Exception: log.exception(...)`
  plus `finally` (which already guards `self._module is not None`) should handle this for free —
  worth a dedicated test rather than assuming.
