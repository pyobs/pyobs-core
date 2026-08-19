# Plan: `pyobs-auth` + Keycloak integration

See `specs/design/shared-auth-keycloak.md` for the reasoning behind this plan. Tracks #748.
Repos: pyobs-archive, pyobs-robotic-backend.

Status: implemented, closed 2026-08-19. Sections 1-3 complete — `pyobs-auth` and both service
cutovers are implemented and released (`pyobs-auth` `2.0.0.dev7`, `pyobs-archive` `2.0.0.dev8`,
`pyobs-robotic-backend` released with the dependency). Live verification done 2026-08-19: browser
Keycloak login and logout confirmed working end to end against the running Keycloak (PKCE redirect
→ callback → token validation → user mapping → session, and logout ending the SSO session). Section
0 remains open but is Keycloak admin/deployment config, not pyobs code — tracked separately (see
#748), not part of this plan's closure.

Keycloak is the single issuer for all services; observation-portal is brokered behind it (Keycloak
admin config, not pyobs code) rather than integrated as a second, separately-validated provider.

## 0. observation-portal (Keycloak admin config + small observation-portal config change)

The plan's only remaining open section as of 2026-08-19 — the Keycloak server, realm, and
per-service clients are set up, but observation-portal is not yet brokered behind Keycloak. All
three items below are Keycloak admin/deployment config, not pyobs code; tracked separately from
this plan (see #748).

- [ ] Enable OIDC on our observation-portal deployment: `OAUTH2_PROVIDER` settings
      `"OIDC_ENABLED": True`, `"OIDC_RSA_PRIVATE_KEY": <PEM>`, add `"openid"` to `SCOPES`; set
      existing `Application` objects' `algorithm` to `RS256`. No new URL wiring needed —
      `/o/.well-known/openid-configuration/`, `/o/userinfo/`, JWKS are already routed via the
      existing `re_path(r'^o/', include('oauth2_provider.urls'))`.
- [ ] Register observation-portal as a Keycloak Identity Provider (generic "OpenID Connect v1.0"
      type, auto-configured from the discovery document above).
- [ ] Configure account-linking behavior for first broker login (match by email or a mapper) so a
      given observation-portal user doesn't mint a duplicate Keycloak user on login.

## 1. `pyobs-auth` package (new repo) — done, released

Implemented and released: [github.com/pyobs/pyobs-auth](https://github.com/pyobs/pyobs-auth)
(public), `2.0.0.dev7` on PyPI (dev6 added the inactive-user gate, dev7 a styled error page).

- [x] Scaffold repo (matches other pyobs packages — `do-python-release` conventions).
- [x] OIDC discovery + token handling against Keycloak — authorization-code grant (+ PKCE) for
      user login, client-credentials grant for service-to-service. Single issuer only (Keycloak);
      no multi-issuer logic needed since observation-portal is brokered behind it, not validated
      directly. (`pyobs_auth.client.KeycloakClient`, `pyobs_auth.discovery`)
- [x] Bearer-token validation: signature/issuer/audience checks against Keycloak's JWKS endpoint —
      stateless, no per-request round-trip (unlike observation-portal's current
      `BearerAuthentication`, which piggybacks on `PROFILE_URL`/`ProfileApiView` for validation
      instead of the real RFC 7662 introspection endpoint `/o/introspect/`; confirmed an
      implementation shortcut, not a deliberate revocation trade-off, moot once the classes below
      are retired). (`pyobs_auth.validation.TokenValidator`)
- [x] DRF `authentication.BaseAuthentication` implementation (`pyobs_auth.authentication.
      KeycloakAuthentication`) that archive/robotic-backend both wire into
      `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`. Also shipped: `pyobs_auth.views`/`urls`
      for the browser-facing PKCE login-redirect + callback flow (not originally itemized here,
      needed to actually complete user-facing SSO end to end) plus a `LogoutView` doing
      RP-Initiated Logout — ends the Keycloak SSO session too, but only for sessions that actually
      came from Keycloak (checked via whether an `id_token` was stored at login), so a plain local
      password session still just gets an ordinary local logout through the same URL.
- [x] Stacking-safety fix: `KeycloakAuthentication` defers (returns `None`) instead of raising for
      a Bearer token whose issuer doesn't match ours, rather than blocking a second, unmodifiable
      Bearer-scheme authenticator from getting a turn (DRF stops the whole authenticator chain on
      a raise, not on `None`). Not load-bearing for archive's full cutover (no second Bearer
      authenticator there once `BearerAuthentication` is removed), but a real correctness fix kept
      for future stacking scenarios.
- [x] Config surface: one shared realm URL (same across services), per-service client ID/secret
      (one Keycloak client per service, within that shared realm — see design doc). Implemented as
      a single `PYOBS_AUTH` Django setting dict (`SERVER_URL`, `REALM`, `CLIENT_ID`,
      `CLIENT_SECRET`, `REDIRECT_URI`, ...).
- [x] User-mapping helper: resolve a validated token's `sub` claim to a local Django `User`.
      Shape differs slightly from what this line originally said — rather than one shared
      `sub`-lookup function baked into `pyobs-auth` itself, it's a pluggable `USER_RESOLVER`
      setting (dotted path to a `callable(claims) -> User | None`), since archive and
      robotic-backend have different local `User`/`Profile` schemas and pyobs-auth can't assume
      one. Each service still keys its own resolver on `claims["sub"]`, per the design doc.

## 2. pyobs-archive — cutover, not dual-path — landed

Landed 2026-08-18/19 and released as `v2.0.0.dev8` (commits `01eb06e` "Add Keycloak
login/logout via pyobs-auth, remove LCO OAuth2 integration", `3e5bd3f` resolve_user fixes,
`1a117df` settings-configured admin account + error-page bump, `2cbda4b` v2.0.0.dev8). Every item
below re-verified against the repo 2026-08-19: `backends.py`/`OAuth2Backend`/`BearerAuthentication`
and the `OAUTH_CLIENT` setting are gone (no references remain), `pyobs-auth>=2.0.0.dev7` is a
dependency, `Profile.keycloak_sub` (migration 0006) and `resolve_user` are in place with tests.

- [x] Add `pyobs-auth` dependency; wire `KeycloakAuthentication` into
      `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`. No `AUTHENTICATION_BACKENDS` entry for
      Keycloak — the redirect-based OIDC flow doesn't fit that shape (see design doc/pyobs-auth's
      own notes), it's handled by `pyobs_auth.views` instead. `ModelBackend` (local Django
      username/password) stays the sole `AUTHENTICATION_BACKENDS` entry and the default login on
      the login page — Keycloak is an additive option next to it, not a replacement.
- [x] User mapping: `pyobs_archive.authentication.keycloak.resolve_user`, mint-on-first-login,
      keyed on `Profile.keycloak_sub` (new field + migration), not username/email.
- [x] Migration path for existing users: `resolve_user` links an existing `User` by email on
      first Keycloak login rather than minting a duplicate — see design doc's realm/user-mapping
      decision. `Profile.access_token`/`refresh_token` columns (written by the old flow) left in
      place rather than dropped — dead but low-risk to leave vs. a destructive migration.
- [x] Remove `OAuth2Backend`/`BearerAuthentication` (`pyobs_archive/authentication/backends.py`)
      and the `OAUTH_CLIENT` setting — full cutover, no permanent second code path. Real trade-off:
      until observation-portal is actually brokered behind Keycloak, users whose only credential
      was an LCO/observation-portal account have no way in until they're otherwise provisioned in
      Keycloak.
- [x] Env vars for Keycloak client config (`KEYCLOAK_SERVER_URL`, `_REALM`, `_CLIENT_ID`,
      `_CLIENT_SECRET`, `_REDIRECT_URI`, `_POST_LOGOUT_REDIRECT_URI`), documented in `README.md`/
      `.env.example`. Leaving `KEYCLOAK_SERVER_URL` unset disables Keycloak entirely — the login
      page's "Log in with Keycloak" button only renders when it's actually configured (new
      `pyobs_archive.context_processors.keycloak`).
- [x] Login template's "Log out" posts to `pyobs_auth:logout` instead of Django's built-in logout
      view, so it does the right thing (local-only vs. also ending the Keycloak SSO session)
      regardless of how the session was established.

## 3. pyobs-robotic-backend — done

- [x] Added `pyobs-auth` dependency (now pinned `>=2.0.0.dev7`). Blocked initially: pyobs-auth
      pinned `Django>=5.2,<6` on PyPI, conflicting with robotic-backend's `django>=6.0.7` — fixed
      by widening the pin to `<7` in pyobs-auth (full 36-test suite re-verified green against
      Django 6.1) and releasing `2.0.0.dev5`.
- [x] Added `pyobs_auth.authentication.KeycloakAuthentication` to
      `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` (`pyobs_robotic_backend/settings.py`),
      alongside the existing `TokenAuthentication`/`SessionAuthentication` — additive, existing
      pyobs-core → robotic-backend token calls unaffected. `pyobs_auth` added to `INSTALLED_APPS`;
      `PYOBS_AUTH` setting (`KEYCLOAK_SERVER_URL`/`_REALM`/`_CLIENT_ID`/`_CLIENT_SECRET` env vars,
      unset disables it) documented in README.md/.env.example. Browser SSO login was subsequently
      added too (this started as API Bearer-token auth only): `pyobs_auth.urls` is included under
      `accounts/keycloak/` and the login template renders a "Log in with Keycloak" button behind a
      `keycloak_login_enabled` context processor.
- [x] User mapping: new `pyobs_robotic_backend.authentication` app (robotic-backend had no
      `Profile`-equivalent) with a `KeycloakIdentity` model (`OneToOneField` to `User` +
      `keycloak_sub`, migration `0001_initial`) and a `resolve_user` `USER_RESOLVER`, mirroring
      archive's planned `resolve_user` shape — matches an existing `User` by email (falling back
      to username) on first Keycloak login, else mints one inactive (`is_active=False`, so a fresh
      Keycloak login needs local activation before it can act).

## 4. Not in this plan

- Migrating pyobs-core's `taskarchive.py`/`observationarchive.py` off static `Token` auth to
  Keycloak client-credentials — explicitly optional per the design doc, do separately if/when
  wanted.
- Configuring any upstream IdP behind Keycloak beyond observation-portal (e.g. a future
  institute-wide provider) — Keycloak admin config, independent of this plan, do whenever that
  provider is confirmed.
