.. _installing:

Installing pyobs
================

A *pyobs* installation consists of an XMPP server, through which all modules talk to each other, and one or more
hosts that run the modules. This page shows how to set up both on Linux. A computer that only runs *pyobs-gui* needs
neither, see :doc:`quickstart`.

The steps for a host running modules are:

1. Set up an XMPP server, if you don't have one yet (:ref:`installing-ejabberd`).
2. Install *pyobs* into a virtual environment (:ref:`installing-pyobs`).
3. Run :program:`pyobsd setup` to set up the host (:ref:`installing-setup`).
4. Put the module configs into the *config* directory and start them (:ref:`installing-modules`).

.. _installing-ejabberd:

Setting up ejabberd
-------------------
In case you already have a working XMPP server, skip this step.

Automated setup
~~~~~~~~~~~~~~~~
On Debian and Ubuntu, :file:`scripts/xmpp/install-ejabberd.sh` in the *pyobs-core* repository installs and configures
ejabberd. Run it as root on the machine that will host ejabberd::

    sudo ./scripts/xmpp/install-ejabberd.sh <hostname>

It:

- installs ejabberd (package *ejabberd-contrib*) if it's missing, and *yq* for editing the config,
- adds the host name to ``hosts`` (run it again with another name to add a second vhost),
- adds an HTTP API listener on 127.0.0.1:5281 for *pyobs-web-admin*, with a read-only permission rule,
- adds an XMPP-over-WebSocket listener on 127.0.0.1:5282, meant to sit behind a reverse proxy,
- raises the shaper limits and puts the clients of this host on the fast shaper. With the default limits, a fleet of
  modules starting together can run into `an ejabberd bug <https://github.com/processone/xmpp>`__ where a throttled
  connection stops reading (see :ref:`xmpp-diagnostics`),
- restarts ejabberd, and restores the old config if ejabberd doesn't come up with the new one.

It edits :file:`/etc/ejabberd/ejabberd.yml` in place, backing it up first, and is safe to run again. It doesn't
create the shared roster group or any users, so steps 4 and 5 below are still needed.

Manual setup
~~~~~~~~~~~~
1. Install ejabberd, e.g. ``apt install ejabberd`` on Debian and Ubuntu, or from
   https://www.process-one.net/en/ejabberd/downloads/.

2. Raise the shaper limits in :file:`/etc/ejabberd/ejabberd.yml` and use the fast one for the clients of your host
   (replace <host> with its name)::

    shaper:
      normal:
        rate: 30000
        burst_size: 200000
      fast: 2000000

    acl:
      pyobs_modules:
        server:
          - <host>

    shaper_rules:
      c2s_shaper:
        none: admin
        fast: pyobs_modules
        normal: all

3. Restart ejabberd::

    systemctl restart ejabberd

4. Add a shared roster group, so that all clients are in each others roster::

    ejabberdctl srg_create all <host> all all all
    ejabberdctl srg_user_add @all@ <host> all <host>

5. Register a user for each module, e.g.::

    ejabberdctl register <name> <host> <password>

Troubleshooting: module hangs at "Opening module..."
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If a module logs ``Opening module...`` and never reaches ``Started successfully.``, it can't connect to the XMPP
server. If the server is running and not configured for TLS, this is usually a STARTTLS mismatch between pyobs' XMPP
client and ejabberd. Find ``starttls_required: true`` under the ``listen:`` section of :file:`ejabberd.yml` and set it
to ``false``, or configure TLS on both ends (``use_tls`` in the module's ``comm`` section).

In systemd mode, such a module shows up as **starting** and is restarted every two minutes or so, until it can
connect, see :ref:`hosting-troubleshooting`.

For other XMPP problems, e.g. a module that doesn't find its peers, capability fetches timing out, or to see what's
on the pubsub bus, see :ref:`xmpp-diagnostics`.

.. _installing-pyobs:

Install pyobs
-------------
Install *pyobs* into a virtual environment. The recommended place is :file:`/opt/pyobs/venv`, next to the directories
that :program:`pyobsd setup` creates::

    python3 -m venv /opt/pyobs/venv
    /opt/pyobs/venv/bin/pip install "pyobs-core[full]"

On a host that runs modules, always install the **full** extra. The plain ``pyobs-core`` is meant for computers that
only run *pyobs-gui*, many modules don't work without the packages in **full**.

Install the plugins you need (e.g. *pyobs-asi*, *pyobs-brot*, ...) the same way. Some drivers need Python bindings
that only come as system packages, e.g. *pyobs-aravis* needs PyGObject (``python3-gi``). In that case, create the
virtual environment with ``python3 -m venv --system-site-packages /opt/pyobs/venv``. See the plugin's README.

To have :program:`pyobs` and :program:`pyobsd` in the default ``PATH`` (also for ``sudo``), link them::

    ln -s /opt/pyobs/venv/bin/pyobs /opt/pyobs/venv/bin/pyobsd /usr/local/bin/

If you need the latest development version, install it from the repository instead::

    git clone https://github.com/pyobs/pyobs-core.git
    /opt/pyobs/venv/bin/pip install "./pyobs-core[full]"

You now have the :program:`pyobs` (see :ref:`cli-pyobs`) and :program:`pyobsd` (see :ref:`cli-pyobsd`) executables.

.. _installing-setup:

Set up the host
---------------
:program:`pyobsd` starts and stops the modules on a host (see :ref:`cli-pyobsd`). Set up the host for it as root::

    sudo pyobsd setup

It asks for the mode, the user to run the modules as (default **pyobs**, created if you confirm it), the base path
(default **/opt/pyobs**) and how to log. Then it shows what it will do and asks before doing it. It creates the
directories *config*, *log*, *run* and *storage* in the base path, owned by that user, and writes the answers into
the **pyobsd** section of :file:`/etc/pyobs.yaml`. It can be run again at any time, e.g. to change an answer or after a
*pyobs* update.

The mode decides how the modules run:

- **systemd**: every module runs as a systemd unit. systemd starts the modules at boot, restarts them after an error,
  and their logs go to the journal. Recommended for new hosts.
- **pid**: :program:`pyobsd` starts the modules as background processes and keeps their PIDs in *run*. Use it on hosts
  without systemd, for development, and, for now, on hosts managed by *pyobs-web-admin*, which can't start modules
  in systemd mode yet.

For the systemd mode, install polkitd first (``apt install polkitd``), otherwise only root can start and stop
modules. See :doc:`hosting` for what each mode needs, how to switch a host, and how to run setup from a deploy
script. All options of :program:`pyobsd setup` are in :ref:`cli-pyobsd-setup`.

Keep the mode in :file:`/etc/pyobs.yaml`, as setup writes it. A :file:`~/.config/pyobs.yaml` would be used instead
(see :ref:`cli-config-file`), and setup warns if there is one.

.. _installing-modules:

Add modules
-----------
Every YAML file in the *config* directory is a module, named after the file: **camera.yaml** is the module
**camera**. *config* can also be a symlink, e.g. into a git repository with the configs of your observatory.

A module whose file name starts with an underscore (**_camera.yaml**) is disabled: :program:`pyobsd start` without a
module name doesn't start it, and in systemd mode it isn't started at boot. Named explicitly, it can still be started:
``pyobsd start camera`` in systemd mode, ``pyobsd start _camera`` in PID-file mode.

Start all enabled modules and check them::

    pyobsd start
    pyobsd status

In systemd mode, ``pyobsd logs <module>`` shows a module's log. In PID-file mode, logs go to the journal too (with
**syslog**), and to *log* with **--file-log**.
