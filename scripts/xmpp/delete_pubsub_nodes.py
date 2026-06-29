"""Delete pyobs pubsub nodes from ejabberd.

Connects as the specified user (the node owner) and deletes all nodes
matching a given prefix. Run once per module user if you have multiple.

Usage:
    python delete_pubsub_nodes.py --user camera
    python delete_pubsub_nodes.py --user telescope --prefix pyobs:state:telescope:

Env vars (same as integration tests):
    PYOBS_TEST_XMPP_HOST, PYOBS_TEST_XMPP_DOMAIN, PYOBS_TEST_XMPP_PORT
    PYOBS_TEST_XMPP_PASSWORD, PYOBS_TEST_XMPP_IGNORE_CERT
"""

from __future__ import annotations

import argparse
import asyncio
import os
import ssl

import slixmpp
import slixmpp.exceptions


async def main(user: str, prefix: str) -> None:
    host = os.environ.get("PYOBS_TEST_XMPP_HOST", "localhost")
    domain = os.environ.get("PYOBS_TEST_XMPP_DOMAIN", "localhost")
    port = int(os.environ.get("PYOBS_TEST_XMPP_PORT", "5222"))
    password = os.environ.get("PYOBS_TEST_XMPP_PASSWORD", "pyobs")
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

    print(f"Listing nodes on {pubsub} (as {user}) ...")
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
        print(f"Found {len(matching)} node(s) matching '{prefix}':")
        for node in matching:
            print(f"  Deleting: {node}")
            try:
                await asyncio.wait_for(client["xep_0060"].delete_node(pubsub, node), timeout=5)
                print("    ✓ deleted")
            except slixmpp.exceptions.IqError as e:
                print(f"    ✗ failed: {e}")

    client.disconnect()
    await asyncio.sleep(0.3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete pyobs pubsub nodes")
    parser.add_argument(
        "--user",
        default="camera",
        help="XMPP username to connect as (node owner, default: camera)",
    )
    parser.add_argument(
        "--prefix",
        default="pyobs:state:",
        help="Node name prefix to match (default: pyobs:state:)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.user, args.prefix))
