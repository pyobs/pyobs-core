# Shared authentication across pyobs web projects via Keycloak

Status: proposed
Repos: pyobs-archive, pyobs-robotic-backend

## Problem

Tracks #748. Each pyobs web service currently rolls its own auth, uncoordinated:

- **pyobs-archive** (`pyobs_archive/authentication/backends.py`) delegates to our own
  `observation-portal` deployment (a self-hosted instance of the open-source OCS
  `observatorycontrolsystem/observation-portal` project — `django-oauth-toolkit`-based; previously
  referred to as "odin" in this doc and in archive's own code comments, an informal label with no
  meaning outside archive, and previously miscast as an external "LCO" dependency when it's
  actually ours to configure): `OAuth2Backend` does a password-grant token exchange against
  `settings.OAUTH_CLIENT['TOKEN_URL']`, and `BearerAuthentication` validates bearer tokens against
  a `PROFILE_URL`. Successful auth mints/updates a local Django `User` + `Profile` (storing the
  observation-portal access/refresh token — written but never read elsewhere in archive, confirmed
  by grep; no downstream code depends on archive holding a live observation-portal token).
- **pyobs-robotic-backend** (`settings.py` `DEFAULT_AUTHENTICATION_CLASSES`) uses plain DRF
  `TokenAuthentication` + `SessionAuthentication` against its own local Django user database — no
  connection to observation-portal or to archive's users at all.

No shared identity: a user (or a service) authenticated against one pyobs web project has no way
to be recognized by another. This will only get worse as more web services join the ecosystem.

A Keycloak server has since been set up as the shared identity provider, and — since we control our
own observation-portal deployment's config — the design below routes it *through* Keycloak rather
than treating it as a second, permanently-separate integration.

## Scope

Two separable problems, both in scope, with different trust models:

1. **User-facing SSO** — one login across archive/robotic-backend/future dashboards, via Keycloak
   as the sole OIDC provider.
2. **Service-to-service auth** — e.g. Mastermind calling robotic-backend's API, pyobs-core modules
   calling other services' APIs. Optional: what's already in use here (DRF `TokenAuthentication`,
   a static per-module token — this is what's referred to as "PSK" in this doc, not a real
   HMAC/PSK scheme) stays available as an alternative to OIDC client-credentials, not replaced by
   it. Concretely: `pyobs/robotic/storage/backend/taskarchive.py` and `observationarchive.py`
   (pyobs-core) send `Authorization: Token <token>` against robotic-backend today — that path is
   unaffected by this work.

## Decision: Keycloak as the single issuer; observation-portal becomes a brokered upstream, not a second integration

Route observation-portal logins *through* Keycloak instead of maintaining `pyobs-auth`/archive
code that talks to observation-portal directly:

- Enable OIDC on our observation-portal deployment (`OAUTH2_PROVIDER` settings:
  `"OIDC_ENABLED": True`, `"OIDC_RSA_PRIVATE_KEY": <PEM>`, `"openid"` added to `SCOPES`; existing
  `Application` objects need `algorithm` set to `RS256`). This exposes
  `authorization_endpoint`/`token_endpoint`/`userinfo_endpoint` (`/o/userinfo/`) and a discovery
  document at `/o/.well-known/openid-configuration/` — already routed today via the existing
  `re_path(r'^o/', include('oauth2_provider.urls'))` in `urls.py`, so no new URL wiring needed.
- Register observation-portal in Keycloak as an Identity Provider (Keycloak's generic "OpenID
  Connect v1.0" IdP type, auto-configured from that discovery document). A user picks "log in with
  observation-portal" on Keycloak's login screen; Keycloak does the federation handshake and mints
  its own Keycloak token.
- **`pyobs-auth` and every service (archive, robotic-backend, future services) only ever talk to
  Keycloak.** There is exactly one issuer, one JWKS endpoint, one client library code path — no
  multi-issuer validation logic, no `AUTH_PROVIDER` switch, no bespoke `OAuth2Backend`/
  `BearerAuthentication` kept alive as permanent second code. Full cutover, not a dual-path state:
  those two classes get removed from archive once the migration lands (see plan for sequencing —
  existing sessions/local `User` records need a path forward, not a hard cutover on day one).
- **This makes observation-portal purely a Keycloak admin-console configuration concern**, not
  pyobs application code. Whether/how observation-portal is wired up as a broker is the same kind
  of decision as any other upstream IdP Keycloak brokers to (see below) — nothing pyobs-side
  changes based on it.
- Account linking on first broker login (matching a federated observation-portal identity to a
  Keycloak user, e.g. by email or a mapper) is Keycloak config, not code — but a real setting to
  get right, since misconfigured linking can mint duplicate Keycloak users per observation-portal
  login instead of reusing one.
- Along the way: archive's login should move off password-grant (ROPC — `OAuth2Backend`'s current
  `grant_type: password` exchange) to authorization-code + PKCE, since OAuth 2.1 drops ROPC and it
  requires the client app to handle the user's raw password directly. `pyobs-auth`'s OIDC client
  logic (below) already does auth-code, so this falls out of the cutover rather than being separate
  work.
- **pyobs-robotic-backend** currently has no OAuth2 path at all — just DRF `TokenAuthentication`
  + `SessionAuthentication` (`pyobs_robotic_backend/settings.py:148-155`). It goes straight to
  Keycloak, same as every other service — nothing special about it relative to archive post-cutover.
- **Service-to-service auth remains optional and the existing token mechanism stays supported.**
  Keycloak's client-credentials grant is available for services that want OIDC-based service
  auth, but existing token-secured calls (pyobs-core modules → robotic-backend, via
  `Authorization: Token <token>`) don't have to migrate as a precondition of this work.

## Proposed change: `pyobs-auth` package

A new shared package, `pyobs-auth`, holds the Keycloak OIDC client logic once, rather than
duplicating it into archive and robotic-backend separately (which is the situation being fixed).
Released the normal way, like other pyobs repos (`do-python-release`, uv/poetry, GitHub tags) —
nothing unusual about its release process.

Scope of the package (to be refined during implementation):

- OIDC discovery + token exchange (authorization-code grant for user login, client-credentials
  grant for service-to-service).
- Bearer-token validation (signature/issuer/audience checks against Keycloak's JWKS endpoint).
- A DRF `authentication.BaseAuthentication` implementation, so archive/robotic-backend wire it in
  consistently. Single-issuer only — no need to design for multiple trusted issuers, since
  observation-portal (and any other upstream) is brokered behind Keycloak, not validated directly.

## Decision: realm layout and user mapping

- **One shared realm** for the whole pyobs ecosystem, with one Keycloak client registered per
  service (archive, robotic-backend, future services), rather than per-service realms. A user
  authenticated in the realm is inherently known to every service's client — no cross-realm
  federation needed to get the shared-identity property this work is for.
- **Keycloak's `sub` claim (stable subject/user ID) is the join key** to each service's local
  Django `User`, not username or email. Both archive and robotic-backend store the Keycloak `sub`
  against their local `User` (archive: presumably on `Profile`, or its Keycloak equivalent;
  robotic-backend needs an equivalent field added, since it has no `Profile`-like model today).
  Chosen over matching on username/email because those can change (rename, email update) without
  the underlying identity changing — matching on them would silently orphan or misjoin a user
  after such a change. This also applies to brokered logins (observation-portal or any other
  upstream): a brokered user's Keycloak-issued `sub` is still what's stored, not whatever
  identifier the upstream provider uses internally.

## Non-issue: upstream OIDC brokering (including observation-portal)

Keycloak can broker identity to any number of upstream OpenID providers (users federated in, not
just managed locally) — observation-portal is one instance of this, and a possible future
institute-wide provider would be another. Which upstreams exist, and how they're wired up, is
Keycloak admin-console configuration, an operational decision, not a pyobs design question. Each
operator running their own Keycloak instance configures (or skips) their own upstream IdPs as they
see fit; `pyobs-auth` only ever talks to a service's own Keycloak endpoints, so it's invisible to
the pyobs side regardless of what's brokered behind it. `sub`-based joining (above) already means
brokered vs. locally-managed users don't need different handling on the pyobs side either. No open
question remains here.

## Note: observation-portal's own token validation shortcut (context, not adopted)

Archive's current `BearerAuthentication` validates tokens by calling `PROFILE_URL`
(`observation-portal`'s `ProfileApiView`, an ordinary app endpoint, not a dedicated auth check) —
a side-effect way to check token validity, rather than `django-oauth-toolkit`'s actual RFC 7662
introspection endpoint (`/o/introspect/`), which observation-portal already exposes. This was an
implementation shortcut, not a deliberate revocation-related design choice. Moot once the cutover
above lands and this class is removed — noted here only as the reasoning trail for why JWKS-based
validation in `pyobs-auth` isn't a regression.
