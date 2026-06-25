"""List all pyobs pubsub nodes on ejabberd, with their latest item payload.

Usage:
    python list_pubsub_nodes.py [--prefix pyobs:state:] [--user camera]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import ssl

import slixmpp
import slixmpp.exceptions
from slixmpp.xmlstream import ET


async def main(user: str, prefix: str) -> None:
    host = os.environ.get("PYOBS_TEST_XMPP_HOST", "localhost")
    domain = os.environ.get("PYOBS_TEST_XMPP_DOMAIN", "localhost")
    port = int(os.environ.get("PYOBS_TEST_XMPP_PORT", "5222"))
    password = os.environ.get("PYOBS_TEST_XMPP_PASSWORD", "../../pyobs")
    ignore_cert = os.environ.get("PYOBS_TEST_XMPP_IGNORE_CERT", "0") == "1"

    client = slixmpp.ClientXMPP(f"{user}@{domain}/pyobs", password)
    client.register_plugin("xep_0060")

    if ignore_cert:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        client.ssl_context = ctx

    connected = asyncio.Event()
    client.add_event_handler("session_start", lambda _: connected.set())
    client.connect(host=host, port=port)
    client.init_plugins()

    await asyncio.wait_for(connected.wait(), timeout=10)
    await client.get_roster()
    client.send_presence()
    await asyncio.sleep(0.5)

    pubsub = f"pubsub.{domain}"

    try:
        result = await asyncio.wait_for(client["xep_0060"].get_nodes(pubsub), timeout=10)
        items = result["disco_items"]["items"]
    except Exception as e:
        print(f"Failed to list nodes: {e}")
        client.disconnect()
        return

    matching = [node for _, node, _ in items if node.startswith(prefix)]

    if not matching:
        print(f"No nodes found matching '{prefix}'")
    else:
        print(f"Found {len(matching)} node(s):\n")
        for node in sorted(matching):
            print(f"  {node}")
            try:
                result = await asyncio.wait_for(
                    client["xep_0060"].get_items(pubsub, node, max_items=1),
                    timeout=5,
                )
                pubsub_ns = "http://jabber.org/protocol/pubsub"
                pubsub_xml = result.xml.find(f"{{{pubsub_ns}}}pubsub")
                items_xml = pubsub_xml.find(f"{{{pubsub_ns}}}items") if pubsub_xml is not None else None
                item_xml = items_xml.find(f"{{{pubsub_ns}}}item") if items_xml is not None else None
                payload = list(item_xml)[0] if item_xml is not None and len(item_xml) > 0 else None
                if payload is not None:
                    print(f"    payload: {ET.tostring(payload).decode()[:120]}")
                else:
                    print("    (no items published yet)")
            except Exception as e:
                print(f"    (error fetching items: {e})")
            print()

    client.disconnect()
    await asyncio.sleep(0.3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List pyobs pubsub nodes")
    parser.add_argument("--user", default="camera")
    parser.add_argument("--prefix", default="pyobs:state:")
    args = parser.parse_args()
    asyncio.run(main(args.user, args.prefix))
