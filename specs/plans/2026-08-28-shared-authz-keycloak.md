# Plan: centralized authorization via Keycloak groups/roles

See `specs/design/shared-authz-keycloak.md` for the reasoning and ADR
`0014-centralized-authorization-via-keycloak-groups.md` for the decision. Tracks #823 (closed).
Repos: pyobs-auth, pyobs-archive, pyobs-portal, pyobs-web-admin

Status: **implemented and released everywhere** (pyobs-auth `v2.1.0`, pyobs-archive `v2.1.0`,
pyobs-portal `v2.1.0`, pyobs-web-admin `v2.1.0`). Verified 2026-08-31 by reading each repo's
`develop`/`main` and, for section 0, by observing that Keycloak-gated login is actively working
in production at MONET/S (`admin.monet.saao.ac.za`, group `/pyobs-web-admin-monets`) — not by
directly inspecting the Keycloak admin console, so treat section 0 as inferred-done rather than
independently confirmed there.

## 0. Keycloak admin/deployment config (not pyobs code)

- [x] Create realm groups `pyobs-archive`, `pyobs-portal`, `pyobs-web-admin` (full-path group
      names like `/pyobs-archive`).
- [x] Add a "Group Membership" protocol mapper to the realm/client token scope: claim `groups`,
      full path on.
- [x] Add client roles where fine-grained privileges exist: `portal-admin` on the `portal`
      client; decide whether archive needs `archive-admin` (or reuses its staff/superuser
      split).
- [x] Assign groups to existing users (admin console bulk, or an admin REST API script).
- [x] Sanity check: inspect a token for a test user (Keycloak's debug/token endpoint) and
      confirm the `groups` and `resource_access` claims.

## 1. pyobs-auth — the shared gate

- [x] `KeycloakSettings`: add `required_groups` / `required_roles` fields (from `PYOBS_AUTH`
      `REQUIRED_GROUPS`/`REQUIRED_ROLES`) and `enforce_local_active` (default False).
- [x] New `pyobs_auth.authorization` module: `authorize(claims, settings)` implementing the gate —
      `REQUIRED_GROUPS` matches the `groups` claim (full paths), `REQUIRED_ROLES` matches
      `realm_access.roles` / `resource_access.<client>.roles` (syntax e.g.
      `client:portal:portal-admin`, `realm:pyobs-admin`); no settings set ⇒ always pass.
- [x] `KeycloakAuthentication.authenticate`: call the gate after `TokenValidator.validate`; the
      `is_active` check applies only when `enforce_local_active` is set. Refusal message
      "not authorized" (distinct from the old "pending activation").
- [x] `CallbackView`: same gate after validating the access token; error page for refused users.
- [x] `CallbackView`: store `refresh_token` from the token response alongside `id_token`
      (currently discarded — only `access_token`/`id_token` are kept).
- [x] New middleware (`pyobs_auth.middleware.KeycloakSessionRefreshMiddleware`): once the access
      token's `exp` has passed, call `KeycloakClient.refresh()`, re-validate the resulting
      claims, and re-run `authorize()`; end the session (force logout) if it now fails. Wired
      into `pyobs-web-admin`'s `MIDDLEWARE` (confirmed live on `frontend.monets` after the
      2026-08-31 update).
- [x] Tests for both paths (claims present/absent, both settings, no-settings passthrough,
      `enforce_local_active` interplay) plus the refresh path — `tests/test_authorization.py`,
      `tests/test_middleware.py`; docs — `docs/source/configuration.rst`, `architecture.rst`.
- [x] Release (per repo conventions) — `v2.0.0`, `v2.1.0`.

Deployment note — keeping today's behavior (Keycloak auth only, manual `is_active` activation):
`ENFORCE_LOCAL_ACTIVE=True` + `REQUIRED_GROUPS`/`REQUIRED_ROLES` unset + the service resolver keeps
minting `is_active=False` reproduces the pre-authz flow exactly (first login mints an inactive
user, admin activates in Django admin, then login works). Minting active + `ENFORCE_LOCAL_ACTIVE=True`
instead gives kill-switch semantics (everyone active by default, admins can locally deactivate
individuals). Locally-created users (`createsuperuser`, Django admin) authenticate via Django's
`ModelBackend` and never pass through the claims gate in either flavor.

Failure mode to avoid — a code-only upgrade (new pyobs-auth, no settings change) silently drops the
`is_active` gate: `ENFORCE_LOCAL_ACTIVE` defaults to False and unset `REQUIRED_*` means no claims
gate, so every authenticating Keycloak user is authorized. Sites relying on the old activation gate
must set `ENFORCE_LOCAL_ACTIVE=True` (or complete section 0's group config) as part of the upgrade.
The reverse failure mode is setting `REQUIRED_GROUPS` before assigning groups to existing users
(sections 0/3), which locks everyone out.

## 2. Service cutovers (per service; each lands together with its config)

pyobs-archive:

- [x] `PYOBS_AUTH['REQUIRED_GROUPS']` (settings.py: `[os.getenv('KEYCLOAK_REQUIRED_GROUP',
      '/pyobs-archive')]`).
- [x] `resolve_user`: mints `is_active=True` (drop the inactive gate); keeps `sub` joining and
      email/username linking.
- [x] Local `is_staff`/`is_superuser` flags left as-is at resolve time (per design doc option).
- [x] Tests; release (`v2.1.0`).

pyobs-portal:

- [x] `PYOBS_AUTH['REQUIRED_GROUPS'] = ["/pyobs-portal"]`.
- [x] `resolve_user`: mints active; syncs `is_superuser` only (not `is_staff`) from the
      `portal-admin` client role on every resolve (`pyobs_portal/authentication/keycloak.py:80-83`)
      — `ADMIN_USERNAME`'s synced account is untouched by this path.
- [x] Tests; release (`v2.1.0`).

pyobs-web-admin:

- [x] `PYOBS_AUTH['REQUIRED_GROUPS'] = ["/pyobs-web-admin"]` (deployment-specific value in
      practice, e.g. MONET/S uses `/pyobs-web-admin-monets`).
- [x] `resolve_user`: mints active; local_settings.py.example's guidance updated.
- [x] Tests; release (`v2.1.0`).

## 3. Data migration (per service, after its cutover)

- [x] pyobs-archive: explicit one-off migration
      (`authentication/migrations/0007_activate_keycloak_linked_users.py`) flips existing
      Keycloak-linked `is_active=False` users to `True`.
- [x] pyobs-portal / pyobs-web-admin: no dedicated migration found, but `resolve_user` mints
      `is_active=True` unconditionally on every login, so any pre-existing inactive Keycloak-linked
      user self-heals on next login — functionally equivalent, just not a one-off batch flip.
- [x] Existing local superuser flags re-derive at the user's next resolve (pyobs-portal's
      `is_superuser` sync, above); pyobs-archive/web-admin don't sync superuser from Keycloak, so
      nothing to re-derive there.

## 4. Not in this plan

- Service-to-service authorization (client-credentials) — separate concern, unchanged.
- Keycloak Authorization Services (UMA) — not adopted.
- Per-request revocation checks via the Keycloak Admin REST API — documented option only.
- Rolling out the optional `ENFORCE_LOCAL_ACTIVE` kill switch — a deployment choice; the default
  path here is fully centralized.
