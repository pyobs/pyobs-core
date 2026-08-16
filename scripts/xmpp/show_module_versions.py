"""Print the pyobs version each connected module is advertising via IModule capabilities.
Useful to check whether a fix present in this checkout has actually been rolled out to a
deployed fleet yet.

Usage:
    PYOBS_XMPP_JID=admin@monet.saao.ac.za PYOBS_XMPP_PASSWORD=... python show_module_versions.py

Env vars:
    PYOBS_XMPP_JID          bare or full JID to connect as (required)
    PYOBS_XMPP_PASSWORD     password (required)
    PYOBS_XMPP_RESOURCE     resource to bind, appended to a bare JID (default: pyobs-debug) --
                             ignored if PYOBS_XMPP_JID already includes a "/resource"
    PYOBS_XMPP_USE_TLS      "0"/"1" (default: 1)
"""

from __future__ import annotations

import asyncio
import os
import sys

from pyobs.comm.xmpp import XmppComm
from pyobs.interfaces import IModule


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

    comm = XmppComm(jid=jid, password=password, use_tls=use_tls)
    await comm.open()

    # give presence/roster a moment to populate comm.clients
    await asyncio.sleep(3)

    print(f"Connected as {jid}. {len(comm.clients)} client(s) visible.\n")
    for client in sorted(comm.clients):
        cap = await comm.get_capabilities(client, IModule)
        version = cap.version if cap is not None else "(no capabilities published)"
        print(f"{client:20s} version={version}")

    await comm.close()


if __name__ == "__main__":
    asyncio.run(main())
