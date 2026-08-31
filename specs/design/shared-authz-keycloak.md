# Centralized authorization across pyobs web projects via Keycloak groups/roles

Status: implemented — shipped and released (`v2.1.0`) across all four repos, live-verified
2026-08-31. Decision recorded in ADR `0014-centralized-authorization-via-keycloak-groups.md`;
checklist in `specs/plans/2026-08-28-shared-authz-keycloak.md` (issue #823, closed).
Repos: pyobs-auth, pyobs-archive, pyobs-portal, pyobs-web-admin

## Problem

`specs/design/shared-auth-keycloak.md` centralized *authentication*: one Keycloak realm, one
client per service, `pyobs-auth` validating tokens against the realm's JWKS, and each service
mapping the stable `sub` claim to a local Django `User`. *Authorization*, however, is still
per-service and manual:

- Every service's `USER_RESOLVER` (archive `Profile.keycloak_sub`, portal `KeycloakIdentity`,
  web-admin `KeycloakIdentity`) mints a local `User` on **first login** with `is_active=False`.
- `pyobs_auth.authentication.KeycloakAuthentication` and `pyobs_auth.views.CallbackView` refuse
  `is_active=False` users ("Account pending activation").

So a new user must log in to every service once (minting a local account per service) and then be
activated in each service's Django admin / `manage.py` separately. Nothing can be granted before
the first login, and revocation is N service-admin actions instead of one. As more services join
the ecosystem this multiplies.

## Scope

Centralize the *user-facing authorization decision* — "may this person use service X, and with
which role" — in Keycloak, replacing the per-service local activation gate:

1. Service-level access (who may use archive / portal / web-admin at all).
2. Fine-grained roles where a service already distinguishes privilege levels (portal's
   `is_superuser`-gated admin UI/API, archive's staff/superuser permission classes).

Out of scope: service-to-service authorization (client-credentials tokens; the existing static
`Authorization: Token` calls stay as-is — the same carve-out as the shared-auth design doc), and
Keycloak Authorization Services (UMA/entitlements), a resource-server model this fleet doesn't
need.

## Decision: Keycloak groups/roles are the authorization source of truth, delivered as token claims

Keycloak becomes the single place where access is granted and revoked. Services stop gating on a
locally-administered `is_active` flag and instead gate on the Keycloak group/role membership
carried in the (already validated) access token. Because the decision is claim-based, it is made
**before the user's first login**: an admin assigns the group in the Keycloak admin console (or
via the admin REST API / self-registration default groups), and the user's first login to any
service is immediately authorized — no local record needs to exist or be touched beforehand.

### Realm layout

- One realm group per service: `pyobs-archive`, `pyobs-portal`, `pyobs-web-admin` (a future
  service adds its own group). Membership in a service's group authorizes that service.
- Client roles for fine-grained permissions, only where a service has them today: e.g.
  `portal-admin` on the `portal` client (feeds portal's existing `is_superuser` checks), an
  analogous `archive-admin` if archive wants to keep its staff/superuser split. Realm roles are
  available too; groups + client roles cover both access and privilege without realm-role
  proliferation.
- Group/role changes in Keycloak apply to *all* services at once — one admin action per person,
  not N.

### Token claims

Three protocol-mapper outputs carry the decision to the services (all Keycloak admin config, no
pyobs code):

- `groups` — group membership, via the built-in "Group Membership" mapper. Full group paths
  (`/pyobs-archive`) keep names unambiguous.
- `realm_access.roles` — realm roles (Keycloak default).
- `resource_access.<client>.roles` — client roles (Keycloak default unless token audiences are
  restricted).

Services validate the token with the existing JWKS path and read these claims; no new network
dependency, no per-request round trip.

### pyobs-auth changes

- New optional `PYOBS_AUTH` settings: `REQUIRED_GROUPS` (group paths, e.g.
  `["/pyobs-archive"]`) and `REQUIRED_ROLES` (e.g. `["client:portal:portal-admin"]`). Unset ⇒ no
  gate, current behavior unchanged.
- A shared authorization check (`pyobs_auth.authorization`) that, given validated claims,
  decides pass/refuse; both `KeycloakAuthentication` (API bearer path) and `CallbackView`
  (browser path) call it where the `is_active` check lives today. A failed check surfaces as the
  same style of refusal ("not authorized") on both paths.
- The local `is_active` check remains only behind an opt-in `ENFORCE_LOCAL_ACTIVE` (default
  False), preserving the shared-auth design doc's "Keycloak-independent kill switch" property for
  deployments that want it — while the default moves the whole decision to Keycloak.
- Session refresh: `CallbackView` currently discards the `refresh_token` from the token response
  (only `access_token` and `id_token` are kept). It must instead store `refresh_token` alongside
  `id_token`, and new middleware must call `KeycloakClient.refresh()` once the access token's
  `exp` has passed, re-validate the resulting claims, and re-run the authorization gate —
  ending the session if it now fails. Without this, a browser session never re-contacts Keycloak
  after login, and revocation is bounded only by `SESSION_COOKIE_AGE` (whatever each service has
  it set to), not by any token lifetime. See "Revocation model and freshness" below.

### Per-service changes

- Each service's resolver stops minting `is_active=False` as part of its cutover (the claims
  gate replaces the local activation gate); the local `User` remains the per-service data record
  (FKs, profiles, tasks) but is no longer the authorization gate.
- Claim → local permission sync where a service has local privilege flags: portal syncs
  `is_superuser` from the `portal-admin` client role (archive from its analogue) each time a user
  is resolved, so the existing `IsAdminUser`/`is_superuser`-gated endpoints keep working without
  rewriting them. This sync must set `is_superuser` only, **not** `is_staff` — `is_staff` is the
  separate flag that unlocks the raw, unscoped Django admin backend (`/admin/`, every registered
  model, no scoping), a bigger grant than portal's own business-logic superuser checks.
  `admin_sync.py`'s `ADMIN_USERNAME` account sets both together deliberately (it's a local
  password account meant to be a full admin, not a Keycloak user); the Keycloak-derived sync must
  not copy that pattern. The `ADMIN_USERNAME` account itself is untouched by this change.
- Locally-created users are unaffected: `createsuperuser` / Django-admin accounts authenticate
  via Django's `ModelBackend` with local passwords and never pass through the claims gate (the
  gate lives only in `KeycloakAuthentication` and `CallbackView`). The user-facing SSO login stays
  Keycloak-only, so a local-only user's reach is Django admin / session-based access.
- Web-admin: gate on its group like any other service; its Django admin stops being the
  activation UI (there is nothing to activate anymore). The Keycloak admin console becomes the
  people-management surface.

## Revocation model and freshness

JWKS validation is stateless: claims are only as fresh as the token/session that carried them. A
plain Django session, once established, has no further contact with Keycloak until logout or the
session cookie expires — "next login" is not by itself a meaningful bound, since a session can
live for a full `SESSION_COOKIE_AGE` (whatever each service has that set to) with zero
re-validation in between. pyobs-auth must actively re-check, not just check once at login:

- **Browser sessions**: `CallbackView` stores the refresh token (alongside the existing
  `id_token`) and new middleware silently refreshes the access token via
  `KeycloakClient.refresh()` once it expires, re-validates the resulting claims, and re-runs the
  authorization gate — ending the session if it now fails. This bounds revocation to one
  access-token lifetime plus the refresh-check interval, not one `SESSION_COOKIE_AGE`. Synced
  local flags like `is_superuser` are re-derived on the same refresh cycle.
- **API bearer tokens**: changes take effect at the next token issuance; short access-token
  lifetimes make this minutes, not days.

Accepted for this fleet: revocation within one access-token lifetime is fine at institute scale,
and it buys statelessness plus no new runtime dependency (the refresh call happens lazily, off
the request hot path, not once per request). If hard revocation is ever needed for a specific
endpoint, a per-request group check against the Keycloak Admin REST API
(`GET /admin/realms/{realm}/users/{id}/groups`) is a documented, service-local option —
explicitly not adopted now.

## Migration

- Keycloak admin: create the groups and mappers; assign groups to existing users (bulk in the
  admin console or via the admin REST API).
- Each service cutover flips existing local `is_active` to True (one-off
  `update(is_active=True)`); revocations now happen in Keycloak, so this is safe. The
  `ENFORCE_LOCAL_ACTIVE` opt-in remains for anyone who wants a local kill switch anyway.
- Existing local superuser flags re-derive from roles at the user's next resolve.

## Non-goals (recorded so they don't resurface as "missing")

- Service-to-service authorization via client-credentials tokens — separate concern, unchanged
  from the shared-auth design doc.
- Keycloak Authorization Services (UMA) — heavier resource-server model, not needed.
- Per-request revocation checks — documented option only.
