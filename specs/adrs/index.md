# ADRs

Short decision records for choices that had genuine considered-and-rejected alternatives
(MADR-lite: Context, Considered Options, Decision Outcome, Consequences).

- [0001-interface-state-checked-by-own-declaration-not-inheritance.md](0001-interface-state-checked-by-own-declaration-not-inheritance.md) —
  check `Interface.state`/`capabilities` by own declaration, not inherited presence. *accepted*
- [0002-xmpp-stream-conflict-quits-instead-of-reconnecting.md](0002-xmpp-stream-conflict-quits-instead-of-reconnecting.md) —
  on XMPP stream-error `conflict`, quit instead of reconnecting. *accepted*
- [0003-proxy-access-restricted-to-async-with.md](0003-proxy-access-restricted-to-async-with.md) —
  restrict `Proxy` access to `async with`; remove `await self.proxy(...)`. *accepted*
- [0004-acl-enforcement-on-callee-not-caller.md](0004-acl-enforcement-on-callee-not-caller.md) —
  enforce access control on the callee, not the caller. *accepted*
- [0005-iconfig-stays-a-stringly-keyed-fallback.md](0005-iconfig-stays-a-stringly-keyed-fallback.md) —
  `IConfig` stays a stringly-keyed name/value fallback. *accepted*
- [0006-wait-for-state-returns-none-on-timeout.md](0006-wait-for-state-returns-none-on-timeout.md) —
  `Proxy.wait_for_state()` returns `None` on timeout instead of raising. *accepted*
- [0007-get-interfaces-waits-before-raising-indexerror.md](0007-get-interfaces-waits-before-raising-indexerror.md) —
  `XmppComm.get_interfaces()` waits briefly before raising. *accepted*
- [0008-safe-send-keeps-bounded-retry-unlike-capability-subscribe-fetches.md](0008-safe-send-keeps-bounded-retry-unlike-capability-subscribe-fetches.md) —
  `_safe_send` keeps a bounded retry budget. *accepted*
- [0009-event-loop-lag-watchdog-lives-on-module-not-comm-or-application.md](0009-event-loop-lag-watchdog-lives-on-module-not-comm-or-application.md) —
  event-loop lag watchdog lives on `Module`. *accepted*
- [0010-pyobs-gui-stays-on-qtwidgets-not-qml.md](0010-pyobs-gui-stays-on-qtwidgets-not-qml.md) —
  pyobs-gui stays on QtWidgets, not QML. *accepted* (Repos: pyobs-gui)
- [0011-keycloak-identity-broker-for-shared-auth.md](0011-keycloak-identity-broker-for-shared-auth.md) —
  self-hosted Keycloak alongside odin as two parallel auth backends. *superseded 2026-08-19* — the
  design/plan went the other way: observation-portal is brokered *through* Keycloak and archive's
  direct OAuth2 integration was removed (`specs/design/shared-auth-keycloak.md`) (Repos:
  pyobs-core, pyobs-archive, pyobs-portal)
- [0012-event-delivery-explicit-pubsub-subscription-not-presence.md](0012-event-delivery-explicit-pubsub-subscription-not-presence.md) —
  event delivery moves from PEP presence auto-subscribe to explicit pubsub subscription.
  *accepted*
- [0013-renaming-pyobs-robotic-backend.md](0013-renaming-pyobs-robotic-backend.md) —
  rename `pyobs-robotic-backend` to `pyobs-portal` (package/image/Keycloak client in
  lockstep; in pyobs-core, `storage.backend`/`Backend*Archive` → `storage.portal`/
  `Portal*Archive`). *accepted*, execution tracked in
  `specs/plans/2026-08-24-rename-robotic-backend-to-portal.md` (Repos:
  pyobs-portal, pyobs-auth, pyobs-archive, pyobs-web-admin)
