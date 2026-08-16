"""Like watch_log_events_raw.py, but deliberately never declares XEP-0163 "interest" (the
+notify feature via entity caps) for any pyobs event node -- tests whether ejabberd's PEP
implementation delivers notifications purely based on roster/presence subscription, independent
of (or in addition to) the explicit interest mechanism pyobs's XmppComm._register_events() uses.
If this script still receives LogEvents, implicit roster-based delivery exists on this server; if
it receives them exactly once (vs. XmppComm's observed double delivery), that's strong evidence
the explicit add_interest() call is adding a second, redundant delivery path.

Usage:
    PYOBS_XMPP_JID=admin@monet.saao.ac.za PYOBS_XMPP_PASSWORD=... python watch_log_events_no_interest.py

Env vars: same as watch_log_events.py.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import os
import re
import ssl
import sys

import slixmpp
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import MatchXMLMask

logging.basicConfig(level=logging.WARNING)


def make_client(jid: str, password: str, use_tls: bool) -> slixmpp.ClientXMPP:
    c = slixmpp.ClientXMPP(jid, password)
    c.register_plugin("xep_0030")  # service discovery
    c.register_plugin("xep_0060")  # pubsub
    c.register_plugin("xep_0115")  # entity capabilities
    c.register_plugin("xep_0163")  # PEP -- registered so pubsub#event stanzas are understood,
    # but we deliberately never call add_interest()/add_feature() for any pyobs event node below.
    if use_tls:
        ctx = ssl.create_default_context()
        c.ssl_context = ctx
    return c


async def main() -> None:
    jid = os.environ.get("PYOBS_XMPP_JID")
    password = os.environ.get("PYOBS_XMPP_PASSWORD")
    if not jid or not password:
        print("Set PYOBS_XMPP_JID and PYOBS_XMPP_PASSWORD.", file=sys.stderr)
        sys.exit(1)

    if "/" not in jid:
        resource = os.environ.get("PYOBS_XMPP_RESOURCE", "pyobs-debug-noninterest")
        jid = f"{jid}/{resource}"

    use_tls = os.environ.get("PYOBS_XMPP_USE_TLS", "1") != "0"

    client = make_client(jid, password, use_tls)

    counter = itertools.count(1)
    first_seen: dict[str, float] = {}
    pubsub_ns = "http://jabber.org/protocol/pubsub#event"

    def on_raw(msg: object) -> None:
        xml_el = msg.xml  # type: ignore[attr-defined]
        event_xml = xml_el.find(f"{{{pubsub_ns}}}event")
        if event_xml is None:
            return
        items_xml = event_xml.find(f"{{{pubsub_ns}}}items")
        if items_xml is None:
            return
        node = items_xml.get("node", "")
        if "LogEvent" not in node:
            return
        item_xml = items_xml.find(f"{{{pubsub_ns}}}item")
        from_jid = xml_el.get("from")
        payload_el = list(item_xml)[0] if item_xml is not None and len(item_xml) > 0 else None
        payload_text = payload_el.text if payload_el is not None else None
        n = next(counter)

        now = asyncio.get_event_loop().time()
        uuid_match = None
        if payload_text:
            m = re.search(r'"uuid": "([0-9a-f-]+)"', payload_text)
            uuid_match = m.group(1) if m else None
        delta_str = ""
        if uuid_match is not None:
            if uuid_match in first_seen:
                delta_str = f" DUPLICATE, +{now - first_seen[uuid_match]:.3f}s since first seen"
            else:
                first_seen[uuid_match] = now

        print(
            f"[{n:04d}] t={now:.3f} from={from_jid} node={node} uuid={uuid_match}{delta_str} "
            f"payload={(payload_text or '')[:100]!r}",
            flush=True,
        )

    client.register_handler(
        Callback(
            "raw pyobs pubsub event dump (no interest)",
            MatchXMLMask(
                '<message xmlns="jabber:client">'
                '<event xmlns="http://jabber.org/protocol/pubsub#event">'
                "<items /></event></message>"
            ),
            on_raw,
        )
    )

    connected = asyncio.Event()

    async def on_session_start(event: object) -> None:
        client.send_presence()
        await client.get_roster()
        connected.set()

    client.add_event_handler("session_start", on_session_start)

    client.connect()
    await asyncio.wait_for(connected.wait(), timeout=20)
    print(f"Connected as {jid} (no +notify interest declared). Listening...", flush=True)

    try:
        await asyncio.Event().wait()
    finally:
        client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
