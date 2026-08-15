# Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)

Status: investigating, open. Paused 2026-08-05 (session budget) — resume from "Next steps" below.

Repos: pyobs-core (client-side code implicated), pyobs-monet (has the SAAO module configs used
during investigation), production ejabberd on `monet.saao.ac.za` (config/state implicated, not a
repo).

## Problem

User reported: the running pyobs-gui at SAAO (`gui-saao.yaml`, connecting to
`admin@monet.saao.ac.za`) displays every log message twice. Confirmed facts from the user:

- Happens from a fresh launch, no logout/reconnect needed.
- Every module's log lines are duplicated uniformly, not just one module.
- Only one process per module is running (no duplicate publishers).

## What's ruled out

- **pyobs-gui client code**: `MainWindow`'s `add_log` Qt signal is connected exactly once
  (`mainwindow.py:254`), `LogModel.add_entry` appends once. `EventsWidget` explicitly skips
  `LogEvent` (`eventswidget.py:72`). Not a GUI rendering bug.
- **`MainWindow.discard_all_widgets()` leak on logout** (`mainwindow.py:375-381` doesn't
  unregister `MainWindow`'s own direct `self.comm.register_event(LogEvent, ...)` handler) — a
  real latent bug, but not the trigger here since duplication reproduces on a fresh launch with no
  logout involved.
- **pyobs-core `XmppComm._safe_send()` retry-on-timeout** (added 2026-07-15,
  commit `9084f0434044d52ac9562cf6269e6b080e9dac64`, fixes #664): my first theory — blindly
  retries the non-idempotent `xep_0163.publish()` call on a 15s client-side timeout. **Refuted**:
  captured raw XML for duplicate pairs (`scripts/xmpp/watch_log_events_raw.py`) and the two
  copies of a given `uuid` arrive 0.000–0.014s apart, not the ~16-19s a timeout-then-retry would
  produce. Also, all SAAO modules are already on dev28+ (well past dev21, the first release
  containing that commit), so "not yet deployed" doesn't apply either.
- **Duplicate client connections**: `ejabberdctl connected_users_info` on production shows
  exactly one session per module, all on resource `/pyobs`. Not double-connected processes.
- **Leftover/duplicate roster entries**: `ejabberdctl get_roster fli230 monet.saao.ac.za` shows
  one `both`-subscription entry per contact, all under `monet.saao.ac.za` — no stray
  `monti.monet.saao.ac.za` duplicates from the recent host addition (see below).
- **Inherent to ejabberd's PEP+flat plugin combination in general**: built a local docker
  ejabberd (`/tmp/.../scratchpad/ejabberd-repro/`, see below) configured to mirror production's
  actual `mod_pubsub` settings (`plugins: [flat, pep]`, no `default_node_config` override) and
  drove it with pyobs-core's **real, unmodified** `XmppComm` — 5 published events, 5 received, **no
  duplication**. So a from-scratch setup with matching module config does not reproduce it —
  something about the actual state of the SAAO ejabberd instance is the cause, not a general flaw
  in pyobs-core's code or in PEP semantics.

## What's confirmed

1. **Reproduces with a bare, independent XMPP client** — not GUI-specific. Script:
   `pyobs-core/scripts/xmpp/watch_log_events.py`. Connecting as
   `admin@monet.saao.ac.za/pyobs-debug` (a brand-new resource, unrelated to the running GUI) and
   registering only `LogEvent` reproduces the exact same double delivery.

2. **Duplicate pairs share the same event `uuid`** (`Event.uuid`, generated once at construction
   — `pyobs/events/event.py:20`) and arrive near-simultaneously (sub-15ms apart). This is genuine
   near-instant double delivery, not a delayed republish.

3. **Root mechanism, isolated experimentally**: `XmppComm._register_events()`
   (`pyobs/comm/xmpp/xmppcomm.py:802-817`) calls
   `self.client.plugin["xep_0163"].add_interest(...)` for every registered event class
   (line 813) whenever a handler is passed to `register_event()`. This declares explicit
   `+notify` interest via entity caps — standard XEP-0163 client behavior, present since 2019
   (`git log -S add_interest` shows no recent changes to this line).

   Built `scripts/xmpp/watch_log_events_no_interest.py`: a bare slixmpp client that registers
   `xep_0163` (so it understands PEP stanzas) but **never calls `add_interest()`**. Run against
   production: received every `LogEvent` from every module **exactly once**, zero duplicates,
   including fli230's rapid-fire exposure-sequence logging that showed 100% duplication in the
   normal path.

   **Conclusion**: ejabberd on `monet.saao.ac.za` is currently delivering PEP notifications via
   two independent paths simultaneously for subscribers that declare explicit interest — implicit
   roster-presence-based auto-subscribe (which alone is sufficient and fires once), *and*
   explicit-interest-based delivery (which pyobs's `add_interest()` call also triggers). Both
   fire, so every subscriber gets two copies of everything.

4. **Timing correlation, not yet proven causal**: `/etc/ejabberd/ejabberd.yml` on the production
   server (`ssh ms`, i.e. `monet.saao.ac.za` as root) was last modified **2026-08-04 11:18** — the
   day before this investigation, and around when the user says they started noticing the
   duplication (much better fit than the 2026-07-15 pyobs-core commit). Diffing against the
   most recent auto-backup (`ejabberd.yml.bak.20260715083232`, from a `2026-07-15` package
   install) shows three changes landed since:
   - A **new virtual host** `monet.saao.ac.za` was added (previously only
     `monti.monet.saao.ac.za` existed as a vhost on this ejabberd instance).
   - `tls: false` → `tls: true` for c2s (user confirmed: "I enabled TLS").
   - Shaper `rate`/`burst_size`/`fast` limits raised ~10x (3000→30000 / 20000→200000 /
     200000→2000000).

   None of these three, individually, is *proven* to cause the double-PEP-delivery — that's the
   open thread. The local docker repro (point above) used a single, TLS-off, single-vhost setup,
   so it didn't test the "two vhosts on one ejabberd node" configuration at all. That's the most
   likely remaining candidate: **the new `monet.saao.ac.za` vhost coexisting with
   `monti.monet.saao.ac.za` on the same ejabberd node may be causing PEP/roster logic to
   double-fire**, e.g. via shared roster group scoping, s2s/component routing between the two
   similarly-named hosts, or some interaction between `mod_shared_roster` and having two vhosts.

5. **Mnesia state is large and not obviously pruned**: `ejabberdctl mnesia_info_ctl` on
   production shows `pubsub_item: 19751 records` across `pubsub_node: 99 records` — averaging
   ~200 stored items per node. Production's `mod_pubsub` config has no `default_node_config`
   (unlike the local test/repro configs, which set `max_items: 1`), so this may just be
   expected-but-wasteful growth, not directly related to the duplication — not yet investigated
   further.

## Next steps

1. **Finish checking for a literal duplicate subscriber entry** on one specific node
   (`urn:pyobs:event:LogEvent:1` hosted at `fli230@monet.saao.ac.za`, PEP nodes are addressed via
   the owner's own bare JID as the pubsub service). In progress: `admin@monet.saao.ac.za` is
   **not** an actual ejabberd ACL admin (checked `acl.admin.user` in `ejabberd.yml` — it's just a
   template placeholder `[""]`), so only the node *owner* can query `pubsub#owner`
   subscriptions. Found fli230's real production password
   (`pyobs-monet/config/south/frontend/_fli.yaml:91`, do not commit/leak this) and started
   `/tmp/claude-1000/.../scratchpad/check_node_subscriptions.py` to connect as
   `fli230@monet.saao.ac.za/pyobs-debug-owner` (deliberately different resource from the live
   module's `/pyobs`, to avoid conflict-kicking production) and call
   `xep_0060.get_node_subscriptions(service="fli230@monet.saao.ac.za", node="urn:pyobs:event:LogEvent:1")`.
   **This connection attempt timed out** (`TimeoutError` waiting for `session_start`) — not yet
   debugged why (likely needs an explicit `host=`/port on `client.connect()`, unlike the
   `admin`-based scripts which worked fine with the same connect pattern — compare against
   `watch_log_events.py`'s use of pyobs's own `XmppComm(server=...)` vs this script's raw
   `slixmpp.ClientXMPP.connect()` with no host override). Fix and rerun.

2. **Test the two-vhost theory directly**: extend the local docker repro
   (`/tmp/claude-1000/.../scratchpad/ejabberd-repro/`) to configure **two** vhosts
   (e.g. `a.localtest` and `b.localtest`) both with `mod_pubsub`/`pep`, and see if a subscriber on
   one vhost starts getting double delivery for publishers on the same vhost once a second,
   similarly-scoped vhost exists. This is the most promising lead since it's the one config
   change that both (a) isn't present in the already-tried repro and (b) uniquely correlates with
   the timing the user reported.

3. Ask the user directly: did double-logging start specifically after they flipped
   `tls: false → true`, or was `monet.saao.ac.za` added as a vhost around the same time for an
   unrelated reason (e.g. migrating off `monti.monet.saao.ac.za`)? If they know the sequencing it
   narrows this a lot faster than more server-side archaeology.

4. Once root cause is nailed down, decide the fix:
   - If it's genuinely an ejabberd config/vhost issue: fix on the production server (no
     pyobs-core change needed).
   - If it turns out to be something pyobs-core should defend against regardless (e.g. any
     ejabberd multi-vhost setup could trigger this): consider dropping the `add_interest()` call
     in `_register_events()` (`xmppcomm.py:813`) since the no-interest experiment proved implicit
     roster delivery alone is sufficient *on this server* — but note this needs checking against
     deployments where a subscriber might not yet be mutually rostered with a publisher (implicit
     PEP delivery requires an established roster subscription; explicit interest does not
     necessarily, depending on node access model). Don't remove it without checking that case.
   - Defensive, root-cause-independent fallback: dedupe incoming events by `event.uuid` within a
     short window before dispatching to handlers (e.g. in `Comm._send_event_to_module` or
     `XmppComm._handle_event`). Papers over the symptom and wastes bandwidth either way, so treat
     as a last resort, not the fix.

## Artifacts from this session

Committed nowhere yet (all present on disk, none pushed):

- `pyobs-core/scripts/xmpp/watch_log_events.py` — bare `XmppComm`-based LogEvent listener with
  counter, env-var configured (`PYOBS_XMPP_JID`/`PYOBS_XMPP_PASSWORD`/etc, following this
  folder's existing convention).
- `pyobs-core/scripts/xmpp/watch_log_events_raw.py` — same, but taps the raw XML to print
  message-stanza id, pubsub item id, embedded event `uuid`, and flags duplicates with the time
  delta since first seen.
- `pyobs-core/scripts/xmpp/watch_log_events_no_interest.py` — raw `slixmpp.ClientXMPP` that
  registers `xep_0060`/`xep_0163` but deliberately never calls `add_interest()`. This is the
  script that proved implicit-only delivery has zero duplicates.
- `pyobs-core/scripts/xmpp/show_module_versions.py` — prints each connected module's
  `IModule` capabilities version, used to rule out "fix not yet deployed."
- `/tmp/claude-1000/-home-husser-code-pyobs-pyobs-core/b92461b2-00ac-40df-8785-80dbb5b61043/scratchpad/ejabberd-repro/`
  — docker-compose + `ejabberd.yml` mirroring production's `mod_pubsub` config (single vhost
  `localhost`, `flat`+`pep` plugins, no `default_node_config` override), plus `repro.py` driving
  real `pyobs.comm.xmpp.XmppComm` publisher/subscriber pair against it. **Container is still
  running** (`docker compose -p ejabberd-repro ps` from that dir) — tear down with
  `docker compose down` when done, or reuse for the two-vhost test in step 2 above.
- `/tmp/claude-1000/-home-husser-code-pyobs-pyobs-core/b92461b2-00ac-40df-8785-80dbb5b61043/scratchpad/check_node_subscriptions.py`
  — the fli230-owner `pubsub#owner` subscription-list query, currently broken (connection
  timeout, see Next steps #1).
- Note: the `/tmp/claude-1000/...` scratchpad path is session-specific and may not survive to the
  next session — if resuming later and these files are gone, they're all small/quick to
  reconstruct from the descriptions above.

## Access used

- SSH: `ms` alias in `~/.ssh/config` → `root@monet.saao.ac.za`. Used read-only so far
  (`ejabberdctl status/connected_users_info/mnesia_info_ctl/get_roster`, `cat`/`diff` on
  `/etc/ejabberd/ejabberd.yml` and its auto-backups). Attempted `ejabberdctl debug` (interactive
  Erlang shell) to dump raw mnesia table rows — **abandoned as too fragile/risky over piped
  non-TTY stdin against a live production Erlang node**; if this is needed later, do it
  interactively (real terminal), not scripted.
- XMPP: connected to production as `admin@monet.saao.ac.za` (password already known/in
  `pytel-dev/configs/gui-saao.yaml`) on throwaway resources (`/pyobs-debug` etc), and briefly
  attempted `fli230@monet.saao.ac.za` (password from `pyobs-monet/config/south/frontend/_fli.yaml`,
  **do not commit this file's contents anywhere**) on a throwaway resource distinct from the live
  module's `/pyobs` resource, specifically to avoid conflict-kicking the running production
  module.
