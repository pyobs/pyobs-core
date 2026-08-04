# Plan: CORS + token auth for `HttpFileCache`

Status: draft
Repos: pyobs-core (all implementation here), pyobs-web-client (config-only follow-up: must supply
a `token` and send it as `Authorization: Bearer <token>` — no code change expected there beyond
that, tracked as a note in Consequences, not a task of this plan)

Closes #725.

## Problem

`pyobs-web-client`'s Camera page phase 2 fetches `IData.grab_data()`'s VFS path directly via
browser `fetch()`. `HttpFileCache.download_handler` (`pyobs/modules/utils/httpfilecache.py:81`)
returns a plain `aiohttp.web.Response` with no CORS headers, so the browser blocks the
cross-origin read:

```
Access to fetch at 'http://localhost:37075/<file>' from origin 'http://localhost:5173'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.
```

Investigating the fix surfaced a second, pre-existing gap: `HttpFileCache` has no server-side
auth at all. `download_handler`, `upload_handler`, and `ping_handler` accept any request
unconditionally. The VFS client, `pyobs.vfs.HttpFile`, *does* send `aiohttp.BasicAuth` credentials
when `username`/`password` are configured (`pyobs/vfs/httpfile.py:53-54,94,168`) and even handles
a `401` response — but that plumbing is dead code against this server, since nothing on the server
side ever reads the `Authorization` header. Confirmed via grep that no current caller configures
`username`/`password` on `HttpFile` (only `tests/vfs/test_httpfile.py`, which doesn't either), so
nothing today actually depends on Basic auth working.

Adding a bare `Access-Control-Allow-Origin: *` without fixing this would make the already-open
server easier to reach from any browser tab, not just `pyobs-web-client`'s — worth closing both
gaps together rather than shipping CORS on top of no auth.

**Explicitly out of scope:** `BaseVideo` (`modules/camera/basevideo.py`), `Kiosk`
(`modules/utils/kiosk.py`), and the `HttpServer` image processor
(`images/processors/image/httpserver.py`) have the same "no auth" shape but serve images for
direct `<img>`/`<video>`/MJPEG embedding, not JS `fetch()`. A required `Authorization` header
would break that (browsers can't attach custom headers to `<img src>`). `Kiosk` already binds
`localhost` only; `HttpServer` defaults to `localhost` and its docstring already documents "no
authentication... do not expose on untrusted networks" as an accepted tradeoff. Leaving these
three alone; token auth here is scoped to `HttpFileCache` (JS-fetched) and its `HttpFile` client
only.

## Decision

- Add a `token: str | None = None` constructor parameter to `HttpFileCache`. When set, requests to
  `download_handler` and `upload_handler` (write access) must carry a matching
  `Authorization: Bearer <token>` header or get `401`. `ping_handler` stays unauthenticated (a
  bare liveness check, no data exposure). When `token` is `None` (the default), behavior is
  unchanged from today — unauthenticated — so this stays opt-in and backward compatible for
  existing LAN-only deployments that don't set one.
- Add `Access-Control-Allow-Origin: *` to `download_handler` and `ping_handler` responses.
- Add an `OPTIONS` route + handler for the `/{filename}` path. This is required, not optional,
  once `download_handler` starts checking `Authorization`: a GET with a custom `Authorization`
  header is no longer a CORS "simple request," so browsers send a preflight `OPTIONS` first and
  will block the real request if it doesn't get a `200` with the right `Access-Control-Allow-*`
  headers back.
- Replace `HttpFile`'s Basic-auth params (`username`/`password`) with a single `token: str | None`
  param, sent as `Authorization: Bearer <token>`. Full replacement, not additive — confirmed above
  that nothing depends on the old params working.
- Static shared secret (one token per `HttpFileCache` instance, configured in its module YAML),
  not per-client/rotatable tokens. Matches the single-shared-password shape Basic auth already had;
  a token allowlist is more machinery than the current single-consumer (`pyobs-web-client`) use
  case justifies. Can be revisited if a second independent client needs separate revocation later.
- Token compared with `hmac.compare_digest`, not `==`, to avoid a timing side-channel.

Rejected: restricting `Access-Control-Allow-Origin` to a specific configured origin instead of
`*`. The `Authorization` header is sent explicitly by client code (not ambient like cookies/TLS
client certs), so `fetch()` doesn't need `credentials: 'include'` mode here — per the Fetch spec,
`*` is valid in that case. A wildcard is simpler and there's exactly one consumer today; can
tighten to an explicit origin list later if that changes.

## Implementation

### 1. `HttpFileCache` — token check + CORS + preflight

**File:** `pyobs/modules/utils/httpfilecache.py`

```python
import hmac

def __init__(self, port: int = 37075, cache_size: int = 25, max_file_size: int = 100,
             token: str | None = None, **kwargs: Any):
    ...
    self._token = token
    ...
    self._app.add_routes([
        web.get("/ping", self.ping_handler),
        web.get("/{filename}", self.download_handler),
        web.options("/{filename}", self.options_handler),
        web.post("/", self.upload_handler),
    ])

def _check_auth(self, request: web.Request) -> None:
    """Raises HTTPUnauthorized if a token is configured and the request doesn't carry it."""
    if self._token is None:
        return
    header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not header.startswith(prefix) or not hmac.compare_digest(header[len(prefix):], self._token):
        raise web.HTTPUnauthorized()

async def options_handler(self, request: web.Request) -> web.Response:
    """Answers the CORS preflight for /{filename}."""
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "Authorization",
    })

async def download_handler(self, request: web.Request) -> web.Response:
    self._check_auth(request)
    filename = request.match_info["filename"]
    if filename not in self._cache:
        raise web.HTTPNotFound()
    data = self._cache[filename]
    log.info("Serving file %s.", filename)
    return web.Response(body=data, headers={"Access-Control-Allow-Origin": "*"})

async def upload_handler(self, request: web.Request) -> web.Response:
    self._check_auth(request)
    ... # unchanged below

async def ping_handler(self, request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
```

Docstring for `__init__` gets a `token` arg entry: "Shared secret required in the
`Authorization: Bearer <token>` header for download/upload access. If `None` (default), no auth is
enforced."

### 2. `HttpFile` — send the token instead of Basic auth

**File:** `pyobs/vfs/httpfile.py`

Replace:

```python
username: str | None = None,
password: str | None = None,
...
self._auth = None
if username is not None and password is not None:
    self._auth = aiohttp.BasicAuth(username, password)
```

with:

```python
token: str | None = None,
...
self._headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
```

And in `_download`/`_upload`, replace `auth=self._auth` with `headers=self._headers` in the
`session.get`/`session.post` calls. The existing `401` handling (`_download` line ~99, `_upload`
line ~169) needs no change — same status code, different auth scheme underneath.

Update the constructor docstring's `username`/`password` entries to a single `token` entry
matching `HttpFileCache`'s wording.

### 3. Tests

**File:** `tests/vfs/test_httpfile.py` (and add `tests/modules/utils/test_httpfilecache.py` if it
doesn't exist — check first)

- `HttpFileCache` configured with a `token`: request without `Authorization` → `401`; with wrong
  token → `401`; with correct `Bearer <token>` → `200`.
- `HttpFileCache` configured with `token=None` (default): unauthenticated request → `200` (no
  behavior change).
- `download_handler`/`ping_handler` responses carry `Access-Control-Allow-Origin: *`.
- `OPTIONS /{filename}` returns the three CORS headers.
- `HttpFile(..., token=...)` round-trip against a token-protected `HttpFileCache` (write then
  read) — exercises the client's new header-sending path end to end.

## Consequences

- **Good:** Closes #725 — `pyobs-web-client` can fetch cross-origin once it's updated to send a
  configured token.
- **Good:** Closes the latent gap where `HttpFile`'s Basic-auth plumbing implied protection that
  the server never actually enforced.
- **Good:** Fully opt-in server-side (`token=None` default preserves today's behavior for existing
  deployments) — no forced migration for anyone not touching this.
- **Neutral:** `pyobs-web-client` still needs its own follow-up: configure a token, send it as
  `Authorization: Bearer`, and decide where to store it client-side (localStorage vs
  sessionStorage — localStorage is acceptable here since this protects a low-sensitivity LAN image
  cache with a single static shared secret, not user credentials; sessionStorage trades that
  convenience for a smaller XSS exfiltration window). That work lives in the pyobs-web-client repo,
  not tracked further here.
- **Neutral:** `BaseVideo`/`Kiosk`/`HttpServer` remain unauthenticated by design (see Problem) —
  not a regression, just not addressed by this plan.
- **Bad:** Breaking change for any config that already sets `username`/`password` on `HttpFile` —
  confirmed none exist today, but this is not a deprecation path, it's a hard swap.
