# On XMPP stream-error `conflict`, quit the module instead of reconnecting

status: accepted
date: 2026-07-03

## Context and Problem Statement

ejabberd sends the standard XMPP stream-error condition `conflict` (RFC 6120 §4.9.3) both when
an admin explicitly kicks a session (`ejabberdctl kick_session`, also reachable via
`pyobs-web-admin`'s kick button) and when a second login with the same JID/resource genuinely
bumps the first session. At the protocol level these two situations are indistinguishable by
condition alone — verified live against a real ejabberd server for both cases. (A *different*
admin command, `kick_user` with no reason argument, instead produces `policy-violation`, so
even "which admin command was used" doesn't map onto one uniform condition.)

pyobs-core's existing behavior treated all disconnects the same way: auto-reconnect. For
`conflict` specifically, that's the wrong default — if a second session has genuinely taken
over the JID/resource, reconnecting just re-races whoever now holds it, potentially flapping
indefinitely instead of settling.

## Considered Options

* Keep uniform auto-reconnect behavior for every disconnect cause, including `conflict`
* Special-case `conflict`: stop reconnecting and shut the module down, since retrying doesn't
  resolve a takeover and an admin kick is presumably intentional either way
* Try to distinguish "admin kick" from "genuine takeover" using the stream error's `<text>`
  content before deciding whether to reconnect

## Decision Outcome

Chosen option: special-case `conflict` to quit rather than reconnect. `xmppclient.py`/
`xmppcomm.py` hook slixmpp's `stream_error` event; on condition `conflict`,
`XmppComm._disconnected()` logs the stream error's `<text>` (the one piece of information that
does carry "why," e.g. "Kicked via pyobs-web-admin") and calls `self._module.quit()` instead of
attempting reconnection. Every other disconnect cause (`policy-violation`, `system-shutdown`,
plain connection loss, ping timeout) still falls through to the existing auto-reconnect path —
this is a narrow carve-out, not a change to general reconnect behavior.

Distinguishing kick-from-takeover by parsing `<text>` (option 3) was rejected: the text is a
human-readable admin-supplied string, not a structured signal meant for programmatic branching,
and both an intentional kick and a genuine takeover warrant the same response anyway (stop
racing for the resource) — there's no actual behavioral difference the distinction would drive.

### Consequences

* Good, because a genuine duplicate-JID takeover no longer flaps in a reconnect loop against
  the session that now holds the resource
* Good, because an intentional admin kick is now honored (module quits) instead of the module
  silently fighting its way back onto the JID
* Neutral, because the module requires an external supervisor (systemd, `pyobsd`, etc.) to
  notice the quit and decide whether/when to restart it — this decision doesn't itself define
  restart policy, only that reconnect-on-`conflict` is wrong
* Bad, because if ejabberd ever reused `conflict` for a disconnect cause that *should*
  auto-reconnect, this carve-out would incorrectly quit the module — no such case is known
  today
