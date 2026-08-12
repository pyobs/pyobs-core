# Plan: `pyobs-gui` login window

Status: implemented, closed.

Repos: pyobs-gui (primary — all implementation here), pyobs-core (depends on
`gui-interactive-login.md` landing first, no other pyobs-core changes needed)

See `specs/design/gui-standalone-binary.md` for how this fits into the bigger "ship one
compiled binary" goal.

## Problem

`gui-interactive-login.md` gives `pyobs.application.Application` a way to defer building the
`Module` until an async factory resolves — but that factory is 100% `pyobs-gui`-side code, not
part of that plan. This is that factory's content: an actual login window.

## Model: `pyobs-polaris`'s `LoginWindow.qml`

`pyobs-polaris` is a separate, from-scratch QML/C++ client for the same XMPP protocol, and already
solved this exact problem (`qml/LoginWindow.qml`, `src/config/SavedAccountsModel.{h,cpp}`). Reuse
its UX model and the reasoning behind its design choices — not its code, since the toolkit
(QML vs. `QtWidgets`) and language (C++ vs. Python) differ:

- **List-left / detail-right**, not a single form: a `ListView` of saved accounts on the left, a
  detail panel on the right showing whichever account is selected (or a blank "new connection"
  form). Selecting an account prefills the form; it does not connect.
- **Connect always uses whatever's currently in the fields.** Saving an account and storing its
  password are two separate, explicit actions (buttons), never implicit side effects of clicking
  Connect. This is the project's standing rule for anything security-sensitive — visible, opt-in,
  never silent.
- **Password storage is opt-in per account** ("Store password in system keychain" checkbox),
  separate from the rest of the account's metadata (JID, label, optional host/port override),
  which is saved regardless. A failure to store/delete a keychain entry is surfaced visibly
  (`keychainNotice` in the QML), not swallowed.
- **Accounts are keyed by a stable internal id (UUID), not by JID.** The keychain entry is keyed
  on that id too, so renaming an account's JID or label never orphans its stored password.
  (`SavedAccountsModel.h`'s comment on this is the right reasoning to carry over verbatim.)
- **Host/port override is optional and separate from the JID.** Normal connections use DNS SRV
  discovery from the JID's domain (`XmppClient::connectToServer`'s existing default); the override
  checkbox exists only for networks without usable SRV records.

## Goals

1. A login window shown by the `module_factory` from `gui-interactive-login.md`, before any
   `Module`/`XmppComm` exists.
2. A saved-accounts list, persisted locally, surviving restarts.
3. Per-account opt-in password storage in the OS-native credential store (keychain/Credential
   Manager/Secret Service), never on by default.
4. `Connect` always builds a fresh `XmppComm` from the currently-displayed fields; saving is a
   separate, explicit action.

## Non-goals

- Multi-user/shared-machine account isolation (e.g. OS-user-scoped keychain access is whatever the
  underlying credential-store library already gives us for free; no additional sandboxing here).
- SSO/OAuth or any auth scheme beyond plain XMPP JID+password — matches what `XmppComm` supports
  today (`pyobs/comm/xmpp/xmppcomm.py:124-138`: `jid`, `password`, `server`, `use_tls`,
  `ignore_cert_errors`).
- Changing `XmppComm`'s own connection API — this plan is a caller of it, not a modifier.

## Design

### Widget layout

`QtWidgets` equivalent of the QML list-left/detail-right layout: a `QListWidget` (saved accounts)
next to a form panel (`QLineEdit` for JID/label/password/host/port, `QCheckBox` for "store
password" and "skip TLS verification" and "override server", a status label, Connect/Save/Delete
buttons). This is a new top-level window (`QtWidgets.QDialog` or a second `QMainWindow`), shown by
`GUI.new_event_loop()`'s already-created `QApplication` before `MainWindow` exists — mirrors how
`gui.py:50-53` already sets up the Qt/`qasync` event loop, just with a different first window.

### Account metadata storage

`QtCore.QSettings` (already available via the existing PySide6 dependency) for the account list
itself (id, JID, label, host/port override, whether a password is stored) — the direct Python/Qt
analog of polaris's own `QSettings`-backed `SavedAccountsModel`/`AppSettings`, so the two sibling
clients persist their account lists the same way.

### Password storage

The `keyring` package (PyPI, cross-platform: macOS Keychain, Windows Credential Manager, Linux
Secret Service/KWallet) — the direct Python analog of polaris's `QtKeychain`. Store/retrieve keyed
by the account's stable id (not JID/label), matching polaris's reasoning exactly: renaming an
account must not orphan its password.

**Resolved by the Phase 0 spike** (`gui-widget-plugins-and-packaging.md`, 2026-07-27): `keyring`'s
`importlib.metadata` entry-point backend discovery survives a real `pyside6-deploy` standalone
build unmodified — the frozen binary picked the exact same backend
(`keyring.backends.SecretService.Keyring`) as an unfrozen run, with a working roundtrip. No pinning
workaround needed.

### Connect flow

The `module_factory` (from `gui-interactive-login.md`) builds this window, `await`s its "connect
requested" signal (via `qasync`, same pattern `gui.py` already uses for the Qt event loop), then:

```python
comm = XmppComm(
    jid=jid_field.text(),
    password=password_field.text(),
    server=f"{host}:{port}" if override_checked else None,
    use_tls=use_tls_checkbox.isChecked(),
    ignore_cert_errors=skip_tls_checkbox.isChecked(),
)
return GUI(comm=comm, ...)
```

**Correction (2026-07-27):** the snippet above originally omitted `use_tls` entirely — `XmppComm.use_tls`
defaults to `False`, so without an explicit "Use SSL/TLS" checkbox the login window couldn't connect
to any TLS-requiring server at all. Added a `_use_tls_checkbox`, defaulting to **checked** (secure-by-
default for a login window aimed at potentially non-technical remote users, even though `XmppComm`
itself defaults to `False` — more appropriate for its own trusted-local-network callers). Unchecking
it also disables and unchecks "skip TLS certificate verification," since that only means anything
when TLS itself is on. `Account`/`SavedAccountsModel` persist `use_tls` per saved account the same
way they already did `insecure_skip_tls`.

`XmppComm.server` is a single `"host:port"` string (port defaults to 5222 if omitted,
`xmppcomm.py:289-294`) — the two separate host/port fields in the UI get combined into that one
string, mirroring what `overrideHost()`/`overridePort()` do in the QML version.

## Non-goals for `module_factory`'s contract

Whether the factory can be cancelled (user closes the login window without connecting) is
`gui-interactive-login.md`'s open question, not this plan's — this plan assumes that question is
answered by the time this window's "Cancel"/window-close behavior needs to actually do something.

## Implementation checklist

Done 2026-07-27, on `feature/standalone-binary` (both repos). `keyring` added as a real
`pyobs-gui` dependency (was spike-only before). First pytest infrastructure `pyobs-gui` has had
(`pytest`/`pytest-asyncio`/`pytest-mock` added, `tests/` created, offscreen Qt platform default in
`conftest.py`).

- [x] Spike: does `keyring`'s backend auto-detection survive a `pyside6-deploy` build? — yes,
      confirmed in Phase 0 (see Design above).
- [x] `LoginWindow` widget (list-left/detail-right, per Design above) — `pyobs_gui/loginwindow.py`.
      Built directly in `QtWidgets` code rather than a compiled `.ui` file (this repo's usual
      `Ui_XxxWidget` convention) since there's no interactive Qt Designer available in this
      environment — a deliberate deviation, not an oversight.
- [x] Account metadata persistence via `QSettings` — `pyobs_gui/accounts.py`
      (`SavedAccountsModel`), org/app `("pyobs", "pyobs-gui")`.
- [x] Password persistence via `keyring`, keyed by account id — in `LoginWindow`, service name
      `"pyobs-gui"`.
- [x] Wire into `gui-interactive-login.md`'s `module_factory` contract — `pyobs_gui/login.py`
      (`login_and_build_gui`) plus a new standalone entry point, `pyobs_gui/__main__.py`, which
      bypasses the config-file-driven `pyobs` CLI entirely (this is what a compiled binary
      targets). Verified end to end: constructed a real `Application(module_factory=
      login_and_build_gui, loop_module_class=GUI)` against the actual (locally editable-installed)
      updated `pyobs-core`, not just type-checked against it.
- [x] Status/error display (connecting/error/connected, keychain failures) mirroring the QML
      version's visible-not-swallowed handling — status label + a keychain-notice label shown on
      store/delete failure, matching `keychainNotice` in the QML.
- [x] Tests: 23 new tests (`tests/test_accounts.py`, `tests/test_loginwindow.py`) — account CRUD,
      id-stability-across-rename, `build_connection_request()` (pulled out as a plain function so
      the Connect-button logic is testable without simulating Qt clicks) including the
      override-checked-but-host-blank edge case, and window-level behavior (list population,
      selecting an account prefills fields, Connect resolves `wait_for_connect()`, closing without
      connecting cancels it instead of hanging).
- [x] Update this doc's `Status:` to `implemented` once landed — see below.

**Note for whoever continues this branch:** `pyobs-gui`'s venv currently has `pyobs-core` locally
editable-installed from `../pyobs-core` (`uv pip install -e`, not `uv add`) so it actually runs
against this branch's `Application` changes instead of the PyPI-pinned `dev28` in `pyproject.toml`.
This is intentionally *not* committed — a plain `uv sync` reverts it. Needed again after that, or
once a real `pyobs-core` release includes the `module_factory` change and `pyproject.toml`'s pin
can be bumped for real.
