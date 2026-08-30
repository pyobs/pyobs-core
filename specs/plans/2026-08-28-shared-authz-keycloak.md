# Plan: centralized authorization via Keycloak groups/roles

See `specs/design/shared-authz-keycloak.md` for the reasoning and ADR
`0014-centralized-authorization-via-keycloak-groups.md` for the decision. Tracks #823.
Repos: pyobs-auth, pyobs-archive, pyobs-portal, pyobs-web-admin

## 0. Keycloak admin/deployment config (not pyobs code)

- [ ] Create realm groups `pyobs-archive`, `pyobs-portal`, `pyobs-web-admin` (full-path group
      names like `/pyobs-archive`).
- [ ] Add a "Group Membership" protocol mapper to the realm/client token scope: claim `groups`,
      full path on.
- [ ] Add client roles where fine-grained privileges exist: `portal-admin` on the `portal`
      client; decide whether archive needs `archive-admin` (or reuses its staff/superuser
      split).
- [ ] Assign groups to existing users (admin console bulk, or an admin REST API script).
- [ ] Sanity check: inspect a token for a test user (Keycloak's debug/token endpoint) and
      confirm the `groups` and `resource_access` claims.

## 1. pyobs-auth — the shared gate

- [ ] `KeycloakSettings`: add `required_groups` / `required_roles` fields (from `PYOBS_AUTH`
      `REQUIRED_GROUPS`/`REQUIRED_ROLES`) and `enforce_local_active` (default False).
- [ ] New `pyobs_auth.authorization` module: `authorize(claims, settings)` implementing the gate —
      `REQUIRED_GROUPS` matches the `groups` claim (full paths), `REQUIRED_ROLES` matches
      `realm_access.roles` / `resource_access.<client>.roles` (syntax e.g.
      `client:portal:portal-admin`, `realm:pyobs-admin`); no settings set ⇒ always pass.
- [ ] `KeycloakAuthentication.authenticate`: call the gate after `TokenValidator.validate`; the
      `is_active` check applies only when `enforce_local_active` is set. Refusal message
      "not authorized" (distinct from the old "pending activation").
- [ ] `CallbackView`: same gate after validating the access token; error page for refused users.
- [ ] `CallbackView`: store `refresh_token` from the token response alongside `id_token`
      (currently discarded — only `access_token`/`id_token` are kept).
- [ ] New middleware: once the access token's `exp` has passed, call `KeycloakClient.refresh()`
      (exists in `client.py`, currently unused outside its own unit test), re-validate the
      resulting claims, and re-run `authorize()`; end the session (force logout) if it now fails.
      Without this a browser session never re-contacts Keycloak after login and revocation is
      bounded only by `SESSION_COOKIE_AGE`, not by any token lifetime — see the design doc's
      "Revocation model and freshness".
- [ ] Tests for both paths (claims present/absent, both settings, no-settings passthrough,
      `enforce_local_active` interplay) plus the refresh path (expired access token triggers
      refresh, refresh failure ends the session, `authorize()` re-run picks up a
      newly-revoked group/role); docs (`docs/source/configuration.rst`, README).
- [ ] Release (per repo conventions).

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

- [ ] `PYOBS_AUTH['REQUIRED_GROUPS'] = ["/pyobs-archive"]`.
- [ ] `resolve_user`: mint `is_active=True` (drop the inactive gate); keep `sub` joining and
      email/username linking.
- [ ] If archive keeps its staff/superuser admin endpoints: sync `is_staff`/`is_superuser` from
      the chosen role at resolve time (or leave local flags as-is for now — see design doc).
- [ ] Tests; release.

pyobs-portal:

- [ ] `PYOBS_AUTH['REQUIRED_GROUPS'] = ["/pyobs-portal"]`.
- [ ] `resolve_user`: mint active; sync `is_superuser` from the `portal-admin` client role at
      resolve time (frontend `_is_superuser` and `IsAdminUser` API views keep working); the
      `ADMIN_USERNAME` synced account must not be clobbered (admin_sync re-applies on migrate).
      Sync sets `is_superuser` only — do **not** also set `is_staff`, which would additionally
      unlock the raw Django admin backend (`admin_sync.py`'s `ADMIN_USERNAME` account sets both
      deliberately; the Keycloak-derived sync must not copy that pattern).
- [ ] Tests; release.

pyobs-web-admin:

- [ ] `PYOBS_AUTH['REQUIRED_GROUPS'] = ["/pyobs-web-admin"]`.
- [ ] `resolve_user`: mint active; remove the "activate in Django admin" guidance from
      README/local_settings comments (Keycloak admin is now the activation surface).
- [ ] Tests; release.

## 3. Data migration (per service, after its cutover)

- [ ] One-off `User.objects.filter(is_active=False).update(is_active=True)` for Keycloak-linked
      users in each service (revocations now happen in Keycloak).
- [ ] Existing local superuser flags re-derive at the user's next resolve (or a one-off sync for
      users who should keep admin).

## 4. Not in this plan

- Service-to-service authorization (client-credentials) — separate concern, unchanged.
- Keycloak Authorization Services (UMA) — not adopted.
- Per-request revocation checks via the Keycloak Admin REST API — documented option only.
- Rolling out the optional `ENFORCE_LOCAL_ACTIVE` kill switch — a deployment choice; the default
  path here is fully centralized.
