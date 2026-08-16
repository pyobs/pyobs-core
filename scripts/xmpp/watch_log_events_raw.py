"""Like watch_log_events.py, but also prints the raw pubsub <item id="..."> and message stanza
id for each incoming LogEvent notification -- lets you tell a genuine double-publish (two
different item ids for the same content) apart from a single publish somehow delivered twice by
the server (same item id, same message id or two different message ids for one publish).

Usage:
    PYOBS_XMPP_JID=admin@monet.saao.ac.za PYOBS_XMPP_PASSWORD=... python watch_log_events_raw.py

Env vars: same as watch_log_events.py.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import os
import sys

from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import MatchXMLMask

from pyobs.comm.xmpp import XmppComm
from pyobs.events import LogEvent

logging.basicConfig(level=logging.WARNING)


def main_sync() -> None:
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
    pubsub_ns = "http://jabber.org/protocol/pubsub#event"

    async def run() -> None:
        comm = XmppComm(jid=jid, password=password, use_tls=use_tls)
        await comm.open()

        # declare interest in LogEvent so the server actually routes notifications to us --
        # the raw handler below is only a second tap on the same stream, it doesn't itself
        # cause XEP-0163 add_interest() to be called.
        async def _noop(event: LogEvent, sender: str) -> bool:
            return True

        await comm.register_event(LogEvent, _noop)

        first_seen: dict[str, float] = {}

        def on_raw(msg: object) -> None:
            xml_el = msg.xml  # type: ignore[attr-defined]
            event_xml = xml_el.find(f"{{{pubsub_ns}}}event")
            if event_xml is None:
                return
            items_xml = event_xml.find(f"{{{pubsub_ns}}}items")
            if items_xml is None:
                return
            node = items_xml.get("node", "")
            if not node.startswith("urn:pyobs:event:LogEvent"):
                return
            item_xml = items_xml.find(f"{{{pubsub_ns}}}item")
            item_id = item_xml.get("id") if item_xml is not None else None
            msg_id = xml_el.get("id")
            from_jid = xml_el.get("from")
            payload_el = list(item_xml)[0] if item_xml is not None and len(item_xml) > 0 else None
            payload_text = payload_el.text if payload_el is not None else None
            n = next(counter)

            now = asyncio.get_event_loop().time()
            uuid_match = None
            if payload_text:
                import re

                m = re.search(r'"uuid": "([0-9a-f-]+)"', payload_text)
                uuid_match = m.group(1) if m else None
            delta_str = ""
            if uuid_match is not None:
                if uuid_match in first_seen:
                    delta_str = f" DUPLICATE, +{now - first_seen[uuid_match]:.3f}s since first seen"
                else:
                    first_seen[uuid_match] = now

            print(
                f"[{n:04d}] t={now:.3f} from={from_jid} msg_id={msg_id} item_id={item_id} "
                f"uuid={uuid_match}{delta_str} "
                f"payload={(payload_text or '')[:120]!r}",
                flush=True,
            )

        comm._xmpp.register_handler(  # type: ignore[union-attr]
            Callback(
                "raw pyobs pubsub event dump",
                MatchXMLMask(
                    '<message xmlns="jabber:client">'
                    '<event xmlns="http://jabber.org/protocol/pubsub#event">'
                    "<items /></event></message>"
                ),
                on_raw,
            )
        )

        print(f"Connected as {jid}. Listening for raw LogEvent stanzas (Ctrl+C to stop)...", flush=True)
        try:
            await asyncio.Event().wait()
        finally:
            await comm.close()

    asyncio.run(run())


if __name__ == "__main__":
    main_sync()
