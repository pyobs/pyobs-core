"""Subscribe to LogEvent on a live pyobs XMPP deployment and print every one received, with a
running counter -- bare pyobs.comm.xmpp.XmppComm, no Qt/pyobs-gui code involved. Useful for
isolating whether a "duplicate log messages" symptom is coming from the transport/comm layer
or from GUI-side code.

Usage:
    PYOBS_XMPP_JID=admin@monet.saao.ac.za PYOBS_XMPP_PASSWORD=... python watch_log_events.py

Env vars:
    PYOBS_XMPP_JID          bare or full JID to connect as (required)
    PYOBS_XMPP_PASSWORD     password (required)
    PYOBS_XMPP_RESOURCE     resource to bind, appended to a bare JID (default: pyobs-debug) --
                             ignored if PYOBS_XMPP_JID already includes a "/resource"
    PYOBS_XMPP_USE_TLS      "0"/"1" (default: 1)
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import os
import sys

from pyobs.comm.xmpp import XmppComm
from pyobs.events import LogEvent

logging.basicConfig(level=logging.WARNING)


async def main() -> None:
    jid = os.environ.get("PYOBS_XMPP_JID")
    password = os.environ.get("PYOBS_XMPP_PASSWORD")
    if not jid or not password:
        print("Set PYOBS_XMPP_JID and PYOBS_XMPP_PASSWORD.", file=sys.stderr)
        sys.exit(1)

    if "/" not in jid:
        resource = os.environ.get("PYOBS_XMPP_RESOURCE", "pyobs-debug")
        jid = f"{jid}/{resource}"

    use_tls = os.environ.get("PYOBS_XMPP_USE_TLS", "1") != "0"

    counter = itertools.count(1)

    async def on_log_event(event: LogEvent, sender: str) -> bool:
        n = next(counter)
        print(
            f"[{n:04d}] sender={sender!r} level={event.level} time={event.time} "
            f"file={event.filename}:{event.line} msg={event.message!r}",
            flush=True,
        )
        return True

    comm = XmppComm(jid=jid, password=password, use_tls=use_tls)
    await comm.open()
    await comm.register_event(LogEvent, on_log_event)
    print(f"Connected as {jid}. Listening for LogEvents (Ctrl+C to stop)...", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await comm.close()


if __name__ == "__main__":
    asyncio.run(main())
