# Plan: `pyobs-auth` + Keycloak integration

See `specs/design/shared-auth-keycloak.md` for the reasoning behind this plan. Tracks #748.
Repos: pyobs-archive, pyobs-robotic-backend.

## 1. `pyobs-auth` package (new repo)

- [ ] Scaffold repo (matches other pyobs packages — `do-python-release` conventions).
- [ ] OIDC discovery + token handling against Keycloak (authorization-code grant for user login,
      client-credentials grant for service-to-service).
- [ ] Bearer-token validation: signature/issuer/audience checks against Keycloak's JWKS endpoint
      (no round-trip to a profile endpoint per request, unlike odin's `BearerAuthentication`
      today — confirm this is an intended improvement, not an oversight, before implementing).
- [ ] DRF `authentication.BaseAuthentication` implementation, shaped like archive's existing
      `BearerAuthentication` (`pyobs_archive/authentication/backends.py`) so it drops into
      `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` the same way.
- [ ] Config surface: realm URL, client ID/secret, per-service — needs the realm/client layout
      open question resolved first (see design doc).

## 2. pyobs-archive

- [ ] Add `pyobs-auth` dependency.
- [ ] New `KeycloakBackend`/`KeycloakBearerAuthentication`, parallel to existing
      `OAuth2Backend`/`BearerAuthentication` in `pyobs_archive/authentication/backends.py` — do
      not modify the odin classes.
- [ ] `AUTH_PROVIDER` setting (`"odin" | "keycloak"`) in `pyobs_archive/settings.py`, gating which
      backend/authentication class is registered — replaces the current always-both wiring at
      `settings.py:189-194` with a conditional.
- [ ] User mapping: decide whether Keycloak-authenticated users mint a local `User` + `Profile`
      the same way odin's flow does (`backends.py` `get_or_create` + `Profile.update_or_create`),
      or need a different model — open question in design doc, resolve before writing this.
- [ ] Env vars for Keycloak client config, alongside existing `OAUTH_CLIENT` block
      (`settings.py:197-202`).

## 3. pyobs-robotic-backend

- [ ] Add `pyobs-auth` dependency.
- [ ] Add Keycloak authentication class to `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`
      (`pyobs_robotic_backend/settings.py:148-155`), alongside the existing
      `TokenAuthentication`/`SessionAuthentication` — additive, not a replacement (existing
      pyobs-core → robotic-backend token calls must keep working, see design doc).
- [ ] User mapping: robotic-backend has no `Profile`-equivalent model today — decide whether it
      needs one or whether Keycloak's `User` mint-on-login is enough on its own.

## 4. Not in this plan

- Migrating pyobs-core's `taskarchive.py`/`observationarchive.py` off static `Token` auth to
  Keycloak client-credentials — explicitly optional per the design doc, do separately if/when
  wanted.
- Retiring odin — out of scope, no timeline given.
