# Plan: `pyobs-auth` + Keycloak integration

See `specs/design/shared-auth-keycloak.md` for the reasoning behind this plan. Tracks #748.
Repos: pyobs-archive, pyobs-robotic-backend.

Keycloak is the single issuer for all services; observation-portal is brokered behind it (Keycloak
admin config, not pyobs code) rather than integrated as a second, separately-validated provider.

## 0. observation-portal (Keycloak admin config + small observation-portal config change)

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
(private), `2.0.0.dev1` on PyPI.

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
      needed to actually complete user-facing SSO end to end).
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

## 2. pyobs-archive — cutover, not dual-path

- [ ] Add `pyobs-auth` dependency; wire `KeycloakAuthentication` into
      `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` (`settings.py:189-194`) and Keycloak into
      `AUTHENTICATION_BACKENDS` for the login flow.
- [ ] User mapping: mint-on-first-login `User` similar to the current flow's
      `get_or_create` (`backends.py`), but keyed on Keycloak's `sub` claim (new field), not
      username/email — see design doc's realm/user-mapping decision.
- [ ] Migration path for existing users: existing local `User`/`Profile` rows (from
      password-grant observation-portal logins) need to end up linked to the right Keycloak `sub`
      once a user first logs in via Keycloak/broker — decide the linking rule (match existing
      `User` by email on first Keycloak login, vs. requiring a fresh account). Not a hard cutover
      with no path for existing accounts.
- [ ] Once the above is live and working: remove `OAuth2Backend`/`BearerAuthentication`
      (`pyobs_archive/authentication/backends.py`) and the `OAUTH_CLIENT` setting
      (`settings.py:197-202`) — full cutover, no permanent second code path.
- [ ] Env vars for Keycloak client config.

## 3. pyobs-robotic-backend

- [ ] Add `pyobs-auth` dependency.
- [ ] Add `KeycloakAuthentication` to `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`
      (`pyobs_robotic_backend/settings.py:148-155`), alongside the existing
      `TokenAuthentication`/`SessionAuthentication` — additive, not a replacement (existing
      pyobs-core → robotic-backend token calls must keep working, see design doc).
- [ ] User mapping: robotic-backend has no `Profile`-equivalent model today — needs a new field/
      model to store the Keycloak `sub` against its local `User`, mirroring archive's approach
      (see design doc).

## 4. Not in this plan

- Migrating pyobs-core's `taskarchive.py`/`observationarchive.py` off static `Token` auth to
  Keycloak client-credentials — explicitly optional per the design doc, do separately if/when
  wanted.
- Configuring any upstream IdP behind Keycloak beyond observation-portal (e.g. a future
  institute-wide provider) — Keycloak admin config, independent of this plan, do whenever that
  provider is confirmed.
