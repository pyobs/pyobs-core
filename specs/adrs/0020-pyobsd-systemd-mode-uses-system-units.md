# pyobsd's systemd mode uses system units, not user units

status: accepted
date: 2026-11-26

## Context and Problem Statement

pyobsd gets a systemd mode (`specs/plans/2026-11-25-pyobsd-systemd-mode.md`): every module runs as an
instance of a template unit `pyobs@.service`. The modules run as the pyobs user. pyobsd (as root or as pyobs)
and pyobs-web-admin (as pyobs) must be able to start, stop and restart them. The units can live in the pyobs
user's own systemd instance (user units) or in the system instance (system units).

## Considered Options

1. **User units** in `~pyobs/.config/systemd/user/`, managed with `systemctl --user` by the pyobs user, kept
   running without a login by `loginctl enable-linger pyobs`.
2. **System units** in `/etc/systemd/system/` with `User=`/`Group=`, start/stop/restart allowed to the pyobs
   user by a polkit rule restricted to `pyobs@*.service`.
3. System units, with access through sudo rules.

## Decision Outcome

Option 2.

User units looked simpler, since pyobs could manage them without any extra permissions. They have
three problems:

- They only run while the user's systemd instance (`user@<uid>.service`) runs. Without linger, that
  instance only lives while a session is open. A check on a host showed that `systemctl --user -M pyobs@`
  as root starts it for that one call, and it stops about 15 s later, together with every unit in it. So
  linger is required. A missing linger would not show up as an error on start: the modules would just end
  again.
- On a reboot, `user@<uid>.service` is stopped with its own `TimeoutStopSec` (2 min on Debian 13), so a
  camera's warm-up is cut after 2 min, unless the host gets a root drop-in for `user@<uid>.service`.
- They can't be ordered after system targets like `network-online.target`.

System units have none of these. Their cost is permissions: starting and stopping needs root or polkit,
and writing the unit and changing the enable state need root. That's handled by:

- a polkit rule that lets the pyobs user run start/stop/restart/kill only on `pyobs@*.service`;
- a systemd generator, installed once by root, that creates the boot-time wants links from the config
  file names, so no `systemctl enable`/`disable` is ever needed;
- writing the unit, generator and polkit rule only when pyobsd runs as root.

sudo (option 3) was rejected: wildcards in sudoers arguments also match spaces, so `systemctl start
pyobs@*` would allow any unit. It can be made tight (regex arguments in sudo >= 1.9.10, or a root-owned
wrapper), but polkit restricts by unit name directly, and pyobs can call `systemctl` without a wrapper.

## Consequences

- Hosts need polkitd installed (not on most hosts so far) and the pyobs user in `systemd-journal` to read
  the logs.
- Activating or deactivating a module (renaming its config) changes its boot behavior through the generator,
  at the next boot or `daemon-reload`. Starting or stopping it right away is a separate call, as today.
- The generator runs early at boot and reads the config directory, so that has to be on the root file
  system (true on all hosts checked).
- A reboot still cuts a long shutdown after the shutdown targets' `JobTimeoutSec` (30 min on Debian 13),
  unless that is raised with a drop-in.
- systemd passes `unit` and `verb` to polkit for `org.freedesktop.systemd1.manage-units`, so the rule can
  restrict by both (checked on a host with systemd 257, see the plan).
