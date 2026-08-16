"""Same double-delivery trigger test as trigger_duplicate.py, but against iagvtsrv via an SSH
tunnel (127.0.0.1:5226 -> iagvtsrv:5222), using throwaway testpub/testsub accounts that inherited
mutual 'both' presence automatically from the existing @all@ shared roster group.

Usage:
    PYOBS_TEST_PASSWORD=... python trigger_duplicate_iagvt.py

Register the throwaway accounts first (and unregister them afterward):
    ejabberdctl register testpub iagvtsrv.astro.physik.uni-goettingen.de <password>
    ejabberdctl register testsub iagvtsrv.astro.physik.uni-goettingen.de <password>
"""

from __future__ import annotations

import asyncio
import os
import sys
import time

from pyobs.comm.xmpp import XmppComm
from pyobs.events import LogEvent

DOMAIN = "iagvtsrv.astro.physik.uni-goettingen.de"


async def main() -> None:
    password = os.environ.get("PYOBS_TEST_PASSWORD")
    if not password:
        print("Set PYOBS_TEST_PASSWORD.", file=sys.stderr)
        sys.exit(1)

    received: list[tuple[str, float]] = []

    async def on_log_event(event: LogEvent, sender: str) -> bool:
        received.append((event.uuid, time.monotonic()))
        print(f"received uuid={event.uuid} from={sender} wall_time={time.time():.3f}", flush=True)
        return True

    sub = XmppComm(
        jid=f"testsub@{DOMAIN}/debug-trace",
        password=password,
        use_tls=True,
        ignore_cert_errors=True,
        server="localhost:5226",
    )
    await sub.open()
    await sub.register_event(LogEvent, on_log_event)
    print(f"subscriber connected, wall_time={time.time():.3f}", flush=True)

    await asyncio.sleep(2)

    pub = XmppComm(
        jid=f"testpub@{DOMAIN}/debug-trace",
        password=password,
        use_tls=True,
        ignore_cert_errors=True,
        server="localhost:5226",
    )
    await pub.open()
    print(f"publisher connected, wall_time={time.time():.3f}", flush=True)

    await asyncio.sleep(2)

    ev = LogEvent(
        time="2026-08-16T00:00:00",
        level="INFO",
        filename="trigger_duplicate_iagvt.py",
        function="main",
        line=1,
        message="double-delivery trace probe (iagvt)",
    )
    print(f"PUBLISHING uuid={ev.uuid} wall_time={time.time():.3f}", flush=True)
    await pub.send_event(ev)

    await asyncio.sleep(5)

    await sub.close()
    await pub.close()

    uuids = [u for u, _ in received]
    dupes = {u for u in uuids if uuids.count(u) > 1}
    print(f"\nreceived {len(received)} copies")
    if dupes:
        print(f"DUPLICATION REPRODUCED: {len(dupes)} uuid(s) delivered more than once")
    else:
        print("no duplication")


if __name__ == "__main__":
    asyncio.run(main())
