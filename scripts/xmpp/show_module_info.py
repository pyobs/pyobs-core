"""Show full presence and discovery information for a pyobs module.

Usage:
    python show_module_info.py <module_name>
    python show_module_info.py camera
    python show_module_info.py camera telescope focuser

Env vars (same as integration tests):
    PYOBS_TEST_XMPP_HOST      (default: localhost)
    PYOBS_TEST_XMPP_DOMAIN    (default: localhost)
    PYOBS_TEST_XMPP_PORT      (default: 5222)
    PYOBS_TEST_XMPP_PASSWORD  (default: pyobs)
    PYOBS_TEST_XMPP_IGNORE_CERT (default: 0)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import ssl

import slixmpp
from slixmpp.xmlstream import ET

# ── ANSI colours ─────────────────────────────────────────────────────────────
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"


def h1(text: str) -> str:
    return f"\n{BOLD}{CYAN}{'━' * 60}{RESET}\n{BOLD}{CYAN}  {text}{RESET}\n{BOLD}{CYAN}{'━' * 60}{RESET}"


def h2(text: str) -> str:
    return f"\n{BOLD}{YELLOW}  {text}{RESET}"


def kv(key: str, value: str, indent: int = 4) -> str:
    return f"{' ' * indent}{DIM}{key:<22}{RESET}{value}"


def ok(text: str) -> str:
    return f"    {GREEN}✓{RESET} {text}"


def warn(text: str) -> str:
    return f"    {RED}✗{RESET} {text}"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _module_state_from_show(show: str, status: str) -> tuple[str, str]:
    mapping = {"dnd": "ERROR", "away": "LOCAL", "": "READY", None: "READY"}
    return mapping.get(show, "READY"), status


def _interface_from_feature(feature: str) -> str | None:
    if feature.startswith("pyobs:interface:"):
        return feature[len("pyobs:interface:") :]
    return None


def _parse_capabilities_elem(cap_elem: ET.Element) -> dict[str, str]:
    fields: dict[str, str] = {}
    for child in cap_elem:
        tag = child.tag.split("}")[-1]
        value_elems = list(child)
        if value_elems:
            fields[tag] = value_elems[0].text or ""
        elif child.text:
            fields[tag] = child.text
    return fields


# ── Main logic ────────────────────────────────────────────────────────────────


async def inspect_module(client: slixmpp.ClientXMPP, module: str, domain: str, raw: bool = False) -> None:
    print(h1(f"Module: {module}"))

    bare_jid = f"{module}@{domain}"
    print(h2("Presence"))

    if not client.client_roster.has_jid(bare_jid):
        print(warn(f"{bare_jid} not in roster — is it connected?"))
        return

    roster_item = client.client_roster[bare_jid]
    resources = dict(roster_item.resources)
    if not resources:
        print(warn(f"{module} is offline"))
        return

    resource = next(iter(resources))
    full_jid = f"{bare_jid}/{resource}"
    pres = resources[resource]
    show = pres.get("show", "") or ""
    status = pres.get("status", "") or ""
    state, error = _module_state_from_show(show, status)

    colour = GREEN if state == "READY" else (RED if state == "ERROR" else YELLOW)
    print(kv("State:", f"{colour}{state}{RESET}"))
    print(kv("Full JID:", full_jid))
    if error:
        print(kv("Error:", f"{RED}{error}{RESET}"))

    # disco#info
    print(h2("Interfaces (disco#info features)"))
    try:
        iq = await asyncio.wait_for(client["xep_0030"].get_info(jid=full_jid), timeout=10.0)
    except Exception as e:
        print(warn(f"disco#info failed: {e}"))
        return

    disco = iq["disco_info"]
    features = disco.get_features()

    interfaces: list[str] = []
    for feature in sorted(features):
        iface = _interface_from_feature(feature)
        if iface:
            interfaces.append(iface)
            print(ok(iface))

    # Capabilities — deduplicated by interface name
    print(h2("Capabilities (from disco#info)"))

    found_any = False
    query_xml = disco.xml

    for elem in query_xml:
        if elem.tag.split("}")[-1] != "capabilities":
            continue
        if "}" not in elem.tag:
            continue
        ns = elem.tag.split("{")[1].split("}")[0]
        if not ns.startswith("urn:pyobs:capabilities:"):
            continue
        parts = ns.split(":")
        if len(parts) < 5:
            continue
        iface_name = parts[3]
        fields = _parse_capabilities_elem(elem)
        if fields:
            found_any = True
            print(f"\n    {BOLD}{iface_name}.Capabilities{RESET}")
            for k, v in fields.items():
                print(kv(k + ":", v, indent=6))

    if not found_any:
        print(f"    {DIM}(none published){RESET}")

    if raw:
        print(h2("Raw disco#info XML"))
        import xml.dom.minidom

        pretty = xml.dom.minidom.parseString(ET.tostring(query_xml)).toprettyxml(indent="  ")
        # strip the XML declaration line
        lines = pretty.split("\n")[1:]
        pretty = "\n".join(lines)
        print(f"{DIM}{pretty}{RESET}")

    # Other features
    print(h2("Other features"))
    for f in sorted(f for f in features if not f.startswith("pyobs:")):
        print(f"    {DIM}{f}{RESET}")


async def main(modules: list[str], raw: bool = False) -> None:
    host = os.environ.get("PYOBS_TEST_XMPP_HOST", "localhost")
    domain = os.environ.get("PYOBS_TEST_XMPP_DOMAIN", "localhost")
    port = int(os.environ.get("PYOBS_TEST_XMPP_PORT", "5222"))
    password = os.environ.get("PYOBS_TEST_XMPP_PASSWORD", "../../pyobs")
    ignore_cert = os.environ.get("PYOBS_TEST_XMPP_IGNORE_CERT", "0") == "1"

    client = slixmpp.ClientXMPP(f"observer@{domain}/pyobs", password)
    client.register_plugin("xep_0030")
    client.register_plugin("xep_0115")
    client.register_plugin("xep_0199")

    if ignore_cert:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        client.ssl_context = ctx

    connected = asyncio.Event()
    client.add_event_handler("session_start", lambda _: connected.set())
    client.connect(host=host, port=port)
    client.init_plugins()

    print(f"{DIM}Connecting to {host}:{port} as observer@{domain}...{RESET}")
    await asyncio.wait_for(connected.wait(), timeout=10)
    await client.get_roster()
    client.send_presence()
    await asyncio.sleep(1.0)

    for module in modules:
        await inspect_module(client, module, domain, raw=raw)

    print()
    client.disconnect()
    await asyncio.sleep(0.3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show presence and discovery info for pyobs modules")
    parser.add_argument("modules", nargs="+", help="Module name(s) to inspect")
    parser.add_argument("--raw", action="store_true", help="Also print raw disco#info XML")
    args = parser.parse_args()
    asyncio.run(main(args.modules, raw=args.raw))
