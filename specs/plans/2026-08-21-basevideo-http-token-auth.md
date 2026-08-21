# Plan: shared-token auth + browser login for `BaseVideo`

Status: proposed

Design: `specs/design/basevideo-http-auth.md`

Repos: pyobs-core (all server-side implementation + `HttpFile` accessor), pyobs-gui
(one consumer change in `VideoWidget`)

## Problem

`BaseVideo`'s HTTP server (`pyobs/modules/camera/basevideo.py`) is unauthenticated on
every content endpoint — the same gap `HttpFileCache` closed with a shared token in
`2026-08-04-httpfilecache-cors-token-auth.md`, which explicitly left `BaseVideo` out of
scope because browsers can't attach an `Authorization` header to `<img src="video.mjpg">`.
Design doc above covers the full reasoning; this is the checklist.

The consumer split that drives the design: machine clients (`HttpFile`, pyobs-gui's
`VideoWidget`) can and should use `Authorization: Bearer <token>`; browsers need a login
page + cookie for the `<img>`-based index page to keep working.

## Todo

### pyobs-core — `pyobs/modules/camera/basevideo.py`

- [ ] Add `token: str | None = None` to `__init__` (`basevideo.py:78-94`), store
      `self._token`. Docstring entry mirroring `HttpFileCache`'s: "Shared secret required
      in the `Authorization: Bearer <token>` header (or a login-page cookie) for stream
      and data access. If `None` (default), no auth is enforced."
- [ ] Add cookie constants (name e.g. `pyobs_video_session`, lifetime 24 h) and helpers:
      `_make_session_value() -> str` (expiry + HMAC-SHA256 over `str(expiry)` keyed with
      the token), `_check_bearer(request) -> bool`, `_check_cookie(request) -> bool`,
      `_check_auth(request)` (raises `HTTPUnauthorized` unless either passes; no-op when
      `self._token is None`). Constant-time compares via `hmac.compare_digest`
      everywhere — same as `HttpFileCache._check_auth` (`httpfilecache.py:82-93`).
- [ ] Register `/login` (GET + POST) and `/logout` (GET) routes **only when
      `self._token is not None`**, alongside the existing conditional registration of
      `/video.mjpg`/`/video.raw` (`basevideo.py:158-161`).
- [ ] Implement the three handlers:
      - `login_handler` — GET: minimal HTML form (one password input, POST to `/login`),
        served unauthenticated.
      - `login_post_handler` — POST: `await request.post()`, compare form field with
        token via `compare_digest`. Success: `set_cookie(name, value,
        max_age=lifetime, path="/", httponly=True, samesite="Lax")` + `303 See Other
        → /`. Failure: `401` (optional small `asyncio.sleep` delay against brute force).
      - `logout_handler` — GET: `del_cookie(name, path="/")` + `303 → /login`.
- [ ] Call `_check_auth(request)` at the top of `web_handler` (`:199`),
      `video_handler` (`:221`), `raw_handler` (`:267`), and `image_handler` (`:362`).
      `web_handler` failure raises `web.HTTPSeeOther("/login")`; the other three raise
      `web.HTTPUnauthorized()`.
- [ ] Confirm ordering in the streaming handlers: auth check runs before
      `response.prepare(request)` (`:234`, `:283`) and before `activate_camera()` in
      `raw_handler` (`:278`) — an unauthenticated request must not wake the camera.
- [ ] `INDEX_HTML` (`:28-40`) unchanged — the cookie rides the same-origin `<img>`
      request automatically.
- [ ] Update the class docstring (webcam VFS note) with a sentence on token/login.

### pyobs-core — `pyobs/vfs/httpfile.py`

- [ ] Add a public read-only `headers` property returning `self._headers` (`:50`), so
      pyobs-gui doesn't reach into the private attribute. (No behavior change; existing
      callers unaffected.)

### pyobs-gui — `pyobs_gui/videowidget.py`

- [ ] In `_init`, after the `HttpFile` type check (`:140`), store
      `self._auth_header = video_file.headers.get("Authorization")` (None when the VFS
      root configures no token).
- [ ] In `_showEvent`, append `Authorization: <value>\r\n` to the raw-socket GET when
      `self._auth_header` is set (`:206-208`). When unset, bytes written are unchanged.

## Testing

### pyobs-core — `tests/modules/camera/test_basevideo.py`

Existing unit style: direct handler invocation, mocked
`pyobs.modules.camera.basevideo.web.StreamResponse`, `_route_paths()` helper
(`test_basevideo.py:509`). No aiohttp TestClient in the repo — keep it that way.

- [ ] `token=None` (default): `/login`/`/logout` not registered; all handlers accept
      unauthenticated requests — existing tests unchanged.
- [ ] `token` set: `_route_paths` includes `/login`; `/` unauthenticated → `303` to
      `/login`; `/video.mjpg`, `/video.raw`, `/{filename}` unauthenticated → `401`;
      `/ping` → `200`.
- [ ] Bearer header: correct `Authorization: Bearer <token>` → `200`; wrong token →
      `401`.
- [ ] Login POST: correct token → response carries `Set-Cookie` + `303`; wrong token →
      `401`.
- [ ] Cookie: valid cookie → `200` on `/` and stream endpoints; tampered cookie →
      `401`; expired cookie (expiry in the past) → `401`; after `/logout` → `401`.
- [ ] `raw_handler` with a bad/missing credential raises `401` **without** calling
      `activate_camera()` (mock it, assert not called).
- [ ] Streaming handlers: `401` raised before `StreamResponse.prepare()` is reached.

### pyobs-gui — `tests/test_videowidget.py`

- [ ] With an `HttpFile` carrying a token, the bytes written to the (mocked) socket
      include `Authorization: Bearer <token>`.
- [ ] Without a token, the written GET bytes are unchanged from today.

## Explicitly out of scope

- CORS/preflight for `BaseVideo` endpoints (see design doc's Open questions — `<img>`
  doesn't need it and no in-tree web app fetches BaseVideo directly).
- Per-user accounts / Keycloak (design doc; fleet answer is
  `specs/design/shared-auth-keycloak.md`).
- Other unauthenticated HTTP servers (`Kiosk`, `HttpServer` image processor) — same
  reasoning as the HttpFileCache plan left them alone.
- Browser page features beyond the login form (no JS viewer, no player controls).

## Consequences

- **Good:** webcam live view, raw stream, and cached FITS are no longer readable by
  anyone who can reach the port, once a token is configured.
- **Good:** fully opt-in (`token=None` default preserves today's behavior for existing
  deployments); `HttpFile`/VFS config unchanged; the GUI change is one header line on a
  request that today sends no auth.
- **Neutral:** a stolen cookie grants viewing until it expires; rotating the module token
  invalidates all cookies at once (HMAC signatures break) — an implicit revoke.
- **Neutral:** the login page is plaintext over HTTP unless behind TLS — the same
  exposure as the Bearer header; real protection of the stream implies TLS termination
  in front (already the pattern for other pyobs web endpoints).
- **Bad:** with `token` set, the GUI live view breaks until the pyobs-gui change lands —
  land both halves together, and note the coupling in the PR description.

## Open questions

Carried from the design doc: cookie lifetime constant vs param (proposal: 24 h
constant); sliding renewal (deferred); `secure` flag behind TLS (document, add param
only when a site needs it).
