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

"concurrent-many", "reconnect-storm", and "rpc" need more than the two accounts (camera,
observer) the test fixture pre-registers. Pass --register-via <container-name> to have the
script register the extra bench<N> accounts itself, via `docker exec <container> ejabberdctl
register ...`, before running -- or --register-via local to run bare `ejabberdctl register`
directly (no docker), for a real server where ejabberdctl is on PATH (e.g. running the script
on the ejabberd host itself, or over SSH with an interactive shell that has it).

Usage:
    python scripts/xmpp/benchmark_state_throughput.py sequential --n 100
    python scripts/xmpp/benchmark_state_throughput.py concurrent-single --n 100
    python scripts/xmpp/benchmark_state_throughput.py concurrent-many --k 25 --n 20 \\
        --register-via test-ejabberd
    python scripts/xmpp/benchmark_state_throughput.py reconnect-storm --k 4 \\
        --register-via test-ejabberd
    python scripts/xmpp/benchmark_state_throughput.py reconnect-storm --k 4 \\
        --register-via local   # against a real server, no docker
    python scripts/xmpp/benchmark_state_throughput.py late-joiner --k 7 --settle-time 2 \\
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
    # per-account password overrides -- for a real server with pre-existing named
    # accounts (each with its own password), as opposed to uniform throwaway bench<N>
    # accounts that all share PYOBS_TEST_XMPP_PASSWORD.
    passwords: dict[str, str] = field(default_factory=dict)


def env_config() -> XmppConfig:
    host = os.environ.get("PYOBS_TEST_XMPP_HOST", "localhost")
    passwords: dict[str, str] = {}
    creds_file = os.environ.get("PYOBS_TEST_XMPP_CREDENTIALS_FILE")
    if creds_file:
        with open(creds_file) as f:
            passwords = json.load(f)
    return XmppConfig(
        host=host,
        domain=os.environ.get("PYOBS_TEST_XMPP_DOMAIN", host),
        port=int(os.environ.get("PYOBS_TEST_XMPP_PORT", "5222")),
        password=os.environ.get("PYOBS_TEST_XMPP_PASSWORD", "pyobs"),
        use_tls=os.environ.get("PYOBS_TEST_XMPP_TLS", "0") == "1",
        ignore_cert_errors=os.environ.get("PYOBS_TEST_XMPP_IGNORE_CERT", "1") == "1",
        passwords=passwords,
    )


def make_comm(cfg: XmppConfig, user: str) -> XmppComm:
    """Build an unopened XmppComm for ``<user>@<domain>``."""
    return XmppComm(
        user=user,
        domain=cfg.domain,
        password=cfg.passwords.get(user, cfg.password),
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


def register_accounts(domain: str, password: str, users: list[str], container: str | None = None) -> None:
    """Idempotently register accounts via `ejabberdctl register`.

    container: docker container name, for the disposable docker-compose test setup (runs via
        `docker exec <container> ejabberdctl ...`). None runs bare `ejabberdctl` directly --
        for a real server where the script itself runs on (or has ejabberdctl on PATH for)
        the ejabberd host, since production servers aren't necessarily containerized at all.

    Conflicts (already registered) are expected on reruns and ignored -- mirrors the "!"
    prefix convention used for CTL_ON_START in tests/xmpp/docker-compose.yml.
    """
    base_cmd = ["docker", "exec", container, "ejabberdctl"] if container else ["ejabberdctl"]
    for user in users:
        result = subprocess.run(
            [*base_cmd, "register", user, domain, password],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "already registered" not in result.stderr + result.stdout:
            raise RuntimeError(f"Failed to register {user}@{domain}: {result.stdout} {result.stderr}")


def maybe_register(register_via: str | None, cfg: XmppConfig, users: list[str]) -> None:
    """Register users if --register-via was given. "local" means bare `ejabberdctl` (the
    script runs on/with access to the ejabberd host itself, e.g. a real production server);
    anything else is a docker container name for the disposable docker-compose test setup."""
    if register_via is None:
        return
    container = None if register_via == "local" else register_via
    register_accounts(cfg.domain, cfg.password, users, container=container)


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
    maybe_register(register_via, cfg, names)

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


async def run_reconnect_storm(
    cfg: XmppConfig,
    k: int,
    recorder: Recorder,
    register_via: str | None,
    recheck_after: float = 0.0,
    names: list[str] | None = None,
) -> None:
    """K independent clients all connect/auth/bind/publish-presence within the same burst
    (via asyncio.gather), then every client fetches IModule capabilities from every other
    client at once -- modeling a handful of modules restarting together (not necessarily a
    whole-fleet reconnect storm) immediately followed by the mutual capability discovery
    every pyobs proxy triggers on first use (Comm._get_client -> _fetch_and_update_capabilities).

    Motivated by production incidents on pyobs-iag50 (see specs/plans/ejabberd-throughput-
    benchmarking.md's "Full incident timeline" for the complete writeup): disco#info (XEP-0030)
    queries between freshly-restarted modules got no reply at all for a full 10s timeout,
    three attempts in a row, despite every peer already being fully started (not mid-boot) by
    the time the queries were sent -- and, in the largest incident (7 modules, no BROT/MQTT
    module involved at all), one module's own outgoing send_event() (log forwarding, via the
    *bounded* _safe_send retry budget) later hit a genuine unhandled IqTimeout, twice, 39s and
    85s *after* the initial capability-fetch storm had already stopped -- i.e. failures
    recurred well past any plausible "still settling in from reconnecting" window, on
    connections that had been idle and ostensibly fine in between.

    If recheck_after > 0, after the initial connect+fetch burst the same (already-connected,
    not reconnected) clients sit idle for that many seconds and then repeat the mutual fetch
    -- testing whether failures can recur on an already-established, previously-fine
    connection, not just during initial connection churn.
    """
    names = names if names is not None else [f"bench{i}" for i in range(k)]
    maybe_register(register_via, cfg, names)

    comms: dict[str, XmppComm] = {}

    async def _connect(name: str) -> None:
        comms[name] = await open_publisher(cfg, name, [])

    start = time.perf_counter()
    await asyncio.gather(*(_connect(name) for name in names))
    connect_wall = time.perf_counter() - start
    print(f"[reconnect-storm] {k} clients connected+ready in {connect_wall:.2f}s")

    async def _fetch(requester: str, target: str, scenario: str) -> None:
        comm = comms[requester]
        start = time.perf_counter()
        try:
            # get_capabilities (XmppComm) retries forever on failure -- bound our own
            # patience so a genuine reproduction doesn't hang the benchmark script itself
            await asyncio.wait_for(comm.get_capabilities(target, IModule), timeout=60.0)
            recorder.record(scenario, k, "n/a", time.perf_counter() - start, True)
        except Exception as e:
            recorder.record(scenario, k, "n/a", time.perf_counter() - start, False, str(e))

    async def _round(scenario: str) -> None:
        start = time.perf_counter()
        await asyncio.gather(*(_fetch(a, b, scenario) for a in names for b in names if a != b))
        wall = time.perf_counter() - start
        total = k * (k - 1)
        print(f"[{scenario}] {total} mutual capability fetches in {wall:.2f}s")
        recorder.summary(scenario)

    try:
        await _round("reconnect-storm")
        if recheck_after > 0:
            print(f"[reconnect-storm] {k} clients idle for {recheck_after:.0f}s, then re-checking...")
            await asyncio.sleep(recheck_after)
            await _round("reconnect-storm-recheck")
    finally:
        await asyncio.gather(*(c.close() for c in comms.values()))


async def run_late_joiner(
    cfg: XmppConfig,
    k: int,
    recorder: Recorder,
    register_via: str | None,
    settle_time: float = 2.0,
    existing_names: list[str] | None = None,
    joiner_name: str = "benchjoiner",
) -> None:
    """K clients connect and settle (staying open, idle) for settle_time seconds -- modeling an
    already-stable fleet. Then one *more* client connects and immediately exchanges IModule
    capabilities with every existing peer, both directions -- modeling a single module joining an
    already-running fleet, not a simultaneous multi-client reconnect.

    Motivated by two production incidents on pyobs-iag50, staggered ~5 minutes apart per module
    specifically to rule out simultaneity: a fleet of exactly 7 already-connected, already-stable
    modules (no restarts, no reconnects) had an 8th module join -- once `flatfield`, once (in a
    separate occurrence) `dome` -- and both times, 30-something seconds later, every single
    capability-fetch pair involving the newcomer failed with a silent 10s timeout, while none of the
    7 already-established peers ever failed to reach each other. Two independent occurrences, same
    exact peer count (7 existing + 1 joining), same result, regardless of which module joined --
    this scenario tests whether that specific peer-count threshold reproduces locally. Sweep --k to
    find where (if anywhere) it breaks against a given server.
    """
    existing_names = existing_names if existing_names is not None else [f"bench{i}" for i in range(k)]
    maybe_register(register_via, cfg, [*existing_names, joiner_name])

    comms: dict[str, XmppComm] = {}

    async def _connect(name: str) -> None:
        comms[name] = await open_publisher(cfg, name, [])

    await asyncio.gather(*(_connect(name) for name in existing_names))
    print(f"[late-joiner] {k} peers connected+ready, settling for {settle_time:.0f}s...")
    await asyncio.sleep(settle_time)

    start = time.perf_counter()
    await _connect(joiner_name)
    connect_wall = time.perf_counter() - start
    print(f"[late-joiner] joiner connected in {connect_wall:.2f}s (existing fleet size {k})")

    async def _fetch(requester: str, target: str) -> None:
        comm = comms[requester]
        start = time.perf_counter()
        try:
            await asyncio.wait_for(comm.get_capabilities(target, IModule), timeout=60.0)
            recorder.record("late-joiner", k, "n/a", time.perf_counter() - start, True)
        except Exception as e:
            recorder.record("late-joiner", k, "n/a", time.perf_counter() - start, False, str(e))

    try:
        pairs = [(joiner_name, name) for name in existing_names] + [(name, joiner_name) for name in existing_names]
        start = time.perf_counter()
        await asyncio.gather(*(_fetch(a, b) for a, b in pairs))
        wall = time.perf_counter() - start
        print(f"[late-joiner] {len(pairs)} capability fetches between joiner and {k} existing peers in {wall:.2f}s")
        recorder.summary("late-joiner")
    finally:
        await asyncio.gather(*(c.close() for c in comms.values()))


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
    maybe_register(register_via, cfg, ["camera", "observer"] + [f"bench{i}" for i in range(k)])

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
        "scenario",
        choices=[
            "sequential",
            "concurrent-single",
            "concurrent-many",
            "reconnect-storm",
            "late-joiner",
            "rpc",
            "payload",
            "all",
        ],
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
        help="docker container name to run `ejabberdctl register` in (or the literal value "
        "'local' to run bare `ejabberdctl register`, no docker -- for a real server) for the "
        "extra accounts concurrent-many/reconnect-storm/rpc need beyond camera/observer",
    )
    parser.add_argument(
        "--rpc-with-load", action="store_true", help="run the rpc scenario with concurrent-many background load"
    )
    parser.add_argument(
        "--recheck-after",
        type=float,
        default=0.0,
        help="reconnect-storm only: after the initial burst, wait this many seconds (same "
        "connections, no reconnect) then repeat the mutual capability fetch -- tests whether "
        "failures can recur on an already-idle, previously-fine connection (default: 0, disabled)",
    )
    parser.add_argument(
        "--settle-time",
        type=float,
        default=2.0,
        help="late-joiner only: seconds the existing --k peers sit idle before the one extra "
        "client joins (default: 2.0)",
    )
    parser.add_argument(
        "--users",
        default=None,
        help="reconnect-storm/late-joiner only: comma-separated real account names to use "
        "instead of the generated bench<N> accounts (e.g. a real fleet's pre-registered "
        "module JIDs). Overrides --k to len(--users). Pair with "
        "PYOBS_TEST_XMPP_CREDENTIALS_FILE for per-account passwords.",
    )
    parser.add_argument(
        "--joiner",
        default="benchjoiner",
        help="late-joiner only: account name for the one extra client that joins after "
        "--settle-time (default: benchjoiner)",
    )
    args = parser.parse_args()

    cfg = env_config()
    recorder = Recorder(output=args.output, shaper_label=args.shaper_label)
    users = args.users.split(",") if args.users else None
    k = len(users) if users is not None else args.k

    if args.scenario in ("sequential", "all"):
        await run_sequential(cfg, args.n, recorder)
    if args.scenario in ("concurrent-single", "all"):
        await run_concurrent_single(cfg, args.n, recorder)
    if args.scenario in ("concurrent-many", "all"):
        await run_concurrent_many(cfg, args.k, args.n, recorder, args.register_via)
    if args.scenario in ("reconnect-storm", "all"):
        await run_reconnect_storm(cfg, k, recorder, args.register_via, args.recheck_after, names=users)
    if args.scenario in ("late-joiner", "all"):
        await run_late_joiner(
            cfg, k, recorder, args.register_via, args.settle_time, existing_names=users, joiner_name=args.joiner
        )
    if args.scenario in ("rpc", "all"):
        await run_rpc(cfg, args.n, recorder, args.register_via, args.rpc_with_load, args.k, args.n)
    if args.scenario in ("payload", "all"):
        await run_payload(cfg, args.n, recorder)


if __name__ == "__main__":
    asyncio.run(main())
