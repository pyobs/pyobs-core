# Plan: One-click IdP login via `kc_idp_hint` (dual login buttons)

Follow-up to `specs/plans/2026-08-12-shared-auth-keycloak.md` (closed 2026-08-19) and the design it
implements (`specs/design/shared-auth-keycloak.md`). No GitHub issue filed yet — this came out of a
discussion of the login UX; file one before implementation if the repo convention wants it.

Status: implemented, closed. Verified against code 2026-08-23: `IDP_HINT`/`kc_idp_hint` support in
`pyobs_auth/settings.py`, `client.py`, `views.py` (pyobs-auth `2.0.0.dev9`, full test suite green —
43 passed); dual-button `registration/login.html` (with the `|urlencode` fix) + `IDP_HINT`/
`IDP_LABEL` settings + context-processor keys landed in pyobs-archive, pyobs-robotic-backend, and
pyobs-web-admin, all pinned to `pyobs-auth>=2.0.0.dev9`; design-doc note added to
`specs/design/shared-auth-keycloak.md`. Live-environment items (browser E2E per service, SSO
short-circuit behavior, and setting `KEYCLOAK_IDP_HINT` in production deployments) are operational
and outside what this repo checkout can verify — confirm those separately before relying on the
one-click flow in production.

Repos: pyobs-auth, pyobs-archive, pyobs-robotic-backend, pyobs-web-admin

## Problem

Logging in through Keycloak takes an unnecessary extra click: the app login page's "Log in with
Keycloak" button lands the user on Keycloak's own login/IdP-selection page (local username/password
form + "Login with gwdg" button), and only then on GWDG's SSO page. The middle page exists purely
because the realm offers more than one login route: local Keycloak accounts (external collaborators
without a GWDG identity — the reason direct-GWDG-only auth was rejected in ADR 0011) plus the GWDG
identity provider.

Goal: one click from the app login page straight to the GWDG SSO page, **while keeping the
local-Keycloak-account path reachable** (option D of the discussion, not a forced-single-IdP
replacement).

## Mechanism

Keycloak's authorization endpoint accepts `kc_idp_hint=<idp-alias>`; when present it skips the
login/IdP-selection page and redirects straight to that IdP. Unknown/invalid aliases fall back to
the normal login page, so a misconfigured hint degrades gracefully to today's behavior. The alias is
deployment-specific (whatever the GWDG IdP is registered under in the realm), so it must be a
setting, consistent with the design doc's stance that upstream-IdP wiring is per-deployment
config, not pyobs design. No Keycloak admin changes needed.

## 1. pyobs-auth — `IDP_HINT` support (new release)

- [x] `pyobs_auth/settings.py`: add `idp_hint: str | None = None` to `KeycloakSettings`; read it in
      `get_settings()` from `raw.get("IDP_HINT")`. (The human-readable label for the button is a
      per-service config concern surfaced by the template, so it deliberately does **not** live
      here — see section 2.)
- [x] `pyobs_auth/client.py`: `KeycloakClient.start_authorization(*, idp_hint: str | None = None,
      redirect_uri=None)` — add `"kc_idp_hint": idp_hint` to the params dict when truthy. Backward
      compatible: new optional kwarg, existing callers unaffected.
- [x] `pyobs_auth/views.py` `LoginView`: the hint comes from the `?idp_hint=` query param with
      settings as the default, giving the template three distinct cases:
      - `?idp_hint=` absent → use `settings.idp_hint` (configured default, e.g. `gwdg`) — the fast
        path;
      - `?idp_hint=` present but empty → **no** hint — the local-Keycloak-account path;
      - `?idp_hint=gwdg` → that specific hint (future-proofing for multiple IdPs).
      Implemented as `value = request.GET.get("idp_hint"); if value is None: value =
      settings.idp_hint`, then `start_authorization(idp_hint=value or None)`. Preserve the existing
      `next` handling unchanged.
- [x] Tests:
      - `tests/test_client.py`: `start_authorization(idp_hint="gwdg")` produces a URL containing
        `kc_idp_hint=gwdg`; without the hint the param is absent.
      - `tests/test_views.py`: login view with a configured hint redirects to a URL containing
        `kc_idp_hint`; `?idp_hint=` suppresses it (no `kc_idp_hint` in the redirect URL); `next` is
        still honored on both.
      - Use `override_settings(PYOBS_AUTH={..., "IDP_HINT": ...})` per test rather than editing the
        shared `tests/django_settings.py` dict (which has no `IDP_HINT`), so the "absent → settings
        default" and "present-but-empty → no hint" cases stay independently testable.
- [x] `README.md`: document `IDP_HINT` in the `PYOBS_AUTH` example and the `?idp_hint=` override on
      the login view.
- [x] Release the next dev version (currently `2.0.0.dev7`; bump per `do-python-release`
      conventions) and update the `pyobs-auth>=...` pins in the consuming services (section 2).

## 2. Consuming services — dual buttons on the login page

Same change in each of pyobs-archive, pyobs-robotic-backend, pyobs-web-admin (all three share the
same `registration/login.html` + `keycloak_login_enabled` context-processor pattern):

- [x] `settings.py` `PYOBS_AUTH` dict: add `"IDP_HINT"` and `"IDP_LABEL"`.
      - archive/robotic-backend (env-driven): `os.getenv("KEYCLOAK_IDP_HINT", "")`,
        `os.getenv("KEYCLOAK_IDP_LABEL", "")` (see `pyobs_archive/settings.py:205`,
        `pyobs_robotic_backend/settings.py:163`).
      - web-admin (static dict, `pyobs_web_admin/settings.py:89`): `"IDP_HINT": ""`,
        `"IDP_LABEL": ""`, configured directly rather than via env, matching how the rest of its
        `PYOBS_AUTH` block works.
- [x] Context processor: alongside `keycloak_login_enabled`, expose `keycloak_idp_hint` and
      `keycloak_idp_label` read from `settings.PYOBS_AUTH` (`pyobs_archive/context_processors.py`,
      `pyobs_robotic_backend/frontend/context_processors.py`,
      `pyobs_web_admin/modules/context_processors.py`). In archive/robotic-backend these go in the
      dedicated `keycloak()` processor; in web-admin `keycloak_login_enabled` is one key of the
      `sidebar_modules()` processor (`modules/context_processors.py:64`), so the new keys go into
      that same return dict (or extract a dedicated processor for symmetry).
- [x] `templates/registration/login.html`: three states, all preserving `next` on every link
      (`pyobs_auth:login` is the generic entry; the IdP button keeps pointing at it, since the hint
      is a server-side default — no per-service Keycloak URL construction needed). The hinted
      branch is additionally gated on `keycloak_login_enabled`, so an operator setting `IDP_HINT`
      without `SERVER_URL` (Keycloak disabled) degrades to no Keycloak buttons at all rather than
      rendering links that would 500:

      ```html
      {% if keycloak_idp_hint and keycloak_login_enabled %}
      <a href="{% url 'pyobs_auth:login' %}?next={{ next|urlencode }}" class="btn ...">
          Log in with {{ keycloak_idp_label|default:"Keycloak" }}</a>
      <a href="{% url 'pyobs_auth:login' %}?idp_hint=&next={{ next|urlencode }}" class="btn ...">
          Log in with local Keycloak account</a>
      {% elif keycloak_login_enabled %}
      <a href="{% url 'pyobs_auth:login' %}?next={{ next|urlencode }}" class="btn ...">
          Log in with Keycloak</a>
      {% endif %}
      ```

      Styling is per-service cosmetic; suggestion: make the IdP button the visually primary option
      of the two, and keep the local-account one outline. The existing local username/password
      "Sign in" form stays as-is (Keycloak remains additive next to it, per the 2026-08-12 plan).
      While touching each template, also add `|urlencode` to that existing single-button
      `?next={{ next }}` line (currently unescaped in all three:
      `templates/registration/login.html:53` (archive),
      `pyobs_robotic_backend/frontend/templates/registration/login.html:53`,
      `templates/registration/login.html:53` (web-admin)) — a pre-existing issue, not caused by
      this change, but worth fixing now that the file's already open rather than propagating it into
      the two new links as well.
- [x] Docs: `.env.example` (archive: add `KEYCLOAK_IDP_HINT`/`KEYCLOAK_IDP_LABEL` next to the
      existing `KEYCLOAK_*` block; robotic-backend/web-admin: wherever their `PYOBS_AUTH` is
      documented) and README login-section mention.

## 3. Docs (pyobs-core)

- [x] `specs/design/shared-auth-keycloak.md`: short note (a few lines) under the existing status
      block: the `kc_idp_hint` mechanism, the dual-button pattern ("log in with <hinted IdP>" vs.
      "local Keycloak account"), and that the alias/label are per-deployment `PYOBS_AUTH` config —
      an instance of the design's "upstream wiring is operational config" principle.
- [x] `specs/plans/index.md`: this plan entry (done — see entry below).

## 4. Verification

- [x] pyobs-auth full test suite green (client + views + existing) — 43 passed, 2026-08-23.
- [ ] Browser end-to-end per service, hint set: login page shows the two buttons; the IdP button
      lands directly on GWDG's SSO page (no Keycloak selection page); the local-account button
      lands on Keycloak's normal login page; both complete the callback → `resolve_user` → session.
      **Not verified — needs a live Keycloak/GWDG environment, outside what a repo checkout can
      confirm.**
- [ ] Regression: hint unset (or empty env) → the login page renders exactly the current single
      "Log in with Keycloak" button and behavior. **Not verified live**, though the template's
      `{% elif keycloak_login_enabled %}` branch (unchanged from before this plan) covers it by
      construction.
- [ ] Check behavior with an existing Keycloak SSO session: confirm the hinted flow doesn't force a
      fresh GWDG round-trip every time (SSO short-circuit) — note the observed behavior in the
      plan on closure. **Not verified — needs a live session.**
- [ ] Deployments: set `KEYCLOAK_IDP_HINT=gwdg` (+ `KEYCLOAK_IDP_LABEL` as desired). No Keycloak
      admin-console changes. **Not verified — operational/deployment-side, not visible from the
      repos.**

## 5. Not in this plan

- observation-portal brokering behind Keycloak (section 0 of the 2026-08-12 plan, tracked in
  #748) — unchanged; when it lands, a service with users on both IdPs can either add a second
  hinted button or rely on the local/no-hint path to reach Keycloak's selection page.
- Removing or de-emphasizing the local-Keycloak-account path (external collaborators) — rejected:
  ADR 0011 exists precisely to serve them.
- Keycloak login-theme changes (auto-redirect, hiding the local form) — rejected in favor of the
  per-request hint, which keeps the fallback.
- Direct OIDC against GWDG, bypassing Keycloak — rejected in ADR 0011.
- Sanitizing `next` beyond the `|urlencode` template fix — pre-existing and out of scope:
  pyobs-auth's `LoginView`→`CallbackView` round-trip stores and redirects to the raw GET `next`
  without a host check (open-redirect-ish on the Keycloak path), and robotic-backend/web-admin's
  custom login views redirect POST `next` unsanitized (archive's is sanitized by Django's built-in
  `LoginView`). Not caused by this change, but acknowledged here since it adds more URLs that carry
  `next`.
