"""Minimal ejabberd notification test — no pyobs code involved."""

import asyncio
import os
import ssl

import slixmpp
from slixmpp.xmlstream import ET


def make_client(jid, password):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    c = slixmpp.ClientXMPP(jid, password)
    c.register_plugin("xep_0060")
    c.register_plugin("xep_0030")
    c.register_plugin("xep_0115")
    c.ssl_context = ctx
    c.enable_starttls = True
    c.enable_direct_tls = True
    c.enable_plaintext = False
    c["feature_mechanisms"].unencrypted_scram = False
    return c


async def connect(client):
    done = asyncio.Event()
    client.add_event_handler("session_start", lambda e: done.set())
    await client.connect(host="localhost", port=5222)
    client.init_plugins()
    await asyncio.wait_for(done.wait(), 15)
    await client.get_roster()
    client.send_presence()
    await asyncio.sleep(1)


async def main():
    pw = os.environ.get("PYOBS_TEST_XMPP_PASSWORD", "../../pyobs")
    node = "test:notify:1"
    service = "pubsub.localhost"

    pub = make_client("camera@localhost/pyobs", pw)
    sub = make_client("observer@localhost/pyobs2", pw)

    print("Connecting publisher...")
    await connect(pub)
    print("Connecting subscriber...")
    await connect(sub)
    print("Both connected.")

    # Create node
    print("Creating node...")
    try:
        await asyncio.wait_for(pub["xep_0060"].create_node(service, node), 5)
        print("  Created.")
    except Exception as e:
        print(f"  (already exists or error: {e})")

    # Subscribe
    print("Subscribing...")
    try:
        result = await asyncio.wait_for(sub["xep_0060"].subscribe(service, node), 5)
        print(f"  Subscribed: {result['pubsub']['subscription']['subscription']}")
    except Exception as e:
        print(f"  Error: {e}")

    # Listen for notifications
    received = []

    async def on_msg(msg):
        received.append(msg)
        print("  >>> pubsub_publish fired!")

    sub.add_event_handler("pubsub_publish", on_msg)

    await asyncio.sleep(0.5)

    # Publish with payload
    print("Publishing with payload...")
    payload = ET.fromstring('<test xmlns="urn:test">hello</test>')
    try:
        await asyncio.wait_for(pub["xep_0060"].publish(service, node, payload=payload), 5)
        print("  Published OK.")
    except Exception as e:
        print(f"  Publish error: {e}")

    print("Waiting 3s for notification...")
    await asyncio.sleep(3)
    print(f"\nResult: received {len(received)} notifications.")
    if len(received) == 0:
        print("PROBLEM: ejabberd is not delivering notifications to subscribers.")
    else:
        print("OK: ejabberd delivers notifications correctly.")

    # Cleanup
    try:
        await asyncio.wait_for(pub["xep_0060"].delete_node(service, node), 5)
    except Exception:
        pass

    pub.disconnect()
    sub.disconnect()
    await asyncio.sleep(0.5)


asyncio.run(main())
