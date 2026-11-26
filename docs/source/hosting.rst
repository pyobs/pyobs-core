.. _hosting:

Running modules on a host
=========================

:program:`pyobsd` starts and stops the modules on a host, in one of two modes. :program:`pyobsd setup` sets up the host
for either of them (see :ref:`installing-setup` for the first setup and :ref:`cli-pyobsd-setup` for all options). The
commands are the same in both modes, see :ref:`cli-pyobsd`.

.. _hosting-modes:

Which mode?
-----------

:systemd:
    Every module runs as an instance of the systemd unit **pyobs@.service**. systemd starts the enabled modules at
    boot (after the network and a local ejabberd), restarts a module after an error, waits for a module that needs
    long to shut down (e.g. a cooled camera warming up), and writes everything a module prints to the journal,
    including tracebacks and output of C libraries. The user running the modules can start and stop them without
    root. Recommended for new hosts.

:pid:
    :program:`pyobsd` starts the modules as background processes and keeps their PIDs in the *run* directory. Nothing
    starts them at boot and nothing restarts them after an error. Use it on hosts without systemd, for development,
    and, for now, on hosts managed by *pyobs-web-admin*: it can't start modules in systemd mode yet.

The mode is set in the **pyobsd** section of :file:`/etc/pyobs.yaml`, which :program:`pyobsd setup` writes. Don't put
it into :file:`~/.config/pyobs.yaml`, that would only apply to one user (see :ref:`cli-config-file`).

.. _hosting-systemd:

Requirements of the systemd mode
--------------------------------

- **polkitd** (``apt install polkitd``). :program:`pyobsd setup` installs a polkit rule that lets the module user
  start, stop, restart and kill ``pyobs@*.service``, and nothing else. Without polkitd, only root can do that. Setup
  warns if polkitd is missing, but doesn't install it.
- The module user is added to the group **systemd-journal** by setup, so that ``pyobsd logs`` can read the logs of
  the modules. A login session of that user that is already open only gets the group after logging in again.
- **Cooled cameras:** on a reboot or poweroff, systemd waits for the modules to stop, also for a camera warming up.
  But on Debian 13, a reboot is forced after 30 minutes. On a host with cooled cameras, answer the question about
  them in setup (or use ``--shutdown-timeout <minutes>``), so it raises that limit (default 60 minutes).
- Module names must be valid unit names: letters, digits and ``_.:-``. Setup warns about config files with other
  names, :program:`pyobsd` skips them.

.. _hosting-switch:

Switching a host to the systemd mode
------------------------------------

1. Stop the modules, still in PID-file mode::

    pyobsd stop

2. Install polkitd, if it's missing::

    apt install polkitd

3. Run setup and answer **systemd** (and the question about cooled cameras)::

    sudo pyobsd setup

   If an old *pyobs.service* is still enabled, setup reports it. Disable it, otherwise it starts the modules a
   second time at boot::

    systemctl disable --now pyobs.service

4. Start the enabled modules::

    pyobsd start

Modules that still run in PID-file mode are refused by ``pyobsd start``, and ``pyobsd status`` shows them as
**running (pid mode)**, so a half-switched host is visible.

To switch back, stop the modules and run ``sudo pyobsd setup --mode pid``. It removes the unit, the generator, the
polkit rule and the shutdown drop-ins, so a reboot doesn't start the modules as units anymore, and refuses that while
modules still run as units. :file:`/etc/pyobs.yaml`, the user, its membership in **systemd-journal** and the
directories stay.

Run setup again after moving *pyobs* to another virtual environment: the unit runs the :program:`pyobsd` that setup
was started with. Every other :program:`pyobsd` call warns if the installed files differ from what setup would
write, e.g. after an update that changed them.

.. _hosting-unattended:

Setup from a deploy script
--------------------------

Every question of :program:`pyobsd setup` has an option. With **-y**, or if stdin isn't a terminal, nothing is asked
and options not given take their default (the current value, else the built-in default)::

    pyobsd setup --mode systemd --user pyobs --create-user --path /opt/pyobs --shutdown-timeout 60 -y

Without **--create-user**, a missing user is an error. The exit code is 0 if the host is set up and 1 on an error.
With **--strict**, warnings (e.g. polkitd missing) give 1, too, but the changes are still made. Setup only changes
what differs, so it's safe to run it on every deploy.

.. _hosting-troubleshooting:

Troubleshooting
---------------

``pyobsd status`` shows the state of every module, ``pyobsd logs <module>`` its log (``-f`` to follow it).

A module stays **starting**:
    It hasn't finished opening yet. Most often it can't reach the XMPP server (see
    :ref:`installing-ejabberd`). It keeps trying: after two minutes, systemd stops it and starts it again ten seconds
    later, until the server is back.

A module is **failed**:
    It stopped after an error, see its log. systemd starts it again after ten seconds, shown as
    "failed (restarting)". After five failed starts within five minutes, systemd gives up. Once the error is fixed,
    start it again with ``pyobsd start <module>``, which also resets that counter.

A module isn't started at boot:
    Its config file starts with an underscore, or its name isn't a valid unit name. Renaming the config file takes
    effect at the next boot, no ``systemctl enable`` needed.

``pyobsd stop`` takes long:
    A module asked for more time to shut down, e.g. a camera warming up. ``pyobsd status`` shows how long it may
    still take. ``pyobsd stop --kill`` stops it right away, but cuts the warm-up.
