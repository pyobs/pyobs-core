# PushNotifier: cap the push payload to FCM's 4 KB limit

Status: implemented, uncommitted (2026-09-23). Written 2026-09-23 after the MONET/S incident in
which FCM rejected pushes with `InvalidArgumentError: Message is too large. The maximum is 4K
(4096 bytes).`

Repos: pyobs-core

## Context

FCM caps a message at 4096 bytes, measured over the *whole serialized message* (token + title +
body + JSON envelope), not the body alone. `PushNotifier._process_log_entry` passes
`LogEvent.message` straight through as the notification body. For a record logged with
`exc_info=True` (any `log.exception(...)`), that message is the formatted record **plus the full
traceback** — easily ≈4 KB — so exactly the alerts that matter most (crashes) can never be
delivered, and the send failure is itself logged at `ERROR`, amplifying the outage. See
`specs/design/push-notification-module.md`, "Confirmed defects (MONET/S incident)".

The other alert source (module-`ERROR` state) is unaffected: `_make_state_callback` produces a
fixed short string, so only log-event bodies are unbounded.

## Decision

The body of a log-event alert becomes **"first non-empty line — last non-empty line"** of the
message, then byte-capped:

- first non-empty line = the human-facing message (e.g. "Failed to send push notification to a
  device.");
- last non-empty line = the exception summary a traceback ends with (`ExceptionType: message`);
- joined with `" — "` **only when the two lines differ** (a single-line message stays itself —
  no `"x — x"` duplication);
- then truncated to a budget that leaves room for the token, title, and JSON envelope.

For a plain non-traceback message the rule degrades gracefully: single-line messages are
unchanged, multi-line messages collapse to first/last.

This also makes `_sender_thread`'s `(kind, title, body)` exact-match dedup work for repeated
identical exceptions — currently defeated by the full traceback (the open question in the design
doc), because traceback line numbers/chains differ between occurrences while the
`Type: message` tail does not.

## Change

All in `pyobs/modules/utils/pushnotifier.py`.

1. Add a module-level constant near `_FIREBASE_CALL_TIMEOUT`:

   ```python
   # FCM caps the whole message at 4096 bytes; reserve room for the token (~160), the title
   # ("{sender}: {level}") and the JSON envelope before budgeting the body.
   _MAX_BODY_BYTES = 3600
   ```

2. Add a module-level helper:

   ```python
   def _notification_body(message: str) -> str:
       """Reduce a log message to a push-notification body that fits FCM's 4 KB message limit.

       A formatted traceback puts the exception on its final line, so for multi-line messages the
       body is "first non-empty line — last non-empty line"; single-line messages pass through.
       The result is truncated to _MAX_BODY_BYTES on a UTF-8 codepoint boundary.
       """
   ```

   Implementation detail: split on `\n`, drop empty/whitespace-only lines, take `first` and
   `last`; `body = f"{first} — {last}" if first != last else first`. Truncate by
   `body.encode("utf-8")[: _MAX_BODY_BYTES].decode("utf-8", errors="ignore")` and append a
   `"…"` marker when a cut happened. (Byte-slice then lossy-decode is what avoids splitting a
   multibyte codepoint.)

3. Use it where the alert is built, so the queued alert **and** the dedup key already hold the
   concise form:

   ```python
   self._enqueue_alert(kind, f"{sender}: {entry.level}", _notification_body(entry.message))
   ```

   Normalizing at enqueue time (not in `_send`) is deliberate: dedup keys on the body.

Title stays as-is (`{sender}: {level}`, bounded by a controlled module name).

## Tests

In `tests/modules/utils/test_pushnotifier.py`, next to the existing `_process_log_entry` tests
(`test_process_log_entry_enqueues_error`, …) which already assert `alert.body` via
`make_pushnotifier()` + a directly-constructed `LogEvent`:

- traceback message → body is `first — last` (feed a `message` shaped like a real formatted
  traceback, ending in `ExceptionType: msg`).
- single-line plain message → unchanged.
- multi-line non-traceback message → `first — last`.
- leading/trailing blank lines → first/last are the *non-empty* lines.
- message over budget → `len(body.encode("utf-8")) <= _MAX_BODY_BYTES`, ends with the `"…"`
  marker, decodes cleanly.
- multibyte character straddling the byte boundary → not split (the lossy-decode keeps valid
  UTF-8).

Optionally one helper-level test each for `_notification_body` directly (it's module-level, easy
to unit-test without a module instance).

## Non-goals / follow-ups — since implemented (2026-09-23)

These were deliberately excluded from the payload-cap change, then landed separately the same day
(see the design doc's "Confirmed defects (MONET/S incident)" section):

- [x] own-log feedback self-skip in `_process_log_entry` (real on `LocalComm`, already guarded on
  XMPP);
- [x] per-token `ERROR` logging aggregation (one log per alert instead of one per token);
- [x] `firebase_admin.initialize_app(options={"httpTimeout": _FIREBASE_HTTP_TIMEOUT})` so a single
  hung request finishes inside the `wait_for` window;
- [x] dead-token pruning on `NotFoundError` (the long-standing open question).

## Checklist

- [x] add `_MAX_BODY_BYTES` + `_notification_body()`
- [x] use it in `_process_log_entry`
- [x] add the tests (8 new; `test_pushnotifier.py` 36 → 44 passing)
- [x] `pytest tests/modules/utils/test_pushnotifier.py`
- [x] `ruff check` + `black` + `pyrefly`
- [x] mark this plan `implemented` and update the design doc's "Confirmed defects" bullet
- [x] follow-ups: self-skip, per-alert logging, `httpTimeout`, pruning (4 more tests; 48 passing)
- [ ] commit (working tree only so far)
