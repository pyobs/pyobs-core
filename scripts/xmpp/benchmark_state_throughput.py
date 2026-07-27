"""Benchmark pyobs's XMPP state-push (XEP-0060) and RPC (XEP-0009) throughput/latency
against a live ejabberd server.

See specs/plans/ejabberd-throughput-benchmarking.md for the full design, the questions
this is meant to answer, and the three shaper configs to compare (default, 10x-rate,
fast-track). Deliberately not a pytest test: long-running, resource-heavy, meant to be
triggered manually and to produce a data file for analysis, not a fast pass/fail
assertion for CI.

Connection config via env vars (same names as tests/integration/conftest.py):
    PYOBS_TEST_XMPP_HOST        (default: localhost)
    PYOBS_TEST_XMPP_DOMAIN      (default: same as host)
    PYOBS_TEST_XMPP_PORT        (default: 5222)
    PYOBS_TEST_XMPP_PASSWORD    (default: pyobs)
    PYOBS_TEST_XMPP_TLS         (default: 0 -- this repo's test ejabberd is plain TCP)
    PYOBS_TEST_XMPP_IGNORE_CERT (default: 1)

"concurrent-many" and "rpc" need more than the two accounts (camera, observer) the
test fixture pre-registers. Pass --register-via <container-name> to have the script
register the extra bench<N> accounts itself, via `docker exec <container> ejabberdctl
register ...`, before running.

Usage:
    python scripts/xmpp/benchmark_state_throughput.py sequential --n 100
    python scripts/xmpp/benchmark_state_throughput.py concurrent-single --n 100
    python scripts/xmpp/benchmark_state_throughput.py concurrent-many --k 25 --n 20 \\
        --register-via test-ejabberd
    python scripts/xmpp/benchmark_state_throughput.py rpc --n 50 --register-via test-ejabberd
    python scripts/xmpp/benchmark_state_throughput.py payload --n 50
    python scripts/xmpp/benchmark_state_throughput.py all --n 100 --k 25 --register-via test-ejabberd

Tag results with --shaper-label when comparing shaper configs -- the script itself
doesn't manage the docker container, restart it with the desired shaper config first:
    docker compose -f tests/xmpp/docker-compose.yml up -d                                                # default
    docker compose -f tests/xmpp/docker-compose.yml -f scripts/xmpp/docker-compose.shaper-10x.yml up -d   # 10x
    docker compose -f tests/xmpp/docker-compose.yml -f scripts/xmpp/docker-compose.fast-shaper.yml up -d  # fast-track

Results: appends one JSON object per measurement to --output (JSONL), plus a printed
summary (mean/median/p95/p99/max latency, msgs/sec throughput) after each scenario.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.interfaces import (
    BinningState,
    CoolingState,
    FilterState,
    GainState,
    IBinning,
    ICooling,
    IFilters,
    IGain,
    IMode,
    IModule,
    Interface,
    IReady,
    ITemperatures,
    IWindow,
    ModeState,
    ReadyState,
    SensorReading,
    TemperaturesState,
    WindowState,
)
from pyobs.modules.camera.dummycamera import DummyCamera
from pyobs.utils.enums import ModuleState

# ---------------------------------------------------------------------------
# connection config (mirrors tests/integration/conftest.py's XmppConfig)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class XmppConfig:
    host: str
    domain: str
    port: int
    password: str
    use_tls: bool
    ignore_cert_errors: bool


def env_config() -> XmppConfig:
    host = os.environ.get("PYOBS_TEST_XMPP_HOST", "localhost")
    return XmppConfig(
        host=host,
        domain=os.environ.get("PYOBS_TEST_XMPP_DOMAIN", host),
        port=int(os.environ.get("PYOBS_TEST_XMPP_PORT", "5222")),
        password=os.environ.get("PYOBS_TEST_XMPP_PASSWORD", "pyobs"),
        use_tls=os.environ.get("PYOBS_TEST_XMPP_TLS", "0") == "1",
        ignore_cert_errors=os.environ.get("PYOBS_TEST_XMPP_IGNORE_CERT", "1") == "1",
    )


def make_comm(cfg: XmppConfig, user: str) -> XmppComm:
    """Build an unopened XmppComm for ``<user>@<domain>``."""
    return XmppComm(
        user=user,
        domain=cfg.domain,
        password=cfg.password,
        server=f"{cfg.host}:{cfg.port}",
        use_tls=cfg.use_tls,
        ignore_cert_errors=cfg.ignore_cert_errors,
    )


def attach_module(comm: XmppComm, interfaces: list[type[Interface]], name: str) -> MagicMock:
    """Minimal module stub satisfying what XmppComm needs to publish state.

    IModule must be included -- peers only add a JID to their client list once they see
    IModule in the disco#info features, mirroring tests/integration/conftest.py's
    make_module (not reused directly: that helper hardcodes name="camera", which doesn't
    work for the concurrent-many scenario's K distinct client identities).
    """
    m = MagicMock()
    m.interfaces = list({IModule} | set(interfaces))
    m.name = name
    m.get_label = AsyncMock(return_value=name)
    m.get_version = AsyncMock(return_value="2.0.0.dev1")
    m._comm = comm
    comm.module = m
    return m


async def open_publisher(cfg: XmppConfig, name: str, interfaces: list[type[Interface]]) -> XmppComm:
    """Build, open, and announce-ready an XmppComm publishing the given interfaces."""
    comm = make_comm(cfg, name)
    attach_module(comm, interfaces, name)
    await comm.open()
    await comm.set_presence(ModuleState.READY)
    return comm


def register_accounts(container: str, domain: str, password: str, users: list[str]) -> None:
    """Idempotently register accounts via `docker exec <container> ejabberdctl register`.

    Conflicts (already registered) are expected on reruns and ignored -- mirrors the "!"
    prefix convention used for CTL_ON_START in tests/xmpp/docker-compose.yml.
    """
    for user in users:
        result = subprocess.run(
            ["docker", "exec", container, "ejabberdctl", "register", user, domain, password],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "already registered" not in result.stderr + result.stdout:
            raise RuntimeError(f"Failed to register {user}@{domain}: {result.stdout} {result.stderr}")


# ---------------------------------------------------------------------------
# curated state-bearing interfaces, for "N distinct nodes" without inventing
# arbitrary state classes. Cycled via index % len(...) when N exceeds this list --
# a fleet-realistic node identity is (module JID, interface), so a single
# publishing client is inherently capped at "however many distinct interfaces it
# implements" many nodes; scenario 3 (concurrent-many) gets its N x K distinct
# nodes for free from K distinct client JIDs instead.
# ---------------------------------------------------------------------------

STATE_INTERFACES: list[tuple[type[Interface], Callable[[], Any]]] = [
    (ICooling, lambda: CoolingState(setpoint=-20.0, power=65, enabled=True)),
    (IBinning, lambda: BinningState(x=1, y=1)),
    (IGain, lambda: GainState(gain=1.5, offset=0.0)),
    (IFilters, lambda: FilterState(filter="clear")),
    (IMode, lambda: ModeState(modes={"default": "normal"})),
    (IWindow, lambda: WindowState(x=0, y=0, width=1024, height=1024)),
]

SMALL_STATE: tuple[type[Interface], Callable[[], Any]] = (IReady, lambda: ReadyState(ready=True))
LARGE_STATE: tuple[type[Interface], Callable[[], Any]] = (
    ITemperatures,
    lambda: TemperaturesState(readings=[SensorReading(name=f"sensor{i}", value=20.0 + i) for i in range(50)]),
)

ALL_PUBLISHED_INTERFACES = [i for i, _ in STATE_INTERFACES] + [SMALL_STATE[0], LARGE_STATE[0]]


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------


@dataclass
class Timing:
    timestamp: float
    scenario: str
    concurrency: int
    payload: str
    shaper_label: str
    latency: float
    ok: bool
    error: str | None = None


@dataclass
class Recorder:
    output: str | None
    shaper_label: str
    timings: list[Timing] = field(default_factory=list)

    def record(
        self, scenario: str, concurrency: int, payload: str, latency: float, ok: bool, error: str | None = None
    ) -> None:
        t = Timing(time.time(), scenario, concurrency, payload, self.shaper_label, latency, ok, error)
        self.timings.append(t)
        if self.output:
            with open(self.output, "a") as f:
                f.write(json.dumps(t.__dict__) + "\n")

    def summary(self, scenario: str, payload: str | None = None) -> None:
        rows = [t for t in self.timings if t.scenario == scenario and (payload is None or t.payload == payload)]
        latencies = [t.latency for t in rows if t.ok]
        failed = sum(1 for t in rows if not t.ok)
        label = scenario if payload is None else f"{scenario}/{payload}"
        if not latencies:
            print(f"[{label}] no successful measurements ({failed} failed)")
            return
        latencies.sort()

        def pct(p: float) -> float:
            idx = min(len(latencies) - 1, int(len(latencies) * p))
            return latencies[idx]

        print(
            f"[{label}] n={len(latencies)} failed={failed} "
            f"mean={statistics.mean(latencies) * 1000:.1f}ms "
            f"median={statistics.median(latencies) * 1000:.1f}ms "
            f"p95={pct(0.95) * 1000:.1f}ms "
            f"p99={pct(0.99) * 1000:.1f}ms "
            f"max={max(latencies) * 1000:.1f}ms"
        )


async def timed_set_state(comm: XmppComm, interface: type[Interface], state: Any) -> float:
    start = time.perf_counter()
    await comm.set_state(interface, state)
    return time.perf_counter() - start


# ---------------------------------------------------------------------------
# scenarios
# ---------------------------------------------------------------------------


async def run_sequential(
    cfg: XmppConfig,
    n: int,
    recorder: Recorder,
    payload_label: str = "mixed",
    pair: tuple[type[Interface], Callable[[], Any]] | None = None,
) -> None:
    """One client, N publishes to N distinct nodes (cycling through STATE_INTERFACES,
    or a fixed single (interface, state) pair for the payload-size sweep), awaited one
    at a time."""
    comm = await open_publisher(cfg, "camera", ALL_PUBLISHED_INTERFACES)
    try:
        start = time.perf_counter()
        for i in range(n):
            interface, factory = pair if pair is not None else STATE_INTERFACES[i % len(STATE_INTERFACES)]
            try:
                latency = await timed_set_state(comm, interface, factory())
                recorder.record("sequential", 1, payload_label, latency, True)
            except Exception as e:
                recorder.record("sequential", 1, payload_label, 0.0, False, str(e))
        wall = time.perf_counter() - start
        print(f"[sequential/{payload_label}] {n} publishes in {wall:.2f}s -> {n / wall:.1f} msgs/sec")
        recorder.summary("sequential", payload_label)
    finally:
        await comm.close()


async def run_concurrent_single(cfg: XmppConfig, n: int, recorder: Recorder) -> None:
    """Same client, same N publishes, fired via asyncio.gather."""
    comm = await open_publisher(cfg, "camera", ALL_PUBLISHED_INTERFACES)

    async def _one(i: int) -> None:
        interface, factory = STATE_INTERFACES[i % len(STATE_INTERFACES)]
        try:
            latency = await timed_set_state(comm, interface, factory())
            recorder.record("concurrent-single", n, "mixed", latency, True)
        except Exception as e:
            recorder.record("concurrent-single", n, "mixed", 0.0, False, str(e))

    try:
        start = time.perf_counter()
        await asyncio.gather(*(_one(i) for i in range(n)))
        wall = time.perf_counter() - start
        print(f"[concurrent-single] {n} publishes in {wall:.2f}s -> {n / wall:.1f} msgs/sec")
        recorder.summary("concurrent-single")
    finally:
        await comm.close()


async def run_concurrent_many(
    cfg: XmppConfig, k: int, n_per_client: int, recorder: Recorder, register_via: str | None
) -> None:
    """K independent clients, each its own XmppComm, each publishing n_per_client times
    sequentially, all K running at the same time -- the "fleet of modules" scenario."""
    names = [f"bench{i}" for i in range(k)]
    if register_via:
        register_accounts(register_via, cfg.domain, cfg.password, names)

    async def _client(name: str) -> None:
        comm = await open_publisher(cfg, name, ALL_PUBLISHED_INTERFACES)
        try:
            for i in range(n_per_client):
                interface, factory = STATE_INTERFACES[i % len(STATE_INTERFACES)]
                try:
                    latency = await timed_set_state(comm, interface, factory())
                    recorder.record("concurrent-many", k, "mixed", latency, True)
                except Exception as e:
                    recorder.record("concurrent-many", k, "mixed", 0.0, False, str(e))
        finally:
            await comm.close()

    start = time.perf_counter()
    await asyncio.gather(*(_client(name) for name in names))
    wall = time.perf_counter() - start
    total = k * n_per_client
    print(
        f"[concurrent-many] {k} clients x {n_per_client} publishes ({total} total) "
        f"in {wall:.2f}s -> {total / wall:.1f} msgs/sec"
    )
    recorder.summary("concurrent-many")


async def run_rpc(
    cfg: XmppConfig,
    n: int,
    recorder: Recorder,
    register_via: str | None,
    with_background_load: bool,
    k: int,
    n_per_client: int,
) -> None:
    """RPC round-trip latency (XEP-0009 execute()), optionally with scenario-3-style
    background state-push load running concurrently, to isolate whether state traffic
    degrades RPC responsiveness."""
    if register_via:
        register_accounts(
            register_via, cfg.domain, cfg.password, ["camera", "observer"] + [f"bench{i}" for i in range(k)]
        )

    camera_comm = make_comm(cfg, "camera")
    camera = DummyCamera(name="camera", comm=camera_comm)
    observer_comm = make_comm(cfg, "observer")

    background_task = None
    try:
        await camera.startup()
        await observer_comm.open()

        deadline = time.perf_counter() + 15.0
        while "camera" not in observer_comm.clients and time.perf_counter() < deadline:
            await asyncio.sleep(0.1)
        if "camera" not in observer_comm.clients:
            raise RuntimeError('"camera" never appeared in observer_comm.clients')

        scenario = "rpc-under-load" if with_background_load else "rpc-baseline"
        if with_background_load:
            background_recorder = Recorder(output=None, shaper_label=recorder.shaper_label)
            background_task = asyncio.ensure_future(
                run_concurrent_many(cfg, k, n_per_client, background_recorder, None)
            )

        async with observer_comm.proxy("camera", ICooling) as cam:
            for i in range(n):
                start = time.perf_counter()
                try:
                    await cam.set_cooling(enabled=True, setpoint=-20.0 - (i % 5))
                    recorder.record(scenario, 1, "n/a", time.perf_counter() - start, True)
                except Exception as e:
                    recorder.record(scenario, 1, "n/a", 0.0, False, str(e))
        recorder.summary(scenario)
    finally:
        if background_task is not None:
            await background_task
        await observer_comm.close()
        await camera.close()


async def run_payload(cfg: XmppConfig, n: int, recorder: Recorder) -> None:
    """Repeat the sequential scenario with a minimal state and a much larger one, to
    separate serialization cost from fixed per-publish IQ/transport overhead."""
    await run_sequential(cfg, n, recorder, payload_label="small", pair=SMALL_STATE)
    await run_sequential(cfg, n, recorder, payload_label="large", pair=LARGE_STATE)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "scenario", choices=["sequential", "concurrent-single", "concurrent-many", "rpc", "payload", "all"]
    )
    parser.add_argument("--n", type=int, default=100, help="publishes per client (default: 100)")
    parser.add_argument("--k", type=int, default=10, help="number of clients for concurrent-many/rpc (default: 10)")
    parser.add_argument("--output", default="benchmark_results.jsonl", help="JSONL output file (default: %(default)s)")
    parser.add_argument(
        "--shaper-label", default="default", help="tag for the shaper config under test (default: %(default)s)"
    )
    parser.add_argument(
        "--register-via",
        default=None,
        help="docker container name to run `ejabberdctl register` in for extra bench<N> accounts "
        "(needed by concurrent-many/rpc when --k exceeds the pre-registered camera/observer)",
    )
    parser.add_argument(
        "--rpc-with-load", action="store_true", help="run the rpc scenario with concurrent-many background load"
    )
    args = parser.parse_args()

    cfg = env_config()
    recorder = Recorder(output=args.output, shaper_label=args.shaper_label)

    if args.scenario in ("sequential", "all"):
        await run_sequential(cfg, args.n, recorder)
    if args.scenario in ("concurrent-single", "all"):
        await run_concurrent_single(cfg, args.n, recorder)
    if args.scenario in ("concurrent-many", "all"):
        await run_concurrent_many(cfg, args.k, args.n, recorder, args.register_via)
    if args.scenario in ("rpc", "all"):
        await run_rpc(cfg, args.n, recorder, args.register_via, args.rpc_with_load, args.k, args.n)
    if args.scenario in ("payload", "all"):
        await run_payload(cfg, args.n, recorder)


if __name__ == "__main__":
    asyncio.run(main())
