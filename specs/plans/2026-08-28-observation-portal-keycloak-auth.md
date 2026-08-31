# Plan: Attach observation-portal to Keycloak via generic OIDC (mozilla-django-oidc)

Our self-hosted `observation-portal` ([thusser/observation-portal](https://github.com/thusser/observation-portal),
the MONET fork of the OCS
[observatorycontrolsystem/observation-portal](https://github.com/observatorycontrolsystem/observation-portal)
project) currently authenticates entirely against its own local Django user database. This plan
gives it OIDC login (Keycloak in our deployment, any OIDC provider in general) using
`mozilla-django-oidc` — **not** `pyobs-auth`, specifically so the feature has no pyobs dependency
and is realistic to submit upstream to OCS. It's **additive and config-gated** on top of the
existing local username/password auth: `OIDC_ENABLED` unset/false ⇒ portal behaves exactly as
today.

Status: proposed, 2026-08-31 (revised from 2026-08-28 — see "Direction change" below). No GitHub
issue filed yet.

Repos: observation-portal (MONET fork). No pyobs-auth/pyobs-core dependency — this plan does not
touch pyobs-auth.

## Direction change from the 2026-08-28 version

The original version of this plan ported the pyobs-auth integration pattern (`PYOBS_AUTH` settings
dict, `pyobs_auth.authentication.KeycloakAuthentication`, `pyobs_auth.urls`) used by
pyobs-archive/pyobs-portal/pyobs-web-admin, and required a Django 4.2 → 5.2 upgrade first
(`pyobs-auth` pins `Django>=5.2,<7`).

That's dropped. Reasoning:

- `pyobs-auth` is a pyobs-specific package (our conventions, our IDP_HINT pattern) — a PR adding a
  dependency on it would never be accepted into `observatorycontrolsystem/observation-portal`
  upstream.
- `mozilla-django-oidc` (checked 2026-08-31, current release 5.0.2) declares
  `Requires-Dist: Django>=4.2` and `Requires-Python: >=3.10`, both of which the portal already
  satisfies (Django 4.2.30, Python 3.10/3.11). **The Django 5.2 upgrade is not a prerequisite for
  this plan** — it may still be worth doing for other reasons, but nothing here gates on it.

This still supersedes Section 0 of `specs/plans/2026-08-12-shared-auth-keycloak.md` (brokering the
portal *behind* Keycloak as an upstream IdP) for the same reason as before: the portal becomes a
relying party of Keycloak directly, which makes brokering unnecessary for MONET. The design doc's
"observation-portal is brokered behind Keycloak" stance still gets the Section 10 status note.

`specs/plans/2026-08-21-keycloak-idp-hint-login.md`'s dual-button login pattern
(`IDP_HINT`/`kc_idp_hint`) is **not directly reusable** — it's a `pyobs-auth` feature. Section 6
below reimplements the equivalent behavior generically.

## Problem

Unchanged from the original survey of `observation_portal/`:

- **Login**: session-based `CustomLoginView` (`accounts/views.py:132`) + JSON `ApiLoginView`
  (`accounts/views.py:174`); self-registration via `django-registration-redux`
  (`accounts/urls.py:15`).
- **Backends** (`settings.py:205`): `EmailOrUsernameModelBackend`, Django `ModelBackend`,
  `oauth2_provider.backends.OAuth2Backend` (portal-issued tokens only).
- **DRF auth** (`settings.py:303`): Session, Token (`rest_framework.authtoken`), and
  `oauth2_provider.contrib.rest_framework.OAuth2Authentication`.
- **Users**: standard `django.contrib.auth.User` + a required `Profile` (`accounts/models.py:18`),
  created by the registration flow — **not** by a signal, so any user minted outside registration
  must create its `Profile` explicitly.

No shared identity: a user authenticated against any pyobs web service, or any other OIDC-fronted
system, has no way to be recognized by the portal.

## Approach

Two layers, deliberately kept separable:

- **Part A — generic, upstream-submittable.** Standard `mozilla-django-oidc` wiring: login/callback/
  logout views, a custom `OIDCAuthenticationBackend` subclass for user resolution, DRF bearer-token
  auth via `mozilla_django_oidc.contrib.drf`, everything gated by one `OIDC_ENABLED` flag and
  generic `OIDC_*` settings. Nothing in this layer names Keycloak, MONET, or pyobs. This is the part
  a PR to `observatorycontrolsystem/observation-portal` would contain.
- **Part B — MONET deployment config.** The actual `OIDC_OP_*` endpoint values, client
  ID/secret, and realm for our Keycloak instance. Lives in MONET's private site-config repo /
  deployment env files, never in this repo or any public one
  ([[feedback_no_internal_names_in_public_repos]]).

## Part A: generic OIDC support in observation-portal

### A0. Dependency + settings gate

- [ ] `pyproject.toml`: add `mozilla-django-oidc[drf]` (pin latest stable — 5.0.2 as of
      2026-08-31; re-check at implementation time).
- [ ] `observation_portal/settings.py`: single toggle,
      ```python
      OIDC_ENABLED = os.getenv("OIDC_ENABLED", "False").lower() == "true"
      ```
      Everything below (`AUTHENTICATION_BACKENDS` entry, DRF authenticator, URL include, context
      processor) is added conditionally on this flag, at settings/urls load time — **this is the
      literal config option**: false ⇒ zero behavioral change from today, no new code path
      executes, no network calls to any OIDC provider happen.
- [ ] Generic `OIDC_*` env vars, read only when `OIDC_ENABLED` (mirrors mozilla-django-oidc's own
      naming, not Keycloak-specific):
      ```python
      if OIDC_ENABLED:
          OIDC_RP_CLIENT_ID = os.environ["OIDC_RP_CLIENT_ID"]
          OIDC_RP_CLIENT_SECRET = os.environ["OIDC_RP_CLIENT_SECRET"]
          OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ["OIDC_OP_AUTHORIZATION_ENDPOINT"]
          OIDC_OP_TOKEN_ENDPOINT = os.environ["OIDC_OP_TOKEN_ENDPOINT"]
          OIDC_OP_USER_ENDPOINT = os.environ["OIDC_OP_USER_ENDPOINT"]
          OIDC_OP_JWKS_ENDPOINT = os.environ["OIDC_OP_JWKS_ENDPOINT"]
          OIDC_RP_SIGN_ALGO = os.getenv("OIDC_RP_SIGN_ALGO", "RS256")
          OIDC_OP_LOGOUT_ENDPOINT = os.getenv("OIDC_OP_LOGOUT_ENDPOINT", "")  # optional, see A6
          AUTHENTICATION_BACKENDS = AUTHENTICATION_BACKENDS + [
              "observation_portal.accounts.oidc.ObservationPortalOIDCBackend",
          ]
      ```
      **Explicit endpoints, not discovery-URL auto-fetch.** `mozilla-django-oidc` doesn't do
      `.well-known/openid-configuration` discovery itself. We could add a small helper that fetches
      it once at settings-load time from `OIDC_OP_ISSUER` — deliberately *not* doing that: it turns
      "app fails to start" into a new failure mode whenever the OIDC provider is briefly
      unreachable during a deploy/restart. Four explicit endpoint env vars is more typing but keeps
      Django startup independent of the OIDC provider's uptime.
- [ ] Document the `OIDC_*` env vars in `README.md`'s environment-variable table.

### A1. User mapping — `Profile.oidc_sub` + custom backend

- [ ] `observation_portal/accounts/models.py`: add `oidc_sub = models.CharField(max_length=255,
      unique=True, blank=True, null=True)` to `Profile` + migration. (Generic name — not
      `keycloak_sub` — since Part A doesn't know it's Keycloak.)
- [ ] New `observation_portal/accounts/oidc.py`:
      ```python
      from mozilla_django_oidc.auth import OIDCAuthenticationBackend

      class ObservationPortalOIDCBackend(OIDCAuthenticationBackend):
          def filter_users_by_claims(self, claims):
              sub = claims.get("sub")
              if sub:
                  matches = self.UserModel.objects.filter(profile__oidc_sub=sub)
                  if matches.exists():
                      return matches
              return super().filter_users_by_claims(claims)  # falls back to email match

          def verify_claims(self, claims):
              if not super().verify_claims(claims):
                  return False
              # mozilla-django-oidc does NOT verify the `aud` claim by default
              # (jwt.decode(..., options={"verify_aud": False}) in _verify_jws) —
              # verify it explicitly against our client id.
              aud = claims.get("aud")
              if isinstance(aud, str):
                  aud = [aud]
              return self.OIDC_RP_CLIENT_ID in (aud or [])

          def create_user(self, claims):
              user = super().create_user(claims)
              user.is_active = False  # per-portal activation gate, unchanged from today
              user.save(update_fields=["is_active"])
              Profile.objects.create(
                  user=user, institution="", title="", oidc_sub=claims.get("sub", ""),
              )
              return user

          def update_user(self, user, claims):
              profile = user.profile
              sub = claims.get("sub", "")
              if sub and profile.oidc_sub != sub:
                  profile.oidc_sub = sub
                  profile.save(update_fields=["oidc_sub"])
              return user
      ```
      `Profile` post-save fires `update_or_create_client_applications_user`
      (`accounts/signals/handlers.py:22`) — harmless, no-ops without `OAUTH_CLIENT_APPS_BASE_URLS`,
      same as the original plan noted.
- [ ] Auto-link by email is the effective default (`filter_users_by_claims` falls through to the
      base class's email match) — same recommendation as the 2026-08-28 version, same
      non-unique-email caveat (base class uses `.filter()`, not `.first()` — check whether multiple
      matches should raise or pick one; mozilla-django-oidc's base `get_or_create_user` raises
      `SuspiciousOperation` on multiple matches, which is stricter than the original plan's
      `.first()` — decide whether that's acceptable or needs overriding).

### A2. URLs

- [ ] `observation_portal/urls.py`:
      ```python
      if settings.OIDC_ENABLED:
          urlpatterns = [path("oidc/", include("mozilla_django_oidc.urls"))] + urlpatterns
      ```
      Prepend (not append) for the same reason as the original plan's ordering note: the portal's
      `accounts/urls.py` ends in a catch-all `re_path(r'', include('registration.backends...'))`
      that would otherwise swallow `oidc/...`.
- [ ] Resulting endpoints when enabled: `/oidc/authenticate/`, `/oidc/callback/`, `/oidc/logout/`.

### A3. DRF authentication — bearer tokens

- [ ] `observation_portal/settings.py`, conditionally on `OIDC_ENABLED`, append
      `"mozilla_django_oidc.contrib.drf.OIDCAuthentication"` to
      `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`, **after**
      `OAuth2Authentication` — ordering here is load-bearing in a way it wasn't in the original
      plan (see the open question below).

### A4. Login page + context processor

- [ ] New `observation_portal/accounts/context_processors.py`: `oidc(request)` exposing
      `oidc_login_enabled` (= `settings.OIDC_ENABLED`) and an `oidc_login_url` (reverse of
      `oidc_authentication_init`, preserving `next`); register in `TEMPLATES['OPTIONS']
      ['context_processors']`.
- [ ] `templates/registration/login.html`: single "Log in with OIDC" / provider-labeled button
      behind `{% if oidc_login_enabled %}`, `next` preserved via `|urlencode` (and fix the existing
      unescaped `next` in the local form while the file is open). No dual-button/IDP-hint pattern
      here — that's Keycloak-specific UX (multiple upstream IdPs behind one realm), doesn't belong
      in the generic layer. If MONET wants it, it's a Part B template override, not upstream code.

### A5. Logout

- [ ] `mozilla_django_oidc.urls` gives `/oidc/logout/`, which by default only ends the local Django
      session. RP-initiated logout at the OP (ending its SSO session too) needs
      `OIDC_OP_LOGOUT_URL_METHOD` pointed at a function that builds the provider's end-session URL
      (`id_token_hint` + `post_logout_redirect_uri`) — generic in shape (reads
      `OIDC_OP_LOGOUT_ENDPOINT` from settings, which is why A0 declares it optional), but the
      function itself still has to be written; add it in `accounts/oidc.py` alongside the backend.

### A6. Interplay with existing portal features

Same as the original plan, unchanged: self-registration, `password_expiration` (local-password
logins only), the portal's own OAuth2 *provider* role, `LimitAnonymousAccessMiddleware` — none of
these are touched.

### A7. Tests

- [ ] `ObservationPortalOIDCBackend`: sub-match on repeat login, email-fallback match on first
      login, inactive-user creation with empty Profile fields, `verify_claims` rejects a token with
      the wrong `aud`.
- [ ] DRF: `OIDCAuthentication` authenticates a valid userinfo response; a portal-issued OAuth2
      token still authenticates (via `OAuth2Authentication`, first in the list) without ever
      reaching the OIDC authenticator.
- [ ] `OIDC_ENABLED=False` (the default): login page identical to today, no `AUTHENTICATION_BACKENDS`
      /DRF-authenticator/URL changes — importing `settings.py` and `urls.py` must not require any
      `OIDC_*` env var to be set.

## Part B: MONET deployment config (not upstream)

- [ ] Concrete `OIDC_RP_CLIENT_ID`/secret, endpoint URLs, and `OIDC_ENABLED=true` in MONET's
      private site-config repo / `deploy/.env` — not this repo, not the OCS fork's public
      `README.md` example values ([[feedback_no_internal_names_in_public_repos]]).
- [ ] If MONET wants the dual-button "GWDG SSO vs. local Keycloak account" UX from
      `2026-08-21-keycloak-idp-hint-login.md`: a template override of `login.html` in the private
      config (or a documented extension point in A4's template, e.g. a block tag) rather than
      baking `kc_idp_hint` into the upstream login flow. Worth deciding at implementation time
      whether this is worth the extra complexity for one deployment.
- [ ] Keycloak admin config: register `observation-portal` as a client, redirect URIs — operational,
      outside repo code, same as the original plan's "Not in this plan" item.

## Docs (pyobs-core)

- [ ] `specs/design/shared-auth-keycloak.md` Section 10: status note — observation-portal attaches
      via generic OIDC (`mozilla-django-oidc`), not `pyobs-auth`; Section 0 of the 2026-08-12 plan
      is superseded, same as the original plan intended.
- [ ] `specs/plans/index.md`: update this entry's one-liner (currently describes the `pyobs-auth`
      approach — needs to say generic OIDC / no pyobs-auth dependency / upstream-submittable).

## Verification

- [ ] Full portal test suite green (existing + new).
- [ ] Regression: `OIDC_ENABLED` unset ⇒ login page renders exactly today's form; settings/urls
      import cleanly with zero `OIDC_*` env vars present. (Verifiable from a checkout.)
- [ ] Live E2E against real Keycloak (operational, not verifiable from a checkout): login button →
      Keycloak → callback → backend resolves user → portal session; logout ends both sessions; a
      Keycloak-issued bearer token authenticates a portal API call; a portal-issued OAuth2 token
      still authenticates unaffected.

## Not in this plan

- **Upstreaming itself** — Part A is *written* to be upstream-submittable (no pyobs dependency,
  generic naming, config-gated), but actually filing the PR against
  `observatorycontrolsystem/observation-portal`, engaging with their maintainers, and carrying any
  review-driven rework is a separate decision/step, not automatic once Part A lands in the fork.
- **Service-to-service auth** — the portal's OAuth2 provider for downstream LCO apps, and
  pyobs-core's static-token calls to the portal, stay as-is.
- **Django 5.2 upgrade** — not gating this plan (see "Direction change"); may still be worth doing
  independently.

## Open questions

- **DRF authenticator cost/deferral semantics.** `pyobs_auth.authentication.KeycloakAuthentication`
  (the original plan) checks the token's `iss` claim locally and defers (returns `None`) for
  non-matching issuers — cheap, no network call for foreign tokens.
  `mozilla_django_oidc.contrib.drf.OIDCAuthentication` instead calls
  `backend.get_or_create_user(access_token, ...)`, which hits `OIDC_OP_USER_ENDPOINT` (the OIDC
  provider's userinfo endpoint) over the network for **every** bearer token it's asked to
  authenticate, and only works correctly here because `OAuth2Authentication` (checked first) claims
  portal-issued tokens before OIDC's class is ever reached. Any bearer token that is neither a valid
  portal OAuth2 token nor a valid OIDC access token costs a live call to the OIDC provider before
  failing. Options: (a) accept it — simplest, standard mozilla-django-oidc DRF pattern, provider
  must be reachable for the API to reject foreign tokens promptly; (b) write a custom DRF
  authenticator that verifies the JWT locally via `OIDC_OP_JWKS_ENDPOINT` and checks `iss` to decide
  whether to defer, closer to `pyobs-auth`'s behavior, more code. Recommend (a) for the upstream PR
  (simpler, uses the library as intended) unless portal API latency/availability under a
  flaky-or-down OIDC provider turns out to matter.
- **Multiple-email-match behavior**: mozilla-django-oidc's base `filter_users_by_claims`/
  `get_or_create_user` raises `SuspiciousOperation` on multiple email matches; the original plan
  assumed silent `.first()`-style resolution. Decide which behavior is wanted for the portal's known
  duplicate-email accounts before implementation.
- **Discovery-URL vs. explicit endpoints** (A0): explicit is recommended above; revisit if the
  number of env vars becomes a real deployment annoyance.
- **Dual-button IDP-hint UX** (Part B): worth it for one deployment, or is a single generic button
  acceptable for MONET too?
