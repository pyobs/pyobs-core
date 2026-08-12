# Shared authentication across pyobs web projects via Keycloak

Status: proposed
Repos: pyobs-archive, pyobs-robotic-backend

## Problem

Tracks #748. Each pyobs web service currently rolls its own auth, uncoordinated:

- **pyobs-archive** (`pyobs_archive/authentication/backends.py`) delegates to an external OAuth2
  provider ("odin"): `OAuth2Backend` does a password-grant token exchange against
  `settings.OAUTH_CLIENT['TOKEN_URL']`, and `BearerAuthentication` validates bearer tokens against
  a `PROFILE_URL`. Successful auth mints/updates a local Django `User` + `Profile` (storing the
  odin access/refresh token).
- **pyobs-robotic-backend** (`settings.py` `DEFAULT_AUTHENTICATION_CLASSES`) uses plain DRF
  `TokenAuthentication` + `SessionAuthentication` against its own local Django user database — no
  connection to odin or to archive's users at all.

No shared identity: a user (or a service) authenticated against one pyobs web project has no way
to be recognized by another. This will only get worse as more web services join the ecosystem.

A Keycloak server has since been set up as the intended shared identity provider (resolves the
"does odin still exist / is it still the intended provider" open question from #748: it's neither
retired nor sole source of truth — see below).

## Scope

Two separable problems, both in scope, with different trust models:

1. **User-facing SSO** — one login across archive/robotic-backend/future dashboards, via Keycloak
   as an OIDC provider.
2. **Service-to-service auth** — e.g. Mastermind calling robotic-backend's API, pyobs-core modules
   calling other services' APIs. Optional: what's already in use here (DRF `TokenAuthentication`,
   a static per-module token — this is what's referred to as "PSK" in this doc, not a real
   HMAC/PSK scheme) stays available as an alternative to OIDC client-credentials, not replaced by
   it. Concretely: `pyobs/robotic/storage/backend/taskarchive.py` and `observationarchive.py`
   (pyobs-core) send `Authorization: Token <token>` against robotic-backend today — that path is
   unaffected by this work.

## Decision: Keycloak alongside odin, not a replacement

- **pyobs-archive** keeps `OAuth2Backend`/odin working
  (`pyobs_archive/authentication/backends.py`, wired in via `REST_FRAMEWORK` +
  `OAUTH_CLIENT` in `pyobs_archive/settings.py:189-202`). Keycloak is added as a second backend;
  a Django setting selects which is active (per-deployment, not per-request) — e.g.
  `AUTH_PROVIDER = "odin" | "keycloak"`. This is a deliberate two-provider state, not a
  migration-in-progress shim: odin isn't being retired by this change.
- **pyobs-robotic-backend** currently has no OAuth2 path at all — just DRF `TokenAuthentication`
  + `SessionAuthentication` (`pyobs_robotic_backend/settings.py:148-155`). It and all other/future
  services go straight to Keycloak — no odin integration is added there.
- **Service-to-service auth remains optional and the existing token mechanism stays supported.**
  Keycloak's client-credentials grant is available for services that want OIDC-based service
  auth, but existing token-secured calls (pyobs-core modules → robotic-backend, via
  `Authorization: Token <token>`) don't have to migrate as a precondition of this work.

## Proposed change: `pyobs-auth` package

A new shared package, `pyobs-auth`, holds the Keycloak OIDC client logic once, rather than
duplicating it into archive and robotic-backend separately (which is the situation being fixed).

Scope of the package (to be refined during implementation):

- OIDC discovery + token exchange (authorization-code grant for user login, client-credentials
  grant for service-to-service).
- Bearer-token validation (signature/issuer/audience checks against Keycloak's JWKS endpoint).
- A DRF `authentication.BaseAuthentication` implementation, so archive/robotic-backend wire it in
  the same way `BearerAuthentication` works today in archive.
- Deliberately *not* in scope: the `AUTH_PROVIDER` odin/keycloak switch itself — that's
  archive-local settings logic, not shared client code.

## Open questions (need to be resolved before/while implementing)

- Keycloak realm/client layout: one realm for the whole pyobs ecosystem vs. per-service clients
  within one realm? Affects how `pyobs-auth` is configured per service.
- Does a Keycloak-authenticated user get mapped to each service's local Django `User` model the
  same way odin's does today in archive (mint-on-first-login + `Profile`), or does robotic-backend
  need a different mapping since it has no odin-derived `Profile` concept yet?
- Keycloak will also broker identity to an upstream OpenID provider (users not just managed
  locally in Keycloak, but federated in) — still waiting on confirmation of that upstream server.
  Brokering itself is Keycloak-internal and transparent to `pyobs-auth` (it only ever talks to
  Keycloak's own OIDC endpoints), so it doesn't change the design above. But brokered users can
  carry different token claims than locally-managed ones (email-verified flag, username format,
  federated identity link) — confirm attribute mapping is consistent between the two before
  writing the local-`User` mapping logic above, so it doesn't silently branch on auth source.
- Where does `pyobs-auth` fit release/versioning-wise — is it a normal `do-python-release` package
  like other pyobs repos?
