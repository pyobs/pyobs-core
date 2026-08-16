"""Trigger one controlled LogEvent publish on production while debug logging is on, so the
resulting duplicate delivery can be traced in the server log by uuid/timestamp.

Subscriber: admin@monet.saao.ac.za on a throwaway resource (known to reliably reproduce the
double delivery per the investigation's "What's confirmed" #1).
Publisher: fli230@monet.saao.ac.za on a throwaway resource distinct from the live module's
/pyobs, to avoid conflict-kicking it.

Usage:
    PYOBS_ADMIN_PASSWORD=... PYOBS_FLI_PASSWORD=... python trigger_duplicate.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time

from pyobs.comm.xmpp import XmppComm
from pyobs.events import LogEvent


async def main() -> None:
    admin_password = os.environ.get("PYOBS_ADMIN_PASSWORD")
    fli_password = os.environ.get("PYOBS_FLI_PASSWORD")
    if not admin_password or not fli_password:
        print("Set PYOBS_ADMIN_PASSWORD and PYOBS_FLI_PASSWORD.", file=sys.stderr)
        sys.exit(1)

    received: list[tuple[str, float]] = []

    async def on_log_event(event: LogEvent, sender: str) -> bool:
        received.append((event.uuid, time.monotonic()))
        print(f"received uuid={event.uuid} from={sender} wall_time={time.time():.3f}", flush=True)
        return True

    sub = XmppComm(jid="admin@monet.saao.ac.za/pyobs-debug-trace", password=admin_password, use_tls=True)
    await sub.open()
    await sub.register_event(LogEvent, on_log_event)
    print(f"subscriber connected, wall_time={time.time():.3f}", flush=True)

    await asyncio.sleep(2)

    pub = XmppComm(jid="fli230@monet.saao.ac.za/pyobs-debug-trace", password=fli_password, use_tls=True)
    await pub.open()
    print(f"publisher connected, wall_time={time.time():.3f}", flush=True)

    await asyncio.sleep(2)

    ev = LogEvent(
        time="2026-08-16T00:00:00",
        level="INFO",
        filename="trigger_duplicate.py",
        function="main",
        line=1,
        message="double-delivery trace probe",
    )
    print(f"PUBLISHING uuid={ev.uuid} wall_time={time.time():.3f}", flush=True)
    await pub.send_event(ev)

    await asyncio.sleep(5)

    await sub.close()
    await pub.close()

    print(f"\nreceived {len(received)} copies")


if __name__ == "__main__":
    asyncio.run(main())
