# Plan: Attach observation-portal to Keycloak via `pyobs-auth`

Our self-hosted `observation-portal` (the MONET fork of the OCS
[observatorycontrolsystem/observation-portal](https://github.com/observatorycontrolsystem/observation-portal)
project) currently authenticates entirely against its own local Django user database. This plan
makes it a first-class `pyobs-auth` client like pyobs-archive / pyobs-portal / pyobs-web-admin:
the portal's login page gains a Keycloak login button and its API accepts Keycloak bearer tokens —
**additive and env-gated** on top of the existing local username/password auth, with
`KEYCLOAK_SERVER_URL` unset disabling Keycloak entirely.

Status: proposed, 2026-08-28. No GitHub issue filed yet — file one before implementation if the
repo convention wants it.

Repos: observation-portal (MONET fork), pyobs-auth.

## Relationship to prior auth work (direction change)

- **ADR 0011** (parallel Keycloak + "odin" backends) was superseded 2026-08-19 by the brokering
  design; not relevant here.
- **`specs/design/shared-auth-keycloak.md` + `specs/plans/2026-08-12-shared-auth-keycloak.md`
  (Section 0)** — the original direction was to *broker* observation-portal **behind** Keycloak:
  enable OIDC on the portal's own `django-oauth-toolkit` provider, register the portal in Keycloak
  as an upstream Identity Provider (pure Keycloak admin config, tracked in #748, still open).
  **This plan changes that direction**: the portal becomes a *relying party* (client) of Keycloak
  instead, exactly like the other pyobs services. Users then log into the portal with Keycloak
  identities directly, which makes brokering the portal behind Keycloak unnecessary for the MONET
  deployment — Section 0 is superseded. The design doc's "observation-portal is brokered behind
  Keycloak" stance gets a status note (section 10) when this lands.
- **`specs/plans/2026-08-21-keycloak-idp-hint-login.md`** — `pyobs-auth >= 2.0.0.dev9` ships
  `IDP_HINT`/`kc_idp_hint`; the portal adopts the same dual-button login-page pattern as
  archive/portal/web-admin.
- **Single-issuer stance is unaffected**: `pyobs_auth.authentication.KeycloakAuthentication`
  validates Keycloak tokens only; the portal's own OAuth2 provider role (`oauth2_provider`,
  `OAUTH_CLIENT_APPS_BASE_URLS`, `OAUTH_SERVER_KEY`) and its tokens keep working unchanged
  (stacking-safety: KeycloakAuthentication defers on non-matching issuers, section 5).

## Problem

The portal today (`observation_portal/`):

- **Login**: session-based `CustomLoginView` (username/email + password,
  `accounts/views.py:132`) + JSON `ApiLoginView` (`accounts/views.py:174`); self-registration via
  `django-registration-redux` (`accounts/urls.py:15`, `CustomRegistrationView`).
- **Backends** (`settings.py:205`): `EmailOrUsernameModelBackend`, Django `ModelBackend`,
  `oauth2_provider.backends.OAuth2Backend` (portal-issued tokens only).
- **DRF auth** (`settings.py:303`): Session, Token (`rest_framework.authtoken`), and
  `oauth2_provider.contrib.rest_framework.OAuth2Authentication`.
- **Users**: standard `django.contrib.auth.User` + a required `Profile` (`accounts/models.py:18`)
  created by the registration flow — **not** by a signal, so any user minted outside registration
  (which is what `resolve_user` will do) must create its Profile explicitly.
- **Dependencies**: Django 4.2.30 (`poetry.lock`), Python 3.10/3.11 (Dockerfile
  `python:3.10-slim`, CI matrix `.github/workflows/build.yaml`).

No shared identity: a user authenticated against any pyobs web service has no way to be
recognized by the portal, and vice versa — the gap this plan closes, consistent with the
shared-auth design.

## Approach

Port the pyobs-portal integration (2026-08-12 plan section 3) into the portal's existing
`observation_portal.accounts` app, using pyobs-archive's user-mapping shape
(`Profile.keycloak_sub`, section 3). Everything is additive: local username/password login,
self-registration, the portal's OAuth2 *provider* role for downstream LCO apps, and DRF token auth
all stay. `KEYCLOAK_SERVER_URL` unset ⇒ portal behaves exactly as today.

## 0. Prerequisite: Django 5.2 upgrade (gating)

`pyobs-auth` requires `Django>=5.2,<7` and `Python>=3.11`; the portal is on Django 4.2.30 /
Python 3.10+. This is the only hard external prerequisite and the biggest chunk of the plan —
**recommend running it as its own track/plan first** if it balloons.

- [ ] `pyproject.toml`: `django = "^4"` → `^5.2` (or 6.x, within pyobs-auth's `<7` pin);
      `python = ">=3.9,<3.12"` → `>=3.11`.
- [ ] Dockerfile (`python:3.10-slim` → 3.11/3.12-slim) and CI matrix (drop 3.10).
- [ ] Dependency audit for Django 5.2:
      - `django-oauth-toolkit ^2` → `^3` (DOT 3.0 supports Django 5.2; needed for the portal's
        OIDC provider role).
      - `django-registration-redux ^2.9` → `>=2.13`.
      - `drf-yasg ^1.20` → `>=1.21.10`.
      - Verify/`bump`: `django-filter`, `django-bootstrap4 <4.0` (effectively unmaintained — real
        risk for the Django-5 upgrade; fallback `django-bootstrap5` or drop if unused beyond the
        login/registration templates), `django-storages`, `django-extensions`, `django-cors-headers`,
        `django-dramatiq`, `django-health-check`, `django-object-actions`.
- [ ] Settings sweep for removed/renamed Django 5 APIs (concrete hits already in
      `observation_portal/settings.py`):
      - `USE_L10N` (line 240) — removed in Django 5.0, delete.
      - `STATICFILES_STORAGE` / `DEFAULT_FILE_STORAGE` (lines 261, 265) — removed in Django 5.1,
        migrate to the `STORAGES` dict.
      - grep for deprecated `django.utils.timezone.utc` / other 4.x deprecations; run
        `manage.py check --deploy` and the test suite to surface the rest.

## 1. Dependency + app wiring

- [ ] `pyproject.toml`: add `pyobs-auth>=2.0.0.dev9` (pin whatever dev version is current at
      implementation, per `do-python-release` conventions).
- [ ] `observation_portal/settings.py` `INSTALLED_APPS`: add `'pyobs_auth'` (no new local app —
      resolver/model/context-processor live in the existing `observation_portal.accounts`,
      mirroring pyobs-archive rather than pyobs-portal's separate `authentication` app).

## 2. `PYOBS_AUTH` settings (env-driven)

- [ ] `observation_portal/settings.py`: add the `PYOBS_AUTH` dict, matching the other services:

      ```python
      PYOBS_AUTH = {
          "SERVER_URL": os.getenv("KEYCLOAK_SERVER_URL", ""),
          "REALM": os.getenv("KEYCLOAK_REALM", "pyobs"),
          "CLIENT_ID": os.getenv("KEYCLOAK_CLIENT_ID", "observation-portal"),
          "CLIENT_SECRET": os.getenv("KEYCLOAK_CLIENT_SECRET", ""),
          "REDIRECT_URI": os.getenv("KEYCLOAK_REDIRECT_URI", ""),
          "POST_LOGOUT_REDIRECT_URI": os.getenv("KEYCLOAK_POST_LOGOUT_REDIRECT_URI", ""),
          "IDP_HINT": os.getenv("KEYCLOAK_IDP_HINT", ""),
          "IDP_LABEL": os.getenv("KEYCLOAK_IDP_LABEL", ""),
          "USER_RESOLVER": "observation_portal.accounts.keycloak.resolve_user",
      }
      ```

      Unset `SERVER_URL` disables Keycloak entirely (pyobs-auth's `get_settings()` raises only on
      first use — harmless while nothing presents a Keycloak token or hits the login views).
- [ ] Document the `KEYCLOAK_*` env vars in `README.md`'s environment-variable table and in
      `deploy/.env` / `k8s/envs/local/settings.env` (next to the existing auth-related vars).

## 3. User mapping — `Profile.keycloak_sub` + `resolve_user`

Mirror pyobs-archive's implemented pattern (`Profile.keycloak_sub` migration + resolver), not
pyobs-portal's separate `KeycloakIdentity` model — the portal already has a `Profile`
(`accounts/models.py:18`).

- [ ] `observation_portal/accounts/models.py`: add `keycloak_sub = models.CharField(max_length=255,
      unique=True, blank=True, null=True)` to `Profile` + migration. Keycloak's `sub` claim is the
      join key (stable; email/username can change), per the design doc.
- [ ] New `observation_portal/accounts/keycloak.py` with `resolve_user(claims) -> User`, shaped like
      `pyobs_portal.authentication.keycloak.resolve_user`:
      - `sub` → `Profile.keycloak_sub` lookup first;
      - else match existing `User` by email, falling back to username (use `.first()` — Django's
        `User.email` is not unique, duplicates exist in practice);
      - else mint `User(username=..., email=..., is_active=False)` **and** a `Profile` with
        `institution=''`, `title=''` (non-blank CharFields; no auto-creation signal exists — the
        registration flow creates Profiles today). Note: `Profile` post-save fires
        `update_or_create_client_applications_user` (`accounts/signals/handlers.py:22`) — harmless,
        it no-ops without `OAUTH_CLIENT_APPS_BASE_URLS`.
      - store/refresh `Profile.keycloak_sub`; refuse/inactive users are handled by pyobs-auth
        (new accounts minted inactive ⇒ per-portal activation gate, unchanged from the design).
- [ ] Decision to confirm (open question below): auto-link existing portal users by email on first
      Keycloak login (design-doc default, what archive/portal do) vs. requiring an explicit
      admin-side link. Recommended: auto-link by email.

## 4. URLs — mount `pyobs_auth.urls`

- [ ] `observation_portal/urls.py`: add `path('accounts/keycloak/', include('pyobs_auth.urls'))`
      **before** `re_path(r'^accounts/', include(accounts_urls))` (line 119). Ordering matters:
      `accounts/urls.py` ends in the catch-all
      `re_path(r'', include('registration.backends.default.urls'))`, which would swallow
      `accounts/keycloak/...` and 404 it.
- [ ] Resulting endpoints: `/accounts/keycloak/login/`, `/callback/`, `/logout/`
      (`pyobs_auth.urls`). No change to the portal's own `/accounts/login/` etc.

## 5. DRF authentication — stack `KeycloakAuthentication`

- [ ] `observation_portal/settings.py` `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`: append
      `'pyobs_auth.authentication.KeycloakAuthentication'` after
      `'oauth2_provider.contrib.rest_framework.OAuth2Authentication'`. Safe to stack:
      KeycloakAuthentication returns `None` (defers) for any Bearer token whose issuer isn't the
      Keycloak realm, so portal-minted OAuth2 tokens still authenticate via the oauth2_provider
      class.
- [ ] No `AUTHENTICATION_BACKENDS` change — the redirect-based OIDC flow is handled by
      `pyobs_auth.views`, not a backend class (see design doc).

## 6. Login page + context processor

- [ ] New `observation_portal/accounts/context_processors.py` with `keycloak(request)` exposing
      `keycloak_login_enabled`, `keycloak_idp_hint`, `keycloak_idp_label` (mirror
      `pyobs_portal/frontend/context_processors.py`); register it in
      `settings.py` `TEMPLATES['OPTIONS']['context_processors']`.
- [ ] `observation_portal/accounts/templates/registration/login.html`: add the Keycloak buttons
      behind `{% if keycloak_login_enabled %}` — dual-button pattern when `IDP_HINT` is configured
      ("Log in with {{ keycloak_idp_label }}" via `{% url 'pyobs_auth:login' %}` and "Log in with
      local Keycloak account" via `?idp_hint=`), single button otherwise; **preserve `next` with
      `|urlencode`** on every link (and fix the existing unescaped `next` in the local form while
      the file is open). The local username/password form stays as-is.

## 7. Logout

- [ ] The portal has no user-facing logout URL today (`accounts/urls.py` only wires login/register/
      password views; logout is admin-only). Wire the site's logout action to POST
      `{% url 'pyobs_auth:logout' %}` (pyobs-auth's RP-Initiated Logout ends the Keycloak SSO
      session for Keycloak-originated sessions, and does an ordinary local logout otherwise), or
      add a plain `django.contrib.auth.urls` logout include as the non-Keycloak fallback.

## 8. Interplay with existing portal features

- [ ] Self-registration (`CustomRegistrationView`, `registration.backends.default.urls`) untouched —
      local accounts remain a first-class path.
- [ ] `password_expiration` (`CustomLoginView.get_success_url`, `ApiLoginView`) applies to
      local-password logins only; Keycloak sessions bypass those views entirely — no change.
- [ ] Portal's OAuth2 provider role (`/o/` endpoints, `OAUTH2_PROVIDER` OIDC settings,
      `OAUTH_CLIENT_APPS_BASE_URLS`, `OAUTH_SERVER_KEY`) untouched — this plan does not enable OIDC
      on the portal's own provider, so Section 0's Keycloak-admin items are not needed either.
- [ ] `LimitAnonymousAccessMiddleware` / throttles / `ApiLoginView` unchanged.

## 9. Tests

- [ ] `resolve_user`: first-login links existing user by email and by username; mints
      User+Profile (inactive) with empty-string profile fields; re-login resolves via `sub`;
      duplicate-email case resolves deterministically.
- [ ] DRF: `KeycloakAuthentication` authenticates a valid Keycloak token; defers (returns `None`)
      on a foreign-issuer token; refuses an inactive user.
- [ ] Stacking: a portal-minted oauth2 access token still authenticates with both
      `OAuth2Authentication` and `KeycloakAuthentication` registered.
- [ ] Context processor / template: `keycloak_login_enabled` false ⇒ login page identical to today.

## 10. Docs (pyobs-core)

- [ ] `specs/design/shared-auth-keycloak.md`: status note — observation-portal is attached as a
      `pyobs-auth` client (relying party) rather than brokered behind Keycloak; Section 0 of the
      2026-08-12 plan is superseded.
- [ ] `specs/plans/index.md`: this plan's entry.

## Verification

- [ ] Full portal test suite green (existing + new).
- [ ] Regression: `KEYCLOAK_SERVER_URL` unset ⇒ login page renders exactly today's form; API
      behavior unchanged. (Verifiable from a checkout.)
- [ ] Live browser E2E against the running Keycloak (operational — not verifiable from a repo
      checkout): Keycloak login button → GWDG SSO (with `IDP_HINT`) / local Keycloak account →
      callback → `resolve_user` → portal session; logout ends both the portal and the Keycloak SSO
      session; a Keycloak bearer token authenticates a portal API call.

## Not in this plan

- **Brokering the portal behind Keycloak** (Section 0 of the 2026-08-12 plan) — superseded by this
  direction. A deployment that wants Keycloak to federate the portal's own users can still do it as
  optional Keycloak admin config (enable OIDC on the portal's provider, register it as upstream
  IdP), independent of this plan.
- **Service-to-service auth** — the portal's OAuth2 provider for downstream LCO apps, and
  pyobs-core's static-token calls to portal (`Authorization: Token`), both stay as-is; Keycloak
  client-credentials remains optional (see design doc).
- **Upstreaming the changes to `observatorycontrolsystem/observation-portal`** — the changes are
  additive and env-gated, so upstreaming is feasible, but it's a separate decision (the OCS project
  is the upstream; the MONET fork is the vehicle here).
- **Keycloak admin/deployment config** for the MONET realm (registering an
  `observation-portal` client, redirect URIs) — operational, outside repo code.

## Open questions

- **Django target**: 5.2 LTS vs 6.x for the prerequisite upgrade (pyobs-auth allows `<7`).
- **`keycloak_sub` on `Profile` vs a separate `KeycloakIdentity` model** — recommended:
  `Profile.keycloak_sub` (mirrors pyobs-archive, no new app).
- **Auto-linking existing portal users by email on first Keycloak login** vs explicit admin-side
  linking — recommended: auto-link by email (design-doc default), acknowledging the
  non-unique-email caveat (`.first()`).
- **Post-login redirect for Keycloak sessions**: pyobs-auth defaults `next` to `/`; the portal's
  local login redirects to `/accounts/loggedinstate/` — decide whether the Keycloak button should
  pass `next=/accounts/loggedinstate/` to keep the post-login landing consistent.
