# `BaseVideo`: shared-token auth with a browser login page

Status: implemented (see `specs/plans/2026-08-21-basevideo-http-token-auth.md` for the landing
checklist)

Repos: pyobs-core (this doc, implementation), pyobs-gui (consumer change)

## Problem

`BaseVideo`'s built-in HTTP server (`pyobs/modules/camera/basevideo.py`) serves four
content endpoints — `/` (index page with embedded MJPEG), `/video.mjpg` (MJPEG stream),
`/video.raw` (raw frame stream), `/{filename}` (cached FITS from `grab_data()`) — plus
`/ping`. Like `HttpFileCache` before the `2026-08-04-httpfilecache-cors-token-auth` plan,
none of them check any credentials: anyone who can reach the port can watch the live view
or pull data. `HttpFileCache` closed that gap with a shared `token` checked as
`Authorization: Bearer <token>`; `BaseVideo` has the same shape and should get the same
protection.

The catch is the consumer mix. `BaseVideo` is consumed by two very different clients:

- **Machine clients** — `pyobs.vfs.HttpFile` (already sends `Authorization: Bearer <token>`
  on GET/POST and handles `401`; `pyobs/vfs/httpfile.py:50,90,165`) and pyobs-gui's
  `VideoWidget` (opens the MJPEG URL as an `HttpFile` just to get its URL, then streams over
  a raw `QTcpSocket`/`QSslSocket` with a hand-written GET that currently sends **no** auth;
  `pyobs_gui/videowidget.py:135-161,206-208`).
- **Browsers** — the index page (`INDEX_HTML`, `basevideo.py:28-40`) embeds the stream as
  `<img src="video.mjpg">`. Browsers cannot attach an `Authorization` header to an `<img>`
  request, so header-only auth would break the built-in page — which is exactly why the
  HttpFileCache plan explicitly left `BaseVideo` out of scope (its "Explicitly out of
  scope" note: "browsers can't attach custom headers to `<img src>`").

So the design question is how to give browsers a way to authenticate without a
token-in-URL and without rewriting the page into a JS application.

## Constraint

- One shared static secret per module instance, configured in its module YAML — same shape
  as `HttpFileCache.token`. No user accounts, no per-client revocation.
- Machine clients keep working unchanged (Bearer header): no changes to `HttpFile`'s
  behavior, to VFS config, or to the raw-stream consumer.
- The browser path must work with the existing zero-JS index page.

## Proposed change

`BaseVideo` gains a `token: str | None = None` constructor parameter. When `None` (the
default), everything behaves exactly as today — fully opt-in, backward compatible. When
set:

- all four content endpoints require **either** a valid `Authorization: Bearer <token>`
  header **or** a valid session cookie;
- `/ping` stays open (bare liveness check, mirrors `HttpFileCache`);
- a minimal login page at `/login` (GET form + POST verify) issues the cookie; `/logout`
  clears it.

### 1. Where the check runs

A `_check_auth(request)` helper — the exact same contract as `HttpFileCache._check_auth`
(`httpfilecache.py:82-93`): no-op when `self._token is None`, otherwise raises
`web.HTTPUnauthorized` unless a valid Bearer header or a valid session cookie is present.
It always raises the same exception type, regardless of caller — it does not know which
handler called it.

`video_handler`, `raw_handler`, and `image_handler` call it directly at the top and let
the `HTTPUnauthorized` propagate: a clean `401`, just like `HttpFileCache` (and
`VideoWidget`'s stream parser then simply shows nothing, which is the same failure mode
as an unreachable camera). `web_handler` is the one exception: a browser landing on `/`
should be taken to the login form, not shown a bare 401. It wraps the call itself:

```python
try:
    self._check_auth(request)
except web.HTTPUnauthorized:
    raise web.HTTPSeeOther("/login")
```

Machine clients never GET `/`, so this translation never affects them.

Placement matters twice in the streaming handlers:

- **Before `response.prepare(request)`** (`video_handler` `basevideo.py:234`,
  `raw_handler` `:283`) — a `401` cannot be raised after the stream has started. Since
  `_check_auth` runs at the top of the handler, this is automatic.
- **Before `activate_camera()`** in `raw_handler` (`:278`) — an unauthenticated request
  must not wake the camera hardware.

### 2. The cookie

Stateless and HMAC-signed — the cookie value is **not** the raw token:

```
value = "{expiry_ts}.{hex}"    where hex = HMAC-SHA256(key=token, msg=str(expiry_ts))
```

Verification parses the expiry, rejects when `expiry_ts < now`, recomputes the HMAC and
compares with `hmac.compare_digest`. Properties that fall out of this design:

- No server-side session state — nothing to add to `web.Application`, nothing lost on
  module restart.
- A leaked cookie does **not** reveal the master secret.
- Cookies expire (lifetime constant, default 24 h), so a stale cookie isn't a permanent
  pass.
- Rotating the module's `token` invalidates every outstanding cookie at once (all
  signatures break) — a poor-man's revocation with zero extra machinery.

Set with `response.set_cookie(..., max_age=lifetime, path="/", httponly=True,
samesite="Lax")`. `path="/"` so the `<img>` and both stream requests carry it;
`httponly` — the page has no JS, but belt-and-braces; `samesite="Lax"` as cheap CSRF
hygiene on the login POST. `secure` is deliberately **not** set by default: `BaseVideo`
serves plain HTTP on the LAN, and a `Secure` cookie would never be sent, breaking the
login. Behind a TLS-terminating reverse proxy `secure=True` becomes correct — see Open
questions.

### 3. Login/logout flow

- `GET /login` — a tiny HTML form (single password input, POST to `/login`), served
  unauthenticated. This is the point of a login page: it is the bootstrap that the
  `<img>`-can't-send-headers problem requires, without putting the token in any URL.
- `POST /login` — read the form field, compare with `self._token` via
  `hmac.compare_digest`. Success: `set_cookie(...)` + `303 See Other → /` — the redirect
  makes the cookie stick before the browser loads the page and its `<img>`. Failure:
  `401` (optionally after a small `asyncio.sleep` to slow brute force; constant-time
  compare either way).
- `GET /logout` — `del_cookie(...)` + `303 → /login`.

Routes are registered only when `self._token is not None`, mirroring how
`/video.mjpg`/`/video.raw` are gated on `video_path`/`raw_path` today
(`basevideo.py:158-161`).

### 4. Machine clients: one small pyobs-gui change

`HttpFile` needs no change — it already sends the Bearer header. `VideoWidget` is the
exception: its raw-socket GET (`pyobs_gui/videowidget.py:206-208`) currently sends no
auth at all, so once `BaseVideo` enforces a token the live view dies with a `401` that
the MJPEG parser never surfaces (it strips the response headers and then finds no
`--jpgboundary`). Fix, entirely inside the widget:

- in `_init`, after the `HttpFile` type check (`:140`), store the Authorization header
  from the `HttpFile` instance the widget already opens: `self._auth_header =
  video_file.headers.get("Authorization")`;
- in `_showEvent`, append `Authorization: <value>\r\n` to the raw GET when set.

To avoid the GUI reaching into the private `_headers` attribute (`httpfile.py:50`),
`HttpFile` gains a public read-only `headers` property. The cookie/login machinery is
never used by machine clients — the header path is strictly simpler for them.

### 5. What stays unauthenticated

`/ping` (liveness), `/login` (the form), `/logout` (idempotent). Everything that exposes
data or touches hardware requires header-or-cookie.

## Alternatives considered

- **Bearer-header-only (no browser path).** Rejected — the built-in index page is a
  documented feature; breaking it for the common LAN case would force a JS rewrite on
  everyone, not just token users.
- **Query-string token fallback** (`/video.mjpg?token=...`). Rejected — the token lands
  in reverse-proxy/access logs. (The browser-history worry is mostly moot for an `<img>`
  asset — history records the page URL, not image URLs — but logs are real, and the
  pattern of secrets-in-URLs would rub off on every other consumer.)
- **localStorage + JS `fetch()` viewer.** Rejected — localStorage is never sent
  automatically; keeping header auth would require rewriting the page as a JS
  application (fetch + `multipart/x-mixed-replace` parser + canvas blitting), and
  localStorage is the XSS-readable store. A cookie is both simpler (zero JS) and more
  robust (`HttpOnly`).
- **HTTP Basic auth (browser-native prompt).** Rejected — it would work for `<img>` via
  the browser's `401` challenge, but it conflicts with the Bearer scheme the machine
  clients already use (the server would have to accept two schemes), gives an
  unbranded/ugly prompt, and has no logout story. The login page is comparable code with
  a better UX.
- **Per-user accounts / Keycloak.** Rejected for this — overkill for a shared webcam
  secret; the fleet-level answer already exists as `specs/design/shared-auth-keycloak.md`
  and is a different feature.

## Open questions

- Cookie lifetime: fixed 24 h constant for v1, or a constructor param? (Proposal:
  constant; revisit if a site needs it configurable.)
- Sliding renewal (re-issue the cookie on each authenticated request so an active viewer
  never logs out): nice-to-have, deferred.
- `secure` cookie flag behind a TLS-terminating reverse proxy: no clean auto-detect
  exists; proposal is to document the knob and add a `cookie_secure` param only if a
  site actually needs it.
- CORS: `BaseVideo` endpoints carry no CORS headers today. `<img>` embedding doesn't
  need them, and no in-tree web app fetches `BaseVideo` directly (browser-side image
  fetching goes through `HttpFileCache`, which got its own `OPTIONS` preflight in the
  HttpFileCache plan). If a JS browser consumer of `BaseVideo` appears later, mirror
  that `OPTIONS` handler — out of scope here.
