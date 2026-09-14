# Plan: Staleness detection + setpoint resend for BROT settle loops

Status: implemented, closed (2026-09-14). Shipped in `pybrotlib`
[1.2.2](https://github.com/BROTLib/pyBROT/releases/tag/v1.2.2) and `pyobs-brot`
[2.0.4](https://github.com/pyobs/pyobs-brot/releases/tag/v2.0.4). See "Resend: verified against the
real PLC code" below — the resend half is confirmed safe but does **not** explain #61's actual
symptom; kept as defense-in-depth, not as the root-cause fix. The genuine drive-fault/following-
error investigation #61 originally asked for is still open, just no longer tracked by that (now
closed) issue.

Repos: pyobs-brot, pybrotlib (`BROTLib/pyBROT`, not on the `pyobs` GitHub org)

Issue: [pyobs/pyobs-brot#61](https://github.com/pyobs/pyobs-brot/issues/61) — `set_offsets_altaz`
times out (120s) repeatedly during autoguiding on MONET South.

## Problem

Every "wait for the mount/dome/roof to reach a target state" loop across `pyobs_brot` follows the
same shape:

```python
while <raw telemetry field comparison>:
    await asyncio.sleep(0.1 or 1)
```

bounded only by the method's outer `@timeout(...)`. Confirmed by reading the code (2026-09-14
session) that this is systemic, not unique to `set_offsets_altaz`:

- `pyobs_brot/brottelescope.py`: `BrotBaseTelescope._wait_for_focus` (used by `set_focus`/
  `set_focus_offset`), `_wait_for_tracking` (used by `_move_radec`), `_move_altaz`, `init`, `park`,
  `stop_motion`; `BrotRaDecTelescope.set_offsets_radec`; `BrotAltAzTelescope.set_offsets_altaz`
- `pyobs_brot/brotdome.py`: `BrotDome.init` (two settle loops), `park` (three settle loops)
- `pyobs_brot/brotroof.py`: `BrotRoof.init`, `park`

None of these loops can distinguish "still genuinely moving/settling" from "the MQTT telemetry
stream stalled and we're reading frozen data" — they just spin until the value crosses threshold
or the blunt outer timeout fires with no diagnostic signal either way. This reproduces exactly the
symptom in #61: three consecutive `set_offsets_altaz` calls hit their 120s timeout in a row during
a MONET South autoguiding run, while earlier, larger offsets in the same run settled fine.

Before the pybrotlib 1.2.1 auto-reconnect fix (pyobs-brot#68, `pyBROT`'s own
`specs/plans/mqtt-reconnect.md`), a dropped MQTT connection mid-loop was *permanent* until the
module restarted —
telemetry would freeze forever, not just stall temporarily. #68 makes a stall recoverable on its
own (auto-reconnect within seconds), but the settle loops still have no way to notice a stall is
happening, or to tell it apart from an actually-stuck mount — they just get a working connection
back eventually and keep spinning on the same blunt timeout.

## Design

**1. `pybrotlib`: staleness primitive on `Transport`**

- Track `last_message_at: float | None` (via `time.monotonic()`), updated whenever a message is
  received in `MQTTTransport.run()`'s message loop.
- Expose `Transport.telemetry_age() -> float | None` (seconds since the last received message,
  `None` if none ever received). Lives on the base `Transport` class (generic concept), even though
  only `MQTTTransport` currently updates it.

**2. `pyobs_brot`: shared `wait_until_settled()` helper**

Standalone function (not a method — `BrotBaseTelescope`/`BrotDome`/`BrotRoof` share no common base),
in a new small module (e.g. `pyobs_brot/_settle.py`):

```python
async def wait_until_settled(
    condition: Callable[[], bool],
    transport: Transport,
    *,
    resend: Callable[[], Awaitable[None]] | None = None,
    resend_interval: float = 20.0,
    stale_after: float = 5.0,
    poll_interval: float = 0.1,
) -> None:
    ...
```

- Loops on `condition()`.
- Each iteration: if `not transport.connected` or `telemetry_age() > stale_after`, raise
  `exc.MoveError("Telemetry stream stalled while waiting to settle.")` — a distinct, immediate
  signal instead of silently spinning to the outer `@timeout`.
- If `resend` is given and `resend_interval` has elapsed since the last resend, call it again
  (re-publishing the same setpoint — see below for why this is safe only for some commands).
- The method's existing outer `@timeout(...)` stays as-is: it's still the real backstop for "mount
  genuinely can't reach target" (drive fault, mechanical issue); this helper only closes the
  "telemetry stream stalled" blind spot and adds a cheap mitigation for "command silently dropped."

**3. Per-call-site: resend only where the underlying command is a confirmed-idempotent absolute
setpoint** (a single `command <field>=<value>` publish, no accompanying trigger flag). Checked
against `pybrotlib/src/pybrotlib/components/{telescope,focus}.py`:

| Method | Command(s) | Resend? |
|---|---|---|
| `BrotAltAzTelescope.set_offsets_altaz` | `set_offset_alt`/`set_offset_az` (`elevationoffset=X`/`azimuthoffset=X`) | **Yes** |
| `BrotRaDecTelescope.set_offsets_radec` | `set_offset_ha`/`set_offset_dec` | **Yes** |
| `BrotBaseTelescope._wait_for_focus` (`set_focus`/`set_focus_offset`) | `focus.set(...)` (`focus=X`) | **Yes** |
| `BrotBaseTelescope._wait_for_tracking`/`_move_radec` | `track()` (setpoints + `track=1` trigger) | No — staleness only |
| `BrotBaseTelescope._move_altaz` | `move()` (setpoints + `slew=1` trigger) | No — staleness only |
| `BrotBaseTelescope.init`/`park`/`stop_motion` | `power_on()`/`park()`/`stop()` (trigger) | No — staleness only |
| `BrotDome.init`/`park` (all loops) | `dome.open()`/`start_tracking()`/`stop_tracking()`/`close()`/`park()` (triggers) | No — staleness only |
| `BrotRoof.init`/`park` | `roof.open()`/`close()` (triggers) | No — staleness only |

Trigger-type commands (`slew=1`, `track=1`, `dome_open=1`, etc.) are deliberately **not** resent in
this plan — whether the PLC/TwinCAT side treats a repeated trigger as a safe no-op or re-triggers
the action (restarting a slew ramp, re-opening an already-opening shutter) isn't visible from the
MQTT-layer code and hasn't been confirmed. Staleness detection is added everywhere uniformly;
resend is added only for the three methods above.

## Resend: verified against the real PLC code (2026-09-14, `~/code/brotlib`)

Checked the actual TwinCAT source (not inferred): `BROTLib/BROTLib/BROTLib/POUs/Comm/FB_Comm_MQTT.TcPOU`
and `FB_AltAzTelescopeControl.TcPOU`, `MONETcommon/FB_MonetTelescopeControl.TcPOU`.

**Resend is confirmed safe and genuinely closes a real gap:**
- `AltitudeOffset`/`AzimuthOffset`/etc. (`FB_AltAzTelescopeControl.TcPOU:46-65`) are plain properties
  that just assign a persistent field (`THIS^.fElevationOffset := AltitudeOffset`) — no rising edge,
  no one-shot trigger. Resending the identical value is a true no-op if it already arrived.
- `FB_Comm_MQTT.TcPOU:77` subscribes with `TcIotMqttQos.AtMostOnceDelivery` (**QoS 0** — no ack, no
  retry, no persistence). A `SET elevationoffset=X` message genuinely can be silently dropped in
  transit with zero trace anywhere in the stack. This is a real, structurally-guaranteed possibility,
  not a hypothetical.

**But resend almost certainly does not explain #61's actual symptom.**
`MONETcommon/FB_MonetTelescopeControl.TcPOU:1019` recomputes the axis target every PLC cycle while
tracking: `fbElevation.Position := fElevation + fElevationPointingOffset + fElevationOffset`. And
`TARGETDISTANCE` (line 922) is `ABS(fElevationCurrent - fbElevation.Position)`. So if the offset
`SET` command were simply dropped, `fElevationOffset` never changes, the axis target never moves,
and `TARGETDISTANCE` would already read ~0 immediately — **not** stay elevated for a sustained 120s.
A lost command produces "correction silently ignored, instant false convergence," which is the
*opposite* of #61's reported pattern (three consecutive 120s timeouts with `TARGETDISTANCE`
apparently elevated throughout). That pattern is only consistent with the command having landed and
the axis genuinely struggling to get there (drive fault/oscillation — still open, see #61's own
"check for drive fault" item, not covered by this plan) or with telemetry itself having stalled
(covered by the staleness check above).

**Conclusion: keep resend as cheap, verified-safe defense-in-depth against the confirmed QoS-0
command-loss gap — but it is not the fix for #61's specific timeout pattern.** The staleness
detection is the part of this plan that actually targets the diagnosed symptom.

## Checklist

- [x] `pybrotlib`: add `last_message_at`/`telemetry_age()` to `Transport`, updated in
      `MQTTTransport.run()`'s message loop.
- [x] `pybrotlib`: unit test for `telemetry_age()` (`None` before first message, increases over
      time, resets on each new message); plus a `MQTTTransport.run()` integration test confirming a
      real received message stamps it.
- [x] `pyobs_brot`: add `wait_until_settled()` helper (plus `check_settling_alive()` for loops that
      need their own per-iteration error-state handling alongside the staleness check — e.g. the
      dome/roof/telescope loops that also detect a hardware ERROR state via `match`).
- [x] `pyobs_brot`: unit tests for the helper — settles normally; raises `MoveError` on stale
      telemetry; raises on disconnected transport; raises when no telemetry ever received; resend
      callback fires at `resend_interval` cadence and not before.
- [x] Convert all call sites in the table above to use the helper.
- [x] Check `pyobs-brot`'s existing `tests/test_brotroof.py`/`tests/test_brottelescope.py` don't
      assume the old bare `while` loops' exact structure — one test
      (`test_set_offsets_radec_waits_until_both_axes_converge`) needed `telescope.mqtt._connected`/
      `_last_message_at` set so the new staleness check doesn't fire against its bare mock transport;
      fixed.
- [x] Bump `pybrotlib` version (1.2.1 → 1.2.2); update `pyobs-brot`'s floor to match; release both
      (`pyobs-brot` 2.0.3 → 2.0.4).
- [x] Close pyobs-brot#61, referencing the release and the PLC-verified caveat about resend above.

## Non-goals / open follow-ups

- Resending trigger-type commands — left as a PLC-side question, not decided here.
- `stale_after=5s`/`resend_interval=20s` are starting defaults based on the existing 0.1-1s polling
  cadence, not validated against real telemetry jitter across sites (MONET vs iag50) — revisit if
  production logs show false-positive staleness triggers.
- #61's original "check for drive fault / following-error condition" and "pull iag50/monet
  telemetry for the actual incident window" investigation items are about *why* a mount might
  genuinely fail to settle, not the staleness-detection gap this plan closes — separate follow-up,
  not covered here. **Confirmed still open and still the more likely explanation** for #61's actual
  symptom, per the PLC-code analysis above. Split out to
  [pyobs-brot#71](https://github.com/pyobs/pyobs-brot/issues/71) so it stays tracked now that #61
  is closed.
