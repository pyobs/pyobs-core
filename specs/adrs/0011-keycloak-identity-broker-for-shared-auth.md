# Use a self-hosted Keycloak alongside odin, as two parallel auth backends

status: superseded 2026-08-19 — this ADR's decision was **not** what shipped. The later
design/plan (`specs/design/shared-auth-keycloak.md`, `specs/plans/2026-08-12-shared-auth-keycloak.md`)
reversed it: "odin" was recognized as our own `observation-portal` deployment (miscast here as an
external LCO dependency), and it is **brokered through Keycloak** rather than run in parallel —
pyobs-archive's direct OAuth2 integration was removed outright (archive commit `01eb06e`,
2026-08-12) and Keycloak is the single issuer. Kept as the historical record of the
considered-and-rejected parallel-backends option.

date: 2026-08-10

Repos: pyobs-core (this doc), pyobs-archive, pyobs-portal

## Context and Problem Statement

Tracks #748. Each pyobs web service currently rolls its own auth, uncoordinated:

- **pyobs-archive** delegates to an external OAuth2 provider ("odin") via a password-grant
  token exchange (`OAuth2Backend`) and bearer-token validation against a `PROFILE_URL`
  (`BearerAuthentication`). odin is archive's connection to LCO (Las Cumbres Observatory) — this
  needs to keep working, since archive must continue to support LCO as a login/identity option,
  not just GWDG and local accounts.
- **pyobs-portal** uses plain DRF `TokenAuthentication`/`SessionAuthentication` against
  its own local Django user table, with no connection to odin or to archive's users.

A user authenticated against one pyobs web service has no way to be recognized by another, and
this gets worse as more services join. Beyond that, the user base isn't limited to people with
institutional (GWDG) accounts — external collaborators without a GWDG identity also need to log
in, which rules out authenticating directly against GWDG's OIDC provider as a complete solution.

## Considered Options

* **Standardize on odin** — reuse archive's existing `OAuth2Backend`/`BearerAuthentication`
  pattern in portal and future services.
* **Authenticate directly against GWDG's OIDC provider** — GWDG runs a standard, working OIDC
  provider (proven via a separate GWDG-affiliated Django project, `labcourse`, which integrates
  it through `authlib`'s Django OIDC client: discovery via `server_metadata_url`, authorization
  code flow, userinfo endpoint, RP-initiated logout via `end_session_endpoint`).
* **Self-hosted Keycloak, run alongside odin as a separate backend** — run our own Keycloak
  realm, configure GWDG OIDC as a federated Identity Provider inside it (Keycloak's "Identity
  Brokering" with a "First Login Flow" to auto-provision local accounts on first GWDG login),
  and also allow local Keycloak accounts for people with no GWDG identity. odin is left
  untouched as archive's existing, independent LCO auth backend — not brokered through
  Keycloak. A user authenticates via *either* odin (LCO) *or* Keycloak (GWDG/local), never both
  at once; which backend(s) a given service enables is a `settings.py` choice
  (`DEFAULT_AUTHENTICATION_CLASSES`, DRF already supports a list tried in order) — odin-only,
  Keycloak-only, or both, per deployment.

## Decision Outcome

Chosen option: self-hosted Keycloak run alongside odin as a second, independent auth backend —
not a broker that odin sits behind. Keycloak will be deployed at `auth.monet.uni-goettingen.de`.

Authenticating directly against GWDG (option 2) was rejected on its own because it structurally
cannot serve the external-collaborator case — those users have no GWDG account to authenticate
with, and GWDG's provider has no facility for us to add accounts to it. Standardizing on odin as
the *sole* identity source (option 1) was rejected because it doesn't cover GWDG-account users
either, and it uses OAuth2 password-grant (credentials pass through the client) rather than a
standard authorization-code flow — a weaker posture than what GWDG's OIDC and Keycloak both
support natively. odin itself isn't going away: it's archive's existing connection to LCO, and
that needs to keep working exactly as it does today.

Rather than brokering odin through Keycloak (which would mean shimming odin's password-grant
flow into something Keycloak can federate — real integration risk, since Keycloak's identity
brokering expects OIDC/SAML-shaped upstream providers, not password-grant), odin and Keycloak
run as two separate, parallel auth backends. Keycloak covers GWDG-account users (via federated
GWDG OIDC) and external users with no GWDG or LCO identity (via local Keycloak accounts); odin
continues to cover LCO users exactly as it does now, untouched. Which backend(s) are active is a
per-deployment `settings.py` choice, not hardcoded: `DEFAULT_AUTHENTICATION_CLASSES` (DRF already
supports a list, tried in order) picks any combination of `OAuth2Backend`/`BearerAuthentication`
(odin) and the new Keycloak/OIDC backend. A deployment that only ever sees LCO users can run
odin-only; one that only serves GWDG/external users can run Keycloak-only; archive itself likely
runs both. This is additive configuration, not a rewrite of archive's existing odin integration.
A user is either an odin/LCO identity or a Keycloak identity; there's no merged/linked-account
concept between the two, and none is needed since they're disjoint user populations today.

Keycloak itself is off-the-shelf — no custom identity-provider code. GWDG federation is realm
configuration (registering GWDG as an Identity Provider in the Keycloak admin console), not
code. The only code we write is the client side, once per service: an `authlib` OIDC client
pointed at our Keycloak realm's discovery URL, same shape as `labcourse`'s `openid/` app
(`login`/`authorize`/`logout` views wrapping `authlib.integrations.django_client.OAuth`).
`labcourse`'s `openid/` app and its dev `docker-compose.yml` (Keycloak + Postgres) are a working
reference for both that client integration and for running Keycloak itself — this isn't a
from-scratch build. Keycloak's own operational footprint
at this scale (an institute, plus external collaborators — not internet-scale traffic) is modest;
Keycloak's HA sizing guide targets much larger deployments than this.

This ADR covers user-facing SSO only. Service-to-service auth (e.g. Mastermind calling
portal's API) is a separate concern — likely a Keycloak client-credentials grant per
service, in the same realm — and is left for separate design work rather than folded in here.

Access isn't role-gated by GWDG affiliation: any valid GWDG account is treated as equally
trusted at the identity layer, and every new account (GWDG-federated or locally registered) is
approved manually regardless of source. Requested scopes are therefore just
`openid profile email`, keyed on the stable `sub`/`uid` claim (not email, which can change).
GWDG-specific claims like `org`/`goeId` aren't needed since no authorization decision depends on
institutional affiliation. Because activation is manual, Keycloak's "First Login Flow" must
create newly-federated accounts inactive (e.g. Django's `is_active=False`) rather than
auto-activating on first GWDG login — the default auto-provisioning behavior would otherwise let
any GWDG account holder in before we've reviewed them.

### Consequences

* Good, because external collaborators without a GWDG or LCO account get a real login path,
  which no option relying solely on GWDG's or odin's own provider could offer
* Good, because LCO users keep working via odin completely unchanged — this is additive to
  archive's current auth, not a migration or rewrite of the existing integration
* Good, because avoiding brokering odin through Keycloak sidesteps the integration risk of
  shimming a password-grant-only provider into Keycloak's OIDC/SAML-shaped brokering model
* Good, because GWDG-account users and external users get one shared identity across services
  (Keycloak), using a standard protocol (OIDC via `authlib` on the Django side)
* Good, because there's already a working reference implementation to copy from (`labcourse`),
  for both the client integration and the Keycloak deployment itself
* Neutral, because we now operate a new stateful service (Keycloak + its Postgres backing store)
  — modest resource cost at this scale, but real ongoing burden: upgrades, backups, uptime
* Bad, because identity stays split into two disjoint populations (odin/LCO vs.
  Keycloak/GWDG+external) rather than one unified identity — a person with both an LCO and a
  GWDG account gets two unrelated logins to the same service, not one
* Bad, because service-to-service auth is explicitly out of scope here and remains an open
  problem — a second design decision, not automatically solved by standing up Keycloak
