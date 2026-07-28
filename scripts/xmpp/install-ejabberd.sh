#!/usr/bin/env bash
#
# setup-ejabberd.sh — idempotent ejabberd.yml configuration
#
# Does three things:
#   1. Adds a host to `hosts:` (appends — safe to run multiple times with
#      different hostnames to configure multiple vhosts)
#   2. Adds a loopback-only HTTP API listener on port 5281 for
#      pyobs-web-admin, plus a scoped api_permissions rule
#   3. Raises the c2s shaper limits (see step 6/6b below) — see
#      specs/plans/ejabberd-throughput-benchmarking.md in pyobs-core for why
#
# Usage:
#   sudo ./setup-ejabberd.sh <hostname>
#   sudo ./setup-ejabberd.sh xmpp.pyobs.example.org
#
set -euo pipefail

CONFIG="/etc/ejabberd/ejabberd.yml"
NEW_HOST="${1:?Usage: $0 <new-hostname>}"

# --- 0. Install ejabberd if missing --------------------------------------
if ! command -v ejabberdctl &>/dev/null; then
    echo "ejabberd not found — installing ejabberd-contrib"
    apt-get update
    apt-get install -y ejabberd-contrib
else
    echo "ejabberd already installed — skipping install"
fi

yq_is_correct_variant() {
    # Mikefarah's Go yq supports `-eval`/`eval` subcommand syntax; the
    # Python (kislyuk) yq does not and prints an argparse usage error
    # when given it, which is what this whole script depends on.
    command -v yq &>/dev/null && yq --version 2>&1 | grep -qi mikefarah
}

if ! yq_is_correct_variant; then
    if command -v yq &>/dev/null; then
        echo "Found a 'yq' that isn't the mikefarah/yq (Go) variant this script needs — replacing it"
    else
        echo "yq not found — installing mikefarah/yq"
    fi
    case "$(uname -m)" in
        x86_64)  YQ_ARCH=amd64 ;;
        aarch64) YQ_ARCH=arm64 ;;
        *) echo "Unsupported architecture $(uname -m) for yq auto-install" >&2; exit 1 ;;
    esac
    YQ_VERSION="v4.44.3"
    curl -sL "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_${YQ_ARCH}" \
        -o /usr/local/bin/yq
    chmod +x /usr/local/bin/yq
    hash -r
    if ! yq_is_correct_variant; then
        echo "yq install failed or PATH doesn't pick up /usr/local/bin/yq first" >&2
        exit 1
    fi
    echo "Installed $(yq --version)"
fi

if [[ ! -f "$CONFIG" ]]; then
    echo "Config not found at $CONFIG" >&2
    exit 1
fi

# Backup before touching anything
BACKUP="${CONFIG}.bak.$(date +%Y%m%d%H%M%S)"
cp "$CONFIG" "$BACKUP"
echo "Backed up to $BACKUP"

# yq -i rewrites the file rather than editing it in place at the inode
# level, which loses the original owner/group/mode (ejabberd's daemon
# user needs read access, and the shipped file is usually not
# root-owned/world-readable). Capture and restore it after every edit.
ORIG_OWNER="$(stat -c '%U:%G' "$CONFIG")"
ORIG_MODE="$(stat -c '%a' "$CONFIG")"

restore_perms() {
    chown "$ORIG_OWNER" "$CONFIG"
    chmod "$ORIG_MODE" "$CONFIG"
}

# --- 1. Hostname -------------------------------------------------------
# Appends to the hosts list if not already present, rather than
# replacing it — so running the script again with a different host
# adds a second vhost instead of clobbering the first.
if ! yq eval '.hosts[] | select(. == "'"$NEW_HOST"'")' "$CONFIG" | grep -q .; then
    yq eval -i '.hosts += ["'"$NEW_HOST"'"]' "$CONFIG"
    echo "Added host: $NEW_HOST"
else
    echo "Host $NEW_HOST already present — skipping"
fi

# --- 2. HTTP API listener on 127.0.0.1:5281 -----------------------------
# ejabberd allows only one listener per port, so skip if 5281 is already
# in use rather than duplicating/clobbering it.
if ! yq eval '.listen[] | select(.port == 5281)' "$CONFIG" | grep -q .; then
    yq eval -i '.listen += [{
        "port": 5281,
        "ip": "127.0.0.1",
        "module": "ejabberd_http",
        "request_handlers": {"/api": "mod_http_api"}
    }]' "$CONFIG"
    echo "Added listener on port 5281"
else
    echo "Listener on port 5281 already exists — skipping." \
         "Check its request_handlers manually if it's not already mod_http_api."
fi

# --- 3. Ensure mod_http_api module is enabled ---------------------------
# Already present in the default config; kept explicit and non-destructive.
yq eval -i '.modules.mod_http_api = (.modules.mod_http_api // {})' "$CONFIG"

# --- 4. api_permissions --------------------------------------------------
# Leave "console commands" untouched if present, create it if missing.
yq eval -i '.api_permissions["console commands"] =
  (.api_permissions["console commands"] // {
    "from": "ejabberd_ctl",
    "who": "all",
    "what": "*"
  })' "$CONFIG"

# Add/overwrite the pyobs-web-admin readonly rule.
yq eval -i '.api_permissions["pyobs-web-admin readonly"] = {
  "from": ["mod_http_api"],
  "who": {"access": {"allow": [{"acl": "loopback"}]}},
  "what": [
    "status", "stats", "connected_users_info", "registered_users",
    "user_sessions_info", "get_last", "check_account"
  ]
}' "$CONFIG"

echo "Added/updated api_permissions: pyobs-web-admin readonly"

# --- 5. Port 5280 listener: disable TLS, ensure /ws handler --------------
# Merges into the existing listener rather than replacing it outright, so
# /admin and any other existing request_handlers (e.g. the ACME challenge
# path) are preserved unless they conflict.
if yq eval '.listen[] | select(.port == 5280)' "$CONFIG" | grep -q .; then
    yq eval -i '(.listen[] | select(.port == 5280)).tls = false' "$CONFIG"
    yq eval -i '(.listen[] | select(.port == 5280)).request_handlers["/ws"] = "ejabberd_http_ws"' "$CONFIG"
    echo "Updated port 5280 listener: tls=false, /ws -> ejabberd_http_ws"
else
    echo "No listener found on port 5280 — adding one from scratch"
    yq eval -i '.listen += [{
        "port": 5280,
        "ip": "::",
        "module": "ejabberd_http",
        "tls": false,
        "request_handlers": {
            "/ws": "ejabberd_http_ws",
            "/admin": "ejabberd_web_admin"
        }
    }]' "$CONFIG"
fi

# --- 6. Shaper rate/burst_size: raise the "normal" and "fast" tiers -------
# ejabberd's stock default shaper.normal (rate: 3000, burst_size: 20000) is
# low enough that real pyobs fleet traffic (multiple modules' capability
# fetches/state pushes bursting at once) can trip it -- and doing so exposes
# a real bug in ejabberd's own xmpp_socket.erl: throttled connections are
# reactivated via a fragile scheduled-synthetic-message path instead of an
# immediate re-arm, and that path can silently fail, leaving the connection
# permanently unresponsive with no crash, no error log, and no self-recovery.
# See specs/plans/ejabberd-throughput-benchmarking.md (pyobs-core repo) for
# the full investigation. Confirmed live on iag50 (2026-07-28): raising
# these values to match what's already been running fine for a long time at
# monet-south made the bug unreachable in a reproduction that failed
# reliably every time under the stock defaults. This doesn't fix the
# underlying ejabberd bug (not yet reported upstream) -- it just keeps
# real fleet traffic from ever triggering the shaper throttle that exposes
# it.
yq eval -i '.shaper.normal.rate = 30000' "$CONFIG"
yq eval -i '.shaper.normal.burst_size = 200000' "$CONFIG"
yq eval -i '.shaper.fast = 2000000' "$CONFIG"
echo "Raised shaper.normal to rate=30000/burst_size=200000 and shaper.fast to 2000000 (matching monet-south)"

# --- 6b. Route this host onto the fast c2s shaper -------------------------
# Belt-and-braces on top of the step 6 baseline raise above: rather than
# relying solely on the higher "normal" rate for everyone, this also
# matches the host by its vhost domain (acl `server`) and routes it
# specifically onto the (now also raised) "fast" shaper. Accumulates hosts
# across multiple script runs (append, dedup) so running this for a second
# pyobs vhost adds to the same ACL rather than overwriting it.
yq eval -i '.acl.pyobs_modules.server = (((.acl.pyobs_modules.server // []) + ["'"$NEW_HOST"'"]) | unique)' "$CONFIG"

# shaper_rules acts like access_rules: first ACL match wins. "fast" must
# therefore be listed before "normal: all", or every host -- including
# this one -- would match "all" first and never reach the fast rule.
# Rewriting the whole map (rather than appending a key) guarantees that
# order regardless of what yq's key-insertion behavior would otherwise do.
yq eval -i '.shaper_rules.c2s_shaper = {
    "none": "admin",
    "fast": "pyobs_modules",
    "normal": "all"
}' "$CONFIG"

echo "Routed $NEW_HOST onto the fast c2s shaper (acl: pyobs_modules)"

restore_perms

# --- 7. Validate ----------------------------------------------------------
if yq eval '.' "$CONFIG" >/dev/null 2>&1; then
    echo "YAML syntax OK"
else
    echo "YAML syntax check failed — restoring backup" >&2
    cp "$BACKUP" "$CONFIG"
    restore_perms
    exit 1
fi

cat <<EOF

Config updated. Restarting ejabberd to apply changes...
EOF

# --- 8. Restart ejabberd and wait until it's responsive -------------------
systemctl restart ejabberd

up=false
for i in {1..30}; do
    if ejabberdctl status &>/dev/null; then
        up=true
        break
    fi
    sleep 1
done

if [[ "$up" != true ]]; then
    echo "ejabberd did not come up with the new config — rolling back to backup" >&2
    cp "$CONFIG" "${CONFIG}.broken"
    cp "$BACKUP" "$CONFIG"
    chown "$ORIG_OWNER" "$CONFIG"
    chmod "$ORIG_MODE" "$CONFIG"
    systemctl restart ejabberd
    for i in {1..30}; do
        if ejabberdctl status &>/dev/null; then
            echo "Rolled back successfully — ejabberd is running the pre-change config again." >&2
            echo "New config is broken; check: sudo journalctl -xeu ejabberd.service -n 50" >&2
            echo "Failed config left at: ${CONFIG}.broken" >&2
            exit 1
        fi
        sleep 1
    done
    echo "Rollback also failed to bring ejabberd up — manual intervention needed." >&2
    echo "  sudo journalctl -xeu ejabberd.service -n 50" >&2
    exit 1
fi

echo "ejabberd is up."

# --- 9. Shared roster group: all users visible to all users --------------
# Idempotent: srg_create/srg_user_add overwrite/no-op cleanly on re-run.
ejabberdctl srg_create all "$NEW_HOST" all all all
ejabberdctl srg_user_add @all@ "$NEW_HOST" all "$NEW_HOST"

cat <<EOF

Done. Shared roster group "all" created on $NEW_HOST with all users added.

If you need to double check the listener:
  ss -tlnp | grep -E '5280|5281'
EOF
