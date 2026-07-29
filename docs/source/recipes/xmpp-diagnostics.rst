.. _xmpp-diagnostics:

Diagnosing and load-testing the XMPP/ejabberd transport
=========================================================

*pyobs-core* ships a handful of standalone scripts under :file:`scripts/xmpp/` for inspecting a live
ejabberd deployment, tracking down XMPP-layer connectivity problems, and load-testing the transport.
None of these are part of the pytest suite — they're meant to be run manually, against a real (often
local docker-compose) ejabberd server, while investigating something concrete. They all speak raw
``slixmpp`` rather than going through ``XmppComm``, so they work independently of whether pyobs's own
comm layer is behaving correctly.

Most accept the same connection environment variables as the integration test suite
(:file:`tests/integration/conftest.py`):

.. code-block:: text

    PYOBS_TEST_XMPP_HOST         (default: localhost)
    PYOBS_TEST_XMPP_DOMAIN       (default: same as host)
    PYOBS_TEST_XMPP_PORT         (default: 5222)
    PYOBS_TEST_XMPP_PASSWORD     (default: pyobs)
    PYOBS_TEST_XMPP_TLS          (default: 0)
    PYOBS_TEST_XMPP_IGNORE_CERT  (default: 1)

Point them at a real deployment (setting ``PYOBS_TEST_XMPP_TLS=1`` and a real password) to run any of
these against production rather than a local test server — see :ref:`installing-ejabberd` for how to set
one up.

show_module_info.py — inspect a live module's presence and capabilities
-------------------------------------------------------------------------

Connects as an observer and pretty-prints a module's presence state, its disco#info (XEP-0030) features,
and the ``urn:pyobs:capabilities:*`` payloads it's published — i.e. exactly what another module sees
when it discovers this one for the first time. Useful for confirming a module actually announced the
interfaces you expect, or for diagnosing the kind of capability-fetch problems covered in
:file:`specs/plans/ejabberd-throughput-benchmarking.md`::

    python scripts/xmpp/show_module_info.py camera
    python scripts/xmpp/show_module_info.py camera telescope focuser
    python scripts/xmpp/show_module_info.py camera --raw   # also dump the raw disco#info XML

list_pubsub_nodes.py — list pyobs pubsub nodes and their latest item
------------------------------------------------------------------------

Lists every pubsub node on the server matching a prefix (``pyobs:state:`` by default — pyobs's state-push
nodes are named ``pyobs:state:<module>:<Interface>``) along with a preview of its most recently published
item, without needing to know in advance which modules/interfaces exist::

    python scripts/xmpp/list_pubsub_nodes.py
    python scripts/xmpp/list_pubsub_nodes.py --user camera --prefix pyobs:state:telescope:

delete_pubsub_nodes.py — clean up leftover pubsub nodes
-----------------------------------------------------------

Connects as a node's owner and deletes every node matching a prefix. Handy for resetting a test ejabberd
instance between runs, or cleaning up nodes left behind by a module that was renamed or retired::

    python scripts/xmpp/delete_pubsub_nodes.py --user camera
    python scripts/xmpp/delete_pubsub_nodes.py --user telescope --prefix pyobs:state:telescope:

check_ejabberd_notify.py — minimal pubsub notification sanity check
-------------------------------------------------------------------

The most stripped-down possible test: two raw ``slixmpp`` clients, no pyobs code at all, one creates a
pubsub node and publishes to it, the other subscribes and checks whether it actually receives the
notification. If pyobs-level state pushes aren't arriving, run this first — it tells you whether the
problem is in ejabberd's pubsub delivery itself or somewhere in pyobs's own comm layer::

    python scripts/xmpp/check_ejabberd_notify.py

benchmark_state_throughput.py — throughput/latency benchmarking and incident reproduction
---------------------------------------------------------------------------------------------

The most substantial of these scripts: benchmarks XMPP state-push (XEP-0060) and RPC (XEP-0009) latency
and throughput under various concurrency shapes, and can reproduce specific connection-churn incidents
(a module joining an already-stable fleet, several modules reconnecting at once). Deliberately not a
pytest test — these runs are long, resource-heavy, and produce a JSONL data file for analysis rather
than a pass/fail assertion. See the module docstring (``python scripts/xmpp/benchmark_state_throughput.py
--help``) for the full scenario list and options; the short version:

.. code-block:: text

    sequential          one client, N publishes, awaited one at a time (baseline)
    concurrent-single    same, but fired concurrently via asyncio.gather
    concurrent-many      K independent clients publishing concurrently (the realistic fleet case)
    reconnect-storm       K clients connect simultaneously, then mutually fetch capabilities
    late-joiner           K already-stable peers, then one more joins and exchanges capabilities
    rpc                   RPC round-trip latency, optionally with concurrent-many running as background load
    payload                repeats "sequential" with a minimal and a large synthetic state, to separate
                           serialization cost from fixed per-publish overhead
    all                    runs every scenario above in sequence

Scenarios needing more than the two accounts a fresh test fixture pre-registers
(``concurrent-many``/``reconnect-storm``/``late-joiner``/``rpc``) can auto-register the extra ``bench<N>``
accounts they need via ``--register-via <container>`` (for the local docker-compose ejabberd) or
``--register-via local`` (bare ``ejabberdctl register``, for a real server where the script runs on the
ejabberd host itself). To instead run against a real fleet's own already-registered accounts — with each
account's own password, not a shared throwaway one — use ``--users`` (and, for ``late-joiner``,
``--joiner``) together with ``PYOBS_TEST_XMPP_CREDENTIALS_FILE`` pointing at a JSON file of
``{"account": "password", ...}`` (keep this file out of version control)::

    # local docker-compose ejabberd, synthetic throwaway accounts
    python scripts/xmpp/benchmark_state_throughput.py concurrent-many --k 25 --n 20 \
        --register-via test-ejabberd

    # real fleet accounts, real passwords
    PYOBS_TEST_XMPP_CREDENTIALS_FILE=/path/to/creds.json \
    python scripts/xmpp/benchmark_state_throughput.py late-joiner \
        --users acquisition,autofocus,imagewatcher,imagewriter,scheduler,flatfield,focusmodel \
        --joiner dome --settle-time 60

Comparing shaper configs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The script itself doesn't manage the docker container — restart it with the desired shaper config first,
then tag the run with ``--shaper-label`` so results stay distinguishable:

.. code-block:: text

    docker compose -f tests/xmpp/docker-compose.yml up -d                                                # default
    docker compose -f tests/xmpp/docker-compose.yml -f scripts/xmpp/docker-compose.shaper-10x.yml up -d   # 10x rate
    docker compose -f tests/xmpp/docker-compose.yml -f scripts/xmpp/docker-compose.fast-shaper.yml up -d  # fast-track

(``ejabberd-shaper-10x.yml`` and ``ejabberd-fast-shaper.yml`` are the corresponding ejabberd config
overrides these compose files mount in; look there if you need to see or tweak the actual shaper values.)

Background: the incident behind these tools
----------------------------------------------

The investigation that motivated most of these scenarios — a real production incident where modules
joining an ejabberd fleet got silent capability-fetch timeouts — is written up in full, including root
cause, in :file:`specs/plans/ejabberd-throughput-benchmarking.md` in the repository.
