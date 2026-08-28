# Centralize authorization in Keycloak groups/roles instead of per-service local activation

status: accepted
date: 2026-08-28
Repos: pyobs-core (this doc), pyobs-auth, pyobs-archive, pyobs-portal, pyobs-web-admin

## Context and Problem Statement

Authentication is centralized (design: `specs/design/shared-auth-keycloak.md` — one Keycloak
realm, per-service clients, `pyobs-auth`), but authorization is not: every service mints a local
Django `User` on first Keycloak login with `is_active=False`, and `pyobs-auth` refuses inactive
users. Each new user therefore must log in to every service and be activated per service, and
nothing can be granted before the first login. Tracks #823. As more services join, N
service-admin activations per person become the bottleneck; the per-service activation overhead
is the reported pain.

## Considered Options

* **A. Status quo** — keep per-service local `is_active` as the gate (each service's Django
  admin / `manage.py`). Zero code change, but activation stays per-service and post-first-login;
  no way to grant access before first login; revocation is N actions.
* **B. Centralized check via the Keycloak Admin REST API per request** — services call
  `GET /admin/realms/{realm}/users/{id}/groups` (or token introspection) on every request. One
  source of truth and instant revocation, but every request depends on Keycloak being reachable
  and adds a network round trip; gives up the stateless JWKS property the shared-auth design
  deliberately chose, and couples each service's availability to Keycloak's.
* **C. Keycloak Authorization Services (UMA/entitlements)** — Keycloak's resource-based
  authorization server. Powerful for fine-grained per-resource policies, but a new subsystem with
  its own model, per-resource configuration, and client-side changes — disproportionate for a
  fleet whose main question is "may this person use service X, and is it admin?".
* **D. Groups/roles in the access token, checked statelessly** — Keycloak group/role membership
  mapped into token claims (`groups`, `realm_access`, `resource_access`); services gate on the
  claims they already validate via JWKS; an optional per-service local kill switch is preserved
  behind a flag. Centralized, works before first login, no new runtime dependency; trade-off:
  revocation takes effect at next login / next token, not instantly.

## Decision Outcome

Chosen option: **D** — Keycloak groups/roles are the authorization source of truth, delivered as
token claims and enforced in `pyobs-auth` (optional `REQUIRED_GROUPS`/`REQUIRED_ROLES` settings,
checked in `KeycloakAuthentication` and `CallbackView`). Services stop gating on local
`is_active` (resolvers mint active users; the local `User` stays as per-service data). An opt-in
`ENFORCE_LOCAL_ACTIVE` preserves a Keycloak-independent kill switch for deployments that want the
old property; the default is fully centralized. Local privilege flags (portal/archive
`is_superuser`) re-derive from client roles at resolve time, so existing permission-gated
endpoints keep working. Granting/revoking is one Keycloak admin action per person, effective
before the user's first login. Design: `specs/design/shared-authz-keycloak.md`.

### Consequences

* Good — access is granted/revoked in one central place, effective before first login; no
  per-service activation anywhere.
* Good — stays stateless: the JWKS-validated token already carries the claims; no new network
  dependency, no coupling of service availability to Keycloak at request time.
* Good — consistent for every service via one library change; future services get the same gate
  for free.
* Good — preserves the shared-auth design doc's kill-switch property as opt-in
  (`ENFORCE_LOCAL_ACTIVE`) rather than silently dropping it.
* Neutral — revocation is not instant: browser sessions pick up changes at next login, API
  tokens at next issuance. Accepted at this scale; per-request Admin REST checks remain a
  documented per-endpoint option.
* Neutral — the Keycloak admin console becomes the people-management surface; web-admin's Django
  admin loses its activation role.
* Bad — one-time migration: existing users must be assigned their groups in Keycloak, and
  existing local `is_active=False` states flipped (or left behind a flag) as each service cuts
  over.
* Bad — a person is now fully in (or out of) every service from Keycloak alone: there is no
  per-service local veto unless a deployment opts into `ENFORCE_LOCAL_ACTIVE`.
