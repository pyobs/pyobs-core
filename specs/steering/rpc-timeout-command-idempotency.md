# RPC timeout on a mutating command means "unknown," not "failed" — clients must not blind-retry

Applies to every pyobs client that issues RPC calls against physical hardware: `pyobs-gui`,
`pyobs-polaris`, `pyobs-web-client` (and its Capacitor-packaged mobile shell, see
`pyobs-web-client/specs/design/native-app-shell-capacitor.md`). Surfaced while scoping the mobile
app (issue #884) because a phone on cellular/site wifi hits this far more often than a desktop
client on a stable LAN — but the underlying problem isn't mobile-specific, and no client-side
convention for it existed before this doc.

## The problem

`Proxy.execute()` raises `RemoteTimeoutError` (subclass of `RemoteError`,
`pyobs/utils/exceptions.py`) when no response arrives within the RPC timeout. That tells the
caller only that it doesn't know the outcome — not that the command failed to execute on the
module. A command could have been received and acted on with the response lost on the way back,
or never received at all. The wire protocol already surfaces this loudly rather than swallowing it
(`specs/design/pyobs_2_0_wire_protocol.md`); what's missing is a rule for what a client does next.

The wrong thing to do is treat a timeout as "it didn't happen" and just resend the same call. For
a command that starts something non-restartable, that risks doing it twice.

## The rule

On an ambiguous RPC outcome (timeout, or a connection drop mid-call):

1. **Don't resend the same mutating command reflexively.** Resolve the ambiguity first.
2. **Resolve via the module's actual current state** — its state pubsub value, or an explicit
   status query — not by assuming success or failure.
3. **Only then decide whether to retry**, and whether retrying is even safe (see below).
4. **Never queue a mutating/control command for later replay** on reconnect. Unlike local
   config data, a queued control command executed once connectivity returns may act on a
   physical or observational context that no longer holds — weather changed, someone else already
   intervened, the time window passed. Reconnect-and-catch-up applies to *reading* state, never to
   replaying a write.

## Not every command is safe to retry after confirming state — this is a per-command judgment call

Some pyobs commands are state-directed and idempotent by construction: calling them again once you
know the current state is a safe no-op if that state is already reached. `IMotion.park()`,
`IMotion.init()`, and `IMotion.stop_motion()` (`pyobs/interfaces/IMotion.py`, the base of `IRoof`/
`IDome`) are this shape — parking an already-parked device, or stopping an already-stopped one,
does nothing harmful.

Others aren't. Starting an exposure is the clear example: `IExposure`'s `ExposureState`
(`pyobs/interfaces/IExposure.py`) has a `status` (`ExposureStatus.IDLE`/`EXPOSING`/`READOUT`/
`ERROR`, `pyobs/utils/enums.py`) precisely because the caller needs to check it before deciding
whether to retry a start-exposure call after a timeout — reissuing it while `EXPOSING` risks a
second exposure, not resuming the first. Treat any command that begins a discrete, non-restartable
operation the same way: check status before retrying, don't retry blind.

There's no single flag on an interface method that marks it safe or unsafe — this is a judgment
call each client makes per command it exposes, informed by whether the target state is a
declarative endpoint (safe) or the start of a one-shot operation (not safe without a status
check first).

## Staleness, not just connected/disconnected

Any UI showing live module state should indicate how old that state is, not just whether the
client is currently connected. An operator glancing at a dome-position or weather card needs to
know if it's 2 seconds old or 2 minutes old before acting on it — "connected" doesn't mean
"current."
